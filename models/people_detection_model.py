"""
Model for people detection using YOLOv8.
"""

import os
import logging
from contextlib import contextmanager


@contextmanager
def yolo_logging_to_csv(csv_path):
    logger = logging.getLogger("ultralytics")
    old_handlers = logger.handlers[:]
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(csv_path, mode="a", encoding="utf-8")
    formatter = logging.Formatter("%(message)s")
    file_handler.setFormatter(formatter)
    logger.handlers = [file_handler]
    try:
        yield
    finally:
        file_handler.close()
        logger.handlers = old_handlers


class PeopleDetectionModel:
    def __init__(self, device=None):  # Allow specifying device
        self.model = None  # Lazy load
        self.csv_path = os.path.join(os.path.dirname(__file__), "yolo_output.csv")
        self.device = device  # Store device preference

    def detect_people(
        self, frame, imgsz=640, half=False
    ):  # Add imgsz and half parameters
        if self.model is None:
            from ultralytics import YOLO
            from config import (
                YOLO_MODEL_PATH,
            )  # Assuming this points to yolov8n.pt or similar

            self.model = YOLO(YOLO_MODEL_PATH, verbose=False, task="detect")
            if self.device:
                self.model.to(self.device)
            if (
                half and self.device and "cpu" not in str(self.device).lower()
            ):  # half precision only on CUDA
                try:
                    self.model.half()  # Convert model to FP16
                except Exception as e:
                    print(f"Warning: Could not convert model to half precision: {e}")
            elif half and (not self.device or "cpu" in str(self.device).lower()):
                print(
                    "Warning: Half precision (FP16) is typically for GPU. Running on CPU without half precision."
                )

        # Ensure frame is in the correct format if needed (e.g., numpy array)
        # results = self.model(frame, imgsz=imgsz, half=half if self.device and 'cpu' not in str(self.device).lower() else False, verbose=False)
        # Simpler call, verbose is already set on model.
        # Forcing half=False on CPU to prevent potential issues if model.half() was skipped.
        run_half = (
            half
            and self.device
            and "cpu" not in str(self.device).lower()
            and hasattr(self.model, "fp16")
        )  # Check if model was successfully converted

        with yolo_logging_to_csv(self.csv_path):
            results = self.model(
                frame, imgsz=imgsz, half=run_half, verbose=False
            )  # Pass imgsz and half

        people = [
            box for box in results[0].boxes if box.cls[0] == 0
        ]  # Class 0 is 'person'
        boxes = []
        for i, box in enumerate(people):
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
            boxes.append((x1, y1, x2, y2))
        return {"count": len(people), "boxes": boxes}
