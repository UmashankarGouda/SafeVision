"""
Routes for the surveillance functionality.
"""
from flask import Blueprint, Response, jsonify
from controllers.surveillance_controller import SurveillanceController

surveillance_bp = Blueprint('surveillance', __name__)
controller = SurveillanceController()

@surveillance_bp.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(
        controller.get_frame_generator(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@surveillance_bp.route('/get_confidence')
def get_confidence():
    """Get the confidence level of suspicious activity."""
    return Response(
        controller.get_confidence_level(),
        mimetype='application/json'
    )

@surveillance_bp.route('/stop_camera')
def stop_camera():
    """Stop the camera."""
    controller.stop_camera()
    return jsonify({"status": "success"})