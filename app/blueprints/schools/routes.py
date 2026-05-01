from flask import Blueprint, render_template
from flask_login import login_required

from ...extensions import db
from ...models.school import School
from ...permissions import ensure_school_access, require_login

schools_bp = Blueprint("schools", __name__)


@schools_bp.route("/<int:school_id>")
@login_required
@require_login
def detail(school_id: int):
    ensure_school_access(school_id)
    school = db.session.get(School, school_id)
    return render_template("schools/detail.html", school=school)
