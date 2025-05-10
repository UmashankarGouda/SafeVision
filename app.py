from flask import Flask, render_template, Response, jsonify, request
import cv2
import socket
import struct
import pickle
import os
import time
import numpy as np
from ultralytics import YOLO
from transformers import pipeline
from PIL import Image
import random

# Create folders to save images
SAVE_DIR = "detected_behaviors"
os.makedirs(SAVE_DIR, exist_ok=True)

# YOLOv8 for People Detection
class PeopleDetectionModel:
    def __init__(self):
        self.model = YOLO('models/yolov8n.pt')  # Pretrained YOLOv8 model
    
    def detect_people(self, frame):
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

# Behavior Classification Model
class BehaviorClassificationModel:
    def __init__(self):
        self.classifier = pipeline(
            "image-classification", 
            model="microsoft/resnet-50"
        )
        # Load Haar Cascade for face detection (for supplementary face detection)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        # Dictionary to track each person's last position for rapid movement detection
        self.people_tracking = {}
    
    def classify_behavior(self, frame, person_id, box):
        x1, y1, x2, y2 = box
        person_frame = frame[y1:y2, x1:x2]  # Crop person from frame
        
        # Basic behavior detection using ML model
        # Convert OpenCV frame (BGR) to RGB and resize it
        if person_frame.size == 0:  # Skip empty frames
            return "Unknown"
            
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
        
        # Supplementary behavior detection (from the second module)
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
            if movement_x > 40 or movement_y > 40:  # Threshold for sudden movement
                behaviors.append("Rapid Movement")
        
        # Update tracking
        self.people_tracking[f"Person_{person_id}"] = (person_center_x, person_center_y)
        
        # Check if person is at edge of frame (looking away)
        frame_width = frame.shape[1]
        if x1 < 80 or x2 > frame_width - 80:
            behaviors.append("Looking Away")
        
        # Check leaning forward (if face becomes larger)
        for (fx, fy, fw, fh) in faces:
            if fh > 160:  # Face appears larger
                behaviors.append("Leaning Forward")
        
        # Detect raised hands using skin color detection
        hsv = cv2.cvtColor(person_frame, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Find contours with OpenCV 4+ compatible syntax
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 5000:  # Significant skin area
                hx, hy, hw, hh = cv2.boundingRect(cnt)
                if hy < (y2 - y1) // 2:  # If hand is in upper half of person region
                    behaviors.append("Hands Raised")
        
        # Combine ML and rule-based behavior detection
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

# Integrated Surveillance Analyzer
class IntegratedSurveillanceSystem:
    def __init__(self, save_interval=5):  # Default interval of 5 seconds
        self.people_detector = PeopleDetectionModel()
        self.behavior_classifier = BehaviorClassificationModel()
        self.person_counter = 1  # To label persons uniquely
        self.save_interval = save_interval  # Time interval in seconds
        self.last_save_time = time.time()  # Initialize last save time
    
    def analyze_frame(self, frame, save_images=True):
        people_data = self.people_detector.detect_people(frame)
        behaviors = []
        current_time = time.time()
        behavior_detected = False
        
        # Process each detected person
        for i, box in enumerate(people_data['boxes']):
            x1, y1, x2, y2 = box
            person_frame = frame[y1:y2, x1:x2].copy()  # Copy to avoid modifying original
            if person_frame.size == 0:
                behaviors.append(f"Person {i+1}: Not fully visible")
                continue
            behavior = self.behavior_classifier.classify_behavior(frame, i, box)
            behaviors.append(f"Person {i+1}: {behavior}")
            if behavior != "Normal":
                behavior_detected = True

        return {
            'people_count': people_data['count'],
            'behaviors': behaviors,
            'people_boxes': people_data['boxes'],
            'behavior_detected': behavior_detected
        }

# Flask App
app = Flask(__name__)

# Make sure this global variable is declared at the top of your file
latest_analysis = {
    'people_count': 0,
    'behaviors': [],
    'people_boxes': [],
    'behavior_detected': False
}

# Video frame generator
def generate_frames():
    global latest_analysis
    SAVE_INTERVAL = 10 * 60
    analyzer = IntegratedSurveillanceSystem(save_interval=SAVE_INTERVAL)
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        # Analyze frame
        analysis = analyzer.analyze_frame(frame, save_images=False)

        # 🔄 Update global variable for frontend API
        latest_analysis = analysis

        # Save frame if panicked behavior detected
        if any('Panicked' in behavior for behavior in analysis['behaviors']):
            file_path = os.path.join(SAVE_DIR, f"panicked_surveillance_{int(time.time())}.jpg")
            cv2.imwrite(file_path, frame)

        # Draw bounding boxes and labels
        for i, (x1, y1, x2, y2) in enumerate(analysis['people_boxes']):
            color = (0, 255, 0) if "Normal" in analysis['behaviors'][i] else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, analysis['behaviors'][i], (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        # Yield frame for video feed
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Routes
@app.route('/video_feed_data')
def video_feed_data():
    return jsonify(latest_analysis)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), headers={"Access-Control-Allow-Origin": "*"}, mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def home():
    return render_template('home.html')

def generate_confidence_level():
    # Randomly simulate a confidence level between 50 and 100
    return random.randint(50, 100)

# Modify this function to send confidence_level as part of the metrics
@app.route('/get_metrics')
def get_metrics():
    global latest_analysis

    # Simulating a confidence level
    latest_analysis['confidence_level'] = generate_confidence_level()

    return jsonify(latest_analysis)

UPLOAD_FOLDER = 'uploaded_videos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'success': False, 'message': 'No video uploaded'})

    video_file = request.files['video']
    filename = video_file.filename
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    video_file.save(file_path)

    # Optionally analyze the video in the background

    return jsonify({'success': True, 'message': 'Video uploaded successfully'})

if __name__ == '__main__':
    app.run(debug=True)
