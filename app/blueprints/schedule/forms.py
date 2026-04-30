from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class AppointmentForm(FlaskForm):
    professional_id = SelectField("Profissional", coerce=int, validators=[DataRequired()])
    student_id = SelectField("Aluno", coerce=int, validators=[DataRequired()])
    starts_at = DateTimeLocalField(
        "Início", format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    ends_at = DateTimeLocalField(
        "Término", format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    location = StringField("Local", validators=[Optional(), Length(max=150)])
    notes = TextAreaField("Observações", validators=[Optional()])
    submit = SubmitField("Salvar")
