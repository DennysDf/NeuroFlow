from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import login_required

from ...context import get_current_context
from ...extensions import db
from ...models.enums import RoleEnum
from ...models.organization import Organization
from ...models.school import School
from ...permissions import current_organization_id, require_role
from .forms import OrganizationForm, SchoolForm

org_bp = Blueprint("org", __name__)


@org_bp.route("/schools")
@login_required
@require_role(RoleEnum.ORG_SUPER_ADMIN)
def schools_list():
    org_id = current_organization_id()
    schools = (
        db.session.query(School).filter_by(organization_id=org_id).order_by(School.name).all()
    )
    org = db.session.get(Organization, org_id)
    return render_template("org/schools_list.html", schools=schools, organization=org)


@org_bp.route("/schools/new", methods=["GET", "POST"])
@login_required
@require_role(RoleEnum.ORG_SUPER_ADMIN)
def schools_new():
    form = SchoolForm()
    if form.validate_on_submit():
        school = School(
            organization_id=current_organization_id(),
            name=form.name.data,
            address=form.address.data or None,
            phone=form.phone.data or None,
        )
        db.session.add(school)
        db.session.commit()
        flash("Escola criada.", "success")
        return redirect(url_for("org.schools_list"))
    return render_template("org/school_form.html", form=form, mode="new")


@org_bp.route("/schools/<int:school_id>/edit", methods=["GET", "POST"])
@login_required
@require_role(RoleEnum.ORG_SUPER_ADMIN)
def schools_edit(school_id: int):
    school = db.session.get(School, school_id)
    if not school or school.organization_id != current_organization_id():
        abort(404)
    form = SchoolForm(obj=school)
    if form.validate_on_submit():
        school.name = form.name.data
        school.address = form.address.data or None
        school.phone = form.phone.data or None
        db.session.commit()
        flash("Escola atualizada.", "success")
        return redirect(url_for("org.schools_list"))
    return render_template("org/school_form.html", form=form, mode="edit", school=school)


@org_bp.route("/organization", methods=["GET", "POST"])
@login_required
@require_role(RoleEnum.ORG_SUPER_ADMIN)
def organization_edit():
    org = db.session.get(Organization, current_organization_id())
    form = OrganizationForm(obj=org)
    if form.validate_on_submit():
        org.name = form.name.data
        org.cnpj = form.cnpj.data or None
        db.session.commit()
        flash("Organização atualizada.", "success")
        return redirect(url_for("dashboard.home"))
    return render_template("org/organization_form.html", form=form, organization=org)
