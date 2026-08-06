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

## Design Notes

Why the pipeline is shaped this way:

**Two-stage extraction: atoms first, then modes.** Rather than asking the model to produce a
structured, mode-aware object in one pass, extraction is split into two stages. Stage one pulls every
parameter as an independent atomic value with no cross-field inference. Stage two links those atoms
into coherent operating modes. For coherent optics datasheets, recovering which values *co-occur* in a
selectable configuration is the genuinely hard part — a single module may expose a dozen application
codes, each with its own baud rate, modulation, OSNR requirement and reach. Separating "what values
exist" from "which values belong together" keeps the second, harder question from corrupting the first. Separating the extraction into two parts increased the accuracy to 99% as deterministic steps and decisions between the parts made the schema dynamically adaptable to transceiver and easier to debug. Trying to prompt the LLM in one pass to separate the module level and mode level parameter, gather and synthesis the modes across different sections of pdf drastically reduces the extraction quality, accuracy, validity, and success rate.

**Module envelope vs. per-mode specification.** `MODE_FIELDS` in `transceiver_models.py` marks which
parameters vary per configuration and which describe the module as a whole. A worst-case receiver
sensitivity is a hardware envelope; a required OSNR is a per-mode figure. Encoding that distinction in
the schema means mode synthesis only has to reason about the fields that can actually differ.

**Field descriptions do double duty.** Each Pydantic `Field(description=...)` is both the validation
contract and the schema text sent to the model, generated from `model_json_schema()`. There is one
definition of what a field means, so the prompt and the validator cannot drift apart as the schema
evolves.

**Human review sits before extraction, not after.** PDF-to-text on vendor datasheets is unreliable —
merged table cells, footnote markers glued to values, multi-column layouts. The editable markdown step
acknowledges that rather than pretending parsing is solved, and lets the operator trim irrelevant
sections or repair a mangled table before spending inference time on it.

**Runs record exactly what was sent.** `content.md` stores the post-edit markdown that actually reached
the model, alongside the raw LLM response and the validated specs. A run can be understood after the
fact without re-parsing the source PDF.

## Requirements

- Python 3.11+
- [llama-server](https://github.com/ggerganov/llama.cpp) with GGUF models in `C:\Haris\models`

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Dependencies are pinned exactly, because extraction output depends on the versions in use and a stored
run is only reproducible against a known environment. For linting and tests, use
`pip install -r requirements-dev.txt` instead.

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
