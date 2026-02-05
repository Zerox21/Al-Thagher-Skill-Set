import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("app.config.Config")

    os.makedirs(app.instance_path, exist_ok=True)
    for p in [app.config["STORAGE_DIR"], app.config["UPLOADS_DIR"], app.config["MEDIA_DIR"], app.config["REPORTS_DIR"]]:
        os.makedirs(p, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    from app.i18n import t, get_lang, set_lang

    @app.context_processor
    def inject_helpers():
        return {
            "t": t,
            "lang": get_lang(),
            "dir": "rtl" if get_lang() == "ar" else "ltr",
            "has_endpoint": lambda ep: ep in app.view_functions,
            "APP_VERSION": app.config.get("APP_VERSION", "v1"),
        }

    from app.routes.auth import bp as auth_bp
    from app.routes.student import bp as student_bp
    from app.routes.teacher import bp as teacher_bp
    from app.routes.chairman import bp as chairman_bp
    from app.routes.media import bp as media_bp
    from app.routes.imports import bp as imports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(teacher_bp, url_prefix="/teacher")
    app.register_blueprint(chairman_bp, url_prefix="/chairman")
    app.register_blueprint(media_bp, url_prefix="/media")
    app.register_blueprint(imports_bp, url_prefix="/import")

    @app.get("/lang/<code>")
    def lang_switch(code):
        set_lang(code)
        from flask import redirect, request
        return redirect(request.referrer or "/")

    return app
