from flask import Flask
from app.config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.routes import dashboard, campaigns, launch
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(campaigns.bp)
    app.register_blueprint(launch.bp)

    return app