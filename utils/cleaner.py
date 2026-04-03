from __future__ import annotations

import re
import unicodedata


_WHITESPACE_RE = re.compile(r"[ \t\f\v\u00A0]+")
_REPEAT_NEWLINES_RE = re.compile(r"\n{3,}")
_NOISE_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
_SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.;:!?\)\]\}])")
_SPACE_AFTER_OPEN_RE = re.compile(r"([\(\[\{])\s+")
_WATERMARK_RE = re.compile(r"https?://(?:www\.)?teachingbd(?:24)?\.com\S*", re.IGNORECASE)
_PAGE_MARKER_RE = re.compile(r"---\s*PAGE\s*\d+\s*---", re.IGNORECASE)
_SUSPICIOUS_LATIN_TOKEN_RE = re.compile(r"\b(?:ore|wet|fase|sst|pat|vili|eq|ts|so)\b", re.IGNORECASE)
_EG_A_RE = re.compile(r"\bEg\s*[‘'\"`]?a[’'\"`]?\b", re.IGNORECASE)
_BN_CHAR_RE = re.compile(r"[\u0980-\u09FF]")
_EN_CHAR_RE = re.compile(r"[A-Za-z]")
_QUESTION_START_RE = re.compile(
    r"^\s*((\d{1,3}|[০-৯]{1,3})\s*[\.)\:।]|[কখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎ]\s*[\)\.])"
)


def _join_broken_lines(lines: list[str]) -> str:
    """Join OCR-broken lines while keeping structural breaks for question markers."""
    merged: list[str] = []
    for line in lines:
        if not line:
            merged.append("")
            continue

        if not merged or not merged[-1]:
            merged.append(line)
            continue

        if _QUESTION_START_RE.match(line):
            merged.append(line)
            continue

        # Typical OCR wrapping: continuation line should be part of previous sentence.
        merged[-1] = f"{merged[-1]} {line}".strip()

    return "\n".join(merged)


def _fix_mixed_language_artifacts(line: str) -> str:
    """Repair common OCR artifacts in mixed Bangla-English exam text."""
    if not line:
        return line

    has_bn = bool(_BN_CHAR_RE.search(line))
    has_en = bool(_EN_CHAR_RE.search(line))

    if has_bn and has_en:
        line = _EG_A_RE.sub("'অ'", line)
        line = _SUSPICIOUS_LATIN_TOKEN_RE.sub("", line)
        line = line.replace("পীচটি", "পাঁচটি")

        # OCR frequently emits trailing "ore" where Bangla prompt expects "লেখো".
        if re.search(r"\bore\b\s*$", line, flags=re.IGNORECASE):
            line = re.sub(r"\bore\b\s*$", "লেখো", line, flags=re.IGNORECASE)

    return _WHITESPACE_RE.sub(" ", line).strip()


def normalize_mixed_text(text: str) -> str:
    """Normalize mixed Bangla+English OCR text into a clean UTF-8 string."""
    if not text:
        return ""

    # Unicode normalization helps align similar Bangla/English glyph variants.
    normalized = unicodedata.normalize("NFKC", text)

    # Remove non-printable OCR noise characters while preserving newlines.
    normalized = _NOISE_RE.sub("", normalized)

    normalized = _WATERMARK_RE.sub("", normalized)
    normalized = _PAGE_MARKER_RE.sub("", normalized)

    cleaned_lines: list[str] = []
    for line in normalized.splitlines():
        line = _WHITESPACE_RE.sub(" ", line).strip()
        line = _fix_mixed_language_artifacts(line)
        cleaned_lines.append(line)

    normalized = _join_broken_lines(cleaned_lines)
    normalized = _SPACE_BEFORE_PUNCT_RE.sub(r"\1", normalized)
    normalized = _SPACE_AFTER_OPEN_RE.sub(r"\1", normalized)
    normalized = _REPEAT_NEWLINES_RE.sub("\n\n", normalized)

    return normalized.strip()


def clean_text(text: str) -> str:
    """Public cleaner entry point used by the OCR pipeline."""
    return normalize_mixed_text(text)
