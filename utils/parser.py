from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

PAGE_RE = re.compile(r"---\s*PAGE\s*(\d+)\s*---", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")


def clean_payload_text(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip(" |-\n\t")


def split_pages(text: str) -> list[dict]:
    """Split cleaned OCR text into page blocks from PAGE markers."""
    matches = list(PAGE_RE.finditer(text))
    if not matches:
        only = clean_payload_text(text)
        return [{"page_number": 1, "text": only}] if only else []

    pages: list[dict] = []
    for idx, match in enumerate(matches):
        page_number = int(match.group(1))
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        page_text = clean_payload_text(text[start:end])
        pages.append({"page_number": page_number, "text": page_text})
    return pages


def count_words(text: str) -> int:
    cleaned = clean_payload_text(text)
    if not cleaned:
        return 0
    return len(cleaned.split(" "))


def build_structured_payload(text: str, filename: str) -> dict:
    pages = split_pages(text)
    combined_text = clean_payload_text("\n".join(page["text"] for page in pages if page["text"]))
    return {
        "source_file": Path(filename).name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "page_count": len(pages),
        "word_count": count_words(combined_text),
        "text": combined_text,
        "pages": pages,
    }
