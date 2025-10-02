from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


class Checklist(db.Model):
    __tablename__ = "checklists"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    author: Mapped[str] = mapped_column(db.String(255), nullable=True)
    revision: Mapped[str] = mapped_column(db.String(50), nullable=True)
    theme: Mapped[str] = mapped_column(db.String(50), nullable=False, default="boeing")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    sections: Mapped[list[Section]] = relationship(
        "Section",
        back_populates="checklist",
        cascade="all, delete-orphan",
        order_by="Section.position",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "author": self.author,
            "revision": self.revision,
            "theme": self.theme,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "sections": [section.to_dict() for section in self.sections],
        }


class Section(db.Model):
    __tablename__ = "sections"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    checklist_id: Mapped[str] = mapped_column(
        db.ForeignKey("checklists.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(db.String(255), nullable=False)
    position: Mapped[int] = mapped_column(default=0, nullable=False)

    checklist: Mapped[Checklist] = relationship("Checklist", back_populates="sections")
    items: Mapped[list[Item]] = relationship(
        "Item",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="Item.position",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "position": self.position,
            "items": [item.to_dict() for item in self.items],
        }


class Item(db.Model):
    __tablename__ = "items"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    section_id: Mapped[str] = mapped_column(
        db.ForeignKey("sections.id", ondelete="CASCADE"), nullable=False
    )
    left_text: Mapped[str] = mapped_column(db.Text, nullable=False)
    right_text: Mapped[str] = mapped_column(db.Text, nullable=True)
    format_flags: Mapped[dict] = mapped_column(JSON, default=dict)
    position: Mapped[int] = mapped_column(default=0, nullable=False)

    section: Mapped[Section] = relationship("Section", back_populates="items")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "left_text": self.left_text,
            "right_text": self.right_text,
            "format": self.format_flags or {},
            "position": self.position,
        }
