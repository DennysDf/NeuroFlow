from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from ...extensions import db
from ...models.enums import RoleEnum, ScopeTypeEnum
from ...models.professional import Professional, ProfessionalCategory
from ...models.school import School
from ...models.user import Membership, User
from ...permissions import (
    current_organization_id,
    ensure_school_access,
    require_role,
)
from .forms import CategoryForm, ProfessionalForm

professionals_bp = Blueprint("professionals", __name__)

ADMIN_ROLES = (
    RoleEnum.ORG_SUPER_ADMIN,
    RoleEnum.SCHOOL_ADMIN,
    RoleEnum.ADMINISTRATIVE,
)


# -------- Categories --------

@professionals_bp.route("/schools/<int:school_id>/categories")
@login_required
@require_role(*ADMIN_ROLES)
def categories(school_id: int):
    ensure_school_access(school_id)
    school = db.session.get(School, school_id)
    cats = (
        db.session.query(ProfessionalCategory)
        .filter_by(organization_id=school.organization_id)
        .order_by(ProfessionalCategory.name)
        .all()
    )
    return render_template(
        "professionals/categories.html", categories=cats, school_id=school_id
    )


@professionals_bp.route("/schools/<int:school_id>/categories/new", methods=["GET", "POST"])
@login_required
@require_role(*ADMIN_ROLES)
def categories_new(school_id: int):
    ensure_school_access(school_id)
    school = db.session.get(School, school_id)
    form = CategoryForm()
    if form.validate_on_submit():
        cat = ProfessionalCategory(
            organization_id=school.organization_id,
            name=form.name.data,
            description=form.description.data or None,
        )
        db.session.add(cat)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Já existe categoria com esse nome.", "warning")
        else:
            flash("Categoria criada.", "success")
            return redirect(url_for("professionals.categories", school_id=school_id))
    return render_template(
        "professionals/category_form.html", form=form, school_id=school_id, mode="new"
    )


@professionals_bp.route(
    "/schools/<int:school_id>/categories/<int:cat_id>/edit", methods=["GET", "POST"]
)
@login_required
@require_role(*ADMIN_ROLES)
def categories_edit(school_id: int, cat_id: int):
    ensure_school_access(school_id)
    school = db.session.get(School, school_id)
    cat = db.session.get(ProfessionalCategory, cat_id)
    if not cat or cat.organization_id != school.organization_id:
        abort(404)
    form = CategoryForm(obj=cat)
    if form.validate_on_submit():
        cat.name = form.name.data
        cat.description = form.description.data or None
        db.session.commit()
        flash("Categoria atualizada.", "success")
        return redirect(url_for("professionals.categories", school_id=school_id))
    return render_template(
        "professionals/category_form.html", form=form, school_id=school_id, mode="edit"
    )


# -------- Professionals --------

@professionals_bp.route("/schools/<int:school_id>/professionals")
@login_required
@require_role(*ADMIN_ROLES)
def list_view(school_id: int):
    ensure_school_access(school_id)
    profs = (
        db.session.query(Professional)
        .filter_by(school_id=school_id)
        .order_by(Professional.id.desc())
        .all()
    )
    return render_template(
        "professionals/list.html", professionals=profs, school_id=school_id
    )


def _user_choices_for_school(school_id: int) -> list[tuple[int, str]]:
    rows = (
        db.session.query(User, Membership)
        .join(Membership, Membership.user_id == User.id)
        .filter(
            Membership.scope_type == ScopeTypeEnum.SCHOOL,
            Membership.scope_id == school_id,
            Membership.role == RoleEnum.PROFESSIONAL,
        )
        .order_by(User.full_name)
        .all()
    )
    return [(u.id, f"{u.full_name} ({u.cpf})") for u, _ in rows]


@professionals_bp.route("/schools/<int:school_id>/professionals/new", methods=["GET", "POST"])
@login_required
@require_role(*ADMIN_ROLES)
def professionals_new(school_id: int):
    ensure_school_access(school_id)
    school = db.session.get(School, school_id)
    form = ProfessionalForm()
    form.user_id.choices = _user_choices_for_school(school_id)
    form.category_id.choices = [
        (c.id, c.name)
        for c in db.session.query(ProfessionalCategory)
        .filter_by(organization_id=school.organization_id)
        .order_by(ProfessionalCategory.name)
        .all()
    ]
    if not form.user_id.choices:
        flash(
            "Nenhum usuário com perfil 'Profissional' cadastrado nesta escola. Crie um usuário primeiro.",
            "warning",
        )
    if form.validate_on_submit():
        prof = Professional(
            user_id=form.user_id.data,
            school_id=school_id,
            category_id=form.category_id.data,
            registration_number=form.registration_number.data or None,
        )
        db.session.add(prof)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Esse usuário já é profissional desta escola.", "warning")
        else:
            flash("Profissional cadastrado.", "success")
            return redirect(url_for("professionals.list_view", school_id=school_id))
    return render_template(
        "professionals/form.html", form=form, school_id=school_id
    )


@professionals_bp.route(
    "/schools/<int:school_id>/professionals/<int:prof_id>/delete", methods=["POST"]
)
@login_required
@require_role(*ADMIN_ROLES)
def professionals_delete(school_id: int, prof_id: int):
    ensure_school_access(school_id)
    prof = db.session.get(Professional, prof_id)
    if not prof or prof.school_id != school_id:
        abort(404)
    db.session.delete(prof)
    db.session.commit()
    flash("Profissional removido.", "info")
    return redirect(url_for("professionals.list_view", school_id=school_id))
