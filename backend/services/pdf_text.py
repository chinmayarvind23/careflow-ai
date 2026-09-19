import fitz  # PyMuPDF


def extract_pdf_text(pdf_path: str, document_type: str) -> dict:
    """
    Returns page-wise extracted text and merged text.
    Uses direct extraction for digital pages and OCR fallback for image-based pages.
    """
    doc = fitz.open(pdf_path)
    pages = []

    for page in doc:
        if document_type == "digital":
            text = page.get_text("text", sort=True)
            method = "direct_text"
        else:
            direct_text = page.get_text("text", sort=True).strip()
            if len(direct_text) > 40:
                text = direct_text
                method = "direct_text"
            else:
                # OCR fallback for image-based text
                tp = page.get_textpage_ocr()
                text = page.get_text("text", textpage=tp)
                method = "ocr"

        pages.append(
            {
                "page_number": page.number + 1,
                "method": method,
                "text": text.strip(),
            }
        )

    merged_text = "\n\n".join(
        [f"--- PAGE {p['page_number']} ---\n{p['text']}" for p in pages]
    )

    return {
        "pages": pages,
        "merged_text": merged_text,
    }