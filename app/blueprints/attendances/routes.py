from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required

from ...extensions import db
from ...models.attendance import Attendance, AttendanceAnswer
from ...models.enums import AttendanceStatusEnum, FormStatusEnum, RoleEnum
from ...models.form import Form, FormVersion
from ...models.student import Student
from ...permissions import (
    can_view_attendance_of_student,
    current_professional,
    deny_administrative,
    require_role,
    visible_students_query,
)
from .forms import AttendanceStartForm
from .services import save_answers

attendances_bp = Blueprint("attendances", __name__)

NON_ADMINISTRATIVE_ROLES = (
    RoleEnum.ORG_SUPER_ADMIN,
    RoleEnum.SCHOOL_ADMIN,
    RoleEnum.PROFESSIONAL,
)


def _load_student_for_view(student_id: int) -> Student:
    student = visible_students_query().filter(Student.id == student_id).first()
    if not student:
        abort(404)
    if not can_view_attendance_of_student(student):
        abort(403)
    return student


@attendances_bp.route("/students/<int:student_id>/attendances")
@login_required
@deny_administrative
@require_role(*NON_ADMINISTRATIVE_ROLES)
def list_view(student_id: int):
    student = _load_student_for_view(student_id)
    items = (
        db.session.query(Attendance)
        .filter_by(student_id=student.id)
        .order_by(Attendance.started_at.desc())
        .all()
    )
    return render_template("attendances/list.html", student=student, attendances=items)


@attendances_bp.route("/students/<int:student_id>/attendances/new", methods=["GET", "POST"])
@login_required
@deny_administrative
@require_role(RoleEnum.PROFESSIONAL)
def new(student_id: int):
    student = _load_student_for_view(student_id)
    prof = current_professional()
    if not prof:
        abort(403)
    # only forms of professional category, with published version
    available = (
        db.session.query(Form)
        .filter(
            Form.organization_id == student.school.organization_id,
            Form.category_id == prof.category_id,
        )
        .all()
    )
    version_choices = []
    for f in available:
        v = f.latest_published
        if v:
            version_choices.append((v.id, f"{f.name} (v{v.version_number})"))
    form = AttendanceStartForm()
    form.form_version_id.choices = version_choices
    if not version_choices:
        flash(
            "Não há formulários publicados para a sua categoria. Solicite ao administrador.",
            "warning",
        )
    if form.validate_on_submit():
        version = db.session.get(FormVersion, form.form_version_id.data)
        if not version or version.status != FormStatusEnum.PUBLISHED:
            abort(400)
        if version.form.category_id != prof.category_id:
            abort(403)
        att = Attendance(
            student_id=student.id,
            professional_id=prof.id,
            form_version_id=version.id,
            status=AttendanceStatusEnum.DRAFT,
            notes=form.notes.data or None,
        )
        db.session.add(att)
        db.session.commit()
        return redirect(url_for("attendances.detail", attendance_id=att.id))
    return render_template("attendances/new.html", student=student, form=form)


def _load_attendance(attendance_id: int) -> Attendance:
    att = db.session.get(Attendance, attendance_id)
    if not att:
        abort(404)
    if not can_view_attendance_of_student(att.student):
        abort(403)
    return att


@attendances_bp.route("/attendances/<int:attendance_id>", methods=["GET", "POST"])
@login_required
@deny_administrative
def detail(attendance_id: int):
    att = _load_attendance(attendance_id)
    answers_by_field = {a.field_id: a for a in att.answers}

    is_owner_or_admin = (
        (current_professional() and current_professional().id == att.professional_id)
        or _is_school_admin_for(att)
    )

    if request.method == "POST":
        if att.is_submitted:
            abort(409)
        if not is_owner_or_admin:
            abort(403)
        action = request.form.get("action", "save")
        errors = save_answers(
            db.session, att, request.form, submit=(action == "submit")
        )
        if errors:
            for e in errors:
                flash(e, "danger")
            db.session.rollback()
        else:
            db.session.commit()
            flash(
                "Atendimento submetido." if action == "submit" else "Rascunho salvo.",
                "success",
            )
            return redirect(url_for("attendances.detail", attendance_id=att.id))
        # reload after rollback
        att = _load_attendance(attendance_id)
        answers_by_field = {a.field_id: a for a in att.answers}

    return render_template(
        "attendances/detail.html",
        attendance=att,
        answers=answers_by_field,
        editable=(not att.is_submitted) and is_owner_or_admin,
    )


def _is_school_admin_for(attendance: Attendance) -> bool:
    from ...context import get_current_context

    ctx = get_current_context()
    if not ctx:
        return False
    return ctx["role"] in (RoleEnum.SCHOOL_ADMIN, RoleEnum.ORG_SUPER_ADMIN)
