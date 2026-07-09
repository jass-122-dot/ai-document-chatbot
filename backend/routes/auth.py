from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from database import get_db
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'error': 'All fields required'}), 400

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    db = get_db()
    try:
        db.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, hashed))
        db.commit()
        return jsonify({'message': 'Registered successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    db.close()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    stored = user['password']
    if isinstance(stored, str):
        stored = stored.encode('utf-8')

    if bcrypt.checkpw(password.encode('utf-8'), stored):
        token = create_access_token(identity=str(user['id']))
        return jsonify({'token': token, 'name': user['name'], 'user_id': user['id']}), 200
    else:
        return jsonify({'error': 'Wrong password'}), 401
