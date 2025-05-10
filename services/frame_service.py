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

        # Display people count
        cv2.putText(processed_frame, 
            f"People: {analysis['people_count']}", 
            (10, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (255, 255, 255), 
            2
        )
        
        # Indicate if behavior was detected
        if any('Panicked' in behavior for behavior in analysis['behaviors']):
            cv2.putText(processed_frame, 
                "BEHAVIOR DETECTED!", 
                (10, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                (0, 0, 255), 
                2
            )
            
        return processed_frame, analysis
    
    def get_processed_frame(self):
        """
        Get a processed frame with analysis.
        
        Returns:
            bytes: JPEG encoded frame
        """
        ret, frame = self.get_frame()
        if not ret:
            return None
        
        processed_frame, _ = self.analyze_and_process_frame(frame)
        
        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', processed_frame)
        frame_bytes = buffer.tobytes()
        
        return frame_bytes
    
    def generate_frames(self):
        """
        Generator function to continuously yield processed frames.
        
        Yields:
            bytes: HTTP response chunks containing JPEG frames
        """
        print("Starting surveillance stream...")
        
        while True:
            frame_bytes = self.get_processed_frame()
            
            if frame_bytes is None:
                print("Error: Could not read frame.")
                break
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')