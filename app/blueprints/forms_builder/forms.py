from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class FormCreateForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=150)])
    description = TextAreaField("Descrição", validators=[Optional()])
    category_id = SelectField("Categoria do profissional", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Criar formulário")
