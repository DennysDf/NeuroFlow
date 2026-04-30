from app.models.attendance import Attendance
from app.models.enums import AttendanceStatusEnum, FieldTypeEnum, FormStatusEnum
from app.models.form import Form, FormField, FormVersion
from tests.conftest import login_as


def _make_published_form(db, org, cat):
    f = Form(organization_id=org.id, category_id=cat.id, name="Anamnese")
    db.session.add(f)
    db.session.flush()
    v = FormVersion(form_id=f.id, version_number=1, status=FormStatusEnum.PUBLISHED)
    db.session.add(v)
    db.session.flush()
    db.session.add(
        FormField(form_version_id=v.id, order=0, type=FieldTypeEnum.SHORT_TEXT, label="Queixa")
    )
    db.session.commit()
    return v


def test_team_member_can_view_attendance_created_by_other(client, world, db):
    v = _make_published_form(db, world["org"], world["cat_psi"])
    att = Attendance(
        student_id=world["lucas"].id,
        professional_id=world["maria"].id,
        form_version_id=v.id,
        status=AttendanceStatusEnum.SUBMITTED,
    )
    db.session.add(att)
    db.session.commit()

    login_as(client, world["joao_user"])
    res = client.get(f"/attendances/{att.id}")
    assert res.status_code == 200
    assert b"Anamnese" in res.data


def test_school_admin_sees_attendance(client, world, db):
    v = _make_published_form(db, world["org"], world["cat_psi"])
    att = Attendance(
        student_id=world["lucas"].id,
        professional_id=world["maria"].id,
        form_version_id=v.id,
        status=AttendanceStatusEnum.SUBMITTED,
    )
    db.session.add(att)
    db.session.commit()

    login_as(client, world["school_admin"])
    res = client.get(f"/students/{world['lucas'].id}/attendances")
    assert res.status_code == 200
    assert b"Anamnese" in res.data
