import os
from flask import Flask
from api import api
from api import auth
from api import manage
from api.extensions import apispec
from api.extensions import db
from api.extensions import jwt
from api.extensions import migrate
from api.models import User


def create_app(testing=False):
    """Application factory, used to create application"""
    app = Flask("api")
    app.config.from_object("api.config")
    app.config["SERVER_NAME"] = "127.0.0.1:8000"

    if testing is True:
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"

    configure_extensions(app)
    configure_cli(app)
    configure_apispec(app)
    register_blueprints(app)

    with app.app_context():
        db.create_all()
        if not User.query.filter_by(is_admin=True).all():
            admin_mail = os.environ.get("ADMIN_EMAIL") or "admin@admin.com"
            admin_pass = os.environ.get("ADMIN_PASS") or "admin"
            admin = User(email=admin_mail, password=admin_pass, is_admin=True)
            db.session.add(admin)
            db.session.commit()
    
    @app.route("/redoc")
    def redoc():
        print(apispec.swagger_json())
        return (apispec.swagger_ui())
    
    return app


def configure_extensions(app):
    """Configure flask extensions"""
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)


def configure_cli(app):
    """Configure Flask 2.0's cli for easy entity management"""
    app.cli.add_command(manage.init)


def configure_apispec(app):
    """Configure APISpec for swagger support"""
    apispec.init_app(app, security=[{"jwt": []}])
    apispec.spec.components.security_scheme(
        "jwt", {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    )
    apispec.spec.components.schema(
        "PaginatedResult",
        {
            "properties": {
                "total": {"type": "integer"},
                "pages": {"type": "integer"},
                "next": {"type": "string"},
                "prev": {"type": "string"},
            }
        },
    )


def register_blueprints(app):
    """Register all blueprints for application"""
    app.register_blueprint(auth.views.blueprint)
    app.register_blueprint(api.views.blueprint)

