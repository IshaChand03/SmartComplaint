from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from auth_utils import role_required

users_bp = Blueprint("users", __name__)


@users_bp.route("/api/me")
@jwt_required()
def me():
    return jsonify({
        "user_id": get_jwt_identity(),
        "role": get_jwt()["role"],
    })


@users_bp.route("/api/admin/test")
@role_required("Admin")
def admin_test():
    return jsonify({"message": "Welcome, Admin!"})