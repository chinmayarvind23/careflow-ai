def parse_document(extracted: dict) -> dict:
    pages = extracted["pages"]
    merged_text = extracted["merged_text"]

    parsed_sections = {
        "page_text": {str(p["page_number"]): p["text"] for p in pages},
        "merged_text": merged_text,
        "page_count": len(pages),
    }

    return parsed_sections