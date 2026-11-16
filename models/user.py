from typing import TYPE_CHECKING
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

# handle relationship error without circular imports
if TYPE_CHECKING:
    from models.application import Application

class User(Base):
    __tablename__ = "users"

    # Columns
    # Implicit not null
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)

    applications: Mapped[list["Application"]] = relationship(
        back_populates="user"
    )

    # Converting the model object into a dictionary ready to be returned
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email
        }