from collections.abc import Iterable
from functools import wraps

from flask import abort
from flask_login import current_user

from .context import get_current_context
from .extensions import db
from .models.enums import RoleEnum, ScopeTypeEnum
from .models.professional import Professional
from .models.school import School
from .models.student import Student
from .models.user import Membership


def _ensure_authenticated():
    if not current_user.is_authenticated:
        abort(401)


def require_login(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        _ensure_authenticated()
        if not get_current_context():
            abort(403)
        return view(*args, **kwargs)

    return wrapper


def require_role(*roles: RoleEnum):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            _ensure_authenticated()
            ctx = get_current_context()
            if not ctx or ctx["role"] not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapper

    return decorator


def deny_administrative(view):
    """Block ADMINISTRATIVE role from a view (used on attendance content)."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        _ensure_authenticated()
        ctx = get_current_context()
        if not ctx or ctx["role"] == RoleEnum.ADMINISTRATIVE:
            abort(403)
        return view(*args, **kwargs)

    return wrapper


def current_role() -> RoleEnum | None:
    ctx = get_current_context()
    return ctx["role"] if ctx else None


def current_organization_id() -> int | None:
    ctx = get_current_context()
    return ctx["organization_id"] if ctx else None


def current_school_id() -> int | None:
    ctx = get_current_context()
    if not ctx:
        return None
    return ctx["scope_id"] if ctx["scope_type"] == ScopeTypeEnum.SCHOOL else None


def can_access_school(school_id: int) -> bool:
    ctx = get_current_context()
    if not ctx:
        return False
    if ctx["role"] == RoleEnum.ORG_SUPER_ADMIN:
        school = db.session.get(School, school_id)
        return bool(school and school.organization_id == ctx["organization_id"])
    return ctx["scope_type"] == ScopeTypeEnum.SCHOOL and ctx["scope_id"] == school_id


def ensure_school_access(school_id: int) -> None:
    if not can_access_school(school_id):
        abort(403)


def current_professional() -> Professional | None:
    ctx = get_current_context()
    if not ctx or ctx["role"] != RoleEnum.PROFESSIONAL:
        return None
    school_id = current_school_id()
    if not school_id:
        return None
    return (
        db.session.query(Professional)
        .filter_by(user_id=current_user.id, school_id=school_id)
        .first()
    )


def can_view_attendance_of_student(student: Student) -> bool:
    ctx = get_current_context()
    if not ctx:
        return False
    if ctx["role"] == RoleEnum.ADMINISTRATIVE:
        return False
    if not can_access_school(student.school_id):
        return False
    if ctx["role"] in (RoleEnum.ORG_SUPER_ADMIN, RoleEnum.SCHOOL_ADMIN):
        return True
    if ctx["role"] == RoleEnum.PROFESSIONAL:
        prof = current_professional()
        return bool(prof and prof.id in student.professional_ids)
    return False


def visible_students_query():
    """Return base query of Student visible by current user (school scope + role)."""
    from .models.student import Student as _Student

    ctx = get_current_context()
    q = db.session.query(_Student)
    if not ctx:
        return q.filter(False)
    if ctx["role"] == RoleEnum.ORG_SUPER_ADMIN:
        return q.join(_Student.school).filter(
            School.organization_id == ctx["organization_id"]
        )
    if ctx["scope_type"] == ScopeTypeEnum.SCHOOL:
        q = q.filter(_Student.school_id == ctx["scope_id"])
    if ctx["role"] == RoleEnum.PROFESSIONAL:
        prof = current_professional()
        if not prof:
            return q.filter(False)
        ids = [tm.student_id for tm in prof.team_memberships]
        return q.filter(_Student.id.in_(ids or [-1]))
    return q


def has_any_role(roles: Iterable[RoleEnum]) -> bool:
    role = current_role()
    return role is not None and role in roles
