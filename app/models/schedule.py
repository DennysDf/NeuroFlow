from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Model, TimestampMixin
from .enums import AppointmentStatusEnum


class Appointment(Model, TimestampMixin):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    professional_id: Mapped[int] = mapped_column(
        ForeignKey("professionals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[AppointmentStatusEnum] = mapped_column(
        Enum(AppointmentStatusEnum, name="appointment_status_enum"),
        nullable=False,
        default=AppointmentStatusEnum.SCHEDULED,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    attendance_id: Mapped[int | None] = mapped_column(
        ForeignKey("attendances.id", ondelete="SET NULL"), nullable=True
    )

    school = relationship("School", back_populates="appointments")
    professional = relationship("Professional")
    student = relationship("Student")
    attendance = relationship("Attendance", back_populates="appointment")

    def __repr__(self) -> str:
        return f"<Appointment s={self.student_id} p={self.professional_id} {self.starts_at}>"
