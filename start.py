"""
SafeVision Startup Script
Enhanced startup with validation and configuration checks.
"""

import os
import sys


def check_dependencies():
    """Check if all required dependencies are available."""
    required_packages = ["flask", "flask_socketio", "cv2", "numpy", "psutil"]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False

    print("✓ All dependencies available")
    return True


def check_environment():
    """Check environment configuration."""
    print("🔍 Checking environment...")

    if not os.environ.get("SECRET_KEY"):
        print("⚠️  No SECRET_KEY set - using development key")
    else:
        print("✓ SECRET_KEY configured")

    if not os.environ.get("SAFEVISION_ADMIN_PASSWORD"):
        print("⚠️  Using default admin password - change for production")
    else:
        print("✓ Custom admin password configured")

    dirs_to_create = ["recordings", "static/thumbnails", "data"]
    for dir_path in dirs_to_create:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"✓ Created directory: {dir_path}")

    return True


def main():
    """Main startup function."""
    print("🚀 Starting SafeVision AI Surveillance System")
    print("=" * 50)

    if not check_dependencies():
        sys.exit(1)
    if not check_environment():
        sys.exit(1)

    print("\n🎯 System checks passed - starting application...")

    try:
        print("📦 Importing application modules...")
        from app import app, socketio
        from config import DEBUG, HOST, PORT

        print("✓ Imports successful")
        print("🚀 Starting SocketIO server...")

        socketio.run(app, debug=DEBUG, host=HOST, port=PORT)

    except KeyboardInterrupt:
        print("\n\n👋 SafeVision stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start SafeVision: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
