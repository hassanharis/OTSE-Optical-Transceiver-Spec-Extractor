"""Streamlit UI for the transceiver datasheet extraction pipeline.

Uses the local llama-server router (same as C:\\Haris\\Chatbot).
"""

import json
import os
import tempfile
from pathlib import Path

import requests
import streamlit as st
from openai import OpenAI

from pipeline.pdf_parser import parse_pdf
from pipeline.atom_extractor import extract_atoms, BASE_URL
from pipeline.mode_linker import synthesize_modes, store_modes, separate_atoms
from pipeline.runtime_store import store_run, list_runs, load_run
from generate_report import generate_html
from generate_modes_report import generate_modes_html

MODEL_DIR = r"C:\Haris\models"
REPORTS_DIR = Path("reports")

st.set_page_config(page_title="Transceiver Spec Extractor", layout="wide")
st.title("Transceiver Datasheet Extractor")


# --------------------------------------------------------------------------- #
# Server / model helpers (from Chatbot/llm.py pattern)
# --------------------------------------------------------------------------- #

def _server_up() -> bool:
    try:
        return requests.get(f"{BASE_URL}/health", timeout=5).ok
    except requests.RequestException:
        return False


def _list_models() -> list[str]:
    resp = requests.get(f"{BASE_URL}/v1/models", timeout=15)
    resp.raise_for_status()
    return [m["id"] for m in resp.json().get("data", [])]


def _disk_sizes() -> dict[str, float]:
    sizes: dict[str, float] = {}
    if not os.path.isdir(MODEL_DIR):
        return sizes
    for entry in os.scandir(MODEL_DIR):
        if entry.is_file() and entry.name.lower().endswith(".gguf"):
            sizes[os.path.splitext(entry.name)[0]] = entry.stat().st_size / 1024**3
    return sizes


# --------------------------------------------------------------------------- #
# Sidebar: server status + model picker
# --------------------------------------------------------------------------- #

with st.sidebar:
    st.header("LLM Server")

    if not _server_up():
        st.error(
            "llama-server router is not reachable on port 8080.\n\n"
            "Start it with:\n```\nllama-server --models-dir C:\\Haris\\models --models-max 1\n```"
        )
        st.stop()

    st.success("Server online")

    models = _list_models()
    if not models:
        st.error(f"No models found. Place GGUF files in {MODEL_DIR}")
        st.stop()

    sizes = _disk_sizes()
    labels = [f"{m}  ({sizes[m]:.1f} GB)" if m in sizes else m for m in models]
    choice = st.selectbox("Model", labels)
    model_id = models[labels.index(choice)]

    st.divider()
    st.header("Settings")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.05)
    max_tokens = st.slider("Max tokens", 2048, 32768, 16384, 1024)
    st.caption("Thinking models need high token budgets")

# --------------------------------------------------------------------------- #
# Main area
# --------------------------------------------------------------------------- #

tab_extract, tab_history = st.tabs(["Extract", "History"])

