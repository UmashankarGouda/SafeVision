"""SafeVision - AI-Powered Intelligent Surveillance for Assault Prevention.
Main application entry point."""

from flask import Flask
import config
from routes.surveillance_routes import surveillance_bp
from views.home_view import home_view

def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(surveillance_bp)
    
    @app.route('/')
    def home():
        return home_view()
    
    return app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG,reload=True)
