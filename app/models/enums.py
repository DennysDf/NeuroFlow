import enum


class RoleEnum(str, enum.Enum):
    ORG_SUPER_ADMIN = "ORG_SUPER_ADMIN"
    SCHOOL_ADMIN = "SCHOOL_ADMIN"
    ADMINISTRATIVE = "ADMINISTRATIVE"
    PROFESSIONAL = "PROFESSIONAL"

    @property
    def label(self) -> str:
        return {
            "ORG_SUPER_ADMIN": "Super Admin (Organização)",
            "SCHOOL_ADMIN": "Administrador da Escola",
            "ADMINISTRATIVE": "Administrativo",
            "PROFESSIONAL": "Profissional",
        }[self.value]


class ScopeTypeEnum(str, enum.Enum):
    ORG = "ORG"
    SCHOOL = "SCHOOL"


class FieldTypeEnum(str, enum.Enum):
    SHORT_TEXT = "SHORT_TEXT"
    LONG_TEXT = "LONG_TEXT"
    NUMBER = "NUMBER"
    DATE = "DATE"
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTI_CHOICE = "MULTI_CHOICE"
    DROPDOWN = "DROPDOWN"
    SCALE_1_5 = "SCALE_1_5"
    CHECKBOX = "CHECKBOX"
    SECTION_HEADER = "SECTION_HEADER"

    @property
    def label(self) -> str:
        return {
            "SHORT_TEXT": "Texto curto",
            "LONG_TEXT": "Parágrafo",
            "NUMBER": "Número",
            "DATE": "Data",
            "SINGLE_CHOICE": "Escolha única",
            "MULTI_CHOICE": "Múltipla escolha",
            "DROPDOWN": "Lista suspensa",
            "SCALE_1_5": "Escala 1-5",
            "CHECKBOX": "Caixa de seleção",
            "SECTION_HEADER": "Cabeçalho de seção",
        }[self.value]

    @property
    def has_options(self) -> bool:
        return self in {
            FieldTypeEnum.SINGLE_CHOICE,
            FieldTypeEnum.MULTI_CHOICE,
            FieldTypeEnum.DROPDOWN,
        }


class FormStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class AttendanceStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"


class AppointmentStatusEnum(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    DONE = "DONE"
    CANCELED = "CANCELED"
