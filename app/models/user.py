from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin

from .base import Model, TimestampMixin
from .enums import RoleEnum, ScopeTypeEnum


class User(Model, TimestampMixin, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    cpf: Mapped[str] = mapped_column(String(11), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    memberships = relationship(
        "Membership", back_populates="user", cascade="all,delete-orphan", lazy="selectin"
    )
    professional_profiles = relationship(
        "Professional", back_populates="user", cascade="all,delete-orphan"
    )

    def get_id(self) -> str:  # for Flask-Login
        return str(self.id)

    def __repr__(self) -> str:
        return f"<User cpf={self.cpf} {self.full_name}>"


class Membership(Model, TimestampMixin):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "scope_type", "scope_id", "role", name="uq_membership_unique"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scope_type: Mapped[ScopeTypeEnum] = mapped_column(
        Enum(ScopeTypeEnum, name="scope_type_enum"), nullable=False
    )
    scope_id: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[RoleEnum] = mapped_column(
        Enum(RoleEnum, name="role_enum"), nullable=False
    )

    user = relationship("User", back_populates="memberships")

    def __repr__(self) -> str:
        return f"<Membership u={self.user_id} {self.role.value}@{self.scope_type.value}:{self.scope_id}>"
