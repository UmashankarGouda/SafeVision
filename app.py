from flask import Flask
import config
from routes import pages_bp, surveillance_bp, analytics_bp  

def create_app():
    app = Flask(__name__)
    app.register_blueprint(surveillance_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(analytics_bp)  
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
