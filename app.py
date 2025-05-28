from flask import Flask, Blueprint, render_template, jsonify, session
from flask_wtf import CSRFProtect
import sqlite3
from datetime import datetime, timedelta
from routes import user_bp

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'change_this_secret_key'  # Use a secure, random value in production
csrf = CSRFProtect(app)

# Define blueprint
analytics_bp = Blueprint('analytics', __name__)

# Route to show analytics page
@analytics_bp.route('/analytics')
def analytics():
    return render_template('analytics.html')

# API route for fetching analytics data
@analytics_bp.route('/api/analytics/data')
def analytics_data():
    conn = sqlite3.connect('alerts.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Query the database and return JSON data
    # (code for fetching data from the database, as you already have it)

    return jsonify({
        'total_alerts': total_alerts,
        'locations': locations_data,
        'categories': categories_data,
        'trend': trend_data,
        'recent_alerts': recent_alerts
    })

# Register blueprints as needed
# app.register_blueprint(pages_bp)
# app.register_blueprint(surveillance_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(user_bp)
