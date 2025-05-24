"""
Performance monitoring routes for SafeVision.
Provides API endpoints for performance monitoring and alerts.
"""

from flask import Blueprint, jsonify, request
from services.performance_monitor import performance_monitor
import requests
import json

from config import HOST, PORT
import time
from typing import Optional

performance_bp = Blueprint("performance", __name__, url_prefix="/api/performance")


def post_with_retry(
    url: str, json_data: dict, max_retries: int = 3, timeout: int = 5
) -> Optional[requests.Response]:
    """Post data with retry logic."""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=json_data, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2**attempt)  # Exponential backoff
    return None


def alert_callback(alert):
    """Callback function to handle performance alerts."""
    try:
        alert_data = {
            "timestamp": alert.timestamp.isoformat(),
            "location": "System Performance",
            "category": "Performance Alert",
            "description": alert.message,
            "severity": alert.severity,
            "session_id": "system",
            "confidence": 1.0,
            "metadata": json.dumps(
                {
                    "alert_type": alert.alert_type,
                    "value": alert.value,
                    "threshold": alert.threshold,
                    "alert_id": alert.id,
                }
            ),
        }

        # Use HTTPS for secure transmission
        analytics_url = f"http://{HOST}:{PORT}/api/analytics/record_alert"

        # Post with retry logic
        post_with_retry(analytics_url, alert_data)

    except Exception as e:
        print(f"Failed to record performance alert: {e}")


performance_monitor.add_alert_callback(alert_callback)


@performance_bp.route("/status")
def get_performance_status():
    """Get current performance status."""
    try:
        status = performance_monitor.get_current_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@performance_bp.route("/alerts")
def get_performance_alerts():
    """Get recent performance alerts."""
    try:
        limit = request.args.get("limit", 10, type=int)
        alerts = performance_monitor.get_recent_alerts(limit)
        return jsonify({"alerts": alerts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@performance_bp.route("/trends")
def get_performance_trends():
    """Get performance trends."""
    try:
        hours = request.args.get("hours", 24, type=int)
        trends = performance_monitor.get_performance_trends(hours)
        return jsonify(trends)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@performance_bp.route("/thresholds", methods=["GET"])
def get_thresholds():
    """Get current performance thresholds."""
    try:
        return jsonify(performance_monitor.thresholds)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@performance_bp.route("/thresholds", methods=["POST"])
def update_thresholds():
    """Update performance thresholds."""
    try:
        new_thresholds = request.get_json()
        if not new_thresholds:
            return jsonify({"error": "No threshold data provided"}), 400

        performance_monitor.update_thresholds(new_thresholds)
        return jsonify({"success": True, "thresholds": performance_monitor.thresholds})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@performance_bp.route("/start", methods=["POST"])
def start_monitoring():
    """Start performance monitoring."""
    try:
        performance_monitor.start_monitoring()
        return jsonify({"success": True, "message": "Performance monitoring started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@performance_bp.route("/stop", methods=["POST"])
def stop_monitoring():
    """Stop performance monitoring."""
    try:
        performance_monitor.stop_monitoring()
        return jsonify({"success": True, "message": "Performance monitoring stopped"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
