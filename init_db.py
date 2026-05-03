"""Initialize NeuroFlow database schema and seed a demo organization,
super admin, school admin, administrative, professional and a sample
student so every role can be exercised right after the first run.

Idempotent: safe to run multiple times.
"""

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app.auth.services import hash_password, normalize_cpf, validate_cpf  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.enums import RoleEnum, ScopeTypeEnum  # noqa: E402
from app.models.organization import Organization  # noqa: E402
from app.models.professional import Professional, ProfessionalCategory  # noqa: E402
from app.models.school import School  # noqa: E402
from app.models.student import Student, StudentTeamMember  # noqa: E402
from app.models.user import Membership, User  # noqa: E402


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "org"


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def ensure_user(cpf_raw: str, full_name: str, email: str, password: str) -> User:
    cpf = normalize_cpf(cpf_raw)
    if not validate_cpf(cpf):
        raise SystemExit(f"ERRO: CPF invalido para {full_name}: '{cpf_raw}'")
    if not password:
        raise SystemExit(f"ERRO: senha vazia para {full_name}")
    user = db.session.query(User).filter_by(cpf=cpf).first()
    if not user:
        user = User(
            cpf=cpf,
            full_name=full_name,
            email=email or None,
            password_hash=hash_password(password),
        )
        db.session.add(user)
        db.session.flush()
        print(f"  + Usuario {full_name} (CPF {cpf}) criado")
    return user


def ensure_membership(
    user: User, scope_type: ScopeTypeEnum, scope_id: int, role: RoleEnum
) -> Membership:
    m = (
        db.session.query(Membership)
        .filter_by(user_id=user.id, scope_type=scope_type, scope_id=scope_id, role=role)
        .first()
    )
    if not m:
        m = Membership(
            user_id=user.id, scope_type=scope_type, scope_id=scope_id, role=role
        )
        db.session.add(m)
        db.session.flush()
        print(f"    -> vinculo {role.value} concedido")
    return m


def ensure_organization(name: str, cnpj: str) -> Organization:
    org = db.session.query(Organization).filter_by(name=name).first()
    if not org:
        org = Organization(name=name, slug=slugify(name), cnpj=cnpj or None)
        db.session.add(org)
        db.session.flush()
        print(f"+ Organizacao '{name}' criada")
    else:
        print(f"  Organizacao '{name}' ja existia")
    return org


def ensure_school(org: Organization, name: str) -> School:
    school = (
        db.session.query(School)
        .filter_by(organization_id=org.id, name=name)
        .first()
    )
    if not school:
        school = School(organization_id=org.id, name=name)
        db.session.add(school)
        db.session.flush()
        print(f"+ Escola '{name}' criada")
    return school


def ensure_category(org: Organization, name: str) -> ProfessionalCategory:
    cat = (
        db.session.query(ProfessionalCategory)
        .filter_by(organization_id=org.id, name=name)
        .first()
    )
    if not cat:
        cat = ProfessionalCategory(organization_id=org.id, name=name)
        db.session.add(cat)
        db.session.flush()
        print(f"  + Categoria {name} criada")
    return cat


def ensure_professional(
    user: User, school: School, category: ProfessionalCategory
) -> Professional:
    prof = (
        db.session.query(Professional)
        .filter_by(user_id=user.id, school_id=school.id)
        .first()
    )
    if not prof:
        prof = Professional(
            user_id=user.id, school_id=school.id, category_id=category.id
        )
        db.session.add(prof)
        db.session.flush()
        print(f"  + Profissional {user.full_name} ({category.name}) cadastrado")
    return prof


def ensure_student(school: School, full_name: str) -> Student:
    s = (
        db.session.query(Student)
        .filter_by(school_id=school.id, full_name=full_name)
        .first()
    )
    if not s:
        s = Student(school_id=school.id, full_name=full_name)
        db.session.add(s)
        db.session.flush()
        print(f"+ Aluno '{full_name}' cadastrado")
    return s


