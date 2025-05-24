"""
Routes for the surveillance application.
Modified to handle browser-based camera input with multi-user session management.
Enhanced with automatic analytics data recording.
"""

from flask import Blueprint, jsonify, request
from controllers.surveillance_controller import SurveillanceController
from services.performance_monitor import performance_monitor
from services.video_recorder import video_recorder
import time
import requests
import json
from datetime import datetime

# Create Blueprint
surveillance_bp = Blueprint("surveillance", __name__)

# Create controller instance
controller = SurveillanceController()

# Session management
active_sessions = {}  # session_id -> session_info
session_stats = {
    "total_sessions": 0,
    "active_count": 0,
    "total_frames_processed": 0,
    "last_activity": None,
}


def record_analytics_session(session_info, end_time=None):
    """Record session data to analytics database."""
    try:
        duration = (end_time or time.time()) - session_info["start_time"]

        session_data = {
            "session_id": session_info["id"],
            "start_time": datetime.fromtimestamp(
                session_info["start_time"]
            ).isoformat(),
            "end_time": datetime.fromtimestamp(end_time or time.time()).isoformat()
            if end_time
            else None,
            "frames_processed": session_info["frames_processed"],
            "alerts_generated": session_info.get("alerts_generated", 0),
            "user_agent": session_info["user_agent"],
            "ip_address": session_info["ip_address"],
            "duration_seconds": int(duration),
        }

        # Record session in analytics
        requests.post(
            "http://127.0.0.1:5000/api/analytics/record_session",
            json=session_data,
            timeout=5,
        )
    except Exception as e:
        print(f"Failed to record session analytics: {e}")


def record_analytics_alert(session_id, alert_data):
    """Record alert to analytics database."""
    try:
        alert_record = {
            "timestamp": datetime.now().isoformat(),
            "location": alert_data.get("location", "Camera Feed"),
            "category": alert_data.get("category", "Behavioral Alert"),
            "description": alert_data.get(
                "description", "Suspicious behavior detected"
            ),
            "severity": alert_data.get("severity", "medium"),
            "session_id": session_id,
            "confidence": alert_data.get("confidence", 0.0),
            "metadata": json.dumps(alert_data.get("metadata", {})),
        }

        # Record alert in analytics
        requests.post(
            "http://127.0.0.1:5000/api/analytics/record_alert",
            json=alert_record,
            timeout=5,
        )
    except Exception as e:
        print(f"Failed to record alert analytics: {e}")


def record_analytics_detection(session_id, detection_data):
    """Record detection event to analytics database."""
    try:
        detection_record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "people_count": detection_data.get("people_count", 0),
            "behaviors": json.dumps(detection_data.get("behaviors", [])),
            "confidence": detection_data.get("confidence", 0.0),
            "processing_time_ms": detection_data.get("processing_time_ms", 0.0),
            "frame_size": detection_data.get("frame_size", 0),
        }

        # Record detection in analytics
        requests.post(
            "http://127.0.0.1:5000/api/analytics/record_detection",
            json=detection_record,
            timeout=5,
        )
    except Exception as e:
        print(f"Failed to record detection analytics: {e}")


