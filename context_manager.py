from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

def get_relevant_history(chat_history, current_question, top_k=3):
    past_messages = [msg["content"] for msg in chat_history if msg["role"] == "user"]
    if not past_messages:
        return []

    # Embed geçmiş ve yeni soru
    embeddings = model.encode(past_messages + [current_question])
    query_vec = embeddings[-1]
    past_vecs = embeddings[:-1]

    # Benzerliği hesapla
    similarities = util.cos_sim(query_vec, past_vecs)[0]
    scored = list(zip(past_messages, similarities))
    scored.sort(key=lambda x: x[1], reverse=True)

    relevant = [text for text, score in scored[:top_k] if score > 0.5]
    return relevant
