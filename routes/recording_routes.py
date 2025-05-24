"""
Video recording routes for SafeVision.
Provides API endpoints for video recording and management.
"""

from flask import Blueprint, jsonify, request, send_file
from services import video_recorder
import os
import mimetypes

recording_bp = Blueprint("recording", __name__, url_prefix="/api/recording")


@recording_bp.route("/start", methods=["POST"])
def start_recording():
    """Start recording for a session."""
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        user_agent = data.get(
            "user_agent", request.headers.get("User-Agent", "Unknown")
        )

        if not session_id:
            return jsonify({"error": "Session ID is required"}), 400

        result = video_recorder.start_recording(session_id, user_agent)

        if "error" in result:
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@recording_bp.route("/stop", methods=["POST"])
def stop_recording():
    """Stop recording for a session."""
    try:
        data = request.get_json()
        session_id = data.get("session_id")

        if not session_id:
            return jsonify({"error": "Session ID is required"}), 400

        result = video_recorder.stop_recording(session_id)

        if "error" in result:
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@recording_bp.route("/add_frame", methods=["POST"])
def add_frame():
    """Add a frame to the current recording."""
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        frame_data = data.get("frame_data")

        if not session_id or not frame_data:
            return jsonify({"error": "Session ID and frame data are required"}), 400

        success = video_recorder.add_frame(session_id, frame_data)

        if not success:
            return jsonify({"error": "Failed to add frame to recording"}), 400

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@recording_bp.route("/status/<session_id>")
def get_recording_status(session_id):
    """Get recording status for a session."""
    try:
        status = video_recorder.get_recording_status(session_id)
        return jsonify(status)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@recording_bp.route("/list")
def list_recordings():
    """Get list of all recordings."""
    try:
        recordings = video_recorder.get_all_recordings()

        for recording in recordings:
            for key in ["start_time", "end_time", "created_time"]:
                if key in recording and recording[key]:
                    recording[key] = recording[key].isoformat()

        return jsonify({"recordings": recordings})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@recording_bp.route("/download/<filename>")
def download_recording(filename):
    """Download a recording file."""
    try:
        if ".." in filename or "/" in filename or "\\" in filename:
            return jsonify({"error": "Invalid filename"}), 400

        filepath = os.path.join(video_recorder.output_dir, filename)

        if not os.path.exists(filepath):
            return jsonify({"error": "Recording not found"}), 404

        mime_type = mimetypes.guess_type(filepath)[0] or "application/octet-stream"

        return send_file(
            filepath, as_attachment=True, download_name=filename, mimetype=mime_type
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@recording_bp.route("/thumbnail/<filename>")
def get_thumbnail(filename):
    """Get thumbnail for a recording."""
    try:
        if ".." in filename or "/" in filename or "\\" in filename:
            return jsonify({"error": "Invalid filename"}), 400

        thumbnail_filename = filename.replace(".mp4", "_thumb.jpg")
        thumbnail_path = os.path.join(video_recorder.output_dir, thumbnail_filename)

        if not os.path.exists(thumbnail_path):
            return jsonify({"error": "Thumbnail not found"}), 404

        return send_file(thumbnail_path, mimetype="image/jpeg")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@recording_bp.route("/delete/<filename>", methods=["DELETE"])
def delete_recording(filename):
    """Delete a recording."""
    try:
        if ".." in filename or "/" in filename or "\\" in filename:
            return jsonify({"error": "Invalid filename"}), 400

        result = video_recorder.delete_recording(filename)

        if "error" in result:
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@recording_bp.route("/cleanup", methods=["POST"])
def cleanup_recordings():
    """Clean up old recordings."""
    try:
        data = request.get_json() or {}
        max_age_days = data.get("max_age_days", 30)

        if max_age_days < 1:
            return jsonify({"error": "max_age_days must be at least 1"}), 400

        result = video_recorder.cleanup_old_recordings(max_age_days)

        if "error" in result:
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@recording_bp.route("/storage_info")
def get_storage_info():
    """Get storage information for recordings."""
    try:
        recordings_dir = video_recorder.output_dir

        total_size = 0
        file_count = 0

        if os.path.exists(recordings_dir):
            for filename in os.listdir(recordings_dir):
                filepath = os.path.join(recordings_dir, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
                    if filename.endswith(".mp4"):
                        file_count += 1

        import shutil

        total_space, used_space, free_space = shutil.disk_usage(recordings_dir)

        return jsonify(
            {
                "recordings_count": file_count,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "disk_total_gb": round(total_space / (1024 * 1024 * 1024), 2),
                "disk_used_gb": round(used_space / (1024 * 1024 * 1024), 2),
                "disk_free_gb": round(free_space / (1024 * 1024 * 1024), 2),
                "recordings_dir": recordings_dir,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
