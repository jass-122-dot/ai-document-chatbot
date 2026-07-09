const token = localStorage.getItem("token");
const name = localStorage.getItem("name");
const docId = localStorage.getItem("current_doc_id");
const docName = localStorage.getItem("current_doc_name");

if (!token || !docId) {
  window.location.replace("/dashboard");
}

document.getElementById("username").textContent = name;
document.getElementById("doc-name").textContent = docName;

function loadHistory() {
  fetch("/api/docs/history/" + docId, {
    headers: { Authorization: "Bearer " + token },
  })
    .then((r) => r.json())
    .then((history) => {
      if (!Array.isArray(history)) return;
      const chatBox = document.getElementById("chat-box");
      chatBox.innerHTML = "";
      if (history.length === 0) {
        chatBox.innerHTML =
          '<div class="message bot">Hello! Ask me anything about this document.</div>';
        return;
      }
      history.forEach((h) => {
        chatBox.innerHTML += `<div class="message user">${h.question}</div>`;
        chatBox.innerHTML += `<div class="message bot">${h.answer}</div>`;
      });
      chatBox.scrollTop = chatBox.scrollHeight;
    });
}

function sendMessage() {
  const input = document.getElementById("question-input");
  const question = input.value.trim();
  if (!question) return;

  const chatBox = document.getElementById("chat-box");
  chatBox.innerHTML += `<div class="message user">${question}</div>`;
  chatBox.innerHTML += `<div class="message loading" id="loading-msg">Thinking...</div>`;
  chatBox.scrollTop = chatBox.scrollHeight;
  input.value = "";

  fetch("/api/docs/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify({ doc_id: docId, question }),
  })
    .then((r) => r.json())
    .then((data) => {
      const loading = document.getElementById("loading-msg");
      if (loading) loading.remove();
      if (data.answer) {
        chatBox.innerHTML += `<div class="message bot">${data.answer}</div>`;
      } else {
        chatBox.innerHTML += `<div class="message bot">Error: ${data.error}</div>`;
      }
      chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(() => {
      const loading = document.getElementById("loading-msg");
      if (loading) loading.remove();
      chatBox.innerHTML += `<div class="message bot">Something went wrong. Try again.</div>`;
      chatBox.scrollTop = chatBox.scrollHeight;
    });
}

function handleEnter(e) {
  if (e.key === "Enter") sendMessage();
}

function logout() {
  localStorage.clear();
  window.location.replace("login.html");
}

loadHistory();
