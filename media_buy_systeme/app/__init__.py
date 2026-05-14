from flask import Flask
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.routes import dashboard, products, rebrand
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(products.bp)
    app.register_blueprint(rebrand.bp)

    return app