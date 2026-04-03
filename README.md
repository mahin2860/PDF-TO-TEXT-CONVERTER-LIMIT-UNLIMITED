# PDF to Text Converter (OCR)

Python OCR pipeline to convert one or many PDF files into plain text and structured JSON. This project is generic and works for any PDF content, not only question papers.

## What It Does

- Converts PDF pages to images using `pdf2image`
- Runs OCR with `pytesseract`
- Cleans noisy OCR output
- Saves:
  - raw OCR text
  - cleaned text
  - generic JSON output per PDF
- Processes many PDFs in batches with progress bars
- Logs failures to `errors.log` and continues processing

## Folder Layout

```text
project/
  pdfs/           # Put input PDF files here
  raw_text/       # Auto-generated raw OCR output
  cleaned_text/   # Auto-generated cleaned text
  json_output/    # Auto-generated JSON output
  main.py
  requirements.txt
  GUIDE.md
  utils/
    ocr.py
    cleaner.py
    parser.py
```

## Setup

1. Install system dependencies:
   - Tesseract OCR
   - Poppler (required by `pdf2image`)

2. Install Python packages:

```bash
pip install -r requirements.txt
```

3. Add PDF files to `pdfs/`.

## Run

```bash
python main.py
```

## Output Format

Each file in `json_output/` uses a generic schema:

```json
{
  "source_file": "example.pdf",
  "generated_at_utc": "2026-04-03T12:00:00+00:00",
  "page_count": 3,
  "word_count": 845,
  "text": "Full OCR text across all pages...",
  "pages": [
    {
      "page_number": 1,
      "text": "OCR text for page 1"
    }
  ]
}
```

## Optional AI Cleanup

- In `main.py`, set `USE_AI_CLEANUP = True`
- Add `OPENAI_API_KEY` to your environment

If AI cleanup fails, the default parsed output is still saved.

## Notes

- Keep `BATCH_SIZE` in `main.py` at a value suitable for your machine.
- Output folders are created automatically when you run the pipeline.
- `.gitkeep` files in `pdfs/`, `raw_text/`, `cleaned_text/`, and `json_output/` are placeholders so these otherwise empty folders remain visible on GitHub.

## Author

Made by Erfan Noor Mahin.

## Contact

Instagram: https://www.instagram.com/mahin_.nn/

## License

This project is licensed under the MIT License. See the LICENSE file for details.
