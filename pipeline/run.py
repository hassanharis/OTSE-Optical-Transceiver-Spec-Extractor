"""Entry point: parse PDF → extract atomic params → store run."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from pipeline.pdf_parser import parse_pdf
from pipeline.atom_extractor import extract_atoms
from pipeline.runtime_store import store_run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run(
    pdf_path: str | Path,
    *,
    model_id: str | None = None,
    runs_dir: Path | None = None,
) -> Path:
    """Execute the full pipeline and return the run directory."""
    logger.info("=== Step 1: Parsing PDF ===")
    parsed = parse_pdf(pdf_path)

    logger.info("=== Step 2: Extracting atomic parameters ===")
    specs, raw_dict = extract_atoms(parsed, model_id=model_id)

    logger.info("=== Step 3: Storing run ===")
    run_dir = store_run(parsed, raw_dict, specs, model_id=model_id, runs_dir=runs_dir)

    status = "VALID" if specs else "PARTIAL (validation failed)"
    logger.info("=== Done [%s] — results in %s ===", status, run_dir)
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract transceiver specs from a PDF datasheet.")
    parser.add_argument("pdf", help="Path to the PDF datasheet")
    parser.add_argument("--model", default=None, help="Model ID on the llama-server router")
    parser.add_argument("--runs-dir", default=None, help="Directory to store runs")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir) if args.runs_dir else None
    run_dir = run(args.pdf, model_id=args.model, runs_dir=runs_dir)
    print(f"Run saved: {run_dir}")


if __name__ == "__main__":
    main()
