from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Model, TimestampMixin


class School(Model, TimestampMixin):
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)

    organization = relationship("Organization", back_populates="schools")
    professionals = relationship(
        "Professional", back_populates="school", cascade="all,delete-orphan"
    )
    students = relationship("Student", back_populates="school", cascade="all,delete-orphan")
    appointments = relationship(
        "Appointment", back_populates="school", cascade="all,delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<School {self.name}>"
