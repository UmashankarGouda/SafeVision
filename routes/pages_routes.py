from views.public_view import home_view
from flask import Blueprint, render_template
from auth import require_auth

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def home():
    return home_view()


@pages_bp.route("/about")
def about():
    """About page route."""
    return render_template("about.html")


@pages_bp.route("/settings")
@require_auth
def settings():
    """Settings/Configuration page route."""
    return render_template("settings.html")


@pages_bp.route("/recordings")
@require_auth
def recordings():
    """Video recordings page route."""
    return render_template("recordings.html")
