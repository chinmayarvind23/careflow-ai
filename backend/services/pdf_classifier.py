import fitz  # PyMuPDF


def classify_pdf(pdf_path: str) -> dict:
    """
    Heuristic classification:
    - digital: most pages have extractable text
    - scanned: most pages have almost no text but do have images
    - mixed: mixture of both
    """
    doc = fitz.open(pdf_path)

    page_stats = []
    text_pages = 0
    image_pages = 0

    for page in doc:
        text = page.get_text("text", sort=True).strip()
        images = page.get_images(full=True)

        text_len = len(text)
        has_text = text_len > 40
        has_images = len(images) > 0

        if has_text:
            text_pages += 1
        if has_images:
            image_pages += 1

        page_stats.append(
            {
                "page_number": page.number + 1,
                "text_len": text_len,
                "has_text": has_text,
                "image_count": len(images),
                "has_images": has_images,
            }
        )

    total_pages = len(doc)

    if text_pages == total_pages:
        document_type = "digital"
    elif text_pages == 0 and image_pages > 0:
        document_type = "scanned"
    else:
        document_type = "mixed"

    return {
        "document_type": document_type,
        "total_pages": total_pages,
        "text_pages": text_pages,
        "image_pages": image_pages,
        "page_stats": page_stats,
    }