import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest

os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("TEST_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test")

from app import create_app  # noqa: E402
from app.auth.services import hash_password  # noqa: E402
from app.extensions import db as _db  # noqa: E402
from app.models.enums import RoleEnum, ScopeTypeEnum  # noqa: E402
from app.models.organization import Organization  # noqa: E402
from app.models.professional import Professional, ProfessionalCategory  # noqa: E402
from app.models.school import School  # noqa: E402
from app.models.student import Student, StudentTeamMember  # noqa: E402
from app.models.user import Membership, User  # noqa: E402


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def world(db):
    """Build a small org/school/professionals/students universe for tests."""
    org = Organization(name="Org A", slug="org-a")
    db.session.add(org)
    db.session.flush()

    school = School(organization_id=org.id, name="Escola A")
    db.session.add(school)
    db.session.flush()

    cat_psi = ProfessionalCategory(organization_id=org.id, name="Psicólogo")
    cat_social = ProfessionalCategory(organization_id=org.id, name="Assistente Social")
    db.session.add_all([cat_psi, cat_social])
    db.session.flush()

    def mkuser(cpf, name, role, scope_type=ScopeTypeEnum.SCHOOL, scope_id=None):
        u = User(
            cpf=cpf,
            full_name=name,
            password_hash=hash_password("Senha123!"),
        )
        db.session.add(u)
        db.session.flush()
        m = Membership(
            user_id=u.id,
            scope_type=scope_type,
            scope_id=scope_id if scope_id is not None else (org.id if scope_type == ScopeTypeEnum.ORG else school.id),
            role=role,
        )
        db.session.add(m)
        db.session.flush()
        return u, m

    super_admin, super_m = mkuser(
        "11144477735", "Super Admin", RoleEnum.ORG_SUPER_ADMIN, ScopeTypeEnum.ORG
    )
    school_admin, _ = mkuser("52998224725", "School Admin", RoleEnum.SCHOOL_ADMIN)
    administrative, _ = mkuser("39053344705", "Administrativo", RoleEnum.ADMINISTRATIVE)

    maria_user, _ = mkuser("85718189538", "Maria Psi", RoleEnum.PROFESSIONAL)
    joao_user, _ = mkuser("65669511014", "João Psi", RoleEnum.PROFESSIONAL)
    ana_user, _ = mkuser("32802127080", "Ana Outsider", RoleEnum.PROFESSIONAL)

    maria = Professional(user_id=maria_user.id, school_id=school.id, category_id=cat_psi.id)
    joao = Professional(user_id=joao_user.id, school_id=school.id, category_id=cat_psi.id)
    ana = Professional(user_id=ana_user.id, school_id=school.id, category_id=cat_psi.id)
    db.session.add_all([maria, joao, ana])
    db.session.flush()

    lucas = Student(school_id=school.id, full_name="Lucas")
    db.session.add(lucas)
    db.session.flush()
    db.session.add_all(
        [
            StudentTeamMember(student_id=lucas.id, professional_id=maria.id),
            StudentTeamMember(student_id=lucas.id, professional_id=joao.id),
        ]
    )
    db.session.commit()

    return {
        "org": org,
        "school": school,
        "cat_psi": cat_psi,
        "cat_social": cat_social,
        "super_admin": super_admin,
        "school_admin": school_admin,
        "administrative": administrative,
        "maria_user": maria_user,
        "joao_user": joao_user,
        "ana_user": ana_user,
        "maria": maria,
        "joao": joao,
        "ana": ana,
        "lucas": lucas,
    }


def login_as(client, user):
    membership = user.memberships[0]
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
        sess["context"] = {
            "membership_id": membership.id,
            "scope_type": membership.scope_type.value,
            "scope_id": membership.scope_id,
            "role": membership.role.value,
        }
