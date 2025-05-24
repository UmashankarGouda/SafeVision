from flask import Blueprint, render_template, jsonify, request
import sqlite3
from datetime import datetime, timedelta
from auth import require_auth

analytics_bp = Blueprint("analytics", __name__)


def init_database():
    """Initialize the analytics database with required tables."""
    db_path = "analytics.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            location TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'medium',
            session_id TEXT,
            confidence REAL,
            metadata TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            frames_processed INTEGER DEFAULT 0,
            alerts_generated INTEGER DEFAULT 0,
            user_agent TEXT,
            ip_address TEXT,
            duration_seconds INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detection_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            people_count INTEGER DEFAULT 0,
            behaviors TEXT,
            confidence REAL,
            processing_time_ms REAL,
            frame_size INTEGER
        )
    """)

    conn.commit()
    conn.close()


@analytics_bp.route("/analytics")
@require_auth
def analytics():
    """Render the analytics dashboard page."""
    return render_template("analytics.html")


@analytics_bp.route("/api/analytics/data")
@require_auth
def analytics_data():
    """Get analytics data with filtering support."""

    init_database()

    time_range = request.args.get("range", "7d")
    location_filter = request.args.get("location", "all")
    severity_filter = request.args.get("severity", "all")

    now = datetime.now()
    if time_range == "24h":
        start_date = now - timedelta(hours=24)
    elif time_range == "7d":
        start_date = now - timedelta(days=7)
    elif time_range == "30d":
        start_date = now - timedelta(days=30)
    elif time_range == "90d":
        start_date = now - timedelta(days=90)
    else:
        start_date = now - timedelta(days=7)

    start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("analytics.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        where_conditions = ["timestamp >= ?"]
        params = [start_date_str]

        if location_filter != "all":
            where_conditions.append("location = ?")
            params.append(location_filter)

        if severity_filter != "all":
            where_conditions.append("severity = ?")
            params.append(severity_filter)

        where_clause = " AND ".join(where_conditions)

        cursor.execute(
            f"SELECT COUNT(*) as total FROM alerts WHERE {where_clause}", params
        )
        result = cursor.fetchone()
        total_alerts = result["total"] if result else 0

        cursor.execute(
            "SELECT location, COUNT(*) as count FROM alerts GROUP BY location ORDER BY count DESC LIMIT 10"
        )
        locations_data = [dict(row) for row in cursor.fetchall()]

        cursor.execute(
            f"SELECT category, COUNT(*) as count FROM alerts WHERE {where_clause} GROUP BY category ORDER BY count DESC",
            params,
        )
        categories_data = [dict(row) for row in cursor.fetchall()]

        if time_range == "24h":
            cursor.execute(
                f"""
                SELECT strftime('%H:00', timestamp) as time_period, COUNT(*) as count 
                FROM alerts 
                WHERE {where_clause}
                GROUP BY strftime('%H', timestamp) 
                ORDER BY time_period
            """,
                params,
            )
        else:
            cursor.execute(
                f"""
                SELECT date(timestamp) as time_period, COUNT(*) as count 
                FROM alerts 
                WHERE {where_clause}
                GROUP BY date(timestamp) 
                ORDER BY time_period
            """,
                params,
            )

        trend_data = [dict(row) for row in cursor.fetchall()]

        cursor.execute(
            f"""
            SELECT id, timestamp, location, category, description, severity, confidence
            FROM alerts 
            WHERE {where_clause}
            ORDER BY timestamp DESC LIMIT 20
        """,
            params,
        )
        recent_alerts = [dict(row) for row in cursor.fetchall()]

        cursor.execute(
            "SELECT COUNT(DISTINCT session_id) as unique_sessions FROM sessions"
        )
        result = cursor.fetchone()
        unique_sessions = result["unique_sessions"] if result else 0

        cursor.execute(
            "SELECT AVG(frames_processed) as avg_frames FROM sessions WHERE frames_processed > 0"
        )
        result = cursor.fetchone()
        avg_frames_per_session = (
            result["avg_frames"] if result and result["avg_frames"] else 0
        )

        conn.close()

        return jsonify(
            {
                "total_alerts": total_alerts,
                "locations": locations_data,
                "categories": categories_data,
                "trend": trend_data,
                "recent_alerts": recent_alerts,
                "unique_sessions": unique_sessions,
                "avg_frames_per_session": round(avg_frames_per_session, 1),
                "time_range": time_range,
                "filters": {"location": location_filter, "severity": severity_filter},
            }
        )

    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/record_alert", methods=["POST"])
@require_auth
def record_alert():
    """Record a new alert in the analytics database."""
    try:
        data = request.get_json()

        init_database()
        conn = sqlite3.connect("analytics.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO alerts (timestamp, location, category, description, severity, session_id, confidence, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data.get("timestamp", datetime.now().isoformat()),
                data.get("location", "Unknown"),
                data.get("category", "General"),
                data.get("description", "Alert detected"),
                data.get("severity", "medium"),
                data.get("session_id"),
                data.get("confidence", 0.0),
                data.get("metadata", "{}"),
            ),
        )

        conn.commit()
        conn.close()

        return jsonify({"status": "success", "message": "Alert recorded"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/record_session", methods=["POST"])
@require_auth
def record_session():
    """Record session data for analytics."""
    try:
        data = request.get_json()

        init_database()
        conn = sqlite3.connect("analytics.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO sessions 
            (session_id, start_time, end_time, frames_processed, alerts_generated, user_agent, ip_address, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data.get("session_id"),
                data.get("start_time", datetime.now().isoformat()),
                data.get("end_time"),
                data.get("frames_processed", 0),
                data.get("alerts_generated", 0),
                data.get("user_agent"),
                data.get("ip_address"),
                data.get("duration_seconds", 0),
            ),
        )

        conn.commit()
        conn.close()

        return jsonify({"status": "success", "message": "Session recorded"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/analytics/record_detection", methods=["POST"])
@require_auth
def record_detection():
    """Record detection event for detailed analytics."""
    try:
        data = request.get_json()

        init_database()
        conn = sqlite3.connect("analytics.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO detection_events 
            (timestamp, session_id, people_count, behaviors, confidence, processing_time_ms, frame_size)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data.get("timestamp", datetime.now().isoformat()),
                data.get("session_id"),
                data.get("people_count", 0),
                data.get("behaviors", "[]"),
                data.get("confidence", 0.0),
                data.get("processing_time_ms", 0.0),
                data.get("frame_size", 0),
            ),
        )

        conn.commit()
        conn.close()

        return jsonify({"status": "success", "message": "Detection recorded"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
