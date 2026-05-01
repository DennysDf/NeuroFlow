from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import login_required
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ...auth.services import hash_password
from ...extensions import db
from ...models.enums import RoleEnum, ScopeTypeEnum
from ...models.user import Membership, User
from ...permissions import ensure_school_access, require_role
from .forms import MembershipAddForm, UserCreateForm

users_bp = Blueprint("users", __name__)

ADMIN_ROLES = (
    RoleEnum.ORG_SUPER_ADMIN,
    RoleEnum.SCHOOL_ADMIN,
    RoleEnum.ADMINISTRATIVE,
)


@users_bp.route("/schools/<int:school_id>/users")
@login_required
@require_role(*ADMIN_ROLES)
def school_users(school_id: int):
    ensure_school_access(school_id)
    rows = (
        db.session.query(User, Membership)
        .join(Membership, Membership.user_id == User.id)
        .filter(
            Membership.scope_type == ScopeTypeEnum.SCHOOL,
            Membership.scope_id == school_id,
        )
        .order_by(User.full_name)
        .all()
    )
    return render_template("users/school_users.html", rows=rows, school_id=school_id)


@users_bp.route("/schools/<int:school_id>/users/new", methods=["GET", "POST"])
@login_required
@require_role(*ADMIN_ROLES)
def school_users_new(school_id: int):
    ensure_school_access(school_id)
    form = UserCreateForm()
    if form.validate_on_submit():
        cpf = form.cpf.data
        user = db.session.scalar(select(User).where(User.cpf == cpf))
        created = False
        if not user:
            user = User(
                cpf=cpf,
                full_name=form.full_name.data,
                email=form.email.data or None,
                password_hash=hash_password(form.password.data),
            )
            db.session.add(user)
            db.session.flush()
            created = True
        membership = Membership(
            user_id=user.id,
            scope_type=ScopeTypeEnum.SCHOOL,
            scope_id=school_id,
            role=RoleEnum(form.role.data),
        )
        db.session.add(membership)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Esse usuário já possui esse vínculo.", "warning")
            return redirect(url_for("users.school_users", school_id=school_id))
        flash(
            "Usuário criado e vinculado à escola." if created else "Vínculo adicionado ao usuário existente.",
            "success",
        )
        return redirect(url_for("users.school_users", school_id=school_id))
    return render_template("users/user_form.html", form=form, school_id=school_id)


@users_bp.route(
    "/schools/<int:school_id>/memberships/<int:membership_id>/delete",
    methods=["POST"],
)
@login_required
@require_role(*ADMIN_ROLES)
def membership_delete(school_id: int, membership_id: int):
    ensure_school_access(school_id)
    m = db.session.get(Membership, membership_id)
    if not m or m.scope_type != ScopeTypeEnum.SCHOOL or m.scope_id != school_id:
        abort(404)
    db.session.delete(m)
    db.session.commit()
    flash("Vínculo removido.", "info")
    return redirect(url_for("users.school_users", school_id=school_id))
