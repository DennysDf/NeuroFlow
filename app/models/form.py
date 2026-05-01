from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .base import Model, TimestampMixin
from .enums import FieldTypeEnum, FormStatusEnum

# Use portable JSON type so SQLite tests still work
JSONType = JSON().with_variant(JSONB(), "postgresql")


class Form(Model, TimestampMixin):
    __tablename__ = "forms"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("professional_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    organization = relationship("Organization", back_populates="forms")
    category = relationship("ProfessionalCategory", back_populates="forms")
    versions = relationship(
        "FormVersion",
        back_populates="form",
        cascade="all,delete-orphan",
        order_by="FormVersion.version_number",
        foreign_keys="FormVersion.form_id",
    )

    @property
    def latest_published(self) -> "FormVersion | None":
        return next(
            (v for v in reversed(self.versions) if v.status == FormStatusEnum.PUBLISHED),
            None,
        )

    @property
    def draft(self) -> "FormVersion | None":
        return next(
            (v for v in self.versions if v.status == FormStatusEnum.DRAFT), None
        )

    def __repr__(self) -> str:
        return f"<Form {self.name}>"


class FormVersion(Model, TimestampMixin):
    __tablename__ = "form_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    form_id: Mapped[int] = mapped_column(
        ForeignKey("forms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[FormStatusEnum] = mapped_column(
        Enum(FormStatusEnum, name="form_status_enum"),
        nullable=False,
        default=FormStatusEnum.DRAFT,
    )
    schema_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    form = relationship("Form", back_populates="versions", foreign_keys=[form_id])
    fields = relationship(
        "FormField",
        back_populates="form_version",
        cascade="all,delete-orphan",
        order_by="FormField.order",
    )
    attendances = relationship("Attendance", back_populates="form_version")

    @property
    def is_published(self) -> bool:
        return self.status == FormStatusEnum.PUBLISHED

    def __repr__(self) -> str:
        return f"<FormVersion form={self.form_id} v={self.version_number} {self.status.value}>"


class FormField(Model, TimestampMixin):
    __tablename__ = "form_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    form_version_id: Mapped[int] = mapped_column(
        ForeignKey("form_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    type: Mapped[FieldTypeEnum] = mapped_column(
        Enum(FieldTypeEnum, name="field_type_enum"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    help_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    settings_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)

    form_version = relationship("FormVersion", back_populates="fields")
    options = relationship(
        "FormFieldOption",
        back_populates="field",
        cascade="all,delete-orphan",
        order_by="FormFieldOption.order",
    )
    answers = relationship(
        "AttendanceAnswer", back_populates="field", cascade="all,delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FormField {self.type.value} {self.label!r}>"


class FormFieldOption(Model, TimestampMixin):
    __tablename__ = "form_field_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    field_id: Mapped[int] = mapped_column(
        ForeignKey("form_fields.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    label: Mapped[str] = mapped_column(String(150), nullable=False)
    value: Mapped[str] = mapped_column(String(150), nullable=False)

    field = relationship("FormField", back_populates="options")
