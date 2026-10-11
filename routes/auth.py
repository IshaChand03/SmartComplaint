from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from database import get_connection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Basic validation
    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Check duplicate email
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Email already registered"}), 409

    # Save user (everyone who registers is a Customer)
    password_hash = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, 'Customer')",
        (name, email, password_hash),
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Registration successful"}), 201


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, name, email, password_hash, role FROM users WHERE email = %s",
        (email,),
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(
        identity=str(user["id"]),
        additional_claims={"role": user["role"]},
    )

    return jsonify({
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "role": user["role"]},
    })