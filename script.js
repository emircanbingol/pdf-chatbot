// Run when page is loaded
window.addEventListener("DOMContentLoaded", () => {
    fetchPDFList();

    // Dark mode toggle
    const modeToggle = document.getElementById("mode-toggle");
    modeToggle.addEventListener("change", () => {
        document.body.classList.toggle("dark");
    });

    // Upload form handler
    const uploadForm = document.getElementById("upload-form");
    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById("pdf-file");
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        if (response.ok) {
            showPopup("Uploaded successfully");
            fileInput.value = "";
            fetchPDFList();
        } else {
            showPopup("Upload failed", true);
        }
    });

    // Chat message send
    const sendBtn = document.getElementById("send-btn");
    sendBtn.addEventListener("click", sendMessage);

    // Send message on Enter key
    document.getElementById("user-input").addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
            e.preventDefault();
            sendMessage();
        }
    });
});

async function sendMessage() {
    const input = document.getElementById("user-input");
    const question = input.value.trim();
    if (!question) return;

    appendMessage("You", question);
    input.value = "";

    const res = await fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: question })
    });

    const data = await res.json();
    appendMessage("Bot", data.response || "An error occurred.");
}

function fetchPDFList() {
    fetch("/list_pdfs")
        .then(res => res.json())
        .then(files => {
            const list = document.getElementById("pdfs");
            list.innerHTML = "";
            files.forEach(file => {
                const li = document.createElement("li");
                li.textContent = file;
                list.appendChild(li);
            });
        });
}

function appendMessage(sender, text) {
    const history = document.getElementById("chat-history");
    const div = document.createElement("div");
    div.className = sender.toLowerCase();
    div.innerHTML = `<strong>${sender}:</strong> ${text}`;
    history.appendChild(div);
    history.scrollTop = history.scrollHeight;
}

function showPopup(message, isError = false) {
    const popup = document.getElementById("popup");
    popup.textContent = message;
    popup.style.backgroundColor = isError ? "#dc3545" : "#28a745";
    popup.style.display = "block";
    setTimeout(() => {
        popup.style.display = "none";
    }, 2000);
}
