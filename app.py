from flask import Blueprint, render_template, jsonify
import sqlite3
from datetime import datetime, timedelta

# Define blueprint
analytics_bp = Blueprint('analytics', __name__)

# Route to show analytics page
@analytics_bp.route('/analytics')
def analytics():
    return render_template('analytics.html')

# API route for fetching analytics data
@analytics_bp.route('/api/analytics/data')
def analytics_data():
    # Your database logic here (as you've already written)
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
