from __future__ import annotations

from typing import Any

from marshmallow import Schema, ValidationError, fields, post_load, validates_schema


class ItemSchema(Schema):
    id = fields.String(allow_none=True)
    left_text = fields.String(required=True)
    right_text = fields.String(allow_none=True)
    format = fields.Dict(keys=fields.String(), values=fields.Raw(), load_default=dict)
    position = fields.Integer(load_default=0)


class SectionSchema(Schema):
    id = fields.String(allow_none=True)
    title = fields.String(required=True)
    position = fields.Integer(load_default=0)
    items = fields.List(fields.Nested(ItemSchema), load_default=list)


class MetadataSchema(Schema):
    title = fields.String(required=True)
    author = fields.String(allow_none=True)
    revision = fields.String(allow_none=True)
    theme = fields.String(load_default="moeing", allow_none=True)
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)


class ChecklistSchema(Schema):
    id = fields.String(allow_none=True)
    title = fields.String(required=True)
    slug = fields.String(load_default=None, allow_none=True)
    author = fields.String(allow_none=True)
    revision = fields.String(allow_none=True)
    theme = fields.String(load_default="moeing", allow_none=True)
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)
    sections = fields.List(fields.Nested(SectionSchema), required=True)
    metadata = fields.Nested(MetadataSchema, allow_none=True)

    @validates_schema
    def ensure_sections_order(self, data: dict[str, Any], **kwargs: Any) -> None:
        if not data.get("sections"):
            raise ValidationError("Checklist requires at least one section", "sections")


class ChecklistListSchema(Schema):
    id = fields.String(required=True)
    title = fields.String(required=True)
    author = fields.String(allow_none=True)
    revision = fields.String(allow_none=True)
    theme = fields.String(load_default="moeing", allow_none=True)
    updated_at = fields.DateTime(required=True)
