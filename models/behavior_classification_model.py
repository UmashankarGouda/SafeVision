"""
Model for behavior classification using computer vision and ML techniques.
"""
import cv2
import numpy as np
from PIL import Image
from transformers import pipeline
import config
from models.pose_former_model import PoseFormerModel  # Import the new PoseFormer model

class BehaviorClassificationModel:
    def __init__(self):
        """
        Initialize the behavior classification model.
        """
        self.classifier = pipeline(
            "image-classification", 
            model=config.BEHAVIOR_MODEL,
            use_fast=True
        )
        # Load Haar Cascade for face detection (for supplementary face detection)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        # Dictionary to track each person's last position for rapid movement detection
        self.people_tracking = {}
        
        # Initialize PoseFormer model for pose detection
        self.pose_model = PoseFormerModel()
    
    def classify_behavior(self, frame, person_id, box):
        """
        Classify the behavior of a detected person.
        
        Args:
            frame: The full image frame
            person_id: Unique identifier for the person
            box: Bounding box of the person (x1, y1, x2, y2)
            
        Returns:
            str: Classified behavior
        """
        x1, y1, x2, y2 = box
        person_frame = frame[y1:y2, x1:x2]  # Crop person from frame
        
        # Skip empty frames
        if person_frame.size == 0:
            return "Unknown"
        
        # Basic behavior detection using ML model
        # Convert OpenCV frame (BGR) to RGB and resize it
        frame_rgb = cv2.cvtColor(person_frame, cv2.COLOR_BGR2RGB)
        resized_frame = cv2.resize(frame_rgb, (224, 224))  # ResNet expects 224x224 input

        # Convert NumPy array to PIL Image
        pil_image = Image.fromarray(resized_frame)

        # Classify behavior with ML model
        try:
            predictions = self.classifier(pil_image)
            ml_behavior = self.interpret_behavior(predictions)
        except Exception as e:
            print(f"Error in ML classification: {e}")
            ml_behavior = "Normal"
        
        # Supplementary behavior detection
        behaviors = []
        
        # Use face detection within the person region for more detailed analysis
        gray = cv2.cvtColor(person_frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Get person center for tracking
        person_center_x = (x1 + x2) // 2
        person_center_y = (y1 + y2) // 2
        
        # Track movement
        if f"Person_{person_id}" in self.people_tracking:
            prev_x, prev_y = self.people_tracking[f"Person_{person_id}"]
            movement_x = abs(person_center_x - prev_x)
            movement_y = abs(person_center_y - prev_y)
            if movement_x > config.MOVEMENT_THRESHOLD or movement_y > config.MOVEMENT_THRESHOLD:
                behaviors.append("Rapid Movement")
        
        # Update tracking
        self.people_tracking[f"Person_{person_id}"] = (person_center_x, person_center_y)
        
        # Check if person is at edge of frame (looking away)
        frame_width = frame.shape[1]
        if x1 < config.EDGE_THRESHOLD or x2 > frame_width - config.EDGE_THRESHOLD:
            behaviors.append("Looking Away")
        
        # Check leaning forward (if face becomes larger)
        for (fx, fy, fw, fh) in faces:
            if fh > config.FACE_SIZE_THRESHOLD:  # Face appears larger
                behaviors.append("Leaning Forward")
        
        # NEW: PoseFormer-based body language detection
        try:
            # Detect pose keypoints
            keypoints = self.pose_model.detect_pose(person_frame)
            
            # Analyze posture for aggressive patterns
            posture_analysis = self.pose_model.analyze_posture(keypoints)
            
            # Add detected patterns to behaviors
            if posture_analysis["is_aggressive"]:
                for pattern in posture_analysis["detected_patterns"]:
                    behaviors.append(f"Aggressive Posture: {pattern['name']}")
                
            # Store keypoints for visualization (attach to the person object)
            if not hasattr(self, 'person_keypoints'):
                self.person_keypoints = {}
            self.person_keypoints[f"Person_{person_id}"] = keypoints
                
        except Exception as e:
            print(f"Error in pose detection: {e}")
        
        # Combine ML and rule-based behavior detection
        if ml_behavior == "Panicked" or "Rapid Movement" in behaviors or any("Aggressive" in b for b in behaviors):
            final_behavior = "Panicked"
        elif len(behaviors) > 0:
            final_behavior = " & ".join(behaviors)
        else:
            final_behavior = ml_behavior
            
        return final_behavior
    
    def interpret_behavior(self, predictions):
        """
        Interpret ML model predictions to determine behavior.
        
        Args:
            predictions: Raw predictions from the ML model
            
        Returns:
            str: Interpreted behavior
        """
        panic_indicators = ['stressed', 'anxious', 'tense', 'panic', 'afraid', 'scared']
        for pred in predictions:
            if any(indicator in pred['label'].lower() for indicator in panic_indicators):
                return 'Panicked'
        return 'Normal'
        
    def get_person_keypoints(self, person_id):
        """
        Get stored keypoints for a specific person.
        
        Args:
            person_id: Unique identifier for the person
            
        Returns:
            numpy array: Keypoints for the person if available, else None
        """
        if hasattr(self, 'person_keypoints'):
            return self.person_keypoints.get(f"Person_{person_id}")
        return None