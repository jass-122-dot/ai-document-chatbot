from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from database import get_db
from config import Config
import os
import uuid
import importlib
from sklearn.feature_extraction.text import HashingVectorizer

# Dynamically import a PDF reader to avoid hard dependency at static-analysis time.
# Try PyPDF2 first, then pypdf. If neither is available, PdfReader stays None and
# extract_text_from_pdf will raise at runtime.
PdfReader = None
for mod_name in ("PyPDF2", "pypdf"):
    try:
        mod = importlib.import_module(mod_name)
        PdfReader = getattr(mod, "PdfReader", None)
        if PdfReader:
            break
    except Exception:
        continue
# Dynamically import Groq to avoid hard dependency at static-analysis time.
Groq = None
try:
    _groq = importlib.import_module("groq")
    Groq = getattr(_groq, "Groq", None)
except Exception:
    Groq = None

# Dynamically import chromadb to avoid hard dependency at static-analysis time.
chromadb = None
try:
    chromadb = importlib.import_module("chromadb")
except Exception:
    chromadb = None

docs_bp = Blueprint("docs", __name__)

groq_client = Groq(api_key=Config.GROQ_API_KEY) if Groq is not None else None
chroma_client = chromadb.Client()

# Lightweight, stateless vectorizer - no model download, low memory
vectorizer = HashingVectorizer(n_features=256, norm="l2", alternate_sign=False)


def embed_texts(texts):
    """Convert a list of strings into fixed-size numeric vectors using hashing.
    No model download, no neural network - just math. Low memory footprint."""
    return vectorizer.transform(texts).toarray().tolist()


def get_or_create_collection(name):
    try:
        return chroma_client.get_collection(name=name)
    except:
        return chroma_client.create_collection(name=name)


def extract_text_from_pdf(filepath):
    text = ""
    with open(filepath, "rb") as f:
        if PdfReader is None:
            raise RuntimeError("No PDF reader library available. Install PyPDF2 or pypdf.")
        reader = PdfReader(f)
        # PdfReader.pages is iterable; page.extract_text() for PyPDF2/pypdf
        for page in getattr(reader, "pages", []):
            # newer pypdf uses extract_text(), older PyPDF2 may have extract_text
            try:
                extracted = page.extract_text()
            except Exception:
                extracted = ""
            text += extracted or ""
    return text


def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i : i + chunk_size]))
    return chunks


def row_to_dict(row):
    return dict(row) if row else None


def rows_to_list(rows):
    return [dict(row) for row in rows]


@docs_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_document():
    user_id = get_jwt_identity()
    print("FILES:", request.files)
    print("USER ID:", user_id)

    if "file" not in request.files:
        print("NO FILE IN REQUEST")
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF files allowed"}), 400

    original_name = file.filename
    unique_name = str(uuid.uuid4()) + ".pdf"
    filepath = os.path.join(Config.UPLOAD_FOLDER, unique_name)
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    file.save(filepath)
    print("1. File received")

    text = extract_text_from_pdf(filepath)
    print("2. PDF extracted")
    if not text.strip():
        return jsonify({"error": "Could not extract text from PDF"}), 400

    chunks = chunk_text(text)
    print("3. Chunks created:", len(chunks))
    collection_name = f"doc_{user_id}_{unique_name.replace('-', '_').replace('.', '_')}"
    collection = get_or_create_collection(collection_name)
    print("4. Collection created")
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    # Compute lightweight hashing-based embeddings ourselves instead of letting
    # ChromaDB fall back to its default sentence-transformers model (heavy, needs
    # a model download + ~300-400MB RAM - crashes on Render's 512MB free tier).
    embeddings = embed_texts(chunks)
    collection.add(documents=chunks, embeddings=embeddings, ids=ids)
    print("5. Chunks stored")

    db = get_db()
    print("6. DB opened")
    try:
        cursor = db.execute(
            "INSERT INTO documents (user_id, filename, original_name) VALUES (?, ?, ?)",
            (user_id, collection_name, original_name),
        )
        db.commit()
        doc_id = cursor.lastrowid
        return (
            jsonify(
                {
                    "message": "Document uploaded successfully",
                    "doc_id": doc_id,
                    "name": original_name,
                }
            ),
            201,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@docs_bp.route("/list", methods=["GET"])
@jwt_required()
def list_documents():
    user_id = get_jwt_identity()
    db = get_db()
    rows = db.execute(
        "SELECT * FROM documents WHERE user_id = ? ORDER BY uploaded_at DESC",
        (user_id,),
    ).fetchall()
    db.close()
    return jsonify(rows_to_list(rows)), 200


@docs_bp.route("/chat", methods=["POST"])
@jwt_required()
def chat():
    user_id = get_jwt_identity()
    data = request.get_json()
    doc_id = data.get("doc_id")
    question = data.get("question")

    if not doc_id or not question:
        return jsonify({"error": "doc_id and question required"}), 400

    db = get_db()
    doc = row_to_dict(
        db.execute(
            "SELECT * FROM documents WHERE id = ? AND user_id = ?", (doc_id, user_id)
        ).fetchone()
    )
    db.close()

    if not doc:
        return jsonify({"error": "Document not found"}), 404

    collection_name = doc["filename"]
    try:
        collection = get_or_create_collection(collection_name)
        # Use the same hashing vectorizer to embed the question, then query
        # ChromaDB with the precomputed vector instead of query_texts (which
        # would otherwise trigger the default heavy embedding model again).
        query_embedding = embed_texts([question])[0]
        results = collection.query(query_embeddings=[query_embedding], n_results=3)
        context = " ".join(results["documents"][0]) if results["documents"] else ""
    except Exception as e:
        return jsonify({"error": f"Search error: {str(e)}"}), 500

    prompt = f"""You are a helpful assistant. Answer the question based on the document context below.

Context:
{context}

Question: {question}

Answer clearly and concisely based on the context provided."""

    try:
        if groq_client is None:
            return jsonify({"error": "AI provider not available"}), 500

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.choices[0].message.content
    except Exception as e:
        print("GROQ ERROR:", str(e))
        return jsonify({"error": f"AI error: {str(e)}"}), 500

    db = get_db()
    try:
        db.execute(
            "INSERT INTO chat_history (user_id, document_id, question, answer) VALUES (?, ?, ?, ?)",
            (user_id, doc_id, question, answer),
        )
        db.commit()
    except:
        pass
    finally:
        db.close()

    return jsonify({"answer": answer}), 200


@docs_bp.route("/history/<int:doc_id>", methods=["GET"])
@jwt_required()
def get_history(doc_id):
    user_id = get_jwt_identity()
    db = get_db()
    rows = db.execute(
        "SELECT * FROM chat_history WHERE user_id = ? AND document_id = ? ORDER BY created_at ASC",
        (user_id, doc_id),
    ).fetchall()
    db.close()
    return jsonify(rows_to_list(rows)), 200


@docs_bp.route("/delete/<int:doc_id>", methods=["DELETE"])
@jwt_required()
def delete_document(doc_id):
    user_id = get_jwt_identity()
    db = get_db()
    try:
        db.execute(
            "DELETE FROM chat_history WHERE document_id = ? AND user_id = ?",
            (doc_id, user_id),
        )
        db.execute(
            "DELETE FROM documents WHERE id = ? AND user_id = ?", (doc_id, user_id)
        )
        db.commit()
        return jsonify({"message": "Document deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()