def ensure_team_member(student: Student, professional: Professional) -> None:
    exists = (
        db.session.query(StudentTeamMember)
        .filter_by(student_id=student.id, professional_id=professional.id)
        .first()
    )
    if not exists:
        db.session.add(
            StudentTeamMember(student_id=student.id, professional_id=professional.id)
        )
        db.session.flush()
        print(f"    -> {professional.user.full_name} adicionado a equipe de {student.full_name}")


def main() -> int:
    app = create_app()
    with app.app_context():
        print("Criando/atualizando schema do banco...")
        db.create_all()

        # ---------------- Organizacao + Super Admin ----------------
        org = ensure_organization(
            env("SEED_ORG_NAME", "NeuroFlow Org"),
            env("SEED_ORG_CNPJ", ""),
        )

        super_admin = ensure_user(
            env("SEED_ADMIN_CPF"),
            env("SEED_ADMIN_NAME", "Super Admin"),
            env("SEED_ADMIN_EMAIL", ""),
            env("SEED_ADMIN_PASSWORD"),
        )
        ensure_membership(
            super_admin, ScopeTypeEnum.ORG, org.id, RoleEnum.ORG_SUPER_ADMIN
        )

        # ---------------- Categorias padrao ----------------
        cat_psi = ensure_category(org, "Psicologo")
        ensure_category(org, "Assistente Social")
        ensure_category(org, "Neuropedagogo")

        # ---------------- Escola Demo + perfis adicionais ----------------
        if env("SEED_DEMO", "1") == "1":
            school = ensure_school(
                org, env("SEED_SCHOOL_NAME", "Escola Demonstracao")
            )

            if env("SEED_SCHOOL_ADMIN_CPF"):
                u = ensure_user(
                    env("SEED_SCHOOL_ADMIN_CPF"),
                    env("SEED_SCHOOL_ADMIN_NAME", "Diretor Demo"),
                    env("SEED_SCHOOL_ADMIN_EMAIL", ""),
                    env("SEED_SCHOOL_ADMIN_PASSWORD", ""),
                )
                ensure_membership(
                    u, ScopeTypeEnum.SCHOOL, school.id, RoleEnum.SCHOOL_ADMIN
                )

            if env("SEED_ADMINISTRATIVE_CPF"):
                u = ensure_user(
                    env("SEED_ADMINISTRATIVE_CPF"),
                    env("SEED_ADMINISTRATIVE_NAME", "Secretaria Demo"),
                    env("SEED_ADMINISTRATIVE_EMAIL", ""),
                    env("SEED_ADMINISTRATIVE_PASSWORD", ""),
                )
                ensure_membership(
                    u, ScopeTypeEnum.SCHOOL, school.id, RoleEnum.ADMINISTRATIVE
                )

            psi_prof = None
            if env("SEED_PSI_CPF"):
                u = ensure_user(
                    env("SEED_PSI_CPF"),
                    env("SEED_PSI_NAME", "Maria Psi"),
                    env("SEED_PSI_EMAIL", ""),
                    env("SEED_PSI_PASSWORD", ""),
                )
                ensure_membership(
                    u, ScopeTypeEnum.SCHOOL, school.id, RoleEnum.PROFESSIONAL
                )
                psi_prof = ensure_professional(u, school, cat_psi)

            # also give the super admin a SCHOOL_ADMIN membership in the demo
            # school so logging in as super admin lets you exercise school-scoped
            # screens immediately via "Trocar contexto".
            ensure_membership(
                super_admin, ScopeTypeEnum.SCHOOL, school.id, RoleEnum.SCHOOL_ADMIN
            )

            student_name = env("SEED_STUDENT_NAME", "Lucas Demonstracao")
            student = ensure_student(school, student_name)
            if psi_prof:
                ensure_team_member(student, psi_prof)

        db.session.commit()
        print("Banco inicializado com sucesso.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
