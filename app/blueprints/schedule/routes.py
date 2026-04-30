from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import login_required

from ...extensions import db
from ...models.enums import RoleEnum
from ...models.professional import Professional
from ...models.schedule import Appointment
from ...models.student import Student
from ...permissions import (
    current_professional,
    ensure_school_access,
    require_role,
)
from .forms import AppointmentForm

schedule_bp = Blueprint("schedule", __name__)

ALL_ROLES = (
    RoleEnum.ORG_SUPER_ADMIN,
    RoleEnum.SCHOOL_ADMIN,
    RoleEnum.ADMINISTRATIVE,
    RoleEnum.PROFESSIONAL,
)
ADMIN_ROLES = (
    RoleEnum.ORG_SUPER_ADMIN,
    RoleEnum.SCHOOL_ADMIN,
    RoleEnum.ADMINISTRATIVE,
)


@schedule_bp.route("/schools/<int:school_id>/agenda")
@login_required
@require_role(*ALL_ROLES)
def list_view(school_id: int):
    ensure_school_access(school_id)
    q = (
        db.session.query(Appointment)
        .filter_by(school_id=school_id)
        .order_by(Appointment.starts_at)
    )
    from ...permissions import current_role

    if current_role() == RoleEnum.PROFESSIONAL:
        prof = current_professional()
        if not prof:
            abort(403)
        q = q.filter(Appointment.professional_id == prof.id)
    appointments = q.all()
    return render_template(
        "schedule/list.html", appointments=appointments, school_id=school_id
    )


@schedule_bp.route("/schools/<int:school_id>/agenda/new", methods=["GET", "POST"])
@login_required
@require_role(*ALL_ROLES)
def new(school_id: int):
    ensure_school_access(school_id)
    form = AppointmentForm()
    professionals = (
        db.session.query(Professional).filter_by(school_id=school_id).all()
    )
    students = db.session.query(Student).filter_by(school_id=school_id).all()
    form.professional_id.choices = [
        (p.id, f"{p.user.full_name} ({p.category.name})") for p in professionals
    ]
    form.student_id.choices = [(s.id, s.full_name) for s in students]

    from ...permissions import current_role

    if current_role() == RoleEnum.PROFESSIONAL:
        prof = current_professional()
        if not prof:
            abort(403)
        form.professional_id.choices = [
            (p.id, f"{p.user.full_name} ({p.category.name})")
            for p in professionals
            if p.id == prof.id
        ]

    if form.validate_on_submit():
        if form.ends_at.data <= form.starts_at.data:
            flash("O término deve ser após o início.", "danger")
        else:
            appt = Appointment(
                school_id=school_id,
                professional_id=form.professional_id.data,
                student_id=form.student_id.data,
                starts_at=form.starts_at.data,
                ends_at=form.ends_at.data,
                location=form.location.data or None,
                notes=form.notes.data or None,
            )
            db.session.add(appt)
            db.session.commit()
            flash("Compromisso criado.", "success")
            return redirect(url_for("schedule.list_view", school_id=school_id))
    return render_template("schedule/form.html", form=form, school_id=school_id)


@schedule_bp.route(
    "/schools/<int:school_id>/agenda/<int:appt_id>/delete", methods=["POST"]
)
@login_required
@require_role(*ADMIN_ROLES)
def delete(school_id: int, appt_id: int):
    ensure_school_access(school_id)
    appt = db.session.get(Appointment, appt_id)
    if not appt or appt.school_id != school_id:
        abort(404)
    db.session.delete(appt)
    db.session.commit()
    flash("Compromisso removido.", "info")
    return redirect(url_for("schedule.list_view", school_id=school_id))
