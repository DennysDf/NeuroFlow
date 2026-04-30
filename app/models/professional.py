from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Model, TimestampMixin


class ProfessionalCategory(Model, TimestampMixin):
    __tablename__ = "professional_categories"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_category_org_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    organization = relationship("Organization", back_populates="categories")
    professionals = relationship("Professional", back_populates="category")
    forms = relationship("Form", back_populates="category")

    def __repr__(self) -> str:
        return f"<ProfessionalCategory {self.name}>"


class Professional(Model, TimestampMixin):
    __tablename__ = "professionals"
    __table_args__ = (
        UniqueConstraint("user_id", "school_id", name="uq_prof_user_school"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("professional_categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    registration_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    user = relationship("User", back_populates="professional_profiles")
    school = relationship("School", back_populates="professionals")
    category = relationship("ProfessionalCategory", back_populates="professionals")
    team_memberships = relationship(
        "StudentTeamMember", back_populates="professional", cascade="all,delete-orphan"
    )
    attendances = relationship("Attendance", back_populates="professional")

    def __repr__(self) -> str:
        return f"<Professional u={self.user_id} school={self.school_id} cat={self.category_id}>"
