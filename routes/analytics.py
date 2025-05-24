from flask import Blueprint, render_template, jsonify, request
import sqlite3
import logging
from datetime import datetime, timedelta
from marshmallow import Schema, fields, ValidationError

analytics_bp = Blueprint('analytics', __name__)

class AnalyticsQuerySchema(Schema):
    days = fields.Int(missing=30, validate=lambda x: 1 <= x <= 365)

@analytics_bp.route('/analytics')
def analytics():
    return render_template('analytics.html')

@analytics_bp.route('/api/analytics/data')
def analytics_data():
    try:
        schema = AnalyticsQuerySchema()
        args = schema.load(request.args)
        days = args['days']
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    n_days_ago = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    try:
        with sqlite3.connect('alerts.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as total FROM alerts")
            total_alerts = cursor.fetchone()['total']

            cursor.execute("SELECT location, COUNT(*) as count FROM alerts GROUP BY location ORDER BY count DESC")
            locations_data = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT category, COUNT(*) as count FROM alerts GROUP BY category ORDER BY count DESC")
            categories_data = [dict(row) for row in cursor.fetchall()]

            cursor.execute("""
                SELECT date(timestamp) as date, COUNT(*) as count 
                FROM alerts 
                WHERE timestamp >= ? 
                GROUP BY date(timestamp) 
                ORDER BY date
            """, (n_days_ago,))
            trend_data = [dict(row) for row in cursor.fetchall()]

            cursor.execute("""
                SELECT id, timestamp, location, category, description, severity 
                FROM alerts 
                ORDER BY timestamp DESC LIMIT 10
            """)
            recent_alerts = [dict(row) for row in cursor.fetchall()]

    except sqlite3.DatabaseError as db_err:
        logging.error(f"Database error: {db_err}", exc_info=True)
        return jsonify({"error": "Database error"}), 500

    return jsonify({
        'total_alerts': total_alerts,
        'locations': locations_data,
        'categories': categories_data,
        'trend': trend_data,
        'recent_alerts': recent_alerts
    })
