from datetime import datetime

from sqlalchemy.orm import Session

from ...models.enums import FieldTypeEnum, FormStatusEnum
from ...models.form import Form, FormField, FormFieldOption, FormVersion


def get_or_create_draft(session: Session, form: Form) -> FormVersion:
    """Return current DRAFT version, creating one (cloning latest published) if none exists."""
    draft = next((v for v in form.versions if v.status == FormStatusEnum.DRAFT), None)
    if draft:
        return draft
    next_number = max((v.version_number for v in form.versions), default=0) + 1
    draft = FormVersion(
        form_id=form.id, version_number=next_number, status=FormStatusEnum.DRAFT
    )
    session.add(draft)
    session.flush()
    latest_pub = next(
        (v for v in reversed(form.versions) if v.status == FormStatusEnum.PUBLISHED),
        None,
    )
    if latest_pub:
        for f in latest_pub.fields:
            new_f = FormField(
                order=f.order,
                type=f.type,
                label=f.label,
                help_text=f.help_text,
                required=f.required,
                settings_json=f.settings_json,
            )
            draft.fields.append(new_f)
            session.flush()
            for o in f.options:
                new_f.options.append(
                    FormFieldOption(order=o.order, label=o.label, value=o.value)
                )
    session.flush()
    return draft


def serialize_version(version: FormVersion) -> dict:
    return {
        "id": version.id,
        "version_number": version.version_number,
        "status": version.status.value,
        "fields": [
            {
                "id": f.id,
                "type": f.type.value,
                "label": f.label,
                "help_text": f.help_text,
                "required": f.required,
                "settings": f.settings_json or {},
                "options": [
                    {"id": o.id, "label": o.label, "value": o.value, "order": o.order}
                    for o in f.options
                ],
                "order": f.order,
            }
            for f in version.fields
        ],
    }


def activate_form(session: Session, form: Form) -> None:
    """Mark this form active and deactivate all sibling forms in the same category."""
    siblings = (
        session.query(Form)
        .filter(
            Form.organization_id == form.organization_id,
            Form.category_id == form.category_id,
            Form.id != form.id,
            Form.is_active.is_(True),
        )
        .all()
    )
    for s in siblings:
        s.is_active = False
    form.is_active = True
    session.flush()


def publish_draft(session: Session, draft: FormVersion) -> None:
    if draft.status != FormStatusEnum.DRAFT:
        raise ValueError("Apenas versões em rascunho podem ser publicadas.")
    draft.schema_json = serialize_version(draft)
    draft.status = FormStatusEnum.PUBLISHED
    draft.published_at = datetime.utcnow()
    session.flush()


def add_field(
    session: Session, version: FormVersion, field_type: FieldTypeEnum
) -> FormField:
    if version.status != FormStatusEnum.DRAFT:
        raise ValueError("Versão publicada é imutável.")
    next_order = max((f.order for f in version.fields), default=-1) + 1
    field = FormField(
        order=next_order,
        type=field_type,
        label=field_type.label,
        required=False,
    )
    version.fields.append(field)
    session.flush()
    if field_type.has_options:
        for i, lbl in enumerate(["Opção 1", "Opção 2"]):
            field.options.append(
                FormFieldOption(order=i, label=lbl, value=lbl)
            )
    session.flush()
    return field
