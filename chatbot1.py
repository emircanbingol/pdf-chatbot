import faiss
import pickle
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import os
import json 

# Load environment variable for API key
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load model and FAISS index
model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.read_index("gradio_index.index")

# Load original chunks
with open("gradio_chunks.pkl", "rb") as f:
    chunks = pickle.load(f)

# Prompt format
BASE_PROMPT = """Below are pieces of content taken from a PDF. Based on these contents, answer the question as clearly and briefly as possible. Don't guess, just comment according to the data in the content.

CONTENT:
{context}

QUESTION: {question}
"""
# --- Load symbol chunks (symbol_chunks.json)
def load_symbol_chunks(path="symbol_chunks.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

symbol_chunks = load_symbol_chunks()


def get_answer(query, top_k=5):
    # 🧠 YENİ: Her seferinde FAISS ve chunks dosyasını yükle
    index = faiss.read_index("gradio_index.index")
    with open("gradio_chunks.pkl", "rb") as f:
        chunks = pickle.load(f)

    query_vec = model.encode(query).reshape(1, -1)
    scores, indices = index.search(query_vec, top_k)
    selected_chunks = [chunks[i] for i in indices[0] if i < len(chunks)]

    # Sabit ek açıklamalar da dahil et
    all_context_chunks = selected_chunks + [s["content"] for s in symbol_chunks]
    context_text = "\n\n".join(all_context_chunks)

    prompt = BASE_PROMPT.format(context=context_text, question=query)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    question = input("Soru: ")
    answer = get_answer(question)
    print("\nCEVAP:\n", answer)