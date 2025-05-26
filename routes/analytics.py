from flask import Blueprint, render_template, jsonify, session, request
import sqlite3
from datetime import datetime, timedelta
from flask_login import login_required, current_user
from services.recording_service import RecordingService

analytics_bp = Blueprint('analytics', __name__)

recording_services = {}

def get_user_id():
    return str(current_user.get_id()) if current_user.is_authenticated else session.get('user_id')

@analytics_bp.route('/analytics')
def analytics():
    return render_template('analytics.html')

@analytics_bp.route('/api/analytics/data')
def analytics_data():
    conn = sqlite3.connect('alerts.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Total alerts
    cursor.execute("SELECT COUNT(*) as total FROM alerts")
    total_alerts = cursor.fetchone()['total']

    # Alerts by location
    cursor.execute("SELECT location, COUNT(*) as count FROM alerts GROUP BY location ORDER BY count DESC")
    locations_data = [dict(row) for row in cursor.fetchall()]

    # Alerts by category
    cursor.execute("SELECT category, COUNT(*) as count FROM alerts GROUP BY category ORDER BY count DESC")
    categories_data = [dict(row) for row in cursor.fetchall()]

    # Trend (last 30 days)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT date(timestamp) as date, COUNT(*) as count 
        FROM alerts 
        WHERE timestamp >= ? 
        GROUP BY date(timestamp) 
        ORDER BY date
    """, (thirty_days_ago,))
    trend_data = [dict(row) for row in cursor.fetchall()]

    # Recent alerts
    cursor.execute("""
        SELECT id, timestamp, location, category, description, severity 
        FROM alerts 
        ORDER BY timestamp DESC LIMIT 10
    """)
    recent_alerts = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        'total_alerts': total_alerts,
        'locations': locations_data,
        'categories': categories_data,
        'trend': trend_data,
        'recent_alerts': recent_alerts
    })

@analytics_bp.route('/api/recording/start', methods=['POST'])
@login_required
def start_recording():
    user_id = get_user_id()
    recording_services[user_id] = RecordingService(user_id)
    recording_services[user_id].start()
    return jsonify({'status': 'started'})

@analytics_bp.route('/api/recording/stop', methods=['POST'])
@login_required
def stop_recording():
    user_id = get_user_id()
    service = recording_services.get(user_id)
    if not service:
        return jsonify({'error': 'No active recording'}), 400
    filename = service.stop()
    return jsonify({'status': 'stopped', 'filename': filename})

@analytics_bp.route('/api/recording/list', methods=['GET'])
@login_required
def list_recordings():
    user_id = get_user_id()
    service = recording_services.get(user_id) or RecordingService(user_id)
    files = service.list_recordings()
    return jsonify({'recordings': files})
