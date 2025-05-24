"""
Controller for handling surveillance operations.
"""

import random
from services.frame_service import FrameService


class SurveillanceController:
    def __init__(self):
        """Initialize the surveillance controller."""
        self.frame_service = FrameService()
        self._frame_generator = None

    def get_frame_generator(self):
        """
        Get a generator for streaming video frames.

        Returns:
            generator: Frame generator
        """
        if self._frame_generator is None:
            self._frame_generator = self.frame_service.generate_frames()
        return self._frame_generator

    def release_resources(self):
        """Release all resources used by the controller."""
        self.frame_service.stop_processing()
        self._frame_generator = None

    def get_confidence_level(self):
        """
        Get the current confidence level of the system.
        Currently implements a random confidence level for demonstration.

        Returns:
            int: Confidence level (0-100)
        """
        # This is a placeholder. In a real system, this would be calculated
        # based on model confidence scores, detection rates, etc.
        return random.randint(50, 80)
