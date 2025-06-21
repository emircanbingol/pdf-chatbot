import fitz  # PyMuPDF

def extract_text_by_page(pdf_path):
    doc = fitz.open(pdf_path)
    all_chunks = []

    for page_number, page in enumerate(doc, start=1):
        text = page.get_text()
        paragraphs = text.split("\n\n")

        for para in paragraphs:
            sentences = para.split(". ")
            for i in range(len(sentences)):
                chunk = ". ".join(sentences[max(0, i - 1): i + 1]).strip()
                if len(chunk) > 30:
                    all_chunks.append({
                        "content": chunk,
                        "page": page_number
                    })

    return all_chunks
