"""
Configuration settings for the SafeVision application.
"""
import os

# Directory settings
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(ROOT_DIR, "detected_behaviors")
MODELS_DIR = os.path.join(ROOT_DIR, "models")

# Model settings
YOLO_MODEL_PATH = os.path.join(MODELS_DIR, "yolov8n.pt")
BEHAVIOR_MODEL = "microsoft/resnet-50"

# Detection settings
SAVE_INTERVAL = 10 * 60  # Save images every 10 minutes
MOVEMENT_THRESHOLD = 40  # Threshold for sudden movement detection
EDGE_THRESHOLD = 80  # Threshold for edge of frame detection
FACE_SIZE_THRESHOLD = 160  # Threshold for detecting leaning forward
SKIN_AREA_THRESHOLD = 5000  # Threshold for significant skin area

# Behavior detection settings
SKIN_COLOR_LOWER = [0, 20, 70]  # Lower HSV range for skin color
SKIN_COLOR_UPPER = [20, 255, 255]  # Upper HSV range for skin color

# Web server settings
DEBUG = True
HOST = "127.0.0.1"
PORT = 5000

# Create necessary directories
os.makedirs(SAVE_DIR, exist_ok=True)