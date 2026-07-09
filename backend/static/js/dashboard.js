const token = localStorage.getItem("token");
const name = localStorage.getItem("name");

if (!token) {
  window.location.replace("login.html");
}

document.getElementById("username").textContent = name;

function loadDocuments() {
  fetch("/api/docs/list", {
    headers: { Authorization: "Bearer " + token },
  })
    .then((r) => r.json())
    .then((docs) => {
      const grid = document.getElementById("docs-grid");
      grid.innerHTML = "";
      if (docs.length === 0) {
        grid.innerHTML =
          '<div class="empty-state"><p>No documents uploaded yet.</p><p>Upload a PDF to start chatting!</p></div>';
        return;
      }
      docs.forEach((doc) => {
        const date = doc.uploaded_at ? doc.uploaded_at.split(" ")[0] : "";
        grid.innerHTML += `
                <div class="doc-card">
                    <div class="doc-icon">📄</div>
                    <div class="doc-name">${doc.original_name}</div>
                    <div class="doc-date">${date}</div>
                    <div class="doc-actions">
                        <button class="btn-chat" onclick="openChat(${doc.id}, '${doc.original_name}')">Chat</button>
                        <button class="btn-delete-doc" onclick="deleteDoc(${doc.id})">Delete</button>
                    </div>
                </div>
            `;
      });
    });
}

function uploadDocument() {
  const file = document.getElementById("fileInput").files[0];
  if (!file) return;

  const status = document.getElementById("upload-status");
  status.textContent = "Uploading and processing...";

  const formData = new FormData();
  formData.append("file", file);

  fetch("/api/docs/upload", {
    method: "POST",
    headers: { Authorization: "Bearer " + token },
    body: formData,
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.doc_id) {
        status.textContent = "Document uploaded successfully!";
        loadDocuments();
        setTimeout(() => {
          status.textContent = "";
        }, 3000);
      } else {
        status.textContent = "Error: " + data.error;
      }
    })
    .catch(() => {
      status.textContent = "Upload failed. Try again.";
    });
}

function openChat(docId, docName) {
  localStorage.setItem("current_doc_id", docId);
  localStorage.setItem("current_doc_name", docName);
  window.location.href = "chat.html";
}

function deleteDoc(docId) {
  if (confirm("Delete this document and all its chat history?")) {
    fetch("/api/docs/delete/" + docId, {
      method: "DELETE",
      headers: { Authorization: "Bearer " + token },
    })
      .then((r) => r.json())
      .then(() => {
        loadDocuments();
      });
  }
}

function logout() {
  localStorage.clear();
  window.location.replace("login.html");
}

document.getElementById("fileInput").addEventListener("change", uploadDocument);

loadDocuments();
