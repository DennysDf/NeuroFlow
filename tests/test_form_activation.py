from app.blueprints.forms_builder.services import (
    activate_form,
    add_field,
    get_or_create_draft,
    publish_draft,
)
from app.models.enums import FieldTypeEnum, FormStatusEnum
from app.models.form import Form, FormVersion
from tests.conftest import login_as


def _new_published_form(db, world, name: str) -> Form:
    f = Form(
        organization_id=world["org"].id,
        category_id=world["cat_psi"].id,
        name=name,
    )
    db.session.add(f)
    db.session.flush()
    draft = get_or_create_draft(db.session, f)
    add_field(db.session, draft, FieldTypeEnum.SHORT_TEXT)
    publish_draft(db.session, draft)
    db.session.commit()
    return f


def test_activate_form_deactivates_siblings_in_same_category(db, world):
    f1 = _new_published_form(db, world, "Anamnese A")
    f2 = _new_published_form(db, world, "Anamnese B")
    activate_form(db.session, f1)
    db.session.commit()
    assert f1.is_active is True
    assert f2.is_active is False

    activate_form(db.session, f2)
    db.session.commit()
    db.session.refresh(f1)
    db.session.refresh(f2)
    assert f1.is_active is False
    assert f2.is_active is True


def test_activate_does_not_affect_other_categories(db, world):
    f_psi = _new_published_form(db, world, "Anamnese Psi")
    f_social = Form(
        organization_id=world["org"].id,
        category_id=world["cat_social"].id,
        name="Anamnese Social",
    )
    db.session.add(f_social)
    db.session.flush()
    draft = get_or_create_draft(db.session, f_social)
    add_field(db.session, draft, FieldTypeEnum.SHORT_TEXT)
    publish_draft(db.session, draft)
    activate_form(db.session, f_social)
    db.session.commit()

    activate_form(db.session, f_psi)
    db.session.commit()
    db.session.refresh(f_psi)
    db.session.refresh(f_social)
    assert f_psi.is_active is True
    assert f_social.is_active is True


def test_attendance_new_offers_only_active_form(client, db, world):
    inactive = _new_published_form(db, world, "Antiga")
    active = _new_published_form(db, world, "Atual")
    activate_form(db.session, active)
    db.session.commit()

    login_as(client, world["maria_user"])
    res = client.get(f"/students/{world['lucas'].id}/attendances/new")
    assert res.status_code == 200
    assert b"Atual" in res.data
    assert b"Antiga" not in res.data


def test_attendance_new_warns_when_no_active_form(client, db, world):
    _new_published_form(db, world, "Existe mas inativo")
    login_as(client, world["maria_user"])
    res = client.get(f"/students/{world['lucas'].id}/attendances/new")
    assert res.status_code == 200
    assert b"formul" in res.data  # "formulário ativo publicado..." flash


def test_preview_page_renders(client, db, world):
    f = _new_published_form(db, world, "Anamnese Psi")
    login_as(client, world["school_admin"])
    res = client.get(f"/schools/{world['school'].id}/forms/{f.id}/preview")
    assert res.status_code == 200
    assert b"Anamnese Psi" in res.data
    assert b"v1" in res.data


def test_activate_route_requires_published_version(client, db, world):
    f = Form(
        organization_id=world["org"].id,
        category_id=world["cat_psi"].id,
        name="Sem publicar",
    )
    db.session.add(f)
    db.session.commit()

    login_as(client, world["school_admin"])
    res = client.post(
        f"/schools/{world['school'].id}/forms/{f.id}/activate",
        follow_redirects=False,
    )
    assert res.status_code in (302, 303)
    db.session.refresh(f)
    assert f.is_active is False
