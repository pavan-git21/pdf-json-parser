import streamlit as st
import json
import tempfile
import os
from pdf_to_json import parse_pdf_to_json

st.set_page_config(page_title="PDF → JSON extractor", layout="wide")

st.title("PDF → Structured JSON extractor")

uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
use_camelot = st.checkbox("Use Camelot for tables (requires Ghostscript)", value=False)

if uploaded:
    st.info("Parsing PDF — this may take a few seconds for large files.")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    images_dir = os.path.join(tempfile.gettempdir(), "pdf_images")
    os.makedirs(images_dir, exist_ok=True)

    parsed = parse_pdf_to_json(tmp_path, images_out=images_dir, use_camelot=use_camelot)
    st.success("Parsing complete.")

    st.header("Preview JSON (first page)")
    if parsed.get("pages"):
        st.json(parsed["pages"][0])
    else:
        st.write("No pages detected.")

    st.download_button(
        "Download full JSON",
        data=json.dumps(parsed, ensure_ascii=False, indent=2),
        file_name="parsed_pdf.json",
        mime="application/json"
    )

    # list extracted images
    imgs = []
    for p in parsed["pages"]:
        for c in p["content"]:
            if c["type"] in ("chart", "image") and c.get("image_path"):
                imgs.append(c["image_path"])
    if imgs:
        st.header("Extracted images / charts")
        for im in imgs:
            try:
                st.image(im, use_container_width=True)
            except Exception:
                st.write(im)
