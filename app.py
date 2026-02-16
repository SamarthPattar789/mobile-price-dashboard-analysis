from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import os

from config import get_config
from models import Base, User


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__)
    cfg = get_config()
    app.config.update(
        SECRET_KEY=cfg["SECRET_KEY"],
        SQLALCHEMY_DATABASE_URI=cfg["DATABASE_URI"],
        MAX_CONTENT_LENGTH=32 * 1024 * 1024,
        PBI_REPORT_URL=cfg["PBI_REPORT_URL"],  # Add Power BI URL to Flask config
    )

    engine = create_engine(cfg["DATABASE_URI"], future=True)
    Base.metadata.create_all(engine)
    SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        with SessionLocal() as db:
            return db.get(User, int(user_id))

    # Blueprints
    from auth import auth_bp
    from dashboard import dashboard_bp
    from admin_panel import admin_bp
    from insights import insights_bp

    # store db session factory on app
    app.session_factory = SessionLocal  # type: ignore[attr-defined]

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(insights_bp)

    @app.teardown_appcontext
    def remove_session(exception=None):
        SessionLocal.remove()

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=True)


