from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, Date, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

STATUS = ("applied", "interview")
ALLOWED_KEYS = ("company", "title", "date_applied", "status", "date_interview")

# handle relationship error without circular imports
if TYPE_CHECKING:
    from models.user import User

class Application(Base):
    __tablename__ = "applications"

    # Columns
    # Implicit not null
    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="applications")

    # Default value is generated automatically by the DB (server-side) (date)
    date_applied: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    status: Mapped[str] = mapped_column(Text)

    # Can be null
    date_interview: Mapped[date | None]

    # Converting the model object into a dictionary ready to be returned
    def to_dict(self):
        return {
            "id": self.id,
            "company": self.company,
            "title": self.title,
            "date_applied": self.date_applied.isoformat(),
            "status": self.status,
            "date_interview": (
                self.date_interview.isoformat()
                if self.date_interview is not None
                else None
            ),
        }

    __table_args__ = (
        CheckConstraint(status.in_(STATUS), name="check_status_validity"),
    )