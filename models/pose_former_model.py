"""
PoseFormer model for detecting body postures and aggressive stance detection.
"""
import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from transformers import AutoImageProcessor

class PoseFormerModel:
    def __init__(self):
        """
        Initialize the pose estimation model.
        """
        
        try:
            # Try to use MediaPipe as a simpler alternative for pose detection
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.mediapipe_available = True
            print("Using MediaPipe for pose estimation")
        except ImportError:
            # Fall back to a simpler approach if MediaPipe is not available
            self.mediapipe_available = False
            print("MediaPipe not available, using simple detection methods")
        
        # Define keypoint connections for visualization
        self.keypoint_edges = [
            (0, 1), (0, 2), (1, 3), (2, 4),  # Head to shoulders and shoulders to elbows
            (3, 5), (4, 6),  # Elbows to wrists
            (5, 7), (6, 8),  # Wrists to hands
            (9, 10),  # Shoulders
            (9, 11), (10, 12),  # Shoulders to hips
            (11, 13), (12, 14),  # Hips to knees
            (13, 15), (14, 16)  # Knees to ankles
        ]
        
        # Parameters for aggressive pose detection
        self.aggressive_patterns = {
            "raised_arms": {
                "description": "Arms raised above shoulders",
                "condition": lambda kpts: self._check_raised_arms(kpts)
            },
            "forward_stance": {
                "description": "Forward aggressive stance",
                "condition": lambda kpts: self._check_forward_stance(kpts)
            },
            "wide_stance": {
                "description": "Wide aggressive stance",
                "condition": lambda kpts: self._check_wide_stance(kpts)
            }
        }
    
    def _check_raised_arms(self, kpts):
        """Check if arms are raised above shoulders"""
        # MediaPipe format is different, adapt indexes based on the library used
        if self.mediapipe_available:
            left_shoulder = 11
            left_elbow = 13
            right_shoulder = 12
            right_elbow = 14
            
            # Check if keypoints are visible
            if (kpts[left_shoulder][2] > 0.5 and kpts[left_elbow][2] > 0.5 and
                kpts[right_shoulder][2] > 0.5 and kpts[right_elbow][2] > 0.5):
                
                # Check if elbows are above shoulders
                left_raised = kpts[left_elbow][1] < kpts[left_shoulder][1]
                right_raised = kpts[right_elbow][1] < kpts[right_shoulder][1]
                
                return left_raised or right_raised
        return False
    
    def _check_forward_stance(self, kpts):
        """Check if person has an aggressive forward stance"""
        if self.mediapipe_available:
            nose = 0
            mid_hip = 24  # Approximated mid-hip
            left_hip = 23
            right_hip = 24
            
            if (kpts[nose][2] > 0.5 and kpts[mid_hip][2] > 0.5 and
                kpts[left_hip][2] > 0.5 and kpts[right_hip][2] > 0.5):
                
                # Check if head is positioned forward compared to hips
                return kpts[nose][0] > (kpts[mid_hip][0] + 0.2 * abs(kpts[right_hip][0] - kpts[left_hip][0]))
        return False
    
    def _check_wide_stance(self, kpts):
        """Check if feet are positioned in a wide aggressive stance"""
        if self.mediapipe_available:
            left_shoulder = 11
            right_shoulder = 12
            left_ankle = 27
            right_ankle = 28
            
            if (kpts[left_shoulder][2] > 0.5 and kpts[right_shoulder][2] > 0.5 and
                kpts[left_ankle][2] > 0.5 and kpts[right_ankle][2] > 0.5):
                
                # Check if feet are positioned wider than shoulders
                shoulder_width = abs(kpts[right_shoulder][0] - kpts[left_shoulder][0])
                ankle_width = abs(kpts[right_ankle][0] - kpts[left_ankle][0])
                
                return ankle_width > (1.5 * shoulder_width)
        return False
    
    def detect_pose(self, frame):
        """
        Detect human pose keypoints in the given frame.
        
        Args:
            frame: The image frame to analyze
            
        Returns:
            numpy array: Keypoints in the format [x, y, confidence]
        """
        # Ensure input frame is valid
        if frame is None or frame.size == 0:
            return np.zeros((17, 3))
        
        if self.mediapipe_available:
            # Convert BGR to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(frame_rgb)
            
            # MediaPipe returns landmarks in normalized coordinates [0.0, 1.0]
            if not results.pose_landmarks:
                return np.zeros((33, 3))
            
            # Convert to array format
            h, w = frame.shape[:2]
            landmarks = results.pose_landmarks.landmark
            keypoints = np.array([[landmark.x * w, landmark.y * h, landmark.visibility] 
                                 for landmark in landmarks])
            
            return keypoints
        else:
            # If MediaPipe is not available, return zeros (no detection)
            return np.zeros((17, 3))
    
    def analyze_posture(self, keypoints):
        """
        Analyze the detected pose keypoints to identify aggressive postures.
        
        Args:
            keypoints: numpy array of keypoints with [x, y, confidence]
            
        Returns:
            dict: Analysis results including if posture is aggressive and which patterns detected
        """
        detected_patterns = []
        
        # Skip processing if there are no valid keypoints
        if keypoints is None or not np.any(keypoints):
            return {"is_aggressive": False, "detected_patterns": []}
        
        # Check for each aggressive pattern
        for pattern_name, pattern_info in self.aggressive_patterns.items():
            try:
                if pattern_info["condition"](keypoints):
                    detected_patterns.append({
                        "name": pattern_name,
                        "description": pattern_info["description"]
                    })
            except Exception as e:
                print(f"Error checking pattern {pattern_name}: {e}")
        
        return {
            "is_aggressive": len(detected_patterns) > 0,
            "detected_patterns": detected_patterns
        }
    
    def visualize_pose(self, frame, keypoints):
        """
        Visualize the detected pose on the frame.
        
        Args:
            frame: The image frame
            keypoints: numpy array of keypoints
            
        Returns:
            numpy array: Frame with pose visualization
        """
        if frame is None or frame.size == 0 or keypoints is None:
            return frame
            
        viz_frame = frame.copy()
        
        if self.mediapipe_available:
            # Draw the keypoint connections (skeleton)
            connections = self.mp_pose.POSE_CONNECTIONS
            for connection in connections:
                p1, p2 = connection
                if keypoints[p1][2] > 0.5 and keypoints[p2][2] > 0.5:
                    pt1 = (int(keypoints[p1][0]), int(keypoints[p1][1]))
                    pt2 = (int(keypoints[p2][0]), int(keypoints[p2][1]))
                    cv2.line(viz_frame, pt1, pt2, (0, 255, 255), 2)
            
            # Draw the keypoints
            for i, (x, y, conf) in enumerate(keypoints):
                if conf > 0.5:
                    cv2.circle(viz_frame, (int(x), int(y)), 4, (0, 0, 255), -1)
        
        return viz_frame