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
BEHAVIOR_MODEL = "google/mobilenet_v2_1.0_224"
USE_GPU_IF_AVAILABLE = True  # Set to False to force CPU, or add logic to auto-detect

# Detection settings
SAVE_INTERVAL = 10 * 60  # Save images every 10 minutes
MOVEMENT_THRESHOLD = 40  # Threshold for sudden movement detection
EDGE_THRESHOLD = 80  # Threshold for edge of frame detection
FACE_SIZE_THRESHOLD = 160  # Threshold for detecting leaning forward
SKIN_AREA_THRESHOLD = 5000  # Threshold for significant skin area

# Behavior detection settings
SKIN_COLOR_LOWER = [0, 20, 70]  # Lower HSV range for skin color
SKIN_COLOR_UPPER = [20, 255, 255]  # Upper HSV range for skin color

# Browser camera settings
CAMERA_SETTINGS = {
    "frame_rate": 10,  # FPS for frame capture
    "video_quality": 0.8,  # JPEG quality (0.1 to 1.0)
    "video_width": 640,
    "video_height": 480,
    "preferred_facing_mode": "user",  # "user" for front, "environment" for rear
    "enable_recording": True,
    "max_recording_duration": 300,  # 5 minutes max recording
    "enable_mobile_optimizations": True,
}

# Performance settings
PROCESSING_SETTINGS = {
    "max_queue_size": 10,
    "frame_timeout": 1.0,  # seconds
    "enable_frame_dropping": True,  # Drop frames if queue is full
    "webp_quality": 80,  # WebP compression quality for processed frames
}

# Session management
SESSION_SETTINGS = {
    "session_timeout": 1800,  # 30 minutes
    "max_concurrent_sessions": 10,
    "cleanup_interval": 300,  # 5 minutes
    "log_session_stats": True,
}

# Web server settings
DEBUG = True
HOST = "127.0.0.1"
PORT = 5000

# Create necessary directories
os.makedirs(SAVE_DIR, exist_ok=True)
