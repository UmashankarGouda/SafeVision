"""
Model for people detection using YOLOv8.
"""
from ultralytics import YOLO
from config import YOLO_MODEL_PATH

class PeopleDetectionModel:
    def __init__(self):
        """
        Initialize the YOLOv8 model for people detection.
        """
        self.model = YOLO(YOLO_MODEL_PATH)  # Pretrained YOLOv8 model
    
    def detect_people(self, frame):
        """
        Detect people in a given frame.
        
        Args:
            frame: The image frame to analyze
            
        Returns:
            dict: Dictionary containing the count of people and their bounding boxes
        """
        results = self.model(frame)
        people = [box for box in results[0].boxes if box.cls[0] == 0]  # Class 0 is 'person'
        
        boxes = []
        for i, box in enumerate(people):
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
            boxes.append((x1, y1, x2, y2))
        
        return {
            'count': len(people),
            'boxes': boxes
        }