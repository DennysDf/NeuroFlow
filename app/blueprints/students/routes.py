from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from ...extensions import db
from ...models.enums import RoleEnum
from ...models.professional import Professional
from ...models.student import Student, StudentTeamMember
from ...permissions import (
    ensure_school_access,
    require_role,
    visible_students_query,
)
from .forms import StudentForm, TeamAddForm

students_bp = Blueprint("students", __name__)

ADMIN_ROLES = (
    RoleEnum.ORG_SUPER_ADMIN,
    RoleEnum.SCHOOL_ADMIN,
    RoleEnum.ADMINISTRATIVE,
)
ALL_ROLES = (
    RoleEnum.ORG_SUPER_ADMIN,
    RoleEnum.SCHOOL_ADMIN,
    RoleEnum.ADMINISTRATIVE,
    RoleEnum.PROFESSIONAL,
)


@students_bp.route("/schools/<int:school_id>/students")
@login_required
@require_role(*ALL_ROLES)
def list_view(school_id: int):
    ensure_school_access(school_id)
    students = (
        visible_students_query()
        .filter(Student.school_id == school_id)
        .order_by(Student.full_name)
        .all()
    )
    return render_template(
        "students/list.html", students=students, school_id=school_id
    )


@students_bp.route("/schools/<int:school_id>/students/new", methods=["GET", "POST"])
@login_required
@require_role(*ADMIN_ROLES)
def new(school_id: int):
    ensure_school_access(school_id)
    form = StudentForm()
    if form.validate_on_submit():
        student = Student(
            school_id=school_id,
            full_name=form.full_name.data,
            birthdate=form.birthdate.data,
            document=form.document.data or None,
            guardian_name=form.guardian_name.data or None,
            guardian_phone=form.guardian_phone.data or None,
            notes=form.notes.data or None,
        )
        db.session.add(student)
        db.session.commit()
        flash("Aluno cadastrado.", "success")
        return redirect(url_for("students.detail", student_id=student.id))
    return render_template("students/form.html", form=form, school_id=school_id, mode="new")


def _load_visible_student(student_id: int) -> Student:
    student = (
        visible_students_query().filter(Student.id == student_id).first()
    )
    if not student:
        abort(404)
    return student


@students_bp.route("/students/<int:student_id>")
@login_required
@require_role(*ALL_ROLES)
def detail(student_id: int):
    student = _load_visible_student(student_id)
    return render_template("students/detail.html", student=student)


@students_bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
@require_role(*ADMIN_ROLES)
def edit(student_id: int):
    student = _load_visible_student(student_id)
    form = StudentForm(obj=student)
    if form.validate_on_submit():
        form.populate_obj(student)
        db.session.commit()
        flash("Aluno atualizado.", "success")
        return redirect(url_for("students.detail", student_id=student.id))
    return render_template(
        "students/form.html", form=form, school_id=student.school_id, mode="edit"
    )


@students_bp.route("/students/<int:student_id>/team", methods=["GET", "POST"])
@login_required
@require_role(*ADMIN_ROLES)
def team(student_id: int):
    student = _load_visible_student(student_id)
    form = TeamAddForm()
    available = (
        db.session.query(Professional)
        .filter(Professional.school_id == student.school_id)
        .order_by(Professional.id)
        .all()
    )
    form.professional_id.choices = [
        (p.id, f"{p.user.full_name} — {p.category.name}") for p in available
    ]
    if form.validate_on_submit():
        member = StudentTeamMember(
            student_id=student.id, professional_id=form.professional_id.data
        )
        db.session.add(member)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Profissional já está na equipe.", "warning")
        else:
            flash("Profissional adicionado à equipe.", "success")
        return redirect(url_for("students.team", student_id=student.id))
    return render_template("students/team.html", student=student, form=form)


@students_bp.route("/students/<int:student_id>/team/<int:member_id>/delete", methods=["POST"])
@login_required
@require_role(*ADMIN_ROLES)
def team_delete(student_id: int, member_id: int):
    student = _load_visible_student(student_id)
    member = db.session.get(StudentTeamMember, member_id)
    if not member or member.student_id != student.id:
        abort(404)
    db.session.delete(member)
    db.session.commit()
    flash("Profissional removido da equipe.", "info")
    return redirect(url_for("students.team", student_id=student.id))
