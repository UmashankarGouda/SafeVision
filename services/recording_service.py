# Recording service for compiling annotated frames into MP4 files with encryption and session isolation
import os
import cv2
import numpy as np
from cryptography.fernet import Fernet
from flask import session

RECORDINGS_DIR = 'recordings'
KEY_FILE = 'recordings/.key'

# Ensure recordings directory exists
def ensure_recordings_dir():
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)

def get_fernet():
    with open(KEY_FILE, 'rb') as f:
        key = f.read()
    return Fernet(key)

class RecordingService:
    def __init__(self, user_id):
        ensure_recordings_dir()
        self.user_id = user_id
        self.frames = []
        self.recording = False
        self.fernet = get_fernet()

    def start(self):
        self.frames = []
        self.recording = True

    def add_frame(self, frame):
        if self.recording:
            self.frames.append(frame)

    def stop(self):
        if not self.frames:
            return None
        filename = f'{self.user_id}_{int(time.time())}.mp4'
        filepath = os.path.join(RECORDINGS_DIR, filename)
        height, width, _ = self.frames[0].shape
        out = cv2.VideoWriter(filepath, cv2.VideoWriter_fourcc(*'mp4v'), 15, (width, height))
        for frame in self.frames:
            out.write(frame)
        out.release()
        # Encrypt file
        with open(filepath, 'rb') as f:
            data = f.read()
        encrypted = self.fernet.encrypt(data)
        with open(filepath, 'wb') as f:
            f.write(encrypted)
        self.recording = False
        return filename

    def list_recordings(self):
        files = os.listdir(RECORDINGS_DIR)
        return [f for f in files if f.startswith(self.user_id)]

    def get_recording(self, filename):
        filepath = os.path.join(RECORDINGS_DIR, filename)
        with open(filepath, 'rb') as f:
            encrypted = f.read()
        return self.fernet.decrypt(encrypted)
