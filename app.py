"""
    SafeVision - AI-Powered Intelligent Surveillance for Assault Prevention.
    Main application entry point.
"""

from flask import Flask
import config
from routes import pages_bp, surveillance_bp

def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(surveillance_bp)
    app.register_blueprint(pages_bp)
    
    return app


if __name__ == '__main__':
    """
        Main entry point for the application.
        Starts the Flask development server.
    """
    app = create_app()
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
