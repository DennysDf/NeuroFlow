from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Model, TimestampMixin


class Student(Model, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    birthdate: Mapped[date | None] = mapped_column(Date, nullable=True)
    document: Mapped[str | None] = mapped_column(String(30), nullable=True)
    guardian_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    guardian_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    school = relationship("School", back_populates="students")
    team_members = relationship(
        "StudentTeamMember", back_populates="student", cascade="all,delete-orphan"
    )
    attendances = relationship(
        "Attendance", back_populates="student", cascade="all,delete-orphan"
    )

    @property
    def professional_ids(self) -> list[int]:
        return [tm.professional_id for tm in self.team_members]

    def __repr__(self) -> str:
        return f"<Student {self.full_name}>"


class StudentTeamMember(Model, TimestampMixin):
    __tablename__ = "student_team_members"
    __table_args__ = (
        UniqueConstraint("student_id", "professional_id", name="uq_team_student_prof"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    professional_id: Mapped[int] = mapped_column(
        ForeignKey("professionals.id", ondelete="CASCADE"), nullable=False, index=True
    )

    student = relationship("Student", back_populates="team_members")
    professional = relationship("Professional", back_populates="team_memberships")

    def __repr__(self) -> str:
        return f"<StudentTeamMember s={self.student_id} p={self.professional_id}>"
