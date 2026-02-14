from typing import Optional
from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    location: Mapped[str] = mapped_column(nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    __table_args__ = (Index("ix_stores_location", "latitude", "longitude"),)
