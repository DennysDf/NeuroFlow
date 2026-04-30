from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db, limiter
from ..models.user import Membership, User
from .forms import LoginForm
from .services import verify_password

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10/minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(cpf=form.cpf.data).first()
        if user and user.is_active and verify_password(user.password_hash, form.password.data):
            login_user(user)
            session.pop("context", None)
            memberships = user.memberships
            if not memberships:
                logout_user()
                flash("Seu usuário não possui vínculo ativo. Contate o administrador.", "danger")
                return redirect(url_for("auth.login"))
            if len(memberships) == 1:
                _set_context(memberships[0])
                return redirect(url_for("dashboard.home"))
            return redirect(url_for("auth.switch_context"))
        flash("CPF ou senha incorretos.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/switch-context", methods=["GET", "POST"])
@login_required
def switch_context():
    memberships = current_user.memberships
    if not memberships:
        logout_user()
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        membership_id = int(request.form.get("membership_id", 0))
        membership = next((m for m in memberships if m.id == membership_id), None)
        if not membership:
            abort(403)
        _set_context(membership)
        return redirect(url_for("dashboard.home"))
    return render_template("auth/switch_context.html", memberships=memberships)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.pop("context", None)
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))


def _set_context(membership: Membership) -> None:
    session["context"] = {
        "membership_id": membership.id,
        "scope_type": membership.scope_type.value,
        "scope_id": membership.scope_id,
        "role": membership.role.value,
    }
