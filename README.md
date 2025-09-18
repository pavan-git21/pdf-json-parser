# pdf-json-parser

**Objective**

The goal of this project is to design and implement a Python-based program that can read a PDF file and convert its contents into a well-structured JSON format.
Instead of extracting plain text, the program aims to preserve the logical hierarchy of the document such as pages, sections, sub-sections, paragraphs, tables, and charts/images.
This structured JSON output can be further used in data analytics, search engines, or knowledge management systems.
Requirements
**Input & Output**

•	Input: A PDF file (e.g., financial reports, fact sheets, research papers).
•	Output: A JSON file that organizes extracted content into a clear structure with types like paragraph, table, chart.
**Libraries Used**

1.	pdfplumber → for extracting text and simple tables.
2.	PyMuPDF (fitz) → for extracting images and handling layout.
3.	streamlit  → for creating a user interface.
4.	camelot (optional) → for advanced table extraction.
**Methodology**

The project follows a modular approach, where each step of PDF parsing is handled separately:
1.	Text & Paragraph Extraction
o	Text is extracted using pdfplumber.
o	Heuristics are applied to split text into paragraphs by checking line breaks, sentence endings, and spacing.
2.	Heading & Section Detection
o	Font size and capitalization are analyzed to identify sections and sub-sections.
o	Example: Larger font or uppercase lines are treated as section headers.
3.	Table Extraction
o	Tables are identified using pdfplumber’s built-in table detection.
o	Optionally, camelot is used for more accurate extraction of complex tables.
4.	Chart/Image Extraction
o	Images (likely charts or figures) are extracted using PyMuPDF.
o	They are saved as separate PNG files and referenced inside the JSON output.
5.	JSON Structuring
o	Each page is represented as an object in JSON.
o	Inside each page, content is divided into paragraph, table, or chart.
o	Section headers are linked to paragraphs when possible.
**JSON Structure (Example)**

{
  "pages": [
    {
      "page_number": 1,
      "content": [
        {
          "type": "paragraph",
          "section": "Introduction",
          "sub_section": "Background",
          "text": "This project demonstrates how PDF content can be structured..."
        },
        {
          "type": "table",
          "section": "Financial Data",
          "description": null,
          "table_data": [
            ["Year", "Revenue", "Profit"],
            ["2022", "$10M", "$2M"],
            ["2023", "$12M", "$3M"]
          ]
        },
        {
          "type": "chart",
          "section": "Performance Overview",
          "description": "Chart showing revenue growth over years",
          "image_path": "extracted_images/p1_img_0.png",
          "width": 1200,
          "height": 600
        }
      ]
    }
  ]
}


**Conclusion**

This project successfully demonstrates how a PDF file can be transformed into a machine-readable JSON format while preserving the document hierarchy and content types.
The solution can:
•	Extract clean text paragraphs,
•	Detect and store tables,
•	Capture charts/images for reference,
•	Organize everything in a structured JSON.
Such a system is highly valuable for businesses, researchers, and developers who need to convert unstructured documents into structured data for analytics, automation, and search applications.



