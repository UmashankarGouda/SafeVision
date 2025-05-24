"""
Service for handling video frames and frame processing.
Modified to handle frames from browser instead of server camera.
"""

import os
import cv2
import time
import config
from models.integrated_surveillance_system import IntegratedSurveillanceSystem
import threading
import queue
import numpy as np


class FrameService:
    def __init__(self, save_interval=None):
        """
        Initialize the frame service.

        Args:
            save_interval: How often to save frames in seconds (defaults to config value)
        """
        self.save_interval = save_interval or config.SAVE_INTERVAL
        # Configure YOLO parameters here
        self.analyzer = IntegratedSurveillanceSystem(save_interval=self.save_interval)

        # Threading and Queues for asynchronous processing
        self.incoming_frame_queue = queue.Queue(
            maxsize=10
        )  # Queue for incoming frames from browser
        self.processed_frame_queue = queue.Queue(
            maxsize=10
        )  # Queue for processed (encoded) frames
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.is_processing = False

    def process_incoming_frame(self, frame_data):
        """
        Process a frame received from the browser.

        Args:
            frame_data: Frame data dictionary with 'frame' bytes and metadata

        Returns:
            bool: True if frame was successfully queued for processing
        """
        try:
            # Handle both dictionary format and direct bytes format for compatibility
            if isinstance(frame_data, dict) and "frame" in frame_data:
                # Extract timestamp, frameId and quality if available
                timestamp = frame_data.get("timestamp")
                frame_id = frame_data.get("frameId")
                quality = frame_data.get("quality")
                # Get actual frame data
                frame_bytes = frame_data["frame"]
            else:
                # Legacy format - direct bytes
                frame_bytes = frame_data
                timestamp = None
                frame_id = None
                quality = None
                # Convert bytes to numpy array
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                print("Error: Could not decode frame from browser")
                return False

            # Create frame info with metadata
            frame_info = {
                "frame": frame,
                "timestamp": timestamp,
                "frame_id": frame_id,
                "quality": quality,
            }

            # Add to processing queue
            try:
                self.incoming_frame_queue.put(frame_info, timeout=0.1)
                return True
            except queue.Full:
                # print("Incoming frame queue is full, dropping frame")
                return False

        except Exception as e:
            print(f"Error processing incoming frame: {e}")
            return False

    def _process_frames_loop(self):
        """Continuously process frames from incoming_frame_queue and put them in processed_frame_queue."""
        print("Starting frame processing loop...")
        encode_param = [cv2.IMWRITE_WEBP_QUALITY, 80]

        while not self.stop_event.is_set():
            try:
                # Get frame info from incoming queue
                frame_info = self.incoming_frame_queue.get(timeout=1)

                # Extract frame and metadata
                if isinstance(frame_info, dict) and "frame" in frame_info:
                    frame = frame_info["frame"]
                    timestamp = frame_info.get("timestamp")
                    frame_id = frame_info.get("frame_id")
                    quality = frame_info.get("quality")

                    # Adjust WebP quality if provided
                    if (
                        quality
                        and isinstance(quality, (float, int))
                        and 0 <= quality <= 1
                    ):
                        encode_param = [cv2.IMWRITE_WEBP_QUALITY, int(quality * 100)]
                else:
                    # Legacy format - direct frame
                    frame = frame_info
                    timestamp = None
                    frame_id = None

                # Process the frame
                processed_frame_image, analysis = self.analyze_and_process_frame(frame)

                if processed_frame_image is None:
                    continue

                # Encode frame to WebP
                ret, buffer = cv2.imencode(".webp", processed_frame_image, encode_param)

                if not ret:
                    print("Error: Could not encode frame to WebP in processing loop.")
                    continue

                frame_bytes = buffer.tobytes()

                # Prepare result with metadata (timestamp and frame_id)
                result = {
                    "frame": frame_bytes,
                    "analysis": analysis,
                    "timestamp": timestamp,
                    "frame_id": frame_id,
                }

                try:
                    self.processed_frame_queue.put(result, timeout=1)
                except queue.Full:
                    pass  # Drop frame if queue is full
                except Exception as e:
                    print(f"Error putting frame to processed_frame_queue: {e}")
                    break

            except queue.Empty:
                continue  # No frame available, continue waiting
            except Exception as e:
                print(f"Error in frame processing loop: {e}")
                break

        print("Exiting frame processing loop.")

    def start_processing(self):
        """
        Start the frame processing thread.
        """
        if self.is_processing:
            print("Frame processing is already running.")
            return True

        self.stop_event.clear()  # Clear stop signal

        self.processing_thread = threading.Thread(
            target=self._process_frames_loop, daemon=True
        )
        self.processing_thread.start()
        self.is_processing = True

        print("Frame processing thread started.")
        return True

    def stop_processing(self):
        """Stop processing thread and release resources."""
        print("Stopping frame processing thread...")
        self.stop_event.set()  # Signal threads to stop

        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2)

        self.is_processing = False

        # Clear queues
        while not self.incoming_frame_queue.empty():
            try:
                self.incoming_frame_queue.get_nowait()
            except queue.Empty:
                break
        while not self.processed_frame_queue.empty():
            try:
                self.processed_frame_queue.get_nowait()
            except queue.Empty:
                break
        print("Queues cleared. Frame processing stopped.")

    def analyze_and_process_frame(self, frame):
        """
        Analyze a frame and process it for display.

        Args:
            frame: Image frame

        Returns:
            tuple: (processed_frame, analysis_results)
        """
        # Analyze frame
        analysis = self.analyzer.analyze_frame(
            frame, save_images=False
        )  # save_images can be configured

        # Draw bounding boxes and labels
        processed_frame = frame.copy()
        for i, (x1, y1, x2, y2) in enumerate(analysis["people_boxes"]):
            # Use different colors for different behavior states
            behavior_label = (
                analysis["behaviors"][i]
                if i < len(analysis["behaviors"])
                else "Unknown"
            )

            if "Panicked" in behavior_label:
                color = (0, 0, 255)  # Red for panicked
            elif "Normal" in behavior_label:
                color = (0, 255, 0)  # Green for normal
            else:
                color = (255, 255, 0)  # Yellow for other behaviors

            cv2.rectangle(processed_frame, (x1, y1), (x2, y2), color, 2)

            # Draw behavior text above bounding box
            cv2.putText(
                processed_frame,
                behavior_label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

        # Display people count
        cv2.putText(
            processed_frame,
            f"People: {analysis['people_count']}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),  # White color for text
            2,
        )

        # Indicate if behavior was detected (e.g., "Panicked")
        if any("Panicked" in behavior for behavior in analysis["behaviors"]):
            # Save frame if panicked behavior is detected
            file_path = os.path.join(
                config.SAVE_DIR, f"panicked_surveillance_{int(time.time())}.jpg"
            )
            # Save the original frame
            cv2.imwrite(file_path, frame)
            print(f"Panicked behavior detected! Frame saved to {file_path}")

            cv2.putText(
                processed_frame,
                "BEHAVIOR DETECTED!",
                (10, 90),  # Adjusted y-position
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),  # Red color for alert
                2,
            )

        return processed_frame, analysis

    def get_processed_frame(self):
        """
        Get a processed frame result from the queue.

        Returns:
            dict: Processed frame data and analysis results, or None if no frame available
        """
        try:
            return self.processed_frame_queue.get_nowait()
        except queue.Empty:
            return None

    def generate_frames(self):
        """
        Generator function to continuously yield processed frames.
        This is consumed by the SocketIO stream.
        """
        print("generate_frames: Waiting for processed frames...")
        while not self.stop_event.is_set():
            try:
                result = self.processed_frame_queue.get(timeout=1)
                yield result
            except queue.Empty:
                if self.stop_event.is_set():
                    print("generate_frames: Stop event set and queue empty, exiting.")
                    break
                continue
            except Exception as e:
                print(
                    f"Error getting frame from processed_frame_queue in generate_frames: {e}"
                )
                break
        print("Exiting generate_frames loop.")

    # Keep these methods for backward compatibility, but they're deprecated
    def start_camera(self, camera_id=0):
        """Deprecated: Use start_processing() instead."""
        print("Warning: start_camera() is deprecated. Use start_processing() instead.")
        return self.start_processing()

    def stop_camera(self):
        """Deprecated: Use stop_processing() instead."""
        print("Warning: stop_camera() is deprecated. Use stop_processing() instead.")
        self.stop_processing()

    def get_frame(self):
        """Deprecated: Not applicable for browser-based camera."""
        print("Warning: get_frame() is deprecated for browser-based camera.")
        return False, None
