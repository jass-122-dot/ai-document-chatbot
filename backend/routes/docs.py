from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from database import get_db
from config import Config
import os
import uuid
import PyPDF2
from groq import Groq
import chromadb

docs_bp = Blueprint("docs", __name__)

groq_client = Groq(api_key=Config.GROQ_API_KEY)
chroma_client = chromadb.Client()


def get_or_create_collection(name):
    try:
        return chroma_client.get_collection(name=name)
    except:
        return chroma_client.create_collection(name=name)


def extract_text_from_pdf(filepath):
    text = ""
    with open(filepath, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
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

    text = extract_text_from_pdf(filepath)
    if not text.strip():
        return jsonify({"error": "Could not extract text from PDF"}), 400

    chunks = chunk_text(text)
    collection_name = f"doc_{user_id}_{unique_name.replace('-', '_').replace('.', '_')}"
    collection = get_or_create_collection(collection_name)
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    #collection.add(documents=chunks, ids=ids)
    print("1. PDF extracted")

    chunks = chunk_text(text)
    print("2. Chunks created")

    collection = get_or_create_collection(collection_name)
    print("3. Collection created")

    # collection.add(documents=chunks, ids=ids)

    print("4. Skipped collection.add")

    db = get_db()
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
        results = collection.query(query_texts=[question], n_results=3)
        context = " ".join(results["documents"][0]) if results["documents"] else ""
    except Exception as e:
        return jsonify({"error": f"Search error: {str(e)}"}), 500

    prompt = f"""You are a helpful assistant. Answer the question based on the document context below.

Context:
{context}

Question: {question}

Answer clearly and concisely based on the context provided."""

    try:
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
