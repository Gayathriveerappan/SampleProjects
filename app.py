from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from io import BytesIO
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

import db
from llm import COHERE_DEFAULT_MODEL, OPENROUTER_DEFAULT_MODEL, evaluate
from scoring import calculate_and_rank, normalize_scorecard

ROOT = Path(__file__).parent
SAMPLES = [
    ("BharatMold Components", "bharatmold_components.pdf", "2026-10-12", 8.0),
    ("Deccan Polymer Works", "deccan_polymer_works.pdf", "2026-10-10", 4.5),
    ("Narmada Auto Plastics", "narmada_auto_plastics.pdf", "2026-10-11", 7.5),
    ("Kaveri Trim Systems", "kaveri_trim_systems.pdf", "2026-10-09", 9.0),
    ("Eastern Mobility Components", "eastern_mobility_components.pdf", "2026-10-13", 6.5),
]

st.set_page_config(page_title="Sourcing Studio | RFP Intelligence", page_icon="✦", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink:#f3f4f7; --muted:#a7afc0; --line:rgba(255,255,255,.11); --violet:#a78bfa; --mint:#71e0c2; }
html, body, [class*="css"] { font-family:Manrope, sans-serif; }
.stApp { background: radial-gradient(ellipse at 78% -10%, rgba(127,83,255,.20), transparent 34%), #0b0d13; color:var(--ink); }
[data-testid="stSidebar"] { background:#10121a; border-right:1px solid var(--line); }
[data-testid="stMetric"] { background:rgba(255,255,255,.035); border:1px solid var(--line); padding:16px 18px; border-radius:14px; }
[data-testid="stMetricValue"] { color:#fff; }
.hero { padding:28px 30px; border:1px solid var(--line); border-radius:22px; background:linear-gradient(120deg,rgba(124,91,240,.20),rgba(74,208,182,.07) 65%,rgba(255,255,255,.025)); margin:4px 0 22px; }
.eyebrow { text-transform:uppercase; letter-spacing:.16em; color:var(--mint); font:500 11px 'DM Mono',monospace; }
.hero h1 { font-size:34px; letter-spacing:-.045em; margin:8px 0 7px; }
.hero p { color:#b9c0d0; margin:0; font-size:14px; }
.pill { display:inline-block; padding:5px 9px; border-radius:30px; color:#cbbdff; background:rgba(167,139,250,.13); border:1px solid rgba(167,139,250,.24); font:11px 'DM Mono',monospace; }
.section-label { color:#e9eaf1; font-size:17px; font-weight:700; margin:10px 0 12px; }
div.stButton > button[kind="primary"] { background:linear-gradient(95deg,#8a63f6,#5dcfb1); color:#11131a; border:0; font-weight:800; border-radius:10px; }
div.stButton > button { border-radius:10px; }
.note { border-left:2px solid var(--mint); background:rgba(113,224,194,.06); padding:10px 13px; color:#bbc7ce; font-size:12px; border-radius:0 9px 9px 0; }
code, .mono { font-family:'DM Mono',monospace; }
</style>
""", unsafe_allow_html=True)

db.initialize()
if "latest_result" not in st.session_state:
    st.session_state.latest_result = None

with st.sidebar:
    st.markdown("<div class='eyebrow'>PROCUREMENT INTELLIGENCE</div>", unsafe_allow_html=True)
    st.markdown("## ✦ Sourcing Studio")
    st.caption("Evidence-led · explainable · repeatable")
    st.divider()
    st.markdown("### Workspace")
    page = st.radio("Navigate", ["New evaluation", "Run history", "How it works"], label_visibility="collapsed")
    st.divider()
    active = db.get_criteria(active_only=True)
    active_weight = sum(float(c["weight"]) for c in active)
    st.metric("Active criteria", len(active))
    st.metric("Weight allocation", f"{active_weight:g}%")
    st.caption("Weights need to total 100% before a run.")

st.markdown("""
<div class="hero"><div class="eyebrow">AGENTIC RFP EVALUATION · WORKSPACE 01</div>
<h1>Source smarter.<br>Show your working.</h1>
<p>Compare Indian automotive suppliers for a simple molded floor-mat set.</p></div>
""", unsafe_allow_html=True)


def pdf_text(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    if len(reader.pages) == 0:
        raise ValueError("This PDF has no readable pages.")
    text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    if len(text) < 60:
        raise ValueError("This PDF contains too little extractable text. Scanned PDFs need OCR first.")
    return text


def analyze_batch(entries: list[dict], provider: str, key: str, model: str, criteria: list[dict]) -> None:
    run_id = f"RFP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    warnings: list[str] = []
    suppliers = []
    progress = st.progress(0, text="Preparing evaluation…")
    try:
        for index, entry in enumerate(entries):
            with st.status(f"Reviewing {entry['supplier_name']}…", expanded=False) as status:
                extracted = pdf_text(entry["bytes"])
                raw = evaluate(provider, key, model, entry["supplier_name"], extracted, criteria)
                scorecard, row_warnings = normalize_scorecard(raw, criteria, entry["supplier_name"])
                warnings.extend(row_warnings)
                suppliers.append({"supplier_name": entry["supplier_name"],
                                  "submission_date": entry["submission_date"],
                                  "experience_rating": float(entry["experience_rating"]),
                                  "source_file": entry["file_name"], "scorecard": scorecard})
                status.update(label=f"Scored {entry['supplier_name']}", state="complete")
            progress.progress((index + 1) / len(entries), text=f"Evaluated {index + 1} of {len(entries)} proposals")
        ranked = calculate_and_rank(suppliers, criteria)
        payload = {"rfp_run_id": run_id, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "status": "completed", "provider": provider, "model": model,
                   "criteria": criteria, "suppliers": ranked, "warnings": warnings,
                   "business_rules": {"absolute_score": "sum((score / max_score) * weight)",
                                      "criterion_benchmark": "highest valid score for that criterion in this run",
                                      "relative_performance_pct": "score / benchmark * 100; 0 when benchmark is 0",
                                      "ppi": "weighted average of criterion relative-performance percentages",
                                      "tie_break_order": ["PPI descending", "submission date ascending",
                                                          "experience rating descending", "supplier name ascending"]}}
        db.save_run(run_id, provider, model, criteria, ranked, payload)
        st.session_state.latest_result = payload
        st.success(f"Evaluation complete · {run_id}")
    except Exception:
        st.error("The run stopped before saving. Check the provider, credentials, PDFs, and model name, then try again.")
    finally:
        progress.empty()


def show_results(payload: dict) -> None:
    suppliers = payload["suppliers"]
    top = suppliers[0]
    st.markdown(f"<div class='section-label'>Run result <span class='pill'>{payload['rfp_run_id']}</span></div>", unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    a.metric("Rank 01", top["supplier_name"])
    b.metric("Absolute score", f"{top['absolute_score']:.2f} / 100")
    c.metric("Peer Performance Index", f"{top['ppi']:.1f}%")
    d.metric("Suppliers compared", len(suppliers))
    st.markdown("### Supplier leaderboard")
    st.dataframe([{"Rank": s["final_rank"], "Supplier": s["supplier_name"], "Absolute score": s["absolute_score"],
                   "PPI": f"{s['ppi']:.2f}%", "Submission date": s["submission_date"],
                   "Experience / 10": s["experience_rating"]} for s in suppliers],
                 use_container_width=True, hide_index=True)
    chosen = st.selectbox("Explore a supplier scorecard", [s["supplier_name"] for s in suppliers], key="scorecard_select")
    selected = next(s for s in suppliers if s["supplier_name"] == chosen)
    st.markdown(f"#### #{selected['final_rank']} · {selected['supplier_name']} — {selected['absolute_score']:.2f} points")
    st.caption(selected["scorecard"].get("overall_summary", "No summary returned."))
    st.dataframe([{"Criterion": r["name"], "Score": f"{r['score']:g} / {r['max_score']:g}",
                   "Weight": f"{r['weight']:g}%", "Benchmark": r["benchmark"], "Gap": r["gap"],
                   "Relative": f"{r['relative_performance_pct']:.1f}%", "Evidence": r["evidence"],
                   "Justification": r["justification"]} for r in selected["scorecard"]["criteria"]],
                 use_container_width=True, hide_index=True, height=280)
    with st.expander("Risks, validation warnings & ranking rule"):
        st.markdown("**Risks noted by evaluator**")
        st.write(selected["scorecard"].get("risks", []) or ["None reported."])
        st.markdown("**Validation warnings**")
        st.write(payload.get("warnings", []) or ["No normalization warnings."])
        st.caption(selected["tie_break_explanation"])
        st.caption(f"Provider: {payload['provider']} · Model: {payload['model']}")
    st.download_button("↓ Download complete result as JSON", json.dumps(payload, indent=2, ensure_ascii=False),
                       file_name=f"{payload['rfp_run_id'].lower()}.json", mime="application/json", type="primary")


if page == "New evaluation":
    st.markdown("<div class='section-label'>01 / Evaluation criteria</div>", unsafe_allow_html=True)
    all_criteria = db.get_criteria()
    edited = st.data_editor(all_criteria, use_container_width=True, hide_index=True, num_rows="fixed",
                            column_config={"criterion_id": st.column_config.NumberColumn(disabled=True),
                                           "name": st.column_config.TextColumn("Criterion", required=True),
                                           "description": st.column_config.TextColumn("What to inspect", width="large"),
                                           "weight": st.column_config.NumberColumn("Weight %", min_value=0.0, max_value=100.0, step=1.0),
                                           "max_score": st.column_config.NumberColumn("Max score", min_value=1.0, max_value=100.0, step=1.0),
                                           "is_active": st.column_config.CheckboxColumn("Active")}, key="criteria_editor")
    active_weight = sum(float(row["weight"]) for row in edited if row["is_active"])
    ca, cb = st.columns([1, 3])
    if ca.button("Save criteria", key="save_criteria"):
        try:
            db.save_criteria(edited)
            st.success("Criteria saved to SQLite.")
            st.rerun()
        except Exception:
            st.error("Could not save criteria. Check that criterion names are unique.")
    cb.caption(f"Active weight total: **{active_weight:g}%** · active criteria are reloaded for each run")

    st.markdown("<div class='section-label'>02 / Proposal intake</div>", unsafe_allow_html=True)
    demo_mode = st.toggle("Use the five bundled fictional proposals", value=False)
    if not demo_mode:
        files = st.file_uploader("Drop supplier proposals here", type=["pdf"], accept_multiple_files=True,
                                 help="Upload two or more text-readable PDF responses.")
        if files:
            st.caption(f"{len(files)} proposal file(s) selected. Enter one supplier record for each.")
    else:
        files = []
    st.info("Five fictional India-based automotive component manufacturers will be used for the floor-mat sourcing exercise.")

    if not demo_mode and files:
        metadata = []
        with st.form("supplier_metadata"):
            for i, file in enumerate(files):
                with st.expander(f"Supplier {i + 1} · {file.name}", expanded=i == 0):
                    x, y, z = st.columns(3)
                    supplier_name = x.text_input("Supplier name", value=Path(file.name).stem.replace("_", " ").title(), key=f"name_{i}")
                    submitted = y.date_input("Submission date", value=date.today(), key=f"date_{i}")
                    rating = z.number_input("Historical experience / 10", min_value=0.0, max_value=10.0, value=5.0, step=0.5, key=f"rating_{i}")
                    metadata.append({"file": file, "supplier_name": supplier_name.strip(),
                                     "submission_date": submitted.isoformat(), "experience_rating": rating})
            metadata_ready = st.form_submit_button("Save supplier details", type="primary")
        if metadata_ready:
            st.session_state.metadata_ready = True
            st.session_state.supplier_metadata = [{**m, "bytes": m["file"].getvalue(), "file_name": m["file"].name}
                                                  for m in metadata]
            st.success("Supplier records ready. Set the provider below to start the run.")

    st.markdown("<div class='section-label'>03 / Bring your model</div>", unsafe_allow_html=True)
    st.markdown("<div class='note'>Your key is requested here at run time. It is used for this page session only and is never written to SQLite, a config file, or an export.</div>", unsafe_allow_html=True)
    provider = st.selectbox("AI provider", ["OpenRouter", "Cohere"])
    default_model = OPENROUTER_DEFAULT_MODEL if provider == "OpenRouter" else COHERE_DEFAULT_MODEL
    model = st.text_input("Model", value=default_model, help="You can replace the default with a model available to your account.")
    api_key = st.text_input(f"{provider} API key", type="password", placeholder="Paste key for this run", key="runtime_api_key")
    st.caption("OpenRouter sends requests to its Chat Completions endpoint. Cohere uses its v2 Chat endpoint.")
    can_run = active_weight == 100 and len([c for c in edited if c["is_active"]]) > 0
    if not can_run:
        st.warning(f"Active criteria must total exactly 100% (currently {active_weight:g}%).")
    run = st.button("✦  Evaluate proposals", type="primary", disabled=not can_run or not api_key or not model.strip(), use_container_width=True)
    if run:
        criteria = [c for c in db.get_criteria(active_only=True)]
        entries = []
        if demo_mode:
            for name, filename, submitted, rating in SAMPLES:
                entries.append({"supplier_name": name, "submission_date": submitted, "experience_rating": rating,
                                "file_name": filename, "bytes": (ROOT / "sample_proposals" / filename).read_bytes()})
        elif st.session_state.get("metadata_ready"):
            entries = st.session_state.get("supplier_metadata", [])
            selected_names = sorted(file.name for file in (files or []))
            saved_names = sorted(entry["file_name"] for entry in entries)
            if selected_names != saved_names:
                entries = []
                st.error("The selected PDFs changed after supplier details were saved. Save the details again before evaluating.")
        if len(entries) < 2:
            st.error("Choose the bundled sample batch or upload and save at least two supplier records before evaluating.")
        elif len({e["supplier_name"].casefold() for e in entries}) != len(entries):
            st.error("Supplier names must be unique within a batch.")
        elif not all(e["supplier_name"] and len(e["bytes"]) > 0 for e in entries):
            st.error("Each supplier needs a name and a readable PDF.")
        else:
            analyze_batch(entries, provider, api_key, model.strip(), criteria)

    if st.session_state.latest_result:
        st.divider()
        show_results(st.session_state.latest_result)

elif page == "Run history":
    st.markdown("<div class='section-label'>Saved evaluation runs</div>", unsafe_allow_html=True)
    runs = db.list_runs()
    if not runs:
        st.info("Completed runs will appear here.")
    else:
        selected_id = st.selectbox("Select an RFP run", [r["rfp_run_id"] for r in runs])
        payload = db.load_run(selected_id)
        if payload:
            payload["warnings"] = []
            show_results(payload)

elif page == "How it works":
    st.markdown("<div class='section-label'>A controlled evaluation pipeline</div>", unsafe_allow_html=True)
    st.markdown("""
    1. **Criteria** — active criteria and weights come from SQLite; edit and save them in the evaluation workspace.
    2. **Intake** — upload multiple proposal PDFs with a name, submission date, and experience rating.
    3. **Extract** — `pypdf` extracts text; scan-only documents are flagged for OCR.
    4. **Evaluate** — OpenRouter or Cohere receives the active rubric and one proposal at a time. Prompt instructs the model to use document evidence only and return JSON.
    5. **Validate** — malformed/missing rows default to zero; out-of-range scores are clipped; warnings are retained in the downloadable run.
    6. **Calculate** — Python computes weighted absolute scores, criterion benchmarks, gaps, relative performance, and PPI.
    7. **Rank** — deterministic sort: PPI descending → earlier submission → higher experience → supplier name ascending.
    8. **Persist** — the completed batch and full scorecards are stored under one run ID in SQLite.
    9. **Explain** — inspect evidence, justifications, risks, and download the entire result as JSON.

    **Credential handling:** the key is a password field, passed directly to the provider adapter, and not included in run records. Avoid shared/public devices and clear the page session when finished.
    """)

