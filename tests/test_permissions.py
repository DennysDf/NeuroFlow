from tests.conftest import login_as


def test_administrative_cannot_view_attendances_list(client, world):
    login_as(client, world["administrative"])
    res = client.get(f"/students/{world['lucas'].id}/attendances")
    assert res.status_code == 403


def test_administrative_cannot_view_attendance_detail(client, world, db):
    from app.models.attendance import Attendance
    from app.models.enums import AttendanceStatusEnum, FormStatusEnum
    from app.models.form import Form, FormField, FormVersion
    from app.models.enums import FieldTypeEnum

    f = Form(
        organization_id=world["org"].id,
        category_id=world["cat_psi"].id,
        name="X",
    )
    db.session.add(f)
    db.session.flush()
    v = FormVersion(form_id=f.id, version_number=1, status=FormStatusEnum.PUBLISHED)
    db.session.add(v)
    db.session.flush()
    db.session.add(
        FormField(form_version_id=v.id, order=0, type=FieldTypeEnum.SHORT_TEXT, label="Q1")
    )
    db.session.flush()
    att = Attendance(
        student_id=world["lucas"].id,
        professional_id=world["maria"].id,
        form_version_id=v.id,
        status=AttendanceStatusEnum.DRAFT,
    )
    db.session.add(att)
    db.session.commit()

    login_as(client, world["administrative"])
    res = client.get(f"/attendances/{att.id}")
    assert res.status_code == 403


def test_school_admin_can_create_school_users(client, world):
    login_as(client, world["school_admin"])
    res = client.get(f"/schools/{world['school'].id}/users")
    assert res.status_code == 200


def test_only_org_super_admin_can_create_schools(client, world):
    login_as(client, world["school_admin"])
    res = client.get("/org/schools/new")
    assert res.status_code == 403


def test_professional_outside_team_gets_403_for_attendances(client, world, db):
    from app.models.attendance import Attendance
    from app.models.enums import AttendanceStatusEnum, FormStatusEnum
    from app.models.form import Form, FormField, FormVersion
    from app.models.enums import FieldTypeEnum

    f = Form(
        organization_id=world["org"].id,
        category_id=world["cat_psi"].id,
        name="X",
    )
    db.session.add(f)
    db.session.flush()
    v = FormVersion(form_id=f.id, version_number=1, status=FormStatusEnum.PUBLISHED)
    db.session.add(v)
    db.session.flush()
    db.session.add(
        FormField(form_version_id=v.id, order=0, type=FieldTypeEnum.SHORT_TEXT, label="Q1")
    )
    db.session.flush()
    att = Attendance(
        student_id=world["lucas"].id,
        professional_id=world["maria"].id,
        form_version_id=v.id,
        status=AttendanceStatusEnum.SUBMITTED,
    )
    db.session.add(att)
    db.session.commit()

    login_as(client, world["ana_user"])  # not on Lucas's team
    res = client.get(f"/attendances/{att.id}")
    assert res.status_code == 403
