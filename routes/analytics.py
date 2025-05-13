from flask import Blueprint

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
def analytics_home():
    return "Analytics route is working!"
