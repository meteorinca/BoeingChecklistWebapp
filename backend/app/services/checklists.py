from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import yaml
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Checklist, Item, Section
from ..schemas import ChecklistSchema

checklist_schema = ChecklistSchema()


class ChecklistNotFoundError(Exception):
    pass


class ChecklistConflictError(Exception):
    pass


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
    return slug or "checklist"


def generate_unique_slug(base_title: str, checklist_id: str | None = None) -> str:
    base_slug = slugify(base_title)
    slug = base_slug
    counter = 2
    while True:
        query = select(Checklist).where(Checklist.slug == slug)
        if checklist_id:
            query = query.where(Checklist.id != checklist_id)
        exists = db.session.execute(query).scalar_one_or_none()
        if not exists:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def list_checklists() -> list[Checklist]:
    statement = select(Checklist).order_by(Checklist.updated_at.desc())
    return list(db.session.execute(statement).scalars().all())


def get_checklist(checklist_id: str) -> Checklist:
    checklist = db.session.get(Checklist, checklist_id)
    if not checklist:
        raise ChecklistNotFoundError(checklist_id)
    return checklist


def create_checklist(payload: dict, author_override: str | None = None) -> Checklist:
    data = checklist_schema.load(payload)
    checklist = Checklist()
    _apply_checklist_data(checklist, data, author_override)
    db.session.add(checklist)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ChecklistConflictError(str(exc)) from exc
    return checklist


def update_checklist(checklist_id: str, payload: dict, author_override: str | None = None) -> Checklist:
    checklist = get_checklist(checklist_id)
    data = checklist_schema.load(payload)
    _apply_checklist_data(checklist, data, author_override)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ChecklistConflictError(str(exc)) from exc
    return checklist


def patch_checklist(checklist_id: str, payload: dict) -> Checklist:
    checklist = get_checklist(checklist_id)
    merged = checklist_schema.dump(checklist)
    merged.update(payload)
    return update_checklist(checklist_id, merged)


def delete_checklist(checklist_id: str) -> None:
    checklist = get_checklist(checklist_id)
    db.session.delete(checklist)
    db.session.commit()


def import_checklist_from_yaml(checklist_id: str | None, yaml_text: str) -> Checklist:
    payload = _parse_import_payload(yaml_text)
    if checklist_id:
        return update_checklist(checklist_id, payload)
    return create_checklist(payload)


def export_checklist_to_yaml(checklist: Checklist) -> str:
    payload = _normalize_yaml_payload(checklist_schema.dump(checklist))
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def ensure_seed_data(template_path: Path) -> Checklist | None:
    if not template_path.exists():
        return None
    statement = select(Checklist).limit(1)
    existing = db.session.execute(statement).scalar_one_or_none()
    if existing:
        return None
    with template_path.open("r", encoding="utf-8") as handle:
        yaml_text = handle.read()
    checklist = import_checklist_from_yaml(None, yaml_text)
    return checklist


def _apply_checklist_data(checklist: Checklist, data: dict, author_override: str | None) -> None:
    checklist.title = data["title"]
    checklist.author = author_override or data.get("author")
    checklist.revision = data.get("revision")
    checklist.slug = generate_unique_slug(checklist.title, getattr(checklist, "id", None))
    checklist.theme = data.get("theme") or checklist.theme or "boeing"

    metadata = data.get("metadata") or {}
    if metadata.get("created_at"):
        checklist.created_at = metadata["created_at"]
    if metadata.get("updated_at"):
        checklist.updated_at = metadata["updated_at"]

    _sync_sections(checklist, data.get("sections", []))


def _sync_sections(checklist: Checklist, sections_payload: Iterable[dict]) -> None:
    existing_sections = {section.id: section for section in checklist.sections}
    new_sections: list[Section] = []
    for idx, section_data in enumerate(sections_payload, start=1):
        section_id = section_data.get("id")
        section = existing_sections.get(section_id) if section_id else None
        if not section:
            section = Section()
        section.title = section_data["title"]
        section.position = section_data.get("position", idx)
        _sync_items(section, section_data.get("items", []))
        new_sections.append(section)

    checklist.sections[:] = new_sections


def _sync_items(section: Section, items_payload: Iterable[dict]) -> None:
    existing_items = {item.id: item for item in section.items}
    new_items: list[Item] = []
    for idx, item_data in enumerate(items_payload, start=1):
        item_id = item_data.get("id")
        item = existing_items.get(item_id) if item_id else None
        if not item:
            item = Item()
        item.left_text = item_data.get("left_text") or item_data.get("left") or ""
        item.right_text = item_data.get("right_text") or item_data.get("right")
        item.format_flags = item_data.get("format", {}) or {}
        item.position = item_data.get("position", idx)
        new_items.append(item)
    section.items[:] = new_items


def _parse_import_payload(raw_text: str) -> dict:
    if not raw_text or not raw_text.strip():
        raise ValueError("Checklist import is empty")
    sanitized = raw_text.lstrip("\ufeff")
    yaml_error: Exception | None = None
    try:
        parsed_yaml = yaml.safe_load(sanitized)
    except yaml.YAMLError as exc:
        yaml_error = exc
    else:
        if isinstance(parsed_yaml, dict):
            return _normalize_yaml_payload(parsed_yaml)
        if parsed_yaml is not None:
            yaml_error = ValueError("Checklist YAML must be a mapping at the root")
    try:
        markdown_payload = _parse_markdown_checklist(sanitized)
    except ValueError as exc:
        if yaml_error:
            raise ValueError("Checklist import must be valid YAML or Markdown") from exc
        raise
    return _normalize_yaml_payload(markdown_payload)


def _parse_markdown_checklist(markdown_text: str) -> dict:
    lines = [line.rstrip() for line in markdown_text.splitlines()]
    if not any(line.strip() for line in lines):
        raise ValueError("Checklist Markdown is empty")
    cleaned_lines = [line for line in lines if line.strip() != "---"]

    title: str | None = None
    title_level: int | None = None
    sections: list[dict] = []
    current_section: dict | None = None
    current_item: dict | None = None

    def ensure_section(section_title: str) -> dict:
        nonlocal current_section, current_item
        section = {
            "title": section_title.rstrip(":") or f"Section {len(sections) + 1}",
            "items": [],
        }
        sections.append(section)
        current_section = section
        current_item = None
        return section

    for original_line in cleaned_lines:
        stripped = original_line.strip()
        if not stripped:
            current_item = None
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = _strip_markdown_formatting(heading_match.group(2))
            if not title:
                title = heading_text or "Imported Markdown Checklist"
                title_level = level
                current_section = None
                current_item = None
                continue
            effective_level = max(title_level or 2, 2)
            if level >= effective_level:
                ensure_section(heading_text)
                continue

        normalized = original_line.lstrip()

        ordered_match = re.match(r"^\d+[\.)]\s+(.*)", normalized)
        if ordered_match:
            section_title = _strip_markdown_formatting(ordered_match.group(1))
            ensure_section(section_title)
            continue

        bullet_match = re.match(r"^[-+*]\s+(.*)", normalized)
        if bullet_match:
            item_text = _strip_markdown_formatting(bullet_match.group(1))
            if not item_text:
                continue
            if not current_section:
                ensure_section("Checklist")
            item = {
                "left_text": item_text,
                "right_text": None,
                "format": {},
            }
            current_section["items"].append(item)
            current_item = item
            continue

        if current_item and original_line.startswith((" ", "\t")):
            addition = _strip_markdown_formatting(stripped)
            if addition:
                current_item["left_text"] = f"{current_item['left_text']} {addition}".strip()
            continue

        if current_section:
            fallback_text = _strip_markdown_formatting(stripped)
            if fallback_text:
                item = {
                    "left_text": fallback_text,
                    "right_text": None,
                    "format": {},
                }
                current_section["items"].append(item)
                current_item = item
            continue

    if not sections:
        body_items: list[str] = []
        for original_line in cleaned_lines:
            stripped = original_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            text_value = _strip_markdown_formatting(stripped)
            if text_value:
                body_items.append(text_value)
        if body_items:
            sections.append(
                {
                    "title": title or "Checklist",
                    "items": [
                        {"left_text": item, "right_text": None, "format": {}}
                        for item in body_items
                    ],
                }
            )
        else:
            raise ValueError("Checklist Markdown did not contain any sections or items")

    if not title:
        if sections:
            title = sections[0]["title"] or "Imported Markdown Checklist"
        else:
            title = "Imported Markdown Checklist"

    return {
        "title": title,
        "sections": sections,
        "metadata": {"title": title},
        "theme": "boeing",
    }


def _strip_markdown_formatting(value: str | None) -> str:
    if value is None:
        return ""
    text = value.strip()
    if not text:
        return ""
    text = re.sub(r"\r?\n", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)
    text = re.sub(r"~~(.*?)~~", r"\1", text)
    text = text.replace("\\", "")
    return " ".join(text.split())


def _normalize_yaml_payload(parsed: dict) -> dict:
    metadata = parsed.get("metadata", {})
    sections = parsed.get("sections", [])
    theme_value = parsed.get("theme") or metadata.get("theme") or "boeing"
    normalized_sections = []
    for position, section in enumerate(sections, start=1):
        normalized_items = []
        for idx, item in enumerate(section.get("items", []), start=1):
            normalized_items.append(
                {
                    "id": item.get("id"),
                    "left_text": item.get("left_text") or item.get("left"),
                    "right_text": item.get("right_text") or item.get("right"),
                    "format": item.get("format") or {},
                    "position": item.get("position", idx),
                }
            )
        normalized_sections.append(
            {
                "id": section.get("id"),
                "title": section["title"],
                "position": section.get("position", position),
                "items": normalized_items,
            }
        )
    payload = {
        "id": parsed.get("id"),
        "title": parsed.get("title") or metadata.get("title"),
        "author": parsed.get("author") or metadata.get("author"),
        "revision": parsed.get("revision") or metadata.get("revision"),
        "theme": theme_value,
        "sections": normalized_sections,
        "metadata": {
            "title": metadata.get("title") or parsed.get("title"),
            "author": metadata.get("author"),
            "revision": metadata.get("revision"),
            "theme": metadata.get("theme") or theme_value,
            "created_at": metadata.get("created_at"),
            "updated_at": metadata.get("updated_at"),
        },
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return payload
