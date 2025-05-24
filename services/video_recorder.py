"""
Video compilation service for SafeVision.
Handles recording and compilation of video frames from surveillance feeds.
"""

import cv2
import numpy as np
import os
from datetime import datetime
from typing import List, Dict, Optional
import base64


class VideoRecorder:
    """Handles video recording and compilation."""

    def __init__(self, output_dir: str = "recordings"):
        self.output_dir = output_dir
        self.recording_sessions = {}
        self.frame_buffer = {}
        self.max_frames_per_session = 1500
        self.video_writers = {}

        os.makedirs(self.output_dir, exist_ok=True)

        self.video_codec = cv2.VideoWriter_fourcc(*"mp4v")
        self.fps = 5
        self.frame_size = (640, 480)

    def start_recording(self, session_id: str, user_agent: str = "Unknown") -> Dict:
        """Start recording for a session."""
        if session_id in self.recording_sessions:
            return {"error": "Recording already active for this session"}

        timestamp = datetime.now()
        filename = (
            f"surveillance_{session_id[:8]}_{timestamp.strftime('%Y%m%d_%H%M%S')}.mp4"
        )
        filepath = os.path.join(self.output_dir, filename)

        video_writer = cv2.VideoWriter(
            filepath, self.video_codec, self.fps, self.frame_size
        )

        if not video_writer.isOpened():
            return {"error": "Failed to initialize video writer"}

        recording_info = {
            "session_id": session_id,
            "filename": filename,
            "filepath": filepath,
            "start_time": timestamp,
            "frame_count": 0,
            "user_agent": user_agent,
            "status": "recording",
        }

        self.recording_sessions[session_id] = recording_info
        self.frame_buffer[session_id] = []
        self.video_writers[session_id] = video_writer

        print(f"Started recording for session {session_id}: {filename}")
        return {"success": True, "filename": filename, "filepath": filepath}

    def add_frame(self, session_id: str, frame_data: str) -> bool:
        """Add a frame to the recording."""
        if session_id not in self.recording_sessions:
            return False

        try:
            frame_bytes = base64.b64decode(
                frame_data.split(",")[1] if "," in frame_data else frame_data
            )

            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return False

            frame = cv2.resize(frame, self.frame_size)

            video_writer = self.video_writers[session_id]
            video_writer.write(frame)

            self.recording_sessions[session_id]["frame_count"] += 1

            if len(self.frame_buffer[session_id]) < 10:
                self.frame_buffer[session_id].append(frame)
            else:
                self.frame_buffer[session_id].pop(0)
                self.frame_buffer[session_id].append(frame)

            if (
                self.recording_sessions[session_id]["frame_count"]
                >= self.max_frames_per_session
            ):
                self.stop_recording(session_id, auto_stop=True)

            return True

        except Exception as e:
            print(f"Error adding frame to recording {session_id}: {e}")
            return False

    def stop_recording(self, session_id: str, auto_stop: bool = False) -> Dict:
        """Stop recording for a session."""
        if session_id not in self.recording_sessions:
            return {"error": "No active recording for this session"}

        try:
            recording_info = self.recording_sessions[session_id]
            video_writer = self.video_writers[session_id]

            video_writer.release()

            end_time = datetime.now()
            duration = (end_time - recording_info["start_time"]).total_seconds()

            recording_info["end_time"] = end_time
            recording_info["duration_seconds"] = duration
            recording_info["status"] = "completed"
            recording_info["auto_stopped"] = auto_stop

            thumbnail_path = self._generate_thumbnail(session_id)
            if thumbnail_path:
                recording_info["thumbnail"] = thumbnail_path

            file_size = (
                os.path.getsize(recording_info["filepath"])
                if os.path.exists(recording_info["filepath"])
                else 0
            )
            recording_info["file_size_mb"] = round(file_size / (1024 * 1024), 2)

            del self.video_writers[session_id]
            if session_id in self.frame_buffer:
                del self.frame_buffer[session_id]

            print(
                f"Stopped recording for session {session_id}: {recording_info['filename']} "
                f"({recording_info['frame_count']} frames, {duration:.1f}s)"
            )

            return {"success": True, "recording_info": recording_info}

        except Exception as e:
            print(f"Error stopping recording {session_id}: {e}")
            return {"error": str(e)}

    def _generate_thumbnail(self, session_id: str) -> Optional[str]:
        """Generate a thumbnail from the last frame."""
        if session_id not in self.frame_buffer or not self.frame_buffer[session_id]:
            return None

        try:
            frame = self.frame_buffer[session_id][-1]

            thumbnail = cv2.resize(frame, (160, 120))

            recording_info = self.recording_sessions[session_id]
            thumbnail_filename = recording_info["filename"].replace(
                ".mp4", "_thumb.jpg"
            )
            thumbnail_path = os.path.join(self.output_dir, thumbnail_filename)

            cv2.imwrite(thumbnail_path, thumbnail)

            return thumbnail_path

        except Exception as e:
            print(f"Error generating thumbnail for {session_id}: {e}")
            return None

    def get_recording_status(self, session_id: str) -> Dict:
        """Get recording status for a session."""
        if session_id not in self.recording_sessions:
            return {"status": "not_recording"}

        recording_info = self.recording_sessions[session_id].copy()

        if recording_info["status"] == "recording":
            current_time = datetime.now()
            recording_info["current_duration_seconds"] = (
                current_time - recording_info["start_time"]
            ).total_seconds()

        return recording_info

    def get_all_recordings(self) -> List[Dict]:
        """Get list of all recordings."""
        recordings = []

        for session_id, recording_info in self.recording_sessions.items():
            if recording_info["status"] == "completed":
                recordings.append(recording_info.copy())

        try:
            for filename in os.listdir(self.output_dir):
                if filename.endswith(".mp4"):
                    filepath = os.path.join(self.output_dir, filename)
                    file_stats = os.stat(filepath)

                    found = any(r["filename"] == filename for r in recordings)
                    if not found:
                        recordings.append(
                            {
                                "filename": filename,
                                "filepath": filepath,
                                "file_size_mb": round(
                                    file_stats.st_size / (1024 * 1024), 2
                                ),
                                "created_time": datetime.fromtimestamp(
                                    file_stats.st_ctime
                                ),
                                "status": "archived",
                            }
                        )

        except Exception as e:
            print(f"Error listing recordings: {e}")

        recordings.sort(
            key=lambda x: x.get("start_time", x.get("created_time", datetime.min)),
            reverse=True,
        )

        return recordings

    def delete_recording(self, filename: str) -> Dict:
        """Delete a recording file."""
        try:
            filepath = os.path.join(self.output_dir, filename)

            if not os.path.exists(filepath):
                return {"error": "Recording file not found"}

            os.remove(filepath)

            thumbnail_filename = filename.replace(".mp4", "_thumb.jpg")
            thumbnail_path = os.path.join(self.output_dir, thumbnail_filename)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)

            for session_id, recording_info in list(self.recording_sessions.items()):
                if recording_info.get("filename") == filename:
                    del self.recording_sessions[session_id]
                    break

            return {"success": True, "message": f"Recording {filename} deleted"}

        except Exception as e:
            return {"error": f"Failed to delete recording: {e}"}

    def cleanup_old_recordings(self, max_age_days: int = 30) -> Dict:
        """Clean up recordings older than specified days."""
        try:
            deleted_count = 0
            total_size_freed = 0
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)

            for filename in os.listdir(self.output_dir):
                if filename.endswith(".mp4"):
                    filepath = os.path.join(self.output_dir, filename)
                    file_stats = os.stat(filepath)

                    if file_stats.st_ctime < cutoff_time:
                        file_size = file_stats.st_size
                        self.delete_recording(filename)
                        deleted_count += 1
                        total_size_freed += file_size

            return {
                "success": True,
                "deleted_count": deleted_count,
                "size_freed_mb": round(total_size_freed / (1024 * 1024), 2),
            }

        except Exception as e:
            return {"error": f"Cleanup failed: {e}"}


video_recorder = VideoRecorder()
