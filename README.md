# 🚨 SafeVision - AI-Powered Intelligent Surveillance for Assault Prevention

---

## 📖 Project Description

**SafeVision** is an AI-powered real-time surveillance system designed to **detect and prevent potential assaults** by actively analyzing CCTV feeds. Unlike traditional CCTV systems that passively record incidents, SafeVision **detects suspicious activities and sends real-time alerts** to authorities for immediate action.

This project aims to **create safer public environments** by leveraging **computer vision** and **deep learning** models that can recognize aggressive behavior, distress, and abnormal crowd patterns.

> ⚡ **Currently**, SafeVision uses **YOLOv8** for basic crime detection.  
> 🚧 **Future enhancements** include integrating advanced models for **body language analysis**, **facial expression recognition**, and **environmental awareness**.

---

## 🚀 Features

- Real-time monitoring of CCTV video feeds.
- Detects suspicious activities using YOLOv8.
- Sends instant alerts with video snapshots and location data.
- Open-source and modular, welcoming contributions for new AI model integrations.

---

## 🛠 Tech Stack

| Category                  | Tools/Frameworks Used                          |
|----------------------------|-------------------------------------------------|
| **Backend**                | Flask                                           |
| **Computer Vision**        | OpenCV                                          |
| **Current AI Model**       | YOLOv8 (Crime Detection)                        |
| **Planned Models**         | PoseFormer, TokenPose, Swin Transformer, ActionFormer |
| **Deployment**             | Docker (Local Deployment)                      |
| **Alert System**           | Telegram API (Real-Time Notifications)          |
| **Frontend (Planned)**     | Flask-based Web GUI                             |


## 🛠 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/safevision.git
cd safevision
```

### 2. Create and Activate a Virtual Environment (Optional but Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate
# For Windows:
venv\Scripts\activate
# For macOS/Linux:
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```
*(Note: If `requirements.txt` is not present yet, manually install Flask, OpenCV, and Ultralytics)*

```bash
pip install flask opencv-python ultralytics
```

---

### 4. Project Structure

```
/models
    └── yolov8n.pt            # Pretrained YOLOv8 model for crime detection

/static
    ├── /css                  # Styling files
    ├── /images               # Images folder (currently empty)
    └── /js                   # Frontend JavaScript animations

/templates
    └── home.html              # Main frontend page

app.py                         # Main Flask backend
LICENSE                        # License file
README.md                      # Documentation
```

---

### 5. Run the Flask Server

```bash
python app.py
```

By default, the app will run at:  
> **http://127.0.0.1:5000/**

You can now access the SafeVision web interface!

---

### 6. Important Notes

- Place your **input videos** inside a folder (you can modify `app.py` to fetch camera feeds or videos).
- Currently, the detection is handled via **YOLOv8**.
- Future improvements are encouraged (multi-model integration, dashboards, cloud deployment, etc.)

## 🤝 Contribution Guidelines

We welcome contributions to enhance SafeVision!  
Here are ways you can contribute:

- Integrate advanced AI models (PoseFormer, Swin Transformer, etc.)
- Improve real-time detection accuracy.
- Enhance the alert system (SMS, Email, additional APIs).
- Build a responsive user interface.
- Add testing, CI/CD pipelines, and documentation.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions.

---
### 🏗 Good First Issues

- Integrate body language detection model (PoseFormer).
- Add facial expression recognition (Swin Transformer).
- Implement environment/activity recognition (ActionFormer).
- Build basic dashboard for alerts visualization (Flask UI).

> Look for issues labeled **"Good First Issue"** or **"Help Wanted"**!

---

## 📈 Future Scope

- Full multi-model integration with logical risk evaluation algorithms.
- Real-time mobile app notifications for security officers.
- Edge device compatibility for offline processing.
- Integration with city-wide surveillance infrastructure.

---

## 🌍 Real-World Use Cases

- Metro stations, bus stops, and public transport hubs.
- Shopping malls and public spaces.
- University and school campuses.
- Corporate and workplace security.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🌟 Project Impact

SafeVision empowers cities, institutions, and organizations to move from passive video surveillance to **proactive public safety systems**, ensuring faster responses, preventing assaults, and creating safer environments through AI.

---

# 🔥 Get Involved!

🚀 We are at the beginning of an exciting journey.  
🛠️ Your contributions can directly make public spaces safer.  
🌟 **Join us! Improve SafeVision together!**

---