with tab_extract:
    uploaded = st.file_uploader("Upload a PDF datasheet", type=["pdf"])

    # --- Step 1: Parse PDF ---
    if uploaded:
        file_key = uploaded.name + str(uploaded.size)
        if st.session_state.get("_parse_key") != file_key:
            st.session_state.pop("parsed", None)
            st.session_state.pop("edited_md", None)
            st.session_state.pop("extraction_result", None)

        if st.button("Parse PDF", type="secondary"):
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(uploaded.read())
                tmp_path = Path(tmp.name)
            with st.spinner("Parsing..."):
                parsed = parse_pdf(tmp_path)
            st.session_state["parsed"] = parsed
            st.session_state["edited_md"] = parsed.markdown
            st.session_state["_parse_key"] = file_key
            st.session_state.pop("extraction_result", None)

    # --- Step 2: Review / edit parsed markdown ---
    if "parsed" in st.session_state:
        parsed = st.session_state["parsed"]
        st.subheader("Step 1 — Parsed Content")
        st.caption(f"{parsed.page_count} pages | {len(parsed.tables)} tables | {len(parsed.markdown):,} chars")

        edited_md = st.text_area(
            "Edit the markdown before extraction",
            value=st.session_state.get("edited_md", parsed.markdown),
            height=400,
            key="md_editor",
        )
        st.session_state["edited_md"] = edited_md

        # --- Step 3: Extract ---
        if st.button("Extract Parameters", type="primary"):
            # Patch the parsed object with edited markdown
            parsed.markdown = st.session_state["edited_md"]

            with st.status("Extracting...", expanded=True) as status:
                st.write(f"Sending to `{model_id}` ({len(parsed.markdown):,} chars)...")
                specs, raw_dict = extract_atoms(
                    parsed,
                    model_id=model_id,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                st.write("Storing run...")
                run_dir = store_run(parsed, raw_dict, specs, model_id=model_id)
                st.session_state["_last_run_dir"] = str(run_dir)
                st.write(f"Saved to `{run_dir}`")

                if specs:
                    status.update(label="Extraction complete (validated)", state="complete")
                else:
                    status.update(label="Extraction complete (validation failed)", state="error")

            st.session_state["extraction_result"] = (specs, raw_dict)

    # --- Display results ---
    if "extraction_result" in st.session_state:
        specs, raw_dict = st.session_state["extraction_result"]
        st.subheader("Extracted Parameters")
        if specs:
            data = json.loads(specs.model_dump_json())
            col1, col2, col3 = st.columns(3)
            scalar_fields = {}
            list_fields = {}
            null_fields = []
            for k, v in data.items():
                if v is None:
                    null_fields.append(k)
                elif isinstance(v, list):
                    list_fields[k] = v
                else:
                    scalar_fields[k] = v

            with col1:
                st.markdown("**Scalar Values**")
                for k, v in scalar_fields.items():
                    st.write(f"- **{k}:** {v}")
            with col2:
                st.markdown("**List Values**")
                for k, v in list_fields.items():
                    st.write(f"- **{k}:** {v}")
            with col3:
                st.markdown("**Not Found (null)**")
                for k in null_fields:
                    st.write(f"- {k}")
        else:
            st.warning("Pydantic validation failed. Showing raw LLM output:")

        with st.expander("Raw LLM JSON"):
            st.json(raw_dict)

        # --- Step 4: Mode Synthesis ---
        if specs or raw_dict:
            source = json.loads(specs.model_dump_json()) if specs else raw_dict
            multi, general = separate_atoms(source)

            if multi:
                st.divider()
                st.subheader("Step 2 — Mode Synthesis")
                st.caption(f"{len(multi)} multi-valued fields to link into modes")
                with st.expander("Multi-valued atoms"):
                    st.json(multi)

                if st.button("Synthesize Modes", type="primary"):
                    with st.status("Linking atoms into modes...", expanded=True) as status:
                        modes_result, _, _ = synthesize_modes(
                            source,
                            st.session_state["parsed"],
                            model_id=model_id,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        )
                        if modes_result:
                            # Save to latest run dir
                            runs = list_runs()
                            if runs:
                                store_modes(runs[-1], modes_result, multi, general)
                            status.update(label=f"{len(modes_result.get('modes', []))} modes identified", state="complete")
                        else:
                            status.update(label="Mode synthesis failed", state="error")

                    st.session_state["modes_result"] = modes_result

            # --- Generate Report button (after mode synthesis or if skipped) ---
            if st.session_state.get("_last_run_dir"):
                run_dir = Path(st.session_state["_last_run_dir"])
                if st.button("Generate Report", type="secondary"):
                    REPORTS_DIR.mkdir(exist_ok=True)
                    pipeline_path = REPORTS_DIR / f"{run_dir.name}_pipeline.html"
                    html = generate_html(run_dir)
                    pipeline_path.write_text(html, encoding="utf-8")
                    modes_path = REPORTS_DIR / f"{run_dir.name}_modes.html"
                    modes_html = generate_modes_html(run_dir)
                    modes_path.write_text(modes_html, encoding="utf-8")
                    st.success(f"Reports saved: `{pipeline_path}` and `{modes_path}`")

            if "modes_result" in st.session_state and st.session_state["modes_result"]:
                modes_result = st.session_state["modes_result"]
                st.subheader("Configuration Modes")
                for i, mode in enumerate(modes_result.get("modes", [])):
                    label = mode.get("label", f"Mode {i+1}")
                    with st.expander(f"**{label}**", expanded=i == 0):
                        st.json(mode)

with tab_history:
    runs = list_runs()
    if not runs:
        st.info("No runs yet.")
    else:
        selected = st.selectbox("Select a run", [r.name for r in reversed(runs)])
        if selected:
            run_data = load_run(Path("runs") / selected)
            if "meta" in run_data:
                st.json(run_data["meta"])
            if "specs" in run_data:
                st.subheader("Validated Specs")
                st.json(run_data["specs"])
            elif "raw_llm" in run_data:
                st.subheader("Raw LLM Output (no validated specs)")
                st.json(run_data["raw_llm"])

            if st.button("Generate Report", key="hist_report"):
                REPORTS_DIR.mkdir(exist_ok=True)
                sel_run_dir = Path("runs") / selected
                pipeline_path = REPORTS_DIR / f"{selected}_pipeline.html"
                html = generate_html(sel_run_dir)
                pipeline_path.write_text(html, encoding="utf-8")
                modes_path = REPORTS_DIR / f"{selected}_modes.html"
                modes_html = generate_modes_html(sel_run_dir)
                modes_path.write_text(modes_html, encoding="utf-8")
                st.success(f"Reports saved: `{pipeline_path}` and `{modes_path}`")
