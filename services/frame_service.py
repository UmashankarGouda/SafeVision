"""
Service for handling video frames and frame processing.
"""
import os
import cv2
import time
import config
from models.integrated_surveillance_system import IntegratedSurveillanceSystem

class FrameService:
    def __init__(self, save_interval=None):
        """
        Initialize the frame service.
        
        Args:
            save_interval: How often to save frames in seconds (defaults to config value)
        """
        self.save_interval = save_interval or config.SAVE_INTERVAL
        self.analyzer = IntegratedSurveillanceSystem(save_interval=self.save_interval)
        self.camera = None
        self.confidence_level = 0  # Initialize confidence level
    
    def start_camera(self, camera_id=0):
        """
        Start the camera capture.
        
        Args:
            camera_id: Camera device ID
            
        Returns:
            bool: True if camera started successfully
        """
        self.camera = cv2.VideoCapture(camera_id)
        return self.camera.isOpened()
    
    def stop_camera(self):
        """Release camera resources."""
        if self.camera:
            self.camera.release()
    
    def get_frame(self):
        """
        Get a frame from the camera.
        
        Returns:
            tuple: (success, frame)
        """
        if not self.camera:
            self.start_camera()
            
        ret, frame = self.camera.read()
        return ret, frame
    
    def generate_frames(self):
        """
        Generator that yields processed frames for the video feed.
        
        Yields:
            bytes: JPEG encoded frame
        """
        while True:
            success, frame = self.get_frame()
            if not success:
                break
            
            # Process and analyze the frame
            processed_frame, analysis = self.analyze_and_process_frame(frame)
            
            # Update confidence level based on analysis
            if analysis['behavior_detected']:
                # If suspicious behavior detected, increase confidence
                self.confidence_level = min(100, self.confidence_level + 5)
            else:
                # If no suspicious behavior, slowly decrease confidence
                self.confidence_level = max(0, self.confidence_level - 1)
            
            # Encode the frame as JPEG
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            
            # Convert to bytes and yield
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    def get_confidence_level(self):
        """
        Get the current confidence level of suspicious activity.
        
        Returns:
            int: Confidence level (0-100)
        """
        return self.confidence_level
    
    def analyze_and_process_frame(self, frame):
        """
        Analyze a frame and process it for display.
        
        Args:
            frame: Image frame
            
        Returns:
            tuple: (processed_frame, analysis_results)
        """
        # Analyze frame
        analysis = self.analyzer.analyze_frame(frame, save_images=False)
        
        # Print people count and behaviors
        print(f"People Count: {analysis['people_count']}")
        for behavior in analysis['behaviors']:
            print(f"Behavior: {behavior}")
        
        # Save frame if panicked behavior is detected
        if any('Panicked' in behavior for behavior in analysis['behaviors']):
            file_path = os.path.join(config.SAVE_DIR, f"panicked_surveillance_{int(time.time())}.jpg")
            cv2.imwrite(file_path, frame)
            print("Panicked behavior detected! Frame saved.")
        
        # Draw bounding boxes and labels
        processed_frame = frame.copy()
        
        for i, (x1, y1, x2, y2) in enumerate(analysis['people_boxes']):
            # Use different colors for different behavior states
            if "Panicked" in analysis['behaviors'][i]:
                color = (0, 0, 255)  # Red for panicked
            elif "Aggressive" in analysis['behaviors'][i]:
                color = (0, 0, 255)  # Red for aggressive
            elif "Normal" in analysis['behaviors'][i]:
                color = (0, 255, 0)  # Green for normal
            else:
                color = (255, 255, 0)  # Yellow for other behaviors
                
            cv2.rectangle(processed_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw behavior text above bounding box
            cv2.putText(processed_frame, 
                analysis['behaviors'][i], 
                (x1, y1 - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                color, 
                2
            )
            
            # Draw pose keypoints if available
            if i < len(analysis.get('keypoints', [])) and analysis['keypoints'][i] is not None:
                keypoints = analysis['keypoints'][i]
                
                # Draw keypoints and connections based on pose_model.visualize_pose logic
                # This is simplified for consistency with the MediaPipe implementation
                pose_vis = self.analyzer.behavior_classifier.pose_model.visualize_pose(
                    processed_frame[y1:y2, x1:x2], 
                    keypoints
                )
                
                # Replace the region with the visualization if successful
                if pose_vis is not None and pose_vis.size > 0:
                    processed_frame[y1:y2, x1:x2] = pose_vis

        # Display people count
        cv2.putText(processed_frame, 
            f"People: {analysis['people_count']}", 
            (10, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (255, 255, 255), 
            2
        )
        
        # Display confidence level
        cv2.putText(processed_frame, 
            f"Suspicion: {self.confidence_level}%", 
            (10, 70), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (0, 0, 255) if self.confidence_level > 50 else (255, 255, 255), 
            2
        )
        
        return processed_frame, analysis