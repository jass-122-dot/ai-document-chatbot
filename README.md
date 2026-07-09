# AI Document Chatbot

An AI-powered web application that allows users to upload PDF documents and chat with them using natural language questions. Built with Python Flask backend and vanilla HTML/CSS/JavaScript frontend.

---

## Features

- User Registration and Login with JWT Authentication
- PDF Document Upload and Text Extraction
- Semantic Search using ChromaDB Vector Database
- AI-powered Chat using Groq API (LLaMA 3.1)
- Chat History saved per document
- Delete documents and chat history
- Responsive UI

---

## Tech Stack

**Frontend**

- HTML5, CSS3, JavaScript (Vanilla)

**Backend**

- Python 3
- Flask (REST API)
- Flask-JWT-Extended (Authentication)
- Flask-CORS

**Database**

- SQLite (users, documents, chat history)

**AI & Search**

- Groq API with LLaMA 3.1 8B model
- ChromaDB (Vector Database for semantic search)
- PyPDF2 (PDF text extraction)

---

## Project Structure

```
doc-chatbot/
├── backend/
│   ├── app.py              # Flask app entry point
│   ├── config.py           # Configuration and environment variables
│   ├── database.py         # SQLite database setup
│   ├── requirements.txt    # Python dependencies
│   ├── .env                # Environment variables (not pushed to GitHub)
│   ├── uploads/            # Uploaded PDF files stored here
│   └── routes/
│       ├── auth.py         # Register and Login APIs
│       └── docs.py         # Upload, Chat, History APIs
└── frontend/
    ├── deploy/
    │   ├── login.html      # Login page
    │   ├── register.html   # Register page
    │   ├── /dashboard  # Documents dashboard
    │   └── chat.html       # Chat with document page
    ├── css/
    │   ├── style.css       # Global styles
    │   ├── dashboard.css   # Dashboard styles
    │   └── chat.css        # Chat page styles
    └── js/
        ├── login.js        # Login logic
        ├── register.js     # Register logic
        ├── dashboard.js    # Dashboard logic
        └── chat.js         # Chat logic
```

---

## API Endpoints

| Method | Endpoint              | Description                   |
| ------ | --------------------- | ----------------------------- |
| POST   | /api/auth/register    | Register new user             |
| POST   | /api/auth/login       | Login and get JWT token       |
| POST   | /api/docs/upload      | Upload PDF document           |
| GET    | /api/docs/list        | Get all user documents        |
| POST   | /api/docs/chat        | Ask question about document   |
| GET    | /api/docs/history/:id | Get chat history for document |
| DELETE | /api/docs/delete/:id  | Delete document               |

---

## Setup Instructions

### Prerequisites

- Python 3.8+
- Groq API key (free at https://console.groq.com)

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/doc-chatbot.git
cd doc-chatbot
```

### 2. Setup Python virtual environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file inside the `backend` folder:

```
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
SECRET_KEY=your_secret_key_here
```

### 5. Run the backend

```bash
python app.py
```

SQLite database is created automatically on first run.

### 6. Run the frontend

Open `frontend/deploy/login.html` with Live Server in VS Code.

---

## How It Works

1. User registers and logs in
2. User uploads a PDF document
3. Backend extracts text from the PDF using PyPDF2
4. Text is split into chunks and stored in ChromaDB vector database
5. When user asks a question, ChromaDB finds the most relevant chunks
6. Relevant chunks are sent to Groq AI as context
7. Groq AI generates an answer based on the document content
8. Answer is displayed in the chat and saved to SQLite database

---

## Screenshots

> Add screenshots of your login page, dashboard, and chat page here.

---

## Future Enhancements

- Support for multiple file formats (Word, Excel, TXT)
- Multi-document chat (ask questions across multiple documents)
- Export chat history as PDF
- Dark mode
- Deploy on cloud (Render + Netlify)

---

## Author

**Samitha Jasmine H**

- GitHub: https://github.com/yourusername
- LinkedIn: https://linkedin.com/in/yourprofile
