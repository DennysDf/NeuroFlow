from datetime import datetime, date

from sqlalchemy.orm import Session

from ...models.attendance import Attendance, AttendanceAnswer
from ...models.enums import AttendanceStatusEnum, FieldTypeEnum
from ...models.form import FormField


def save_answers(
    session: Session,
    attendance: Attendance,
    payload: dict,
    submit: bool = False,
) -> list[str]:
    """Persist answers from payload (mapping str(field_id) -> value).

    Returns a list of validation error messages.
    """
    errors: list[str] = []
    fields_by_id = {f.id: f for f in attendance.form_version.fields}
    existing = {a.field_id: a for a in attendance.answers}

    for field in fields_by_id.values():
        key = f"field_{field.id}"
        raw = payload.get(key)
        raw_list = payload.getlist(key) if hasattr(payload, "getlist") else None
        ans = existing.get(field.id)
        if not ans:
            ans = AttendanceAnswer(attendance_id=attendance.id, field_id=field.id)
            session.add(ans)

        ans.value_text = None
        ans.value_number = None
        ans.value_date = None
        ans.value_json = None

        ftype = field.type
        if ftype == FieldTypeEnum.SECTION_HEADER:
            continue
        if ftype in (FieldTypeEnum.SHORT_TEXT, FieldTypeEnum.LONG_TEXT, FieldTypeEnum.SINGLE_CHOICE, FieldTypeEnum.DROPDOWN):
            ans.value_text = (raw or "").strip() or None
        elif ftype == FieldTypeEnum.NUMBER:
            if raw not in (None, ""):
                try:
                    ans.value_number = float(raw)
                except ValueError:
                    errors.append(f"Campo '{field.label}': número inválido.")
        elif ftype == FieldTypeEnum.DATE:
            if raw:
                try:
                    ans.value_date = date.fromisoformat(raw)
                except ValueError:
                    errors.append(f"Campo '{field.label}': data inválida.")
        elif ftype == FieldTypeEnum.MULTI_CHOICE:
            ans.value_json = list(raw_list or [])
        elif ftype == FieldTypeEnum.SCALE_1_5:
            if raw not in (None, ""):
                try:
                    n = int(raw)
                    if 1 <= n <= 5:
                        ans.value_number = float(n)
                    else:
                        errors.append(f"Campo '{field.label}': escala fora de 1-5.")
                except ValueError:
                    errors.append(f"Campo '{field.label}': escala inválida.")
        elif ftype == FieldTypeEnum.CHECKBOX:
            ans.value_json = bool(raw)

        if submit and field.required and ftype != FieldTypeEnum.SECTION_HEADER:
            empty = (
                ans.value_text in (None, "")
                and ans.value_number is None
                and ans.value_date is None
                and ans.value_json in (None, [], False)
            )
            if empty:
                errors.append(f"Campo '{field.label}' é obrigatório.")

    if submit and not errors:
        attendance.status = AttendanceStatusEnum.SUBMITTED
        attendance.ended_at = datetime.utcnow()
    return errors
