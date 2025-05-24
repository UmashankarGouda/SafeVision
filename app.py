from flask import Blueprint, render_template, jsonify
import sqlite3
from datetime import datetime, timedelta
import logging
from flask import Flask, jsonify
import os

# Define blueprint
analytics_bp = Blueprint('analytics', __name__)

# Route to show analytics page
@analytics_bp.route('/analytics')
def analytics():
    return render_template('analytics.html')

# API route for fetching analytics data
@analytics_bp.route('/api/analytics/data')
def analytics_data():
    # ...validation code...
    with sqlite3.connect('alerts.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # ...your queries...
        # Example:
        cursor.execute("SELECT COUNT(*) as total FROM alerts")
        total_alerts = cursor.fetchone()['total']
        # ...other queries...
    return jsonify({
        'total_alerts': total_alerts,
        # ...other fields...
    })

def create_app():
    app = Flask(__name__)

    # ...existing blueprint registration...

    # Ensure logs directory exists
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "safevision.log")

    # Prevent duplicate handlers
    if not app.logger.handlers:
        file_handler = logging.FileHandler(log_path)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

    # Centralized error handler
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled Exception: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

    return app

# If you use app = Flask(__name__) directly, add the logging and errorhandler after app = Flask(__name__)
