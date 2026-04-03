from __future__ import annotations

from pathlib import Path
import logging

import pytesseract
from pdf2image import convert_from_path


def extract_text_from_pdf(
    pdf_path: Path,
    *,
    lang: str = "ben+eng",
    dpi: int = 300,
    poppler_path: str | None = None,
    tesseract_config: str = "--oem 1 --psm 6",
) -> str:
    """Convert a PDF to images and run OCR on each page."""
    try:
        pages = convert_from_path(
            str(pdf_path),
            dpi=dpi,
            fmt="jpeg",
            thread_count=2,
            poppler_path=poppler_path,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to render PDF pages: {pdf_path}") from exc

    extracted_pages: list[str] = []
    for page_number, image in enumerate(pages, start=1):
        try:
            text = pytesseract.image_to_string(
                image,
                lang=lang,
                config=tesseract_config,
            )
        except Exception as exc:
            logging.warning(
                "OCR failed for %s page %s: %s",
                pdf_path.name,
                page_number,
                exc,
            )
            text = ""

        extracted_pages.append(f"--- PAGE {page_number} ---\n{text.strip()}")

    return "\n\n".join(extracted_pages).strip()
