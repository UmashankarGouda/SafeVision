from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from routes import pages_bp, surveillance_bp, analytics_bp
from routes.performance_routes import performance_bp
from routes.recording_routes import recording_bp
from routes.auth_routes import auth_bp
from services.performance_monitor import performance_monitor
import os
from config import DEBUG, HOST, PORT
from routes.surveillance_routes import setup_socketio_events

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev_key_for_testing")
app.config["TEMPLATES_AUTO_RELOAD"] = DEBUG

socketio = SocketIO(app, cors_allowed_origins="*")

app.register_blueprint(pages_bp)
app.register_blueprint(surveillance_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(performance_bp)
app.register_blueprint(recording_bp)
app.register_blueprint(auth_bp)

setup_socketio_events(socketio)

performance_monitor.start_monitoring()


@app.route("/health")
def health_check():
    """Health check endpoint for load balancers and monitoring."""
    try:
        status = performance_monitor.get_current_status()
        return jsonify(
            {
                "status": "healthy",
                "timestamp": status.get("timestamp"),
                "uptime": status.get("uptime", 0),
                "version": "1.0.0",
            }
        ), 200
    except Exception as e:
        return jsonify(
            {"status": "unhealthy", "error": str(e), "version": "1.0.0"}
        ), 503


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"Internal server error: {str(e)}")
    return render_template("500.html"), 500


@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all other exceptions."""
    app.logger.error(f"Unhandled exception: {str(e)}")
    if DEBUG:
        raise e
    return render_template("500.html"), 500


if __name__ == "__main__":
    print("Starting SafeVision with browser camera support...")
    print(f"Server will be available at http://{HOST}:{PORT}")
    socketio.run(app, debug=DEBUG, host=HOST, port=PORT)
