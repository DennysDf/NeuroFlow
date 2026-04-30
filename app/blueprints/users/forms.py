from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError

from ...auth.forms import CPFField, cpf_validator
from ...models.enums import RoleEnum


class UserCreateForm(FlaskForm):
    cpf = CPFField("CPF", validators=[DataRequired(), cpf_validator])
    full_name = StringField("Nome completo", validators=[DataRequired(), Length(max=150)])
    email = StringField("E-mail", validators=[Optional(), Email(), Length(max=150)])
    password = PasswordField(
        "Senha inicial", validators=[DataRequired(), Length(min=8, max=128)]
    )
    role = SelectField(
        "Perfil",
        choices=[
            (RoleEnum.SCHOOL_ADMIN.value, RoleEnum.SCHOOL_ADMIN.label),
            (RoleEnum.ADMINISTRATIVE.value, RoleEnum.ADMINISTRATIVE.label),
            (RoleEnum.PROFESSIONAL.value, RoleEnum.PROFESSIONAL.label),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Criar usuário")


class MembershipAddForm(FlaskForm):
    role = SelectField(
        "Perfil",
        choices=[
            (RoleEnum.SCHOOL_ADMIN.value, RoleEnum.SCHOOL_ADMIN.label),
            (RoleEnum.ADMINISTRATIVE.value, RoleEnum.ADMINISTRATIVE.label),
            (RoleEnum.PROFESSIONAL.value, RoleEnum.PROFESSIONAL.label),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Adicionar vínculo")
