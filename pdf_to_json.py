import os
import json
import argparse
from typing import List, Dict, Any, Optional
import io
import pdfplumber
import fitz

try:
    import camelot
    _HAS_CAMELOT = True
except Exception:
    _HAS_CAMELOT = False


def save_image_bytes(img_bytes: bytes, out_dir: str, prefix: str, idx: int) -> str:
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{prefix}_img_{idx}.png"
    path = os.path.join(out_dir, filename)
    with open(path, "wb") as f:
        f.write(img_bytes)
    return path


def extract_images_with_fitz(pdf_path: str, images_out: str) -> Dict[int, List[Dict[str, Any]]]:
    doc = fitz.open(pdf_path)
    page_images = {}
    for i in range(len(doc)):
        page = doc[i]
        images = page.get_images(full=True)
        img_list = []
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            img_path = save_image_bytes(image_bytes, images_out, f"p{i+1}", img_index)
            w = base_image.get("width")
            h = base_image.get("height")
            img_list.append({
                "path": img_path,
                "width": w,
                "height": h,
                "xref": xref,
                "description": None
            })
        page_images[i + 1] = img_list
    doc.close()
    return page_images


def detect_headings_from_chars(page) -> List[Dict[str, Any]]:
    headings = []
    try:
        chars = page.chars
        if not chars:
            return headings
        sizes = [c.get("size", 0) for c in chars]
        if not sizes:
            return headings
        avg = sum(sizes) / len(sizes)
        lines = {}
        for c in chars:
            line_key = int(round(c.get("top", 0)))
            lines.setdefault(line_key, []).append(c)
        for top, chs in lines.items():
            line_text = "".join([c.get("text", "") for c in chs]).strip()
            line_size = sum([c.get("size", 0) for c in chs]) / len(chs)
            if not line_text:
                continue
            uppercase_ratio = sum(1 for ch in line_text if ch.isupper()) / max(1, len(line_text))
            if (line_size >= avg * 1.15 and len(line_text) < 200) or (uppercase_ratio > 0.6 and len(line_text) < 120):
                headings.append({
                    "text": line_text,
                    "font_size": line_size,
                    "top": top
                })
    except Exception:
        pass
    return headings


def split_paragraphs_from_text(full_text: str) -> List[str]:
    if not full_text:
        return []
    txt = full_text.replace("\r", "\n")
    paras = [p.strip() for p in txt.split("\n\n") if p.strip()]
    if len(paras) > 1:
        return paras
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    grouped = []
    current = ""
    for ln in lines:
        if current == "":
            current = ln
        else:
            if current.endswith("-") or (len(current) < 100 and not current.endswith(('.', '?', '!', ':'))):
                current = current + " " + ln
            else:
                if ln and ln[0].isupper() and len(current) > 40:
                    grouped.append(current.strip())
                    current = ln
                else:
                    current = current + " " + ln
    if current:
        grouped.append(current.strip())
    return grouped


def extract_tables_pdfplumber(page) -> List[List[List[str]]]:
    tables = []
    try:
        tbs = page.extract_tables()
        for tb in tbs:
            cleaned = []
            for row in tb:
                cleaned.append([("" if cell is None else str(cell).strip()) for cell in row])
            tables.append(cleaned)
    except Exception:
        pass
    return tables


def extract_tables_camelot(pdf_path: str, page_number: int) -> List[List[List[str]]]:
    results = []
    if not _HAS_CAMELOT:
        return results
    try:
        tables = camelot.read_pdf(pdf_path, pages=str(page_number), flavor='stream')
        for t in tables:
            df = t.df
            results.append(df.values.tolist())
    except Exception:
        pass
    return results


def parse_pdf_to_json(pdf_path: str, images_out: Optional[str] = None, use_camelot: bool = False) -> Dict[str, Any]:
    result = {"pages": []}
    images_map = {}
    if images_out:
        images_map = extract_images_with_fitz(pdf_path, images_out)
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_entry: Dict[str, Any] = {
                "page_number": i,
                "content": []
            }
            headings = detect_headings_from_chars(page)
            text = page.extract_text(x_tolerance=1, y_tolerance=1) or ""
            paragraphs = split_paragraphs_from_text(text)
            section_map = []
            if headings:
                headings_sorted = sorted(headings, key=lambda h: h["top"])
                for h in headings_sorted:
                    section_map.append({"section": h["text"], "paragraphs": []})
                if section_map:
                    remaining_paras = paragraphs.copy()
                    for si, sec in enumerate(section_map):
                        if remaining_paras:
                            sec["paragraphs"].append(remaining_paras.pop(0))
                    if remaining_paras:
                        section_map[-1]["paragraphs"].extend(remaining_paras)
            else:
                for p in paragraphs:
                    page_entry["content"].append({
                        "type": "paragraph",
                        "section": None,
                        "sub_section": None,
                        "text": p
                    })
            if section_map:
                for sec in section_map:
                    for p in sec["paragraphs"]:
                        page_entry["content"].append({
                            "type": "paragraph",
                            "section": sec["section"],
                            "sub_section": None,
                            "text": p
                        })
            page_tables = []
            if use_camelot:
                page_tables = extract_tables_camelot(pdf_path, i)
            if not page_tables:
                page_tables = extract_tables_pdfplumber(page)
            for t in page_tables:
                page_entry["content"].append({
                    "type": "table",
                    "section": None,
                    "description": None,
                    "table_data": t
                })
            imgs = images_map.get(i, [])
            for idx, im in enumerate(imgs):
                desc = "chart" if (im.get("width") and im.get("height") and (im["width"] * im["height"] > 150000)) else "image"
                page_entry["content"].append({
                    "type": "chart" if desc == "chart" else "image",
                    "section": None,
                    "description": None,
                    "image_path": im["path"],
                    "width": im.get("width"),
                    "height": im.get("height")
                })
            result["pages"].append(page_entry)
    return result


def main():
    parser = argparse.ArgumentParser(description="PDF -> structured JSON extractor")
    parser.add_argument("pdf", help="input PDF file path")
    parser.add_argument("json_out", help="output JSON file path")
    parser.add_argument("--images-dir", default="extracted_images", help="directory to save images")
    parser.add_argument("--use-camelot", action="store_true", help="use camelot for tables (optional)")
    args = parser.parse_args()
    pdf_path = args.pdf
    json_out = args.json_out
    images_dir = args.images_dir
    print(f"Parsing PDF: {pdf_path}")
    parsed = parse_pdf_to_json(pdf_path, images_out=images_dir, use_camelot=args.use_camelot)
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON -> {json_out}")
    print(f"Saved images (if any) -> {images_dir}")


if __name__ == "__main__":
    main()
