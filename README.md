# OTSE — Optical Transceiver Spec Extractor

Local LLM-powered tool that parses optical transceiver PDF datasheets into structured data. Extracts atomic parameters (wavelength, baud rate, power, FEC, modulation, reach, etc.) into a validated Pydantic schema. Runs entirely on-device via llama-server with a Streamlit UI for reviewing parsed content before extraction.

## How It Works

```
PDF Upload → Parse (PyMuPDF) → Review/Edit Markdown → LLM Extraction → Validated JSON
```

1. **Parse** — Converts PDF to markdown using PyMuPDF4LLM (text + tables)
2. **Review** — Editable text area to fix OCR errors or trim irrelevant sections
3. **Extract** — Local LLM fills every field in `TransceiverSpecs` as independent atoms
4. **Store** — Each run is saved with metadata, the markdown sent, raw LLM output, and validated specs

## Requirements

- Python 3.11+
- [llama-server](https://github.com/ggerganov/llama.cpp) with GGUF models in `C:\Haris\models`
- Dependencies: `streamlit`, `openai`, `pydantic`, `pymupdf`, `pymupdf4llm`, `requests`

## Setup

```bash
pip install streamlit openai pydantic pymupdf pymupdf4llm requests
```

Start the model server:

```bash
llama-server --models-dir C:\Haris\models --models-max 1
```

## Usage

```bash
streamlit run app.py
```

Or via CLI:

```bash
python -m pipeline.run path/to/datasheet.pdf --model Qwen3.6-27B-Q4_K_M
```

## Project Structure

```
app.py                  Streamlit UI
transceiver_models.py   Pydantic schema (TransceiverSpecs)
pipeline/
  pdf_parser.py         PDF → ParsedDatasheet (pages, tables, markdown)
  atom_extractor.py     LLM extraction → validated specs
  runtime_store.py      Per-run storage (runs/<timestamp>/)
  run.py                CLI entry point
```

## Run Storage

Each extraction run is saved under `runs/<YYYYMMDD_HHMMSS>/`:

| File | Contents |
|------|----------|
| `meta.json` | Timestamp, source file, model used, validation status |
| `content.md` | The markdown actually sent to the LLM |
| `raw_llm.json` | Raw JSON returned by the model |
| `specs.json` | Validated `TransceiverSpecs` (only if validation passed) |
| `parsed.json` | Parse metadata (page count, tables, char count) |

## Extracted Parameters

The schema covers: vendor/model identification, wavelength/frequency, baud rate, modulation formats, TX/RX power, OSNR, chromatic dispersion, PMD/PDL, FEC types and thresholds, reach, host/media interface codes, form factor, and direct-detect specific fields.
