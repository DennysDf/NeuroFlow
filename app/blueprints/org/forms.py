from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class SchoolForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=150)])
    address = StringField("Endereço", validators=[Length(max=255)])
    phone = StringField("Telefone", validators=[Length(max=40)])
    submit = SubmitField("Salvar")


class OrganizationForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=150)])
    cnpj = StringField("CNPJ", validators=[Length(max=20)])
    submit = SubmitField("Salvar")
