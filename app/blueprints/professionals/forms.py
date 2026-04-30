from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class CategoryForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=100)])
    description = StringField("Descrição", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Salvar")


class ProfessionalForm(FlaskForm):
    user_id = SelectField("Usuário", coerce=int, validators=[DataRequired()])
    category_id = SelectField("Categoria", coerce=int, validators=[DataRequired()])
    registration_number = StringField(
        "Registro profissional", validators=[Optional(), Length(max=50)]
    )
    submit = SubmitField("Salvar")
