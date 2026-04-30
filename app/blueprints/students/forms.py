from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class StudentForm(FlaskForm):
    full_name = StringField("Nome completo", validators=[DataRequired(), Length(max=150)])
    birthdate = DateField("Data de nascimento", validators=[Optional()])
    document = StringField("Documento", validators=[Optional(), Length(max=30)])
    guardian_name = StringField("Responsável", validators=[Optional(), Length(max=150)])
    guardian_phone = StringField("Telefone do responsável", validators=[Optional(), Length(max=40)])
    notes = TextAreaField("Observações", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Salvar")


class TeamAddForm(FlaskForm):
    professional_id = SelectField("Profissional", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Adicionar à equipe")
