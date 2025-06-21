from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import json
from utils.chatbot import get_answer
from utils.embedder import embed_all_pdfs
from utils.context_manager import get_relevant_history
from google.cloud import storage
from dotenv import load_dotenv


load_dotenv()
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

def upload_to_gcs(file_obj, filename):
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_file(file_obj)

UPLOAD_FOLDER = "uploaded_pdfs"
ALLOWED_EXTENSIONS = {"pdf"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

chat_history = []

# Ana Sayfa
@app.route("/")
def index():
    return render_template("index.html")

# PDF Yükleme
@app.route("/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return "No file", 400

    file = request.files["file"]
    if file.filename == "":
        return "Empty filename", 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # GCS’ye yükle
        try:
            upload_to_gcs(file, filename)
            # Yükleme sonrası embed'i tetikle
            from utils.embedder import embed_all_pdfs
            embed_all_pdfs()
            return "Uploaded ✅", 200
        except Exception as e:
            return f"Upload failed: {str(e)}", 500

    return "Invalid file", 400


# PDF Listeleme
@app.route("/list_pdfs", methods=["GET"])
def list_pdfs():
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    blobs = bucket.list_blobs()
    pdfs = [blob.name for blob in blobs if blob.name.endswith(".pdf")]
    return jsonify(pdfs)

# Chat Endpoint

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    if not user_input:
        return jsonify({"response": "Soru alınamadı."})

    # Kullanıcı mesajını kaydet
    chat_history.append({"role": "user", "content": user_input})


    try:
        answer = get_answer(user_input, chat_history=convert_history(chat_history))
    except Exception as e:
        return jsonify({"response": f"Hata: {str(e)}"})

    # Bot cevabını da geçmişe ekle
    chat_history.append({"role": "bot", "content": answer})
    return jsonify({"response": answer})

# Yardımcı Fonksiyon
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_history(history):
    user_bot_pairs = []
    for i in range(1, len(history), 2):
        user_msg = history[i - 1]["content"]
        bot_msg = history[i]["content"] if i < len(history) else ""
        user_bot_pairs.append({"user": user_msg, "bot": bot_msg})
    return user_bot_pairs

# Sunucu başlat
if __name__ == "__main__":
    app.run(debug=True)
