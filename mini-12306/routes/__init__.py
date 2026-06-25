from routes.auth import auth_bp
from routes.main import main_bp
from routes.train import train_bp
from routes.order import order_bp
from routes.admin import admin_bp


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(train_bp)
    app.register_blueprint(order_bp, url_prefix="/order")
    app.register_blueprint(admin_bp, url_prefix="/admin")
