from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required

from ...extensions import db
from ...models.enums import FieldTypeEnum, FormStatusEnum, RoleEnum
from ...models.form import Form, FormField, FormFieldOption, FormVersion
from ...models.professional import ProfessionalCategory
from ...models.school import School
from ...permissions import (
    current_organization_id,
    ensure_school_access,
    require_role,
)
from .forms import FormCreateForm
from .services import add_field, get_or_create_draft, publish_draft, serialize_version

forms_bp = Blueprint("forms", __name__)

ADMIN_ROLES = (
    RoleEnum.ORG_SUPER_ADMIN,
    RoleEnum.SCHOOL_ADMIN,
    RoleEnum.ADMINISTRATIVE,
)


@forms_bp.route("/schools/<int:school_id>/forms")
@login_required
@require_role(*ADMIN_ROLES)
def list_view(school_id: int):
    ensure_school_access(school_id)
    school = db.session.get(School, school_id)
    forms = (
        db.session.query(Form)
        .filter_by(organization_id=school.organization_id)
        .order_by(Form.id.desc())
        .all()
    )
    return render_template("forms/list.html", forms=forms, school_id=school_id)


@forms_bp.route("/schools/<int:school_id>/forms/new", methods=["GET", "POST"])
@login_required
@require_role(*ADMIN_ROLES)
def new(school_id: int):
    ensure_school_access(school_id)
    school = db.session.get(School, school_id)
    form = FormCreateForm()
    form.category_id.choices = [
        (c.id, c.name)
        for c in db.session.query(ProfessionalCategory)
        .filter_by(organization_id=school.organization_id)
        .order_by(ProfessionalCategory.name)
        .all()
    ]
    if form.validate_on_submit():
        f = Form(
            organization_id=school.organization_id,
            category_id=form.category_id.data,
            name=form.name.data,
            description=form.description.data or None,
        )
        db.session.add(f)
        db.session.flush()
        # create initial draft
        draft = FormVersion(
            form_id=f.id, version_number=1, status=FormStatusEnum.DRAFT
        )
        db.session.add(draft)
        db.session.commit()
        return redirect(url_for("forms.builder", school_id=school_id, form_id=f.id))
    return render_template("forms/new.html", form=form, school_id=school_id)


def _load_form(school_id: int, form_id: int) -> Form:
    ensure_school_access(school_id)
    school = db.session.get(School, school_id)
    f = db.session.get(Form, form_id)
    if not f or f.organization_id != school.organization_id:
        abort(404)
    return f


@forms_bp.route("/schools/<int:school_id>/forms/<int:form_id>/builder")
@login_required
@require_role(*ADMIN_ROLES)
def builder(school_id: int, form_id: int):
    f = _load_form(school_id, form_id)
    draft = get_or_create_draft(db.session, f)
    db.session.commit()
    db.session.refresh(draft)
    return render_template(
        "forms/builder.html",
        form=f,
        draft=draft,
        school_id=school_id,
        field_types=list(FieldTypeEnum),
    )


# --- Builder API (HTMX) ---


@forms_bp.route(
    "/schools/<int:school_id>/forms/<int:form_id>/fields", methods=["POST"]
)
@login_required
@require_role(*ADMIN_ROLES)
def builder_add_field(school_id: int, form_id: int):
    f = _load_form(school_id, form_id)
    draft = get_or_create_draft(db.session, f)
    raw_type = request.form.get("type")
    try:
        field_type = FieldTypeEnum(raw_type)
    except ValueError:
        abort(400)
    add_field(db.session, draft, field_type)
    db.session.commit()
    db.session.refresh(draft)
    return render_template(
        "forms/_canvas.html", draft=draft, school_id=school_id, form=f
    )


@forms_bp.route(
    "/schools/<int:school_id>/forms/<int:form_id>/fields/<int:field_id>",
    methods=["PATCH", "POST"],
)
@login_required
@require_role(*ADMIN_ROLES)
def builder_update_field(school_id: int, form_id: int, field_id: int):
    f = _load_form(school_id, form_id)
    draft = f.draft
    if not draft:
        abort(409)
    field = db.session.get(FormField, field_id)
    if not field or field.form_version_id != draft.id:
        abort(404)
    data = request.form
    field.label = data.get("label", field.label)[:255]
    field.help_text = (data.get("help_text") or "")[:500] or None
    field.required = data.get("required") in ("on", "true", "1", "yes")
    if field.type.has_options:
        labels = data.getlist("option_label")
        # rewrite options
        for opt in list(field.options):
            db.session.delete(opt)
        db.session.flush()
        for i, lbl in enumerate(labels):
            lbl = (lbl or "").strip()
            if not lbl:
                continue
            db.session.add(
                FormFieldOption(field_id=field.id, order=i, label=lbl, value=lbl)
            )
    db.session.commit()
    db.session.refresh(draft)
    return render_template(
        "forms/_canvas.html", draft=draft, school_id=school_id, form=f
    )


@forms_bp.route(
    "/schools/<int:school_id>/forms/<int:form_id>/fields/<int:field_id>/delete",
    methods=["POST"],
)
@login_required
@require_role(*ADMIN_ROLES)
def builder_delete_field(school_id: int, form_id: int, field_id: int):
    f = _load_form(school_id, form_id)
    draft = f.draft
    if not draft:
        abort(409)
    field = db.session.get(FormField, field_id)
    if not field or field.form_version_id != draft.id:
        abort(404)
    db.session.delete(field)
    db.session.commit()
    db.session.refresh(draft)
    return render_template(
        "forms/_canvas.html", draft=draft, school_id=school_id, form=f
    )


@forms_bp.route(
    "/schools/<int:school_id>/forms/<int:form_id>/fields/reorder", methods=["POST"]
)
@login_required
@require_role(*ADMIN_ROLES)
def builder_reorder(school_id: int, form_id: int):
    f = _load_form(school_id, form_id)
    draft = f.draft
    if not draft:
        abort(409)
    order = request.form.getlist("order[]") or request.json.get("order", [])
    for i, fid in enumerate(order):
        field = db.session.get(FormField, int(fid))
        if field and field.form_version_id == draft.id:
            field.order = i
    db.session.commit()
    return jsonify({"ok": True})


@forms_bp.route(
    "/schools/<int:school_id>/forms/<int:form_id>/publish", methods=["POST"]
)
@login_required
@require_role(*ADMIN_ROLES)
def builder_publish(school_id: int, form_id: int):
    f = _load_form(school_id, form_id)
    draft = f.draft
    if not draft:
        flash("Não há rascunho para publicar.", "warning")
        return redirect(url_for("forms.builder", school_id=school_id, form_id=form_id))
    if not draft.fields:
        flash("Adicione pelo menos um campo antes de publicar.", "warning")
        return redirect(url_for("forms.builder", school_id=school_id, form_id=form_id))
    publish_draft(db.session, draft)
    db.session.commit()
    flash(f"Versão {draft.version_number} publicada.", "success")
    return redirect(url_for("forms.builder", school_id=school_id, form_id=form_id))
