"""
Model for pose estimation using YOLOv8-pose.
"""
from ultralytics import YOLO
import cv2
import numpy as np
import logging
import config # To access POSEFORMER_MODEL (or similar) path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class PoseEstimationModel:
    def __init__(self):
        """
        Initialize the YOLOv8-pose model for pose estimation.
        Assumes 'yolov8n-pose.pt' or similar is available at config.POSEFORMER_MODEL.
        """
        try:
            # We'll use config.POSEFORMER_MODEL as the path for the YOLO-pose model
            self.model = YOLO(config.POSEFORMER_MODEL)
            logger.info(f"YOLOv8-pose model loaded successfully from {config.POSEFORMER_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load YOLOv8-pose model from {config.POSEFORMER_MODEL}: {e}")
            self.model = None # Ensure model is None if loading fails

    def detect_pose(self, frame: np.ndarray, person_box: tuple = None) -> list:
        """
        Detects key points on people in a given frame.

        Args:
            frame (np.ndarray): The full image frame to analyze.
            person_box (tuple, optional): An optional bounding box (x1, y1, x2, y2)
                                          to crop the frame and perform pose detection
                                          only on a specific person. If None, detects in full frame.

        Returns:
            list: A list of detected pose results. Each item in the list corresponds
                  to a person and contains their keypoints and confidence scores.
                  Example structure for one person's pose:
                  [
                      {'keypoints': [[x1, y1, conf1], [x2, y2, conf2], ...],
                       'box': [x1_orig, y1_orig, x2_orig, y2_orig],
                       'score': detection_score}
                  ]
        """
        if self.model is None:
            logger.warning("Pose estimation model not loaded. Skipping pose detection.")
            return []

        cropped_frame = frame
        offset_x, offset_y = 0, 0

        if person_box:
            x1, y1, x2, y2 = map(int, person_box)
            cropped_frame = frame[y1:y2, x1:x2]
            offset_x, offset_y = x1, y1 # Offset for converting cropped coords back to original frame

            if cropped_frame.size == 0:
                logger.warning(f"Empty person_box provided. Skipping pose detection for this instance: {person_box}")
                return []

        try:
            # Run inference on the (possibly cropped) frame
            results = self.model(cropped_frame, verbose=False) # verbose=False to suppress output

            detected_poses = []
            if results and results[0].keypoints is not None:
                for person_idx, keypoints_obj in enumerate(results[0].keypoints):
                    # keypoints_obj.xy contains [[x, y], ...]
                    # keypoints_obj.conf contains [conf, ...]
                    
                    # Convert keypoints to a list of [x, y, confidence]
                    kpts = keypoints_obj.xy[0].cpu().numpy() # Get xy coordinates
                    confs = keypoints_obj.conf[0].cpu().numpy() # Get confidence scores
                    
                    # Combine and apply offset if a person_box was used
                    person_keypoints = []
                    for (x, y), conf in zip(kpts, confs):
                        person_keypoints.append([int(x + offset_x), int(y + offset_y), float(conf)])

                    # Get bounding box relative to original frame
                    box = results[0].boxes[person_idx].xyxy[0].cpu().numpy()
                    x1_orig, y1_orig, x2_orig, y2_orig = map(int, box)
                    # Apply offset to bounding box as well if cropped frame was used
                    bbox_in_original_frame = [x1_orig + offset_x, y1_orig + offset_y, x2_orig + offset_x, y2_orig + offset_y]

                    # Store the pose details
                    detected_poses.append({
                        'keypoints': person_keypoints, # [[x,y,conf], ...] relative to original frame
                        'box': bbox_in_original_frame, # bbox relative to original frame
                        'score': results[0].boxes[person_idx].conf.item() # Detection confidence
                    })
            return detected_poses

        except Exception as e:
            logger.error(f"Error during pose detection: {e}")
            return []

    def draw_keypoints(self, frame: np.ndarray, keypoints: list) -> np.ndarray:
        """
        Draws detected keypoints and skeletal lines on the frame.

        Args:
            frame (np.ndarray): The image frame to draw on.
            keypoints (list): A list of keypoints for one person, e.g., [[x, y, conf], ...].

        Returns:
            np.ndarray: The frame with keypoints drawn.
        """
        if not keypoints:
            return frame

        # Define connections for drawing skeleton (e.g., COCO keypoint model)
        # These are common connections for 17 keypoints (head, shoulders, elbows, wrists, hips, knees, ankles)
        # You might need to adjust these based on the exact keypoint model YOLO-pose uses if it's different.
        CONNECTIONS = [
            (0, 1), (0, 2), (1, 3), (2, 4),  # Head to shoulders, arms
            (5, 6), (5, 7), (6, 8), (7, 9), (8, 10), # Torso and arms
            (5, 11), (6, 12), (11, 13), (12, 14), # Hips to legs
            (13, 15), (14, 16) # Knees to ankles
        ]
        
        # Ensure keypoints are in the expected format (list of lists/tuples with x, y, conf)
        # Filter out keypoints with very low confidence if desired
        valid_keypoints = [kp for kp in keypoints if len(kp) == 3 and kp[2] > 0.3] # Example confidence threshold

        # Draw circles for each keypoint
        for kp in valid_keypoints:
            x, y = int(kp[0]), int(kp[1])
            cv2.circle(frame, (x, y), 3, (0, 255, 255), -1) # Yellow circles

        # Draw lines between connected keypoints
        for connection in CONNECTIONS:
            idx1, idx2 = connection
            if idx1 < len(valid_keypoints) and idx2 < len(valid_keypoints):
                # Find the actual keypoint data based on index, not just index itself
                kp1 = next((kp for i, kp in enumerate(keypoints) if i == idx1), None)
                kp2 = next((kp for i, kp in enumerate(keypoints) if i == idx2), None)

                if kp1 and kp2 and kp1[2] > 0.3 and kp2[2] > 0.3: # Draw only if both points are confident
                    x1, y1 = int(kp1[0]), int(kp1[1])
                    x2, y2 = int(kp2[0]), int(kp2[1])
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2) # Green lines

        return frame
