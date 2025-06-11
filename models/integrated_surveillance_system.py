import cv2
import numpy as np
from PIL import Image
from transformers import pipeline
import config 

class IntegratedSurveillanceSystem:
    def __init__(self):
        self.classifier = pipeline(
            "image-classification", 
            model=config.BEHAVIOR_MODEL,
            use_fast=True
        )
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.people_tracking = {}

    def classify_behavior(self, frame, person_id, box):
        x1, y1, x2, y2 = box
        person_frame = frame[y1:y2, x1:x2]
        if person_frame.size == 0:
            return "Unknown"

        # Preprocess
        try:
            frame_rgb = cv2.cvtColor(person_frame, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(frame_rgb, (224, 224))
            image = Image.fromarray(resized)

            predictions = self.classifier(image)
            ml_behavior = self.interpret_behavior(predictions)
        except Exception as e:
            print(f"[ML Error] {e}")
            ml_behavior = "Normal"

        behaviors = []

        # Face detection (gray for Haar)
        gray = cv2.cvtColor(person_frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

        # Track rapid movement
        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
        prev = self.people_tracking.get(person_id)
        if prev:
            dx, dy = abs(center_x - prev[0]), abs(center_y - prev[1])
            if dx > config.MOVEMENT_THRESHOLD or dy > config.MOVEMENT_THRESHOLD:
                behaviors.append("Rapid Movement")
        self.people_tracking[person_id] = (center_x, center_y)

        # Edge of frame
        if x1 < config.EDGE_THRESHOLD or x2 > frame.shape[1] - config.EDGE_THRESHOLD:
            behaviors.append("Looking Away")

        for (_, _, _, h) in faces:
            if h > config.FACE_SIZE_THRESHOLD:
                behaviors.append("Leaning Forward")

        hsv = cv2.cvtColor(person_frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array(config.SKIN_COLOR_LOWER, dtype=np.uint8), 
                                np.array(config.SKIN_COLOR_UPPER, dtype=np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            if cv2.contourArea(cnt) > config.SKIN_AREA_THRESHOLD:
                _, hy, _, hh = cv2.boundingRect(cnt)
                if hy < (y2 - y1) // 2:
                    behaviors.append("Hands Raised")

        # Combine
        if ml_behavior == "Panicked" or "Rapid Movement" in behaviors:
            return "Panicked"
        elif behaviors:
            return " & ".join(behaviors)
        return ml_behavior

    def interpret_behavior(self, predictions):
        panic_labels = ['stressed', 'anxious', 'tense', 'panic', 'afraid', 'scared']
        for pred in predictions:
            if any(label in pred['label'].lower() for label in panic_labels):
                return 'Panicked'
        return 'Normal'
