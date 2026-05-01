from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import Model, TimestampMixin


class Organization(Model, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(20), nullable=True)

    schools = relationship("School", back_populates="organization", cascade="all,delete-orphan")
    categories = relationship(
        "ProfessionalCategory", back_populates="organization", cascade="all,delete-orphan"
    )
    forms = relationship("Form", back_populates="organization", cascade="all,delete-orphan")

    def __repr__(self) -> str:
        return f"<Organization {self.name}>"
