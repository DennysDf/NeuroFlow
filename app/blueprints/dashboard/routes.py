from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func

from ...context import get_current_context
from ...extensions import db
from ...models.attendance import Attendance
from ...models.enums import RoleEnum, ScopeTypeEnum
from ...models.professional import Professional
from ...models.school import School
from ...models.student import Student
from ...permissions import require_login

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
@require_login
def home():
    ctx = get_current_context()
    stats = {}
    if ctx["scope_type"] == ScopeTypeEnum.ORG:
        org_id = ctx["organization_id"]
        stats["schools"] = db.session.query(func.count(School.id)).filter(
            School.organization_id == org_id
        ).scalar()
        stats["students"] = (
            db.session.query(func.count(Student.id))
            .join(School, Student.school_id == School.id)
            .filter(School.organization_id == org_id)
            .scalar()
        )
        stats["professionals"] = (
            db.session.query(func.count(Professional.id))
            .join(School, Professional.school_id == School.id)
            .filter(School.organization_id == org_id)
            .scalar()
        )
    else:
        school_id = ctx["scope_id"]
        stats["students"] = db.session.query(func.count(Student.id)).filter(
            Student.school_id == school_id
        ).scalar()
        stats["professionals"] = db.session.query(func.count(Professional.id)).filter(
            Professional.school_id == school_id
        ).scalar()
        if ctx["role"] != RoleEnum.ADMINISTRATIVE:
            stats["attendances"] = (
                db.session.query(func.count(Attendance.id))
                .join(Student, Attendance.student_id == Student.id)
                .filter(Student.school_id == school_id)
                .scalar()
            )
    return render_template("dashboard/home.html", stats=stats, ctx=ctx)
