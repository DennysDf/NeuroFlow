from app.blueprints.forms_builder.services import (
    add_field,
    get_or_create_draft,
    publish_draft,
)
from app.models.enums import FieldTypeEnum, FormStatusEnum
from app.models.form import Form, FormVersion


def _new_form(db, world):
    f = Form(
        organization_id=world["org"].id,
        category_id=world["cat_psi"].id,
        name="Anamnese",
    )
    db.session.add(f)
    db.session.flush()
    v = FormVersion(form_id=f.id, version_number=1, status=FormStatusEnum.DRAFT)
    db.session.add(v)
    db.session.commit()
    return f


def test_add_field_increments_order(db, world):
    f = _new_form(db, world)
    draft = get_or_create_draft(db.session, f)
    f1 = add_field(db.session, draft, FieldTypeEnum.SHORT_TEXT)
    f2 = add_field(db.session, draft, FieldTypeEnum.LONG_TEXT)
    db.session.commit()
    assert f1.order == 0
    assert f2.order == 1


def test_publish_creates_immutable_snapshot(db, world):
    f = _new_form(db, world)
    draft = get_or_create_draft(db.session, f)
    add_field(db.session, draft, FieldTypeEnum.SHORT_TEXT)
    publish_draft(db.session, draft)
    db.session.commit()
    assert draft.status == FormStatusEnum.PUBLISHED
    assert draft.schema_json is not None
    assert draft.schema_json["fields"][0]["type"] == "SHORT_TEXT"


def test_get_or_create_draft_clones_published(db, world):
    f = _new_form(db, world)
    draft = get_or_create_draft(db.session, f)
    add_field(db.session, draft, FieldTypeEnum.SHORT_TEXT)
    publish_draft(db.session, draft)
    db.session.commit()

    new_draft = get_or_create_draft(db.session, f)
    db.session.commit()
    assert new_draft.id != draft.id
    assert new_draft.version_number == 2
    assert new_draft.status == FormStatusEnum.DRAFT
    assert len(new_draft.fields) == 1
