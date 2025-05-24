"""
Authentication routes for SafeVision admin access.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth import check_password, login_user, logout_user, is_authenticated

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page for admin access."""
    if request.method == "POST":
        password = request.form.get("password")
        next_url = request.form.get("next") or url_for("pages.home")

        if password and check_password(password):
            login_user()
            flash("Successfully logged in!", "success")
            return redirect(next_url)
        else:
            flash("Invalid password. Please try again.", "error")

    next_url = request.args.get("next", url_for("pages.home"))
    return render_template("auth/login.html", next=next_url)


@auth_bp.route("/logout")
def logout():
    """Logout and redirect to home."""
    logout_user()
    flash("Successfully logged out.", "info")
    return redirect(url_for("pages.home"))


@auth_bp.route("/status")
def status():
    """Check authentication status (for AJAX calls)."""
    return {"authenticated": is_authenticated()}
