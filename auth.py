"""
Simple authentication system for SafeVision settings access.
"""

from functools import wraps
from flask import session, request, redirect, url_for
import hashlib
import os

DEFAULT_ADMIN_PASSWORD = "safevision123"
ADMIN_PASSWORD_HASH = hashlib.sha256(DEFAULT_ADMIN_PASSWORD.encode()).hexdigest()


def check_password(password):
    """Check if provided password is correct."""

    admin_password = os.environ.get("SAFEVISION_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    provided_hash = hashlib.sha256(password.encode()).hexdigest()
    expected_hash = hashlib.sha256(admin_password.encode()).hexdigest()
    return provided_hash == expected_hash


def require_auth(f):
    """Decorator to require authentication for routes."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("authenticated"):
            if request.is_json or "application/json" in request.headers.get(
                "Accept", ""
            ):
                from flask import jsonify

                return jsonify({"error": "Authentication required"}), 401

            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def login_user():
    """Log in the user by setting session."""
    session["authenticated"] = True
    session.permanent = True


def logout_user():
    """Log out the user by clearing session."""
    session.pop("authenticated", None)


def is_authenticated():
    """Check if user is currently authenticated."""
    return session.get("authenticated", False)
