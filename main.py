from __future__ import annotations

from pathlib import Path
import json
import logging
import math
import os
from typing import Iterable, Sequence

from tqdm import tqdm

from utils.cleaner import clean_text
from utils.ocr import extract_text_from_pdf
from utils.parser import build_structured_payload


# Toggle this to True if you want OpenAI-based OCR correction and JSON refinement.
USE_AI_CLEANUP = False
AI_MODEL = "gpt-4.1-mini"

OCR_LANG = "ben+eng"
OCR_DPI = 300
BATCH_SIZE = 10
FORCE_REPROCESS = False
POPPLER_PATH = None  # Example Windows path: r"C:\\poppler\\Library\\bin"

BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "pdfs"
RAW_TEXT_DIR = BASE_DIR / "raw_text"
CLEANED_TEXT_DIR = BASE_DIR / "cleaned_text"
JSON_OUTPUT_DIR = BASE_DIR / "json_output"
ERROR_LOG_PATH = BASE_DIR / "errors.log"


def setup_logging() -> None:
    logging.basicConfig(
        filename=str(ERROR_LOG_PATH),
        level=logging.ERROR,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def ensure_directories() -> None:
    # Keep output locations available for large unattended runs.
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    RAW_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_TEXT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def batched(items: Sequence[Path], size: int) -> Iterable[Sequence[Path]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_json_object(text: str) -> dict | None:
    """Extract the first JSON object from model output if present."""
    text = text.strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        parsed = json.loads(text[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        return None

    return None


def ai_cleanup_payload(cleaned_text: str, fallback_payload: dict) -> dict:
    """Optional OpenAI-based cleanup that returns generic document JSON."""
    if not USE_AI_CLEANUP:
        return fallback_payload

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.error("USE_AI_CLEANUP=True but OPENAI_API_KEY is missing.")
        return fallback_payload

    try:
        from openai import OpenAI
    except Exception as exc:
        logging.error("OpenAI package not installed for AI cleanup: %s", exc)
        return fallback_payload

    system_prompt = (
        "You are given OCR text from a PDF document. "
        "Fix OCR mistakes and return strict JSON with keys: "
        "source_file, generated_at_utc, page_count, word_count, text, pages. "
        "pages must be a list of objects containing page_number and text. "
        "Return JSON only."
    )

    user_prompt = {
        "fallback": fallback_payload,
        "ocr_text": cleaned_text,
    }

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=AI_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
            ],
            temperature=0,
        )

        model_text = response.output_text.strip()
        parsed = extract_json_object(model_text)
        if isinstance(parsed, dict) and "text" in parsed:
            return parsed
    except Exception as exc:
        logging.error("AI cleanup failed: %s", exc)

    return fallback_payload


def process_pdf(pdf_path: Path) -> bool:
    stem = pdf_path.stem
    raw_out = RAW_TEXT_DIR / f"{stem}.txt"
    cleaned_out = CLEANED_TEXT_DIR / f"{stem}.txt"
    json_out = JSON_OUTPUT_DIR / f"{stem}.json"

    try:
        raw_text = extract_text_from_pdf(
            pdf_path,
            lang=OCR_LANG,
            dpi=OCR_DPI,
            poppler_path=POPPLER_PATH,
        )
        write_text(raw_out, raw_text)

        cleaned = clean_text(raw_text)
        write_text(cleaned_out, cleaned)

        fallback_payload = build_structured_payload(cleaned, pdf_path.name)
        final_payload = ai_cleanup_payload(cleaned, fallback_payload)
        write_json(json_out, final_payload)

        return True
    except Exception as exc:
        logging.error("Failed processing %s: %s", pdf_path.name, exc, exc_info=True)
        return False


def is_already_processed(pdf_path: Path) -> bool:
    stem = pdf_path.stem
    raw_out = RAW_TEXT_DIR / f"{stem}.txt"
    cleaned_out = CLEANED_TEXT_DIR / f"{stem}.txt"
    json_out = JSON_OUTPUT_DIR / f"{stem}.json"
    return raw_out.exists() and cleaned_out.exists() and json_out.exists()


def run_pipeline() -> None:
    setup_logging()
    ensure_directories()

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in: {PDF_DIR}")
        return

    total_batches = math.ceil(len(pdf_files) / BATCH_SIZE)
    success_count = 0
    fail_count = 0
    skip_count = 0

    for batch_index, batch in enumerate(batched(pdf_files, BATCH_SIZE), start=1):
        desc = f"Batch {batch_index}/{total_batches}"
        for pdf_path in tqdm(batch, desc=desc, unit="pdf"):
            if not FORCE_REPROCESS and is_already_processed(pdf_path):
                skip_count += 1
                continue

            ok = process_pdf(pdf_path)
            if ok:
                success_count += 1
            else:
                fail_count += 1

    print("Processing complete")
    print(f"Total PDFs: {len(pdf_files)}")
    print(f"Successful: {success_count}")
    print(f"Skipped (already processed): {skip_count}")
    print(f"Failed: {fail_count}")
    print(f"Error log: {ERROR_LOG_PATH}")


if __name__ == "__main__":
    run_pipeline()
