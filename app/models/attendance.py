from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Model, TimestampMixin
from .enums import AttendanceStatusEnum
from .form import JSONType


class Attendance(Model, TimestampMixin):
    __tablename__ = "attendances"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    professional_id: Mapped[int] = mapped_column(
        ForeignKey("professionals.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    form_version_id: Mapped[int] = mapped_column(
        ForeignKey("form_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[AttendanceStatusEnum] = mapped_column(
        Enum(AttendanceStatusEnum, name="attendance_status_enum"),
        nullable=False,
        default=AttendanceStatusEnum.DRAFT,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    student = relationship("Student", back_populates="attendances")
    professional = relationship("Professional", back_populates="attendances")
    form_version = relationship("FormVersion", back_populates="attendances")
    answers = relationship(
        "AttendanceAnswer", back_populates="attendance", cascade="all,delete-orphan"
    )
    appointment = relationship(
        "Appointment", back_populates="attendance", uselist=False
    )

    @property
    def is_submitted(self) -> bool:
        return self.status == AttendanceStatusEnum.SUBMITTED

    def __repr__(self) -> str:
        return f"<Attendance s={self.student_id} p={self.professional_id} {self.status.value}>"


class AttendanceAnswer(Model, TimestampMixin):
    __tablename__ = "attendance_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    attendance_id: Mapped[int] = mapped_column(
        ForeignKey("attendances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_id: Mapped[int] = mapped_column(
        ForeignKey("form_fields.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    value_json: Mapped[dict | list | None] = mapped_column(JSONType, nullable=True)

    attendance = relationship("Attendance", back_populates="answers")
    field = relationship("FormField", back_populates="answers")
