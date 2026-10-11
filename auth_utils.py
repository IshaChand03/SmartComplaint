from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()          # checks the token is valid
            claims = get_jwt()
            if claims.get("role") not in allowed_roles:
                return jsonify({"error": "You do not have permission"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator