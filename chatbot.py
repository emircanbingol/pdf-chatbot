import faiss
import pickle
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import os
import json

from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

model = SentenceTransformer("all-MiniLM-L6-v2")

def load_faiss_and_chunks():
    index = faiss.read_index("gradio_index.index")
    with open("gradio_chunks.pkl", "rb") as f:
        chunks = pickle.load(f)
    return index, chunks

def load_symbol_chunks(path="symbol_chunks.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

symbol_chunks = load_symbol_chunks()

# Yeni prompt: sadece son konuşma çifti dikkate alınır
TURN_PROMPT = """You are a helpful assistant. Always include the PDF filename (source) that the answer was based on. Do not guess or fabricate information. Only answer based on the content and indicate the file name.


Previous Q&A:
User: {last_user_msg}
Assistant: {last_bot_msg}

Now the user says:
"{query}"

Using this context and the content below, answer clearly and only based on the relevant material.

CONTENT:
{context}
"""

def get_answer(query, chat_history=[], top_k=5):
    # Chat history'den son user + bot mesajını al
    last_user_msg = ""
    last_bot_msg = ""
    if len(chat_history) >=1:
        last_user_msg = chat_history[-1]["user"]
        last_bot_msg = chat_history[-1]["bot"]

    index, chunks = load_faiss_and_chunks()

    query_vec = model.encode(query).reshape(1, -1)
    scores, indices = index.search(query_vec, top_k)
    selected_chunks = [chunks[i] for i in indices[0] if i < len(chunks)]
    selected_text = "\n\n".join(
    f"{chunk['text']}\n(Source: {chunk['source']})"
    for chunk in selected_chunks
)
    symbol_text = "\n\n".join(
    s["content"] for s in symbol_chunks
)   
    context_text = selected_text + "\n\n" + symbol_text

    #all_context_chunks = selected_chunks + [s["content"] for s in symbol_chunks]
    #context_text = "\n\n".join(all_context_chunks)
    prompt = TURN_PROMPT.format(
        last_user_msg=last_user_msg,
        last_bot_msg=last_bot_msg,
        query=query,
        context=context_text
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    history = []
    while True:
        question = input("Soru: ")
        response = get_answer(question, history)
        print("\nBot:", response)
        history.append({"user": question, "bot": response})
