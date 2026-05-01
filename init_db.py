"""Initialize NeuroFlow database schema and seed an organization + super admin.

Idempotent: safe to run multiple times. Creates tables if missing
(via SQLAlchemy create_all) and ensures the seed user/org/categories
exist according to the SEED_* environment variables.
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
from app.models.professional import ProfessionalCategory  # noqa: E402
from app.models.user import Membership, User  # noqa: E402


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "org"


def main() -> int:
    app = create_app()
    with app.app_context():
        print("Criando/atualizando schema do banco...")
        db.create_all()

        org_name = os.environ.get("SEED_ORG_NAME", "NeuroFlow Org")
        org_cnpj = os.environ.get("SEED_ORG_CNPJ", "")
        admin_cpf = normalize_cpf(os.environ.get("SEED_ADMIN_CPF", ""))
        admin_name = os.environ.get("SEED_ADMIN_NAME", "Super Admin")
        admin_email = os.environ.get("SEED_ADMIN_EMAIL", "")
        admin_password = os.environ.get("SEED_ADMIN_PASSWORD", "")

        if not admin_cpf or not validate_cpf(admin_cpf):
            print("ERRO: SEED_ADMIN_CPF ausente ou invalido (configure no .env).")
            return 1
        if not admin_password:
            print("ERRO: SEED_ADMIN_PASSWORD ausente (configure no .env).")
            return 1

        org = db.session.query(Organization).filter_by(name=org_name).first()
        if not org:
            org = Organization(
                name=org_name, slug=slugify(org_name), cnpj=org_cnpj or None
            )
            db.session.add(org)
            db.session.flush()
            print(f"Organizacao criada: {org.name}")
        else:
            print(f"Organizacao ja existia: {org.name}")

        user = db.session.query(User).filter_by(cpf=admin_cpf).first()
        if not user:
            user = User(
                cpf=admin_cpf,
                full_name=admin_name,
                email=admin_email or None,
                password_hash=hash_password(admin_password),
            )
            db.session.add(user)
            db.session.flush()
            print(f"Super admin criado: {user.full_name} (CPF {user.cpf})")
        else:
            print(f"Usuario com CPF {user.cpf} ja existia (senha preservada).")

        existing = (
            db.session.query(Membership)
            .filter_by(
                user_id=user.id,
                scope_type=ScopeTypeEnum.ORG,
                scope_id=org.id,
                role=RoleEnum.ORG_SUPER_ADMIN,
            )
            .first()
        )
        if not existing:
            db.session.add(
                Membership(
                    user_id=user.id,
                    scope_type=ScopeTypeEnum.ORG,
                    scope_id=org.id,
                    role=RoleEnum.ORG_SUPER_ADMIN,
                )
            )
            print("Vinculo ORG_SUPER_ADMIN criado.")

        for name in ("Psicologo", "Assistente Social", "Neuropedagogo"):
            if not (
                db.session.query(ProfessionalCategory)
                .filter_by(organization_id=org.id, name=name)
                .first()
            ):
                db.session.add(ProfessionalCategory(organization_id=org.id, name=name))
                print(f"Categoria criada: {name}")

        db.session.commit()
        print("Banco inicializado com sucesso.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
