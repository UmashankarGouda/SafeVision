"""
Integrated surveillance system that combines people detection and behavior classification.
"""

import time
from models.people_detection_model import PeopleDetectionModel
from models.behavior_classification_model import BehaviorClassificationModel


class IntegratedSurveillanceSystem:
    def __init__(
        self, save_interval=5, yolo_device=None, yolo_imgsz=640, yolo_half=False
    ):
        """
        Initialize the integrated surveillance system.

        Args:
            save_interval: Time interval in seconds between saving images
            yolo_device: Device for YOLO model (e.g., 'cuda:0' or 'cpu')
            yolo_imgsz: Image size for YOLO model input
            yolo_half: Whether to use half-precision (FP16) for YOLO model
        """
        self.people_detector = PeopleDetectionModel(device=yolo_device)
        self.behavior_classifier = BehaviorClassificationModel()
        self.person_counter = 1  # To label persons uniquely
        self.save_interval = save_interval  # Time interval in seconds
        self.last_save_time = time.time()  # Initialize last save time
        # Store YOLO inference parameters
        self.yolo_imgsz = yolo_imgsz
        self.yolo_half = yolo_half

    def analyze_frame(self, frame, save_images=True):
        """
        Analyze a frame for people and their behaviors.

        Args:
            frame: The image frame to analyze
            save_images: Whether to save images of detected behaviors

        Returns:
            dict: Analysis results including people count, behaviors, boxes, and detection flag
        """
        people_data = self.people_detector.detect_people(
            frame, imgsz=self.yolo_imgsz, half=self.yolo_half
        )
        behaviors = []
        # current_time = time.time()
        behavior_detected = False

        # Process each detected person
        for i, box in enumerate(people_data["boxes"]):
            x1, y1, x2, y2 = box
            person_frame = frame[
                y1:y2, x1:x2
            ].copy()  # Copy to avoid modifying original

            # Skip if person crop is empty
            if person_frame.size == 0:
                behaviors.append(f"Person {i + 1}: Not fully visible")
                continue

            behavior = self.behavior_classifier.classify_behavior(frame, i, box)
            behaviors.append(f"Person {i + 1}: {behavior}")

            # Check if this is an interesting behavior to save
            if behavior != "Normal":
                behavior_detected = True

        return {
            "people_count": people_data["count"],
            "behaviors": behaviors,
            "people_boxes": people_data["boxes"],
            "behavior_detected": behavior_detected,
        }
