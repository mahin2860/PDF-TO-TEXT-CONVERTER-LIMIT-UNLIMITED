# Quick Guide

## 1) Install requirements

```bash
pip install -r requirements.txt
```

Also install these system tools:

- Tesseract OCR
- Poppler

## 2) Add your PDFs

Put any PDF files into the `pdfs/` folder.

## 3) Run converter

```bash
python main.py
```

## 4) Check output

- `raw_text/` -> direct OCR text
- `cleaned_text/` -> normalized text
- `json_output/` -> structured JSON output
- `errors.log` -> failed files (if any)

## Optional: AI OCR cleanup

1. Open `main.py`
2. Set `USE_AI_CLEANUP = True`
3. Set environment variable `OPENAI_API_KEY`
4. Run `python main.py` again

The tool works on general PDF documents and is not limited to question papers.
