import os
import pickle
import faiss
from pdfminer.high_level import extract_text
from sentence_transformers import SentenceTransformer
import tempfile
from google.cloud import storage
from dotenv import load_dotenv

UPLOAD_DIR = "uploaded_pdfs"

load_dotenv()

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

def embed_all_pdfs():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    dim = model.get_sentence_embedding_dimension()
    index = faiss.IndexFlatL2(dim)
    chunks = []

    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    blobs = bucket.list_blobs()

    for blob in blobs:
        print(f"🔍 Blob found: {blob.name}")  # <--- Ekle bun
        if not blob.name.endswith(".pdf"):
            continue

        print(f"📄 Processing from GCS: {blob.name}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            blob.download_to_filename(temp_file.name)
            text = extract_text(temp_file.name)
            print(f"🔍 Extracted text sample from {blob.name[:40]}: {text[:300]}")

        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 10]

        for para in paragraphs:
            vec = model.encode(para)
            index.add(vec.reshape(1, -1))
            chunks.append({
                "text": para,
                "source": blob.name
})

    if len(chunks) == 0:
        print("⚠️ No content found in PDFs.")
        return

    faiss.write_index(index, "gradio_index.index")
    with open("gradio_chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)

    print(f"✅ {len(chunks)} chunks embedded from GCS PDFs.")

# Manuel çalıştırmak için:
if __name__ == "__main__":
    embed_all_pdfs()
