import os
import json
from PyPDF2 import PdfReader
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_and_symbolize(pdf_path, chunk_path):
    reader = PdfReader(pdf_path)
    chunks = []

    for i in range(0, len(reader.pages), 2):  # Her 2 sayfada bir
        text = ""
        for j in range(i, min(i+2, len(reader.pages))):
            page = reader.pages[j]
            text += page.extract_text() + "\n"

        prompt = f"""
You are analyzing pages {i+1}-{i+2} of an academic PDF.

1. Summarize the key ideas clearly.
2. Identify and explain possible abbreviations (like "FP", "GT").
3. Output as a detailed study chunk.

Text:
{text}
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful educational assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        content = response.choices[0].message.content.strip()
        chunks.append({
            "chunk_id": f"symbol_summary_{i//2+1}",
            "content": content,
            "source": os.path.basename(pdf_path)  # 👈 kaynak dosya adı eklendi
        })

    # JSON olarak kaydet
    with open(chunk_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"✅ {len(chunks)} symbol/summary chunks saved to {chunk_path}")

if __name__ == "__main__":
    pdf_path = "E:/GRAD/FP strategy-ss20-s.pdf"
    chunk_path = "E:/GRAD/symbol_chunks.json"

    summarize_and_symbolize(pdf_path, chunk_path)
