from flask import Flask, session
from flask_login import current_user

from .extensions import db
from .models.enums import RoleEnum, ScopeTypeEnum
from .models.organization import Organization
from .models.school import School
from .models.user import Membership


def get_current_context() -> dict | None:
    """Return active context (org/school) stored in session, validating membership."""
    ctx = session.get("context")
    if not ctx or not current_user.is_authenticated:
        return None
    membership = db.session.get(Membership, ctx.get("membership_id"))
    if not membership or membership.user_id != current_user.id:
        session.pop("context", None)
        return None
    scope_obj = None
    if membership.scope_type == ScopeTypeEnum.ORG:
        scope_obj = db.session.get(Organization, membership.scope_id)
    else:
        scope_obj = db.session.get(School, membership.scope_id)
    return {
        "membership": membership,
        "role": membership.role,
        "scope_type": membership.scope_type,
        "scope_id": membership.scope_id,
        "scope": scope_obj,
        "organization_id": (
            membership.scope_id
            if membership.scope_type == ScopeTypeEnum.ORG
            else (scope_obj.organization_id if scope_obj else None)
        ),
    }


def register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_context():
        ctx = get_current_context() if current_user.is_authenticated else None
        return {
            "current_context": ctx,
            "RoleEnum": RoleEnum,
            "ScopeTypeEnum": ScopeTypeEnum,
        }
