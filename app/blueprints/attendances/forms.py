from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional


class AttendanceStartForm(FlaskForm):
    form_version_id = SelectField("Formulário", coerce=int, validators=[DataRequired()])
    notes = TextAreaField("Notas iniciais", validators=[Optional()])
    submit = SubmitField("Iniciar atendimento")
