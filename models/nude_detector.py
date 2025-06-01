def blur_nudity(self, frame):
    boxes, scores = self.model.predict(frame)  # Assume model returns boxes and scores
    for box, score in zip(boxes, scores):
        if score > 0.5:
            x, y, w, h = box
            roi = frame[y:y+h, x:x+w]
            blurred_roi = cv2.GaussianBlur(roi, (51, 51), 0)
            frame[y:y+h, x:x+w] = blurred_roi
    return frame
