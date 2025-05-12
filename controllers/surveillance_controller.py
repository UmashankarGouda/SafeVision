"""
Controller for handling surveillance functionality.
"""
import cv2
import json
import config
from services.frame_service import FrameService

class SurveillanceController:
    def __init__(self):
        """Initialize the surveillance controller."""
        self.frame_service = FrameService()
        self._frame_generator = None

    def get_frame_generator(self):
        """
        Get a generator that yields processed frames.
        
        Returns:
            generator: Frame generator
        """
        if not self._frame_generator:
            self._frame_generator = self.frame_service.generate_frames()
        return self._frame_generator

    def get_confidence_level(self):
        """
        Get the current confidence level of suspicious activity.
        
        Returns:
            dict: JSON response with confidence level
        """
        confidence = self.frame_service.get_confidence_level()
        return json.dumps({"confidence": confidence})

    def stop_camera(self):
        """Release camera resources."""
        self.frame_service.stop_camera()