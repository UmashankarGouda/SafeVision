"""
Routes for the surveillance application.
"""
from flask import Blueprint, Response, jsonify
from controllers.surveillance_controller import SurveillanceController

# Create Blueprint
surveillance_bp = Blueprint('surveillance', __name__)

# Create controller instance
controller = SurveillanceController()

@surveillance_bp.route('/video_feed')
def video_feed():
    """Stream video feed."""
    return Response(
        controller.get_frame_generator(),
        headers={"Access-Control-Allow-Origin": "*"},
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@surveillance_bp.route('/get_confidence')
def get_confidence():
    """Get the current confidence level."""
    confidence_level = controller.get_confidence_level()
    return jsonify({'confidence_level': confidence_level})