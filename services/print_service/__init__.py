from .routes import print_bp


def init_service(app):
    app.register_blueprint(print_bp)
