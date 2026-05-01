from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError

from .services import normalize_cpf, validate_cpf


class CPFField(StringField):
    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        if self.data:
            self.data = normalize_cpf(self.data)


def cpf_validator(form, field):
    if not validate_cpf(field.data):
        raise ValidationError("CPF inválido.")


class LoginForm(FlaskForm):
    cpf = CPFField(
        "CPF",
        validators=[DataRequired(message="Informe o CPF"), cpf_validator],
        render_kw={"placeholder": "000.000.000-00", "autofocus": True},
    )
    password = PasswordField(
        "Senha",
        validators=[DataRequired(message="Informe a senha"), Length(min=4, max=128)],
    )
    submit = SubmitField("Entrar")
