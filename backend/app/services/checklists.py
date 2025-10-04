from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import yaml
from google.cloud import firestore

from ..extensions import get_firestore
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
        existing = _find_by_slug(slug)
        if not existing:
            return slug
        if existing.id == checklist_id:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def list_checklists() -> list[dict]:
    query = _collection().order_by("updated_at", direction=firestore.Query.DESCENDING)
    return [_serialize_snapshot(snapshot) for snapshot in query.stream()]


def get_checklist(checklist_id: str) -> dict:
    snapshot = _document(checklist_id).get()
    if not snapshot.exists:
        raise ChecklistNotFoundError(checklist_id)
    return _serialize_snapshot(snapshot)


def create_checklist(payload: dict, author_override: str | None = None) -> dict:
    data = checklist_schema.load(payload)
    checklist_id = data.get("id") or _create_id()
    ref = _document(checklist_id)
    if ref.get().exists:
        raise ChecklistConflictError(f"Checklist {checklist_id} already exists")
    record = _build_record(data, checklist_id, author_override, existing=None)
    ref.set(record)
    return _serialize_dict(checklist_id, record)


def update_checklist(checklist_id: str, payload: dict, author_override: str | None = None) -> dict:
    ref = _document(checklist_id)
    snapshot = ref.get()
    if not snapshot.exists:
        raise ChecklistNotFoundError(checklist_id)
    existing = snapshot.to_dict() or {}
    existing["id"] = checklist_id
    data = checklist_schema.load(payload)
    record = _build_record(data, checklist_id, author_override, existing=existing)
    ref.set(record)
    return _serialize_dict(checklist_id, record)


def patch_checklist(checklist_id: str, payload: dict) -> dict:
    current = get_checklist(checklist_id)
    merged = {**current, **payload}
    if "sections" not in payload:
        merged["sections"] = current.get("sections", [])
    return update_checklist(checklist_id, merged)


def delete_checklist(checklist_id: str) -> None:
    ref = _document(checklist_id)
    snapshot = ref.get()
    if not snapshot.exists:
        raise ChecklistNotFoundError(checklist_id)
    ref.delete()


def import_checklist_from_yaml(checklist_id: str | None, yaml_text: str) -> dict:
    payload = _parse_import_payload(yaml_text)
    if checklist_id:
        return update_checklist(checklist_id, payload)
    return create_checklist(payload)


def export_checklist_to_yaml(checklist: dict) -> str:
    payload = _normalize_yaml_payload(checklist)
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def ensure_seed_data(template_path: Path) -> dict | None:
    if not template_path.exists():
        return None
    if next(_collection().limit(1).stream(), None):
        return None
    with template_path.open("r", encoding="utf-8") as handle:
        yaml_text = handle.read()
    return import_checklist_from_yaml(None, yaml_text)


def _collection() -> firestore.CollectionReference:
    return get_firestore().collection("checklists")


def _document(checklist_id: str) -> firestore.DocumentReference:
    return _collection().document(checklist_id)


def _find_by_slug(slug: str) -> firestore.DocumentSnapshot | None:
    query = _collection().where("slug", "==", slug).limit(1).stream()
    for snapshot in query:
        return snapshot
    return None


def _create_id() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _build_record(
    data: dict,
    checklist_id: str,
    author_override: str | None,
    existing: dict | None,
) -> dict:
    author = author_override or data.get("author")
    theme = data.get("theme") or (existing.get("theme") if existing else "boeing")
    slug = generate_unique_slug(data["title"], checklist_id=checklist_id)
    sections = _normalize_sections(data.get("sections", []))
    metadata = _normalize_metadata(data.get("metadata") or {}, data["title"], author, theme)

    now = _now()
    created_at_source = data.get("created_at")
    if created_at_source is None and existing:
        created_at_source = existing.get("created_at")
    created_at = _to_utc(created_at_source) or now

    updated_at = _to_utc(data.get("updated_at")) or now

    if "created_at" in metadata:
        created_at = _to_utc(metadata["created_at"]) or created_at
    if "updated_at" in metadata:
        updated_at = _to_utc(metadata["updated_at"]) or updated_at

    record = {
        "id": checklist_id,
        "title": data["title"],
        "slug": slug,
        "author": author,
        "revision": data.get("revision"),
        "theme": theme,
        "sections": sections,
        "metadata": metadata,
        "created_at": created_at,
        "updated_at": updated_at,
    }
    return record


def _normalize_sections(sections_payload: Iterable[dict]) -> list[dict]:
    normalized: list[dict] = []
    for index, section in enumerate(sections_payload, start=1):
        normalized.append(
            {
                "id": section.get("id") or _create_id(),
                "title": section["title"],
                "position": section.get("position", index),
                "items": _normalize_items(section.get("items", [])),
            }
        )
    return normalized


def _normalize_items(items_payload: Iterable[dict]) -> list[dict]:
    normalized: list[dict] = []
    for index, item in enumerate(items_payload, start=1):
        normalized.append(
            {
                "id": item.get("id") or _create_id(),
                "left_text": item.get("left_text") or item.get("left") or "",
                "right_text": item.get("right_text") or item.get("right"),
                "format": item.get("format") or {},
                "position": item.get("position", index),
            }
        )
    return normalized


def _normalize_metadata(metadata: dict, title: str, author: str | None, theme: str) -> dict:
    normalized = {
        "title": metadata.get("title") or title,
        "author": metadata.get("author") or author,
        "revision": metadata.get("revision"),
        "theme": metadata.get("theme") or theme,
    }
    if metadata.get("created_at"):
        normalized["created_at"] = _to_iso(metadata["created_at"])
    if metadata.get("updated_at"):
        normalized["updated_at"] = _to_iso(metadata["updated_at"])
    return {key: value for key, value in normalized.items() if value is not None}


def _serialize_snapshot(snapshot: firestore.DocumentSnapshot) -> dict:
    return _serialize_dict(snapshot.id, snapshot.to_dict() or {})


def _serialize_dict(checklist_id: str, record: dict) -> dict:
    data = {
        "id": checklist_id,
        "title": record.get("title"),
        "slug": record.get("slug"),
        "author": record.get("author"),
        "revision": record.get("revision"),
        "theme": record.get("theme"),
        "created_at": _to_iso(record.get("created_at")),
        "updated_at": _to_iso(record.get("updated_at")),
        "sections": [],
        "metadata": {},
    }
    for section in record.get("sections", []):
        data["sections"].append(
            {
                "id": section.get("id"),
                "title": section.get("title"),
                "position": section.get("position"),
                "items": [
                    {
                        "id": item.get("id"),
                        "left_text": item.get("left_text"),
                        "right_text": item.get("right_text"),
                        "format": item.get("format") or {},
                        "position": item.get("position"),
                    }
                    for item in section.get("items", [])
                ],
            }
        )
    metadata = record.get("metadata") or {}
    serialized_metadata: dict[str, object] = {}
    for key, value in metadata.items():
        if key in {"created_at", "updated_at"}:
            serialized_metadata[key] = _to_iso(value)
        else:
            serialized_metadata[key] = value
    data["metadata"] = serialized_metadata
    return data


def _to_iso(value):
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        iso_value = value.isoformat(timespec="seconds")
        if iso_value.endswith("+00:00"):
            iso_value = iso_value[:-6] + "Z"
        return iso_value
    return value


def _to_utc(value):
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return None


def _parse_import_payload(raw_text: str) -> dict:
    if not raw_text or not raw_text.strip():
        raise ValueError("Checklist import is empty")
    sanitized = raw_text.lstrip("﻿")
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

        if current_item and original_line.startswith((" ", "	")):
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
