from .routes import monitoring_bp


def init_service(app):
    app.register_blueprint(monitoring_bp)
