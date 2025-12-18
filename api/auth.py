from functools import wraps
from flask import request, jsonify
import jwt
from datetime import datetime, timedelta
from api.config import API_SECRET_KEY, logger


def generate_token(user_id="user"):
    """
    Generates a JWT token for a given user_id.
    """
    if not API_SECRET_KEY:
        raise RuntimeError("API_SECRET_KEY is not set")

    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, API_SECRET_KEY, algorithm="HS256")

    # PyJWT compatibility (string vs bytes)
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    return token


def token_required(f):
    """
    Decorator to protect routes with JWT authentication.
    Injects `current_user` into the route.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Invalid authorization format"}), 401

        token = auth_header.split(" ", 1)[1].strip()

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            data = jwt.decode(
                token,
                API_SECRET_KEY,
                algorithms=["HS256"]
            )

            current_user = data.get("user_id")

            if not current_user:
                return jsonify({"error": "Invalid token payload"}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401

        except jwt.InvalidTokenError:
            return jsonify({"error": "Token is invalid"}), 401

        except Exception:
            logger.exception("❌ Token validation failed")
            return jsonify({"error": "Internal server error"}), 500

        return f(current_user, *args, **kwargs)

    return decorated