# New SocketIO events for browser-based camera
def setup_socketio_events(socketio):
    """Setup SocketIO events for frame processing with session management."""

    @socketio.on("connect")
    def handle_connect():
        session_id = request.sid
        print(f"Client connected: {session_id}")

        # Create session info
        session_info = {
            "id": session_id,
            "start_time": time.time(),
            "last_activity": time.time(),
            "frames_sent": 0,
            "frames_processed": 0,
            "user_agent": request.headers.get("User-Agent", "Unknown"),
            "ip_address": request.remote_addr,
        }

        active_sessions[session_id] = session_info
        session_stats["total_sessions"] += 1
        session_stats["active_count"] = len(active_sessions)
        session_stats["last_activity"] = time.time()

        # Start processing if not already running
        if not controller.frame_service.is_processing:
            controller.frame_service.start_processing()
            print("Frame processing started for new session")

    @socketio.on("disconnect")
    def handle_disconnect():
        session_id = request.sid
        print(f"Client disconnected: {session_id}")

        # Remove session
        if session_id in active_sessions:
            session_info = active_sessions.pop(session_id)
            session_duration = time.time() - session_info["start_time"]
            print(
                f"Session {session_id} lasted {session_duration:.1f} seconds, processed {session_info['frames_processed']} frames"
            )
            # Record session analytics
            record_analytics_session(session_info)

        session_stats["active_count"] = len(active_sessions)

        # Stop processing if no active sessions
        if len(active_sessions) == 0:
            print("No active sessions, stopping frame processing")
            controller.frame_service.stop_processing()

    @socketio.on("process_frame")
    def handle_process_frame(frame_data):
        """Handle incoming frame from browser for processing."""
        session_id = request.sid

        # Update session stats
        if session_id in active_sessions:
            active_sessions[session_id]["last_activity"] = time.time()
            active_sessions[session_id]["frames_sent"] += 1

        try:
            # Process the incoming frame
            success = controller.frame_service.process_incoming_frame(frame_data)

            if success:
                # Update global stats
                session_stats["total_frames_processed"] += 1
                session_stats["last_activity"] = time.time()

                # Update session stats
                if session_id in active_sessions:
                    active_sessions[session_id]["frames_processed"] += (
                        1  # Get processed result
                    )
                result = controller.frame_service.get_processed_frame()
                if result:
                    # Send processed frame back to client with timestamp and frame_id if available
                    processed_frame_data = {
                        "frame": result["frame"],
                        "timestamp": result.get(
                            "timestamp"
                        ),  # Return original timestamp if available
                        "frameId": result.get(
                            "frame_id"
                        ),  # Return original frame ID if available
                    }
                    socketio.emit(
                        "processed_frame", processed_frame_data, room=session_id
                    )
                    # Send analysis results separately
                    analysis_data = result.get("analysis", {})
                    socketio.emit("analysis_result", analysis_data, room=session_id)

                    # Add frame to video recording if recording is active
                    recording_status = video_recorder.get_recording_status(session_id)
                    if recording_status.get("status") == "recording":
                        video_recorder.add_frame(session_id, frame_data)

                    # Record detection analytics
                    if analysis_data:
                        record_analytics_detection(
                            session_id,
                            {
                                "people_count": analysis_data.get("people_count", 0),
                                "behaviors": analysis_data.get("behaviors", []),
                                "confidence": analysis_data.get("confidence", 0.0),
                                "processing_time_ms": analysis_data.get(
                                    "processing_time_ms", 0.0
                                ),
                                "frame_size": len(frame_data) if frame_data else 0,
                            },
                        )

                    # Record alert if suspicious behavior detected
                    if analysis_data.get("behavior_detected"):
                        active_sessions[session_id]["alerts_generated"] = (
                            active_sessions[session_id].get("alerts_generated", 0) + 1
                        )
                        record_analytics_alert(
                            session_id,
                            {
                                "location": "Camera Feed",
                                "category": "Behavioral Alert",
                                "description": f"Suspicious behaviors detected: {', '.join(analysis_data.get('behaviors', []))}",
                                "severity": "high"
                                if len(analysis_data.get("behaviors", [])) > 1
                                else "medium",
                                "confidence": analysis_data.get("confidence", 0.0),
                                "metadata": {
                                    "people_count": analysis_data.get(
                                        "people_count", 0
                                    ),
                                    "behaviors": analysis_data.get("behaviors", []),
                                },
                            },
                        )

        except Exception as e:
            print(f"Error processing frame from session {session_id}: {e}")
            socketio.emit(
                "error", {"message": "Frame processing failed"}, room=session_id
            )


@surveillance_bp.route("/get_confidence")
def get_confidence():
    """Get the current confidence level."""
    try:
        confidence = controller.get_confidence_level()
        return jsonify({"confidence": confidence})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@surveillance_bp.route("/session_stats")
def get_session_stats():
    """Get current session statistics."""
    try:
        # Calculate additional stats
        current_time = time.time()
        active_session_details = []

        for session_id, session_info in active_sessions.items():
            duration = current_time - session_info["start_time"]
            time_since_activity = current_time - session_info["last_activity"]

            active_session_details.append(
                {
                    "id": session_id[:8] + "...",  # Truncated for privacy
                    "duration": round(duration, 1),
                    "frames_sent": session_info["frames_sent"],
                    "frames_processed": session_info["frames_processed"],
                    "time_since_activity": round(time_since_activity, 1),
                    "user_agent": session_info["user_agent"],
                }
            )

        stats = {
            **session_stats,
            "active_sessions": active_session_details,
            "avg_frames_per_session": (
                session_stats["total_frames_processed"]
                / max(session_stats["total_sessions"], 1)
            ),
            "processing_status": controller.frame_service.is_processing,
        }

        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@surveillance_bp.route("/system_status")
def get_system_status():
    """Get comprehensive system status."""
    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        incoming_queue_size = controller.frame_service.incoming_frame_queue.qsize()
        processed_queue_size = controller.frame_service.processed_frame_queue.qsize()

        performance_monitor.check_queue_performance(
            incoming_queue_size, processed_queue_size
        )

        status = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
            },
            "processing": {
                "is_processing": controller.frame_service.is_processing,
                "incoming_queue_size": incoming_queue_size,
                "processed_queue_size": processed_queue_size,
                "max_queue_size": 10,
            },
            "sessions": {
                "active_count": len(active_sessions),
                "total_sessions": session_stats["total_sessions"],
                "total_frames_processed": session_stats["total_frames_processed"],
            },
        }

        return jsonify(status)
    except Exception as e:
        status = {
            "system": {"status": "metrics_unavailable", "error": str(e)},
            "processing": {
                "is_processing": controller.frame_service.is_processing,
                "incoming_queue_size": controller.frame_service.incoming_frame_queue.qsize(),
                "processed_queue_size": controller.frame_service.processed_frame_queue.qsize(),
            },
            "sessions": {
                "active_count": len(active_sessions),
                "total_sessions": session_stats["total_sessions"],
                "total_frames_processed": session_stats["total_frames_processed"],
            },
        }
        return jsonify(status)
