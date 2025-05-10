from flask import Flask, render_template, Response, jsonify,request
import cv2
import torch
import os
import time
import numpy as np
from ultralytics import YOLO
from transformers import pipeline
from PIL import Image
import socket
import struct
import pickle
import random
import argparse
import logging


# Create folders to save images
SAVE_DIR = "detected_behaviors"
os.makedirs(SAVE_DIR, exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
                # Draw hand region (commented out to avoid modifying the original frame)
                # cv2.rectangle(person_frame, (hx, hy), (hx + hw, hy + hh), (0, 255, 0), 2)
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
            
            # Skip if person crop is empty
            if person_frame.size == 0:
                behaviors.append(f"Person {i+1}: Not fully visible")
                continue
                
            behavior = self.behavior_classifier.classify_behavior(frame, i, box)
            behaviors.append(f"Person {i+1}: {behavior}")
            
            # Check if this is an interesting behavior to save
            if behavior != "Normal":
                behavior_detected = True

        return {
            'people_count': people_data['count'],
            'behaviors': behaviors,
            'people_boxes': people_data['boxes'],
            'behavior_detected': behavior_detected
        }

def parse_arguments():
    """Parse command line arguments while maintaining compatibility with Flask"""
    # Create our own parser for custom arguments
    parser = argparse.ArgumentParser(description='Surveillance System with multiple input options')
    
    # Add arguments with '--surveillance-' prefix to avoid conflicts with Flask's own args
    parser.add_argument('--surveillance-source', type=str, default='webcam',
                       choices=['webcam', 'video', 'ip'],
                       help='Input source: "webcam", "video", or "ip" (default: webcam)')
    parser.add_argument('--surveillance-video', type=str, default='',
                       help='Path to video file (required if source is "video")')
    parser.add_argument('--surveillance-ip', type=str, default='',
                       help='URL of IP camera stream (required if source is "ip")')
    parser.add_argument('--surveillance-webcam', type=int, default=0,
                       help='Index of webcam to use (default: 0)')
    
    # Parse known args only to avoid conflicts with Flask
    args, _ = parser.parse_known_args()
    return args

app = Flask(__name__)
# Global state for current source
current_source = {
    'source': 'webcam',
    'video': '',
    'ip': '',
    'webcam': 0,
    'cap': None,
    'last_updated': time.time()
}

def initialize_capture(source, video_path, ip_url, webcam_index):
    global current_source
    if current_source['cap'] is not None:
        current_source['cap'].release()
    try:
        if source == 'video':
            if not video_path or not os.path.exists(video_path):
                raise ValueError(f"Video file {video_path} does not exist")
            cap = cv2.VideoCapture(video_path)
        elif source == 'ip':
            if not ip_url:
                raise ValueError("IP camera URL is required")
            cap = cv2.VideoCapture(ip_url)
        else:
            cap = cv2.VideoCapture(webcam_index)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video source: {source}")
        current_source['cap'] = cap
        logger.info(f"Initialized video source: {source}")
        return True
    except Exception as e:
        logger.error(f"Error initializing video source: {e}")
        current_source['cap'] = None
        return False
def load_config(config_path='config.json'):
    """Load configuration from a JSON file if it exists."""
    import json
    import os
    default_config = {
        'source': 'webcam',
        'video': '',
        'ip': '',
        'webcam': 0
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            default_config.update(config)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {e}")
    return default_config


def generate_frames():
    global current_source
    config = load_config()
    args = parse_arguments()
    source = args.surveillance_source if args.surveillance_source else config['source']
    video_path = args.surveillance_video if args.surveillance_video else config['video']
    ip_url = args.surveillance_ip if args.surveillance_ip else config['ip']
    webcam_index = args.surveillance_webcam if args.surveillance_webcam is not None else config['webcam']
    current_source.update({'source': source, 'video': video_path, 'ip': ip_url, 'webcam': webcam_index})
    
    if not initialize_capture(source, video_path, ip_url, webcam_index):
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(blank_frame, "Error: Invalid Source", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        _, buffer = cv2.imencode('.jpg', blank_frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        return
    
    SAVE_INTERVAL = 10 * 60
    analyzer = IntegratedSurveillanceSystem(save_interval=SAVE_INTERVAL)
    
    while True:
        if current_source['cap'] is None:
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank_frame, "Error: Invalid Source", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            _, buffer = cv2.imencode('.jpg', blank_frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            continue
        ret, frame = current_source['cap'].read()
        if not ret:
            if current_source['source'] == 'video':
                current_source['cap'].set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            logger.error("Error: Could not read frame")
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank_frame, "Error: Frame Read Failed", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            _, buffer = cv2.imencode('.jpg', blank_frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            continue
        analysis = analyzer.analyze_frame(frame)
        cv2.putText(frame, f"Source: {current_source['source']}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')




@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    headers={"Access-Control-Allow-Origin": "*"},
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/get_confidence')
def get_confidence():
    return jsonify({'confidence_level': random.randint(50, 80)})

@app.route('/set_source', methods=['POST'])
def set_source():
    global current_source
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    source = data.get('source', 'webcam')
    video_path = data.get('video', '')
    ip_url = data.get('ip', '')
    webcam_index = data.get('webcam', 0)
    if source not in ['webcam', 'video', 'ip']:
        return jsonify({'status': 'error', 'message': 'Invalid source'}), 400
    current_source.update({'source': source, 'video': video_path, 'ip': ip_url, 'webcam': webcam_index, 'last_updated': time.time()})
    if initialize_capture(source, video_path, ip_url, webcam_index):
        return jsonify({'status': 'success', 'source': source})
    return jsonify({'status': 'error', 'message': f'Failed to initialize {source}'}), 400

if __name__ == '__main__':
    app.run(debug=True)