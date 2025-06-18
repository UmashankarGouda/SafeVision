import cv2
import numpy as np
from PIL import Image
from transformers import pipeline
import config

class BehaviorClassificationModel:
    def __init__(self):
        self.classifier = pipeline(
            "image-classification", 
            model=config.BEHAVIOR_MODEL,
            use_fast=True
        )
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.people_tracking = {}
    
    def classify_behavior(self, frame, person_id, box):
        x1, y1, x2, y2 = box
        person_frame = frame[y1:y2, x1:x2] 
        if person_frame.size == 0:
            return "Unknown"
        frame_rgb = cv2.cvtColor(person_frame, cv2.COLOR_BGR2RGB)
        resized_frame = cv2.resize(frame_rgb, (224, 224)) 
        pil_image = Image.fromarray(resized_frame)

        try:
            predictions = self.classifier(pil_image)
            ml_behavior = self.interpret_behavior(predictions)
        except Exception as e:
            print(f"Error in ML classification: {e}")
            ml_behavior = "Normal"
        
        behaviors = []
        gray = cv2.cvtColor(person_frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        person_center_x = (x1 + x2) // 2
        person_center_y = (y1 + y2) // 2
        if f"Person_{person_id}" in self.people_tracking:
            prev_x, prev_y = self.people_tracking[f"Person_{person_id}"]
            movement_x = abs(person_center_x - prev_x)
            movement_y = abs(person_center_y - prev_y)
            if movement_x > config.MOVEMENT_THRESHOLD or movement_y > config.MOVEMENT_THRESHOLD:
                behaviors.append("Rapid Movement")
        
        self.people_tracking[f"Person_{person_id}"] = (person_center_x, person_center_y)
        
        frame_width = frame.shape[1]
        if x1 < config.EDGE_THRESHOLD or x2 > frame_width - config.EDGE_THRESHOLD:
            behaviors.append("Looking Away")
        for (fx, fy, fw, fh) in faces:
            if fh > config.FACE_SIZE_THRESHOLD: 
                behaviors.append("Leaning Forward")
        hsv = cv2.cvtColor(person_frame, cv2.COLOR_BGR2HSV)
        lower_skin = np.array(config.SKIN_COLOR_LOWER, dtype=np.uint8)
        upper_skin = np.array(config.SKIN_COLOR_UPPER, dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > config.SKIN_AREA_THRESHOLD:  
                hx, hy, hw, hh = cv2.boundingRect(cnt)
                if hy < (y2 - y1) // 2:  
                    behaviors.append("Hands Raised")
        
        if ml_behavior == "Panicked" or "Rapid Movement" in behaviors:
            final_behavior = "Panicked"
        elif len(behaviors) > 0:
            final_behavior = " & ".join(behaviors)
        else:
            final_behavior = ml_behavior
            
        return final_behavior
    
    def interpret_behavior(self, predictions):
        panic_indicators = ['stressed', 'anxious', 'tense', 'panic', 'afraid', 'scared']
        for pred in predictions:
            if any(indicator in pred['label'].lower() for indicator in panic_indicators):
                return 'Panicked'
        return 'Normal'