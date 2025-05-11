
from views.public_view import home_view
from flask import Blueprint, render_template

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/')
def home():
    return home_view()

# @pages_bp.route('/dashboard')
# def dashboard():
#     """Dashboard page route."""
#     return render_template('dashboard.html')

@pages_bp.route('/about')
def about():
    """About page route."""
    return render_template('about.html')

# @pages_bp.errorhandler(404)
# def not_found_error(error):
#     return render_template('errors/404.html'), 404

# @pages_bp.errorhandler(500)
# def internal_error(error):
#     return render_template('errors/500.html'), 500