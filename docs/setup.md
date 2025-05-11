# Setup Instructions for Flask ML App

This document provides step-by-step instructions to set up and run the Flask-based machine learning application locally.

## Prerequisites

- Python 3.8+
- `pip` (Python package installer)
- Git

## 1. Clone the Repository

```bash
git clone https://github.com/UmashankarGouda/SafeVision.git
cd your-ml-flask-app
```

## 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

## 3. Install rest of the dependencies using poetry

```bash
pip install poetry
poetry install
```

## Run the Application

```
flask run
```
