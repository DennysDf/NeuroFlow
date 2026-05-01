from flask import Flask, redirect, url_for
from flask_login import current_user

from .config import get_config
from .extensions import csrf, db, limiter, login_manager, migrate


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from .models import user as user_model  # noqa: F401  ensure models registered
    from .models import (  # noqa: F401
        organization,
        school,
        professional,
        student,
        form,
        attendance,
        schedule,
        audit,
    )

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(user_model.User, int(user_id))

    from .auth.routes import auth_bp
    from .blueprints.org.routes import org_bp
    from .blueprints.schools.routes import schools_bp
    from .blueprints.users.routes import users_bp
    from .blueprints.professionals.routes import professionals_bp
    from .blueprints.students.routes import students_bp
    from .blueprints.forms_builder.routes import forms_bp
    from .blueprints.attendances.routes import attendances_bp
    from .blueprints.schedule.routes import schedule_bp
    from .blueprints.dashboard.routes import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(org_bp, url_prefix="/org")
    app.register_blueprint(schools_bp, url_prefix="/schools")
    app.register_blueprint(users_bp)
    app.register_blueprint(professionals_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(forms_bp)
    app.register_blueprint(attendances_bp)
    app.register_blueprint(schedule_bp)

    from .context import register_context_processors

    register_context_processors(app)

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.home"))
        return redirect(url_for("auth.login"))

    return app
