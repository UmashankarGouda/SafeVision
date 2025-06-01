import cv2
from models.nude_detector import NudeDetector

def process_file(input_path, output_path):
    detector = NudeDetector()
    
    if input_path.lower().endswith(('.jpg', '.png', '.jpeg')):
        frame = cv2.imread(input_path)
        if frame is None:
            raise ValueError(f"Cannot read image file {input_path}")
        processed_frame = detector.blur_nudity(frame)
        cv2.imwrite(output_path, processed_frame)
    elif input_path.lower().endswith(('.mp4', '.avi', '.mov')):
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file {input_path}")
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if not out.isOpened():
            cap.release()
            raise ValueError(f"Cannot write to output file {output_path}")
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                processed_frame = detector.blur_nudity(frame)
                out.write(processed_frame)
            cap.release()
            out.release()
        except Exception as e:
            cap.release()
            out.release()
            raise e
    else:
        raise ValueError("Unsupported file format")
