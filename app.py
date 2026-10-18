from __future__ import annotations

import json
from html import escape
import hashlib
import uuid
from datetime import date, datetime, timezone
from io import BytesIO
from pathlib import Path

import streamlit as st
import pandas as pd
import requests
from pypdf import PdfReader

import db
from llm import evaluate, generate_criteria
from scoring import calculate_and_rank, normalize_scorecard

ROOT = Path(__file__).parent
SAMPLES = [
    ("BharatMold Components", "bharatmold_components.pdf", "2026-10-12", 8.0),
    ("Deccan Polymer Works", "deccan_polymer_works.pdf", "2026-10-10", 4.5),
    ("Narmada Auto Plastics", "narmada_auto_plastics.pdf", "2026-10-11", 7.5),
    ("Kaveri Trim Systems", "kaveri_trim_systems.pdf", "2026-10-09", 9.0),
    ("Eastern Mobility Components", "eastern_mobility_components.pdf", "2026-10-13", 6.5),
]

st.set_page_config(page_title="ProcureLens | Supplier Evaluation", page_icon="✦", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink:#f3f4f7; --muted:#a7afc0; --line:rgba(255,255,255,.11); --violet:#a78bfa; --mint:#71e0c2; }
html, body, [class*="css"] { font-family:Manrope, sans-serif; }
.stApp, [data-testid="stAppViewContainer"] { color:#f4f6fb; }
[data-testid="stWidgetLabel"] p, label { color:#ffffff!important; font-weight:750!important; font-size:.94rem!important; letter-spacing:.01em; }
.stCaption, [data-testid="stMarkdownContainer"] p { color:#c5cedd; }
[data-testid="stWidgetLabel"] { margin-bottom:.35rem; }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stTextArea"] textarea { background:#131824; color:#f7f9fc; }
[data-testid="stSelectbox"] [data-baseweb="select"] > div { background:#131824; color:#f7f9fc; }
h1,h2,h3 { color:#fff!important; letter-spacing:-.025em; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color:#eff2f8; font-weight:650; }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-baseweb="select"] > div { border-color:rgba(191,205,229,.30); }
.stApp { background:radial-gradient(ellipse at 78% -10%,rgba(127,83,255,.22),transparent 34%),radial-gradient(ellipse at 5% 38%,rgba(37,184,159,.075),transparent 28%),#0b0d13; color:var(--ink); }
[data-testid="stAppViewContainer"] { background-image:linear-gradient(rgba(255,255,255,.012) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.012) 1px,transparent 1px); background-size:38px 38px; }
[data-testid="stSidebar"] { background:#10121a; border-right:1px solid var(--line); }
[data-testid="stMetric"] { background:rgba(255,255,255,.035); border:1px solid var(--line); padding:16px 18px; border-radius:14px; }
[data-testid="stMetricValue"] { color:#fff; }
.hero { position:relative; overflow:hidden; padding:30px 34px; border:1px solid rgba(197,183,255,.2); border-radius:24px; background:linear-gradient(112deg,rgba(124,91,240,.23),rgba(74,208,182,.09) 62%,rgba(255,255,255,.025)); margin:4px 0 16px; box-shadow:0 18px 55px rgba(0,0,0,.18); }
.hero:after { content:'✦'; position:absolute; right:8%; top:-40px; font-size:210px; color:rgba(197,183,255,.055); line-height:1; transform:rotate(12deg); }
.eyebrow { text-transform:uppercase; letter-spacing:.16em; color:var(--mint); font:500 10px 'DM Mono',monospace; }
.hero h1 { font-size:36px; letter-spacing:-.05em; margin:9px 0 8px; line-height:1.08; }
.hero p { color:#b9c0d0; margin:0; font-size:14px; max-width:640px; }
.pill { display:inline-block; padding:5px 9px; border-radius:30px; color:#cbbdff; background:rgba(167,139,250,.13); border:1px solid rgba(167,139,250,.24); font:11px 'DM Mono',monospace; }
.section-label { color:#fff; font-size:19px; font-weight:850; margin:16px 0 15px; padding:11px 14px; border-left:4px solid var(--mint); border-radius:0 10px 10px 0; background:linear-gradient(90deg,rgba(113,224,194,.14),rgba(167,139,250,.045) 55%,transparent 90%); box-shadow:inset 0 -1px rgba(255,255,255,.08); }
div.stButton > button[kind="primary"] { background:linear-gradient(95deg,#8a63f6,#5dcfb1); color:#11131a; border:0; font-weight:800; border-radius:10px; }
div.stButton > button { border-radius:10px; transition:transform .18s ease,box-shadow .18s ease; }
div.stButton > button:hover { transform:translateY(-1px); box-shadow:0 8px 22px rgba(117,91,222,.18); border-color:rgba(167,139,250,.55); }
.note { border-left:2px solid var(--mint); background:rgba(113,224,194,.06); padding:10px 13px; color:#bbc7ce; font-size:12px; border-radius:0 9px 9px 0; }
.status-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin:0 0 20px; }
.status-tile { min-height:75px; padding:13px 15px; border:1px solid rgba(159,181,216,.22); border-top:2px solid var(--mint); border-radius:13px; background:linear-gradient(145deg,rgba(29,38,56,.96),rgba(17,22,34,.96)); box-shadow:0 8px 24px rgba(0,0,0,.16); }
.status-tile span { display:block; margin-bottom:7px; color:#9eacc1; font:10px 'DM Mono',monospace; letter-spacing:.12em; }
.status-tile strong { color:#f3f7ff; font-size:12px; font-weight:750; }
.stepper { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; margin:0 0 22px; }
.step { padding:10px 12px; border-radius:12px; background:rgba(255,255,255,.025); border:1px solid var(--line); color:#939bad; font-size:11px; }
.step span { color:var(--mint); font:11px 'DM Mono',monospace; margin-right:7px; }
.step.active { border-color:rgba(167,139,250,.4); background:rgba(167,139,250,.09); color:#f1edff; }
.step.complete { border-color:rgba(113,224,194,.32); color:#d8fff3; }
.winner-card { padding:18px 20px; border-radius:16px; border:1px solid rgba(113,224,194,.22); background:linear-gradient(110deg,rgba(113,224,194,.09),rgba(167,139,250,.08)); margin:8px 0 16px; }
.winner-card .winner-label { color:var(--mint); font:10px 'DM Mono',monospace; letter-spacing:.12em; text-transform:uppercase; }
.winner-card strong { display:block; font-size:20px; margin:5px 0 2px; color:#fff; }
.leader-item { display:grid; grid-template-columns:minmax(135px,1fr) 3fr 56px; gap:12px; align-items:center; margin:9px 0; font-size:12px; color:#d4d8e2; }
.leader-track { height:8px; border-radius:8px; background:rgba(255,255,255,.08); overflow:hidden; }
.leader-fill { height:100%; border-radius:8px; background:linear-gradient(90deg,#8a63f6,#5dcfb1); }
.leader-score { text-align:right; font:11px 'DM Mono',monospace; color:#c7cce0; }
.soft-card { border:1px solid var(--line); background:rgba(255,255,255,.025); padding:14px 16px; border-radius:15px; }
.soft-card h4 { margin:0 0 6px; font-size:13px; }
.soft-card p { margin:0; font-size:11px; line-height:1.55; color:#aeb6c6; }
.info-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin:10px 0 20px; }
.info-card { min-height:112px; border:1px solid var(--line); background:linear-gradient(145deg,rgba(255,255,255,.04),rgba(255,255,255,.015)); padding:15px; border-radius:15px; }
.info-card .icon { font-size:18px; color:var(--mint); }
.info-card strong { display:block; font-size:12px; margin:7px 0 4px; color:#f0f1f6; }
.info-card span { display:block; color:#aeb6c6; font-size:10.5px; line-height:1.5; }
.stTabs [data-baseweb="tab-list"] { gap:8px; }
.stTabs [data-baseweb="tab"] { background:rgba(255,255,255,.025); border-radius:9px 9px 0 0; }
.stProgress > div > div > div > div { background:linear-gradient(90deg,#8a63f6,#5dcfb1); }
code, .mono { font-family:'DM Mono',monospace; }
@media (max-width:900px) { .status-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media (max-width:700px) { .hero h1 { font-size:29px; } .stepper { grid-template-columns:repeat(2,minmax(0,1fr)); } .leader-item { grid-template-columns:minmax(90px,1fr) 2fr 45px; gap:7px; } .status-grid { gap:7px; } .status-tile { padding:10px; } }
</style>
""", unsafe_allow_html=True)

db.initialize()
if "latest_result" not in st.session_state:
    st.session_state.latest_result = None
if "wizard_step" not in st.session_state:
    st.session_state.wizard_step = 1
if "sidebar_provider" not in st.session_state:
    st.session_state.sidebar_provider = "OpenRouter"
MODEL_OPTIONS = {
    "OpenRouter": [("OpenAI · GPT-5 Mini", "openai/gpt-5-mini"),
                   ("OpenAI · GPT-4o mini", "openai/gpt-4o-mini"),
                   ("Google · Gemini 3.8 Flash", "google/gemini-3.8-flash")],
    "Cohere": [("Command A+", "command-a-plus-05-2026"),
               ("Command A", "command-a-03-2025")],
}
if "sidebar_model_choice" not in st.session_state:
    initial_provider = st.session_state.get("sidebar_provider", "OpenRouter")
    st.session_state.sidebar_model_choice = MODEL_OPTIONS[initial_provider][0][1]
if "sidebar_model_custom" not in st.session_state:
    st.session_state.sidebar_model_custom = ""

def sync_default_model() -> None:
    selected_provider = st.session_state.get("sidebar_provider", "OpenRouter")
    st.session_state.sidebar_model_choice = MODEL_OPTIONS[selected_provider][0][1]
    st.session_state.sidebar_model_custom = ""

with st.sidebar:
    st.markdown("<div class='eyebrow'>✦ PROCUREMENT INTELLIGENCE</div>", unsafe_allow_html=True)
    st.markdown("## ProcureLens")
    st.caption("Supplier evaluation workspace")
    st.divider()
    st.markdown("### Your workspace")
    page = st.radio("Navigate", ["New evaluation", "Run history", "How it works"], label_visibility="collapsed",
                    help="Move between a new evaluation, saved analyses, and the scoring method.")
    st.divider()
    st.markdown("### AI evaluator")
    provider = st.selectbox("Provider", ["OpenRouter", "Cohere"], key="sidebar_provider",
                            on_change=sync_default_model,
                            help="Choose the model provider used to draft custom criteria and evaluate proposals.")
    model_options = MODEL_OPTIONS[provider]
    model_ids = [model_id for _, model_id in model_options]
    model_choice = st.selectbox("Model ID", [*model_ids, "__custom__"],
                                format_func=lambda model_id: (next((f"{label} — {value}" for label, value in model_options
                                                                   if value == model_id), "Custom model ID…")
                                                              if model_id != "__custom__" else "Custom model ID…"),
                                key="sidebar_model_choice",
                                help="Choose a suggested model for this provider, or select Custom to enter another supported model ID.")
    if model_choice == "__custom__":
        model = st.text_input("Custom model ID", key="sidebar_model_custom", placeholder="provider/model-id",
                              help="Enter the exact model ID from your provider's catalog.")
    else:
        model = model_choice
        st.caption(f"Selected ID: `{model}`")
    st.session_state.active_model = model
    api_key = st.text_input(f"{provider} API key", type="password", key=f"sidebar_api_key_{provider.lower()}",
                            placeholder="Enter for this session",
                            help="Used for provider requests during this browser session only. It is excluded from SQLite and exports.")
    st.session_state.active_api_key = api_key
    st.caption("Credentials are session-only and are not persisted.")
    st.divider()
    active = db.get_criteria(active_only=True)
    active_weight = sum(float(c["weight"]) for c in active)
    st.metric("Active criteria", len(active), help="Number of rubric criteria included in a new evaluation.")
    st.metric("Weight allocation", f"{active_weight:g}%", help="Active rubric weights should total 100% before comparison.")
    if active_weight == 100:
        st.caption("● Rubric ready · weights are balanced")
    else:
        st.caption("○ Balance active weights to 100% to run an evaluation.")

st.markdown("""
<div class="hero"><div class="eyebrow">PROCURELENS · PROCUREMENT ANALYST WORKSPACE</div>
<h1>Find the best fit.<br>Back it with evidence.</h1>
<p>Bring supplier proposals together, evaluate them against your rubric, and make the trade-offs easy to see.</p></div>
<div class="status-grid"><div class="status-tile"><span>WORKFLOW</span><strong>4 guided review stages</strong></div><div class="status-tile"><span>SCORING</span><strong>Weighted and evidence-led</strong></div><div class="status-tile"><span>HUMAN CONTROL</span><strong>Analyst approval required</strong></div><div class="status-tile"><span>DATA</span><strong>Approved runs in SQLite</strong></div></div>
""", unsafe_allow_html=True)

if page == "New evaluation":
    wizard_step = st.session_state.wizard_step
    wizard_labels = ["Setup", "RFQ & rubric", "Supplier proposals", "Review & compare"]
    step_html = "".join(
        f"<div class='step {'active' if index == wizard_step else 'complete' if index < wizard_step else ''}'><span>{index:02d}</span>{label}</div>"
        for index, label in enumerate(wizard_labels, 1)
    )
    st.markdown(f"<div class='stepper'>{step_html}</div>", unsafe_allow_html=True)


def pdf_text(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    if len(reader.pages) == 0:
        raise ValueError("This PDF has no readable pages.")
    text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    if len(text) < 60:
        raise ValueError("This PDF contains too little extractable text. Scanned PDFs need OCR first.")
    return text


def rfq_text(uploaded_file) -> str:
    data = uploaded_file.getvalue()
    if uploaded_file.name.lower().endswith(".pdf"):
        return pdf_text(data)
    text = data.decode("utf-8-sig", errors="replace").strip()
    if len(text) < 60:
        raise ValueError("The RFQ text file has too little readable content.")
    return text


def analysis_fingerprint(entries: list[dict], criteria: list[dict]) -> str:
    """Bind an AI draft to the exact proposal batch and reviewed rubric."""
    manifest = {
        "suppliers": [{"name": entry["supplier_name"], "file": entry["file_name"],
                       "sha256": hashlib.sha256(entry["bytes"]).hexdigest(),
                       "submission_date": entry["submission_date"],
                       "experience_rating": float(entry["experience_rating"])} for entry in entries],
        "criteria": [{"id": int(row["criterion_id"]), "name": row["name"],
                      "description": row["description"], "weight": float(row["weight"]),
                      "max_score": float(row["max_score"])} for row in criteria],
    }
    encoded = json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def supplier_upload_form(prefix: str, files):
    """Capture supplier metadata without mutating Streamlit widget-owned keys."""
    if not files:
        return []
    records_key = f"{prefix}_supplier_records"
    metadata_ready = False
    metadata = []
    with st.form(f"{prefix}_supplier_details_form"):
        for i, file in enumerate(files):
            with st.expander(f"Supplier {i + 1} · {file.name}", expanded=i == 0):
                x, y, z = st.columns(3)
                supplier_name = x.text_input("Supplier name", value=Path(file.name).stem.replace("_", " ").title(), key=f"{prefix}_name_{i}",
                                              help="Use the legal or bid-submission name shown in the proposal.")
                submitted = y.date_input("Submission date", value=date.today(), key=f"{prefix}_date_{i}",
                                         help="Record the date the buyer received this supplier response.")
                rating = z.number_input("Historical experience / 10", min_value=0.0, max_value=10.0, value=5.0, step=0.5,
                                        key=f"{prefix}_rating_{i}", help="Buyer-assessed prior performance rating; apply the same evidence standard to every bidder.")
                metadata.append({"file": file, "supplier_name": supplier_name.strip(),
                                 "submission_date": submitted.isoformat(), "experience_rating": rating})
        metadata_ready = st.form_submit_button("Save supplier details", type="primary")
    if metadata_ready:
        st.session_state[records_key] = [
            {**m, "bytes": m["file"].getvalue(), "file_name": m["file"].name} for m in metadata
        ]
        st.success("Supplier records saved for this analysis session.")
    records = st.session_state.get(records_key, [])
    selected_names = sorted(file.name for file in files)
    saved_names = sorted(entry["file_name"] for entry in records)
    if records and selected_names == saved_names:
        return records
    if records:
        st.warning("The proposal selection changed. Save supplier details again before running the comparison.")
    return []


def explain_run_failure(exc: Exception, api_key: str) -> tuple[str, str]:
    """Return safe, actionable diagnostics without exposing provider response bodies."""
    if isinstance(exc, requests.exceptions.HTTPError):
        status = exc.response.status_code if exc.response is not None else 0
        guidance = {
            400: "The provider rejected the request. Check whether this model supports chat JSON output, or select another model ID.",
            401: "The API key was rejected. Check that it belongs to the selected provider and has no extra spaces.",
            403: "The key lacks access to this model, or the provider account needs billing/permission enabled.",
            404: "The model ID or endpoint was not found. Choose a listed model or confirm the exact ID in the provider catalog.",
            408: "The provider timed out. Retry once, or choose a faster model.",
            429: "The provider rate limit or account quota was reached. Wait, check usage/billing, or retry later.",
        }.get(status, "Check provider availability and account access, then retry.")
        return f"{type(exc).__name__} (HTTP {status})", guidance
    if isinstance(exc, requests.exceptions.Timeout):
        return type(exc).__name__, "The provider request timed out. Retry, or choose a faster model."
    if isinstance(exc, requests.exceptions.ConnectionError):
        return type(exc).__name__, "Could not reach the provider. Check the host's network connection and retry."
    if isinstance(exc, (ValueError, json.JSONDecodeError)):
        detail = str(exc).replace(api_key, "[redacted]")[:350] if api_key else str(exc)[:350]
        return type(exc).__name__, detail or "The PDF or provider response could not be parsed."
    if isinstance(exc, KeyError):
        return type(exc).__name__, "The provider response did not include the expected chat fields. Try another model ID."
    detail = str(exc).replace(api_key, "[redacted]")[:350] if api_key else str(exc)[:350]
    return type(exc).__name__, detail or "Check the PDF, provider key, and model ID, then retry."


def analyze_batch(entries: list[dict], provider: str, key: str, model: str, criteria: list[dict],
                  analysis_context: dict | None = None) -> None:
    run_id = f"RFP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    warnings: list[str] = []
    suppliers = []
    current_supplier = "the batch"
    current_stage = "preparing the analysis"
    progress = st.progress(0, text="Preparing evaluation…")
    try:
        for index, entry in enumerate(entries):
            current_supplier = entry["supplier_name"]
            with st.status(f"Reviewing {entry['supplier_name']}…", expanded=False) as status:
                current_stage = "extracting proposal text"
                extracted = pdf_text(entry["bytes"])
                current_stage = f"calling {provider} with model {model}"
                raw = evaluate(provider, key, model, entry["supplier_name"], extracted, criteria)
                current_stage = "validating scores and proposal evidence"
                scorecard, row_warnings = normalize_scorecard(raw, criteria, entry["supplier_name"], extracted)
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
                   "input_fingerprint": analysis_fingerprint(entries, criteria),
                   "analysis_context": analysis_context or {"mode": "current_rubric"},
                   "business_rules": {"absolute_score": "sum((score / max_score) * weight)",
                                      "criterion_benchmark": "highest valid score for that criterion in this run",
                                      "relative_performance_pct": "score / benchmark * 100; 0 when benchmark is 0",
                                      "ppi": "weighted average of criterion relative-performance percentages",
                                      "tie_break_order": ["PPI descending", "submission date ascending",
                                                          "experience rating descending", "supplier name ascending"]}}
        payload["status"] = "pending_human_review"
        payload["human_review"] = {"status": "pending", "reviewer_feedback": "", "supplier_reviews": {}}
        st.session_state.latest_result = payload
        st.success(f"AI draft ready for analyst review · {run_id}")
    except Exception as exc:
        error_type, guidance = explain_run_failure(exc, key)
        st.error(f"The run stopped while {current_stage} for **{current_supplier}**. No result was saved.")
        st.warning(guidance)
        st.caption(f"Technical detail: {error_type}")
    finally:
        progress.empty()


def show_results(payload: dict) -> None:
    suppliers = payload["suppliers"]
    top = suppliers[0]
    st.markdown(f"<div class='section-label'>Run result <span class='pill'>{payload['rfp_run_id']}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='winner-card'><div class='winner-label'>✦ Current top-ranked supplier</div><strong>{escape(top['supplier_name'])}</strong><span>{top['absolute_score']:.2f} / 100 absolute score &nbsp; · &nbsp; {top['ppi']:.1f}% peer performance index</span></div>", unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    a.metric("Top rank", "#01")
    b.metric("Absolute score", f"{top['absolute_score']:.2f} / 100")
    c.metric("Peer Performance Index", f"{top['ppi']:.1f}%")
    d.metric("Suppliers compared", len(suppliers))
    st.markdown("### Supplier comparison")
    st.caption("Absolute scores use the weighted rubric; the PPI is relative to the strongest score in this run.")
    with st.expander("View evaluation criteria and weightage used"):
        st.dataframe([{"Criterion": c["name"], "Weight": f"{float(c['weight']):g}%",
                       "Evaluation focus": c["description"],
                       "Weight rationale": c.get("weight_rationale", "Current saved rubric")}
                      for c in payload.get("criteria", [])], use_container_width=True, hide_index=True)
    plot_overall, plot_criteria = st.tabs(["Supplier score comparison", "Criterion comparison"])
    with plot_overall:
        overall_plot = pd.DataFrame(
            {"Weighted score / 100": [float(s["absolute_score"]) for s in suppliers],
             "Peer Performance Index / 100": [float(s["ppi"]) for s in suppliers]},
            index=[s["supplier_name"] for s in suppliers],
        )
        st.bar_chart(overall_plot, height=300, use_container_width=True)
        st.caption("Compare absolute rubric scores with peer-relative performance. Suppliers are shown in final rank order.")
    with plot_criteria:
        criterion_rows = []
        for supplier in suppliers:
            row = {}
            for result in supplier["scorecard"]["criteria"]:
                label = f"{result['criterion_id']}. {result['name']}"
                row[label] = (float(result["score"]) / float(result["max_score"]) * 100.0
                              if float(result["max_score"]) else 0.0)
            criterion_rows.append(row)
        criteria_plot = pd.DataFrame(criterion_rows, index=[s["supplier_name"] for s in suppliers])
        st.bar_chart(criteria_plot, height=380, use_container_width=True)
        st.caption("Each criterion is shown as a percentage of its maximum score, so custom rubrics with different score scales remain comparable.")
    st.markdown("### Ranked shortlist")
    st.dataframe([{"Rank": s["final_rank"], "Supplier": s["supplier_name"], "Absolute score": s["absolute_score"],
                   "PPI": f"{s['ppi']:.2f}%", "Submission date": s["submission_date"],
                   "Experience / 10": s["experience_rating"]} for s in suppliers],
                 use_container_width=True, hide_index=True)
    chosen = st.selectbox("Explore a supplier scorecard", [s["supplier_name"] for s in suppliers], key="scorecard_select",
                          help="Select a bidder to inspect criterion scores, cited evidence, risks, and validation notes.")
    selected = next(s for s in suppliers if s["supplier_name"] == chosen)
    st.markdown(f"#### #{selected['final_rank']} · {selected['supplier_name']} — {selected['absolute_score']:.2f} points")
    tab_score, tab_risk, tab_method = st.tabs(["Scorecard & evidence", "Risks & checks", "Run details"])
    with tab_score:
        st.caption(selected["scorecard"].get("overall_summary", "No summary returned."))
        st.dataframe([{"Criterion": r["name"], "Score": f"{r['score']:g} / {r['max_score']:g}",
                       "Weight": f"{r['weight']:g}%", "Benchmark": r["benchmark"], "Gap": r["gap"],
                       "Relative": f"{r['relative_performance_pct']:.1f}%", "Evidence": r["evidence"],
                       "Justification": r["justification"]} for r in selected["scorecard"]["criteria"]],
                     use_container_width=True, hide_index=True, height=330)
    with tab_risk:
        st.markdown("**Risks noted by evaluator**")
        st.write(selected["scorecard"].get("risks", []) or ["None reported."])
        st.markdown("**Validation warnings**")
        st.write(payload.get("warnings", []) or ["No normalization warnings."])
        st.caption(selected["tie_break_explanation"])
    with tab_method:
        st.caption(f"Provider: {payload['provider']} · Model: {payload['model']}")
        st.caption(f"Run ID: {payload['rfp_run_id']} · Created: {payload['created_at']}")
        context = payload.get("analysis_context", {})
        st.caption(f"Analysis mode: {context.get('mode', 'current_rubric')} · Criteria source: {context.get('criteria_source', 'saved rubric')}")
        if context.get("rfq_document"):
            st.caption(f"RFQ source: {context['rfq_document']}")
        st.caption("Ranking is calculated deterministically in Python after model responses are normalized against the active rubric.")
    if payload.get("status") == "pending_human_review":
        st.divider()
        st.markdown("### Analyst validation & feedback")
        st.warning("This is an AI-generated decision-support draft. Verify each supplier’s scores and proposal evidence before approving it for evaluation history.")
        current_fingerprint = analysis_fingerprint(st.session_state.get("wizard_entries", []),
                                                   st.session_state.get("wizard_criteria", []))
        analysis_is_current = payload.get("input_fingerprint") == current_fingerprint
        if not analysis_is_current:
            st.error("The supplier batch or rubric has changed since this comparison. Rerun the analysis before approving this result.")
        st.markdown("#### Reprioritize and rerun first, if needed")
        st.caption("Change criterion importance before you validate and approve the final result. Edited weights must total 100%.")
        weight_base_criteria = (st.session_state.get("wizard_criteria") or payload["criteria"])
        weight_key = f"rerun_weights_{payload['rfp_run_id']}_{current_fingerprint[:8]}"
        weight_editor = st.data_editor(
            [{"Criterion": c["name"], "Proposed weight %": float(c["weight"])} for c in weight_base_criteria],
            use_container_width=True, hide_index=True, num_rows="fixed",
            column_config={"Criterion": st.column_config.TextColumn(disabled=True, help="Criteria are fixed for this rerun; change their relative priority using the weight field."),
                           "Proposed weight %": st.column_config.NumberColumn(min_value=0.0, max_value=100.0, step=1.0,
                                                                             help="Reprioritize this requirement. All criteria must total 100%.")},
            key=weight_key)
        proposed_weights = [float(row["Proposed weight %"]) for row in weight_editor]
        weight_total = sum(proposed_weights)
        weights_match = (len(weight_base_criteria) == len(payload["criteria"])
                         and all(abs(float(c["weight"]) - w) <= 0.01
                                 for c, w in zip(payload["criteria"], proposed_weights)))
        st.caption(f"Proposed allocation: **{weight_total:g}%**")
        if not weights_match:
            st.info("The allocation differs from the weights used for this result. Rerun with these weights before approving.")
        rerun_disabled = (abs(weight_total - 100.0) > 0.01 or not st.session_state.get("active_api_key")
                          or not str(st.session_state.get("active_model", "")).strip()
                          or not st.session_state.get("wizard_entries"))
        if st.button("↻ Rerun comparison with these weights", disabled=rerun_disabled,
                     key=f"rerun_weights_button_{payload['rfp_run_id']}_{current_fingerprint[:8]}",
                     help="Calls the selected provider again for every supplier. The new result will require analyst validation."):
            revised_criteria = [dict(c, weight=weight) for c, weight in zip(weight_base_criteria, proposed_weights)]
            st.session_state.wizard_criteria = revised_criteria
            analyze_batch(st.session_state.wizard_entries, st.session_state.sidebar_provider,
                          st.session_state.active_api_key, st.session_state.active_model.strip(),
                          revised_criteria, payload.get("analysis_context", {}))
            st.rerun()
        if payload.get("warnings"):
            with st.expander(f"Guardrail findings · {len(payload['warnings'])}", expanded=True):
                for warning in payload["warnings"]:
                    st.markdown(f"- {escape(str(warning))}")
        review_state = {}
        for index, supplier in enumerate(suppliers):
            with st.expander(f"Review #{supplier['final_rank']} · {supplier['supplier_name']}", expanded=index == 0):
                st.markdown("**Supplier risks**")
                st.write(supplier["scorecard"].get("risks", []) or ["No risks reported by the model."])
                st.dataframe([{"Criterion": row["name"], "Score": f"{row['score']:g} / {row['max_score']:g}",
                               "Evidence check": "Located in proposal" if row.get("evidence_verified") else "Needs manual verification",
                               "Evidence excerpt": row["evidence"], "Model rationale": row["justification"]}
                              for row in supplier["scorecard"]["criteria"]], use_container_width=True, hide_index=True)
                review_state[supplier["supplier_name"]] = st.checkbox(
                    f"I reviewed the scores, risks, and cited evidence for {supplier['supplier_name']}",
                    key=f"review_supplier_{payload['rfp_run_id']}_{index}",
                    help="Check after comparing the scorecard and evidence with the source proposal.")
        reviewer_name = st.text_input("Reviewer name", key=f"reviewer_name_{payload['rfp_run_id']}",
                                      help="Name or role of the analyst validating this evaluation.")
        feedback = st.text_area("Analyst feedback / approval rationale", key=f"review_feedback_{payload['rfp_run_id']}",
                                placeholder="Record corrections, concerns, missing evidence, or why the ranking is acceptable…",
                                help="Required. Record corrections, concerns, missing evidence, or why the ranking is acceptable. This note is saved with the approved run.")
        has_warnings = bool(payload.get("warnings"))
        acknowledged = True
        if has_warnings:
            acknowledged = st.checkbox("I reviewed and acknowledge the listed validation and evidence warnings.",
                                       key=f"review_ack_{payload['rfp_run_id']}",
                                       help="Warnings are not automatically cleared by approval; they remain with the run.")
        all_reviewed = bool(review_state) and all(review_state.values())
        approve_col, status_col = st.columns([1, 2])
        can_approve = (analysis_is_current and weights_match and bool(reviewer_name.strip()) and bool(feedback.strip())
                       and all_reviewed and acknowledged)
        if approve_col.button("Approve & save to history", type="primary", disabled=not can_approve,
                              key=f"approve_run_{payload['rfp_run_id']}",
                              help="Saves this run only after all supplier reviews and required warning acknowledgements."):
            approved = {**payload, "status": "approved",
                        "human_review": {"status": "approved", "reviewer": reviewer_name.strip(),
                                         "reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                         "reviewer_feedback": feedback.strip(),
                                         "supplier_reviews": review_state}}
            try:
                db.save_run(payload["rfp_run_id"], payload["provider"], payload["model"],
                            payload["criteria"], suppliers, approved)
                st.session_state.latest_result = approved
                st.success("Analyst review recorded. The approved run is now in Run history.")
                st.rerun()
            except Exception:
                st.error("Could not save the approved run. It remains available in this session for retry.")
        else:
            status_col.caption("Review every supplier, enter reviewer identity and written feedback, and acknowledge any warnings to approve. Rerun first if the batch or rubric changed.")
    else:
        human_review = payload.get("human_review", {})
        if human_review.get("status") == "approved":
            st.success(f"Human review approved by {human_review.get('reviewer', 'analyst')} · {human_review.get('reviewed_at', '')}")
            if human_review.get("reviewer_feedback"):
                st.info(f"Analyst feedback: {human_review['reviewer_feedback']}")
        st.download_button("↓ Download complete result as JSON", json.dumps(payload, indent=2, ensure_ascii=False),
                           file_name=f"{payload['rfp_run_id'].lower()}.json", mime="application/json", type="primary")


if page == "New evaluation":
    wizard_step = st.session_state.wizard_step
    mode_options = ["Current floor-mat rubric", "Customize from an RFQ"]
    analysis_mode = st.session_state.get("wizard_mode", mode_options[0])
    provider = st.session_state.get("sidebar_provider", "OpenRouter")
    model = st.session_state.get("active_model", "")
    api_key = st.session_state.get("active_api_key", "")
    criteria = st.session_state.get("wizard_criteria", [])
    entries = st.session_state.get("wizard_entries", [])
    analysis_context = st.session_state.get("wizard_analysis_context", {})

    if wizard_step == 1:
        st.markdown("<div class='section-label'>Step 1 / Set up your analysis</div>", unsafe_allow_html=True)
        analysis_mode = st.radio("Choose an evaluation path", mode_options,
                                 index=mode_options.index(analysis_mode) if analysis_mode in mode_options else 0,
                                 key="analysis_mode_choice",
                                 help="Use the saved floor-mat exercise rubric, or upload a buyer RFQ to draft criteria for this run.")
        st.markdown("<div class='info-grid'><div class='info-card'><div class='icon'>✦</div><strong>Current floor-mat rubric</strong><span>Use the existing criteria and the bundled supplier comparison as a starting point.</span></div><div class='info-card'><div class='icon'>↗</div><strong>Customize from an RFQ</strong><span>Upload a buyer RFQ next; the selected AI provider will draft reviewable criteria and weights.</span></div></div>", unsafe_allow_html=True)
        st.info(f"AI evaluator selected in the left panel: **{provider} · {model or 'model required'}**. Add the provider key there to continue.")
        if st.button("Continue to criteria  →", type="primary", disabled=not api_key or not model.strip(), key="wizard_step1_next"):
            previous_mode = st.session_state.get("wizard_mode")
            if previous_mode and previous_mode != analysis_mode:
                st.session_state.pop("wizard_criteria", None)
                st.session_state.pop("wizard_entries", None)
                st.session_state.pop("wizard_analysis_context", None)
            st.session_state.wizard_mode = analysis_mode
            st.session_state.wizard_provider = provider
            st.session_state.wizard_model = model.strip()
            st.session_state.wizard_api_key = api_key
            st.session_state.latest_result = None
            st.session_state.wizard_step = 2
            st.rerun()

    elif wizard_step == 2:
        st.markdown("<div class='section-label'>Step 2 / Prepare the evaluation rubric</div>", unsafe_allow_html=True)
        provider = st.session_state.get("sidebar_provider", "OpenRouter")
        model = st.session_state.get("active_model", "")
        api_key = st.session_state.get("active_api_key", "")
        if analysis_mode == "Current floor-mat rubric":
            st.caption("Review the existing floor-mat criteria and weights. Changes here apply to this run; use Save if you also want to update the shared SQLite rubric.")
            initial_criteria = st.session_state.get("wizard_criteria") or db.get_criteria()
            edited = st.data_editor(initial_criteria, use_container_width=True, hide_index=True, num_rows="fixed",
                                    column_config={"criterion_id": st.column_config.NumberColumn(disabled=True),
                                                   "name": st.column_config.TextColumn("Criterion", required=True, help="Short name for one independently scored procurement requirement."),
                                                   "description": st.column_config.TextColumn("What to inspect", width="large", help="Define observable evidence or measurable requirements for the evaluator."),
                                                   "weight": st.column_config.NumberColumn("Weight %", min_value=0.0, max_value=100.0, step=1.0, help="Importance of this criterion. Active weights must total 100%."),
                                                   "max_score": st.column_config.NumberColumn("Max score", min_value=1.0, max_value=100.0, step=1.0, help="Maximum score the model can assign for this criterion."),
                                                   "is_active": st.column_config.CheckboxColumn("Active", help="Only active criteria are included in the current analysis.")}, key="wizard_current_criteria")
            criteria = [dict(row) for row in edited if row["is_active"]]
            active_weight = sum(float(row["weight"]) for row in criteria)
            save_col, total_col = st.columns([1, 3])
            if save_col.button("Save shared rubric", key="wizard_save_current_rubric"):
                try:
                    db.save_criteria(edited)
                    st.success("Shared floor-mat rubric saved in SQLite.")
                except Exception:
                    st.error("Could not save the rubric. Check that criterion names are unique.")
            total_col.caption(f"Active weight: **{active_weight:g}%**")
            analysis_context = {"mode": "current_rubric", "criteria_source": "Current floor-mat rubric; reviewed in wizard",
                                "rfq_document": "Bundled fictional floor-mat RFP"}
            valid_criteria = bool(criteria) and abs(active_weight - 100.0) <= 0.01
            back_col, next_col = st.columns(2)
            if back_col.button("← Back to setup", key="wizard_step2_back_current"):
                st.session_state.wizard_step = 1
                st.rerun()
            if next_col.button("Continue to supplier proposals  →", type="primary", disabled=not valid_criteria, key="wizard_step2_next_current"):
                st.session_state.wizard_criteria = criteria
                st.session_state.wizard_analysis_context = analysis_context
                st.session_state.wizard_step = 3
                st.rerun()
            if not valid_criteria:
                st.warning(f"Active weights must total exactly 100% (currently {active_weight:g}%).")
        else:
            st.caption("Upload the buyer requirement, generate a draft rubric, then review its criteria and weightage.")
            rfq_file = st.file_uploader("Buyer RFQ (searchable PDF or UTF-8 text)", type=["pdf", "txt"], key="custom_rfq_file",
                                        help="Upload the buyer's requirements. Text must be extractable; scanned PDFs need OCR before upload.")
            uploaded_digest = hashlib.sha256(rfq_file.getvalue()).hexdigest() if rfq_file else ""
            stored_digest = st.session_state.get("custom_rfq_digest", "")
            active_digest = uploaded_digest or stored_digest
            has_matching_rubric = bool(active_digest and active_digest == stored_digest
                                       and st.session_state.get("custom_rfq_criteria"))
            if rfq_file:
                generate_clicked = st.button("✦ Generate criteria and weightage", type="primary",
                                             disabled=not api_key or not model.strip(), key="wizard_generate_rfq")
                if generate_clicked:
                    try:
                        with st.spinner(f"{provider} is reading the RFQ and drafting criteria…"):
                            generated, weighting_note = generate_criteria(provider, api_key, model.strip(), rfq_text(rfq_file))
                        st.session_state.custom_rfq_digest = uploaded_digest
                        st.session_state.custom_rfq_name = rfq_file.name
                        st.session_state.custom_rfq_criteria = generated
                        st.session_state.custom_rfq_weighting_note = weighting_note
                        st.session_state.custom_rfq_version = st.session_state.get("custom_rfq_version", 0) + 1
                        st.session_state.pop("wizard_criteria", None)
                        st.session_state.pop("wizard_criteria_source_digest", None)
                        has_matching_rubric = True
                        st.success("Draft generated. Review the criteria and weights before continuing.")
                    except Exception as exc:
                        st.error(f"Could not generate the RFQ rubric: {exc}")
            elif has_matching_rubric:
                st.success(f"Using the RFQ and generated criteria saved in this session: {st.session_state.get('custom_rfq_name', 'uploaded RFQ')}")
            # `stored_digest` is the value from before the generate button ran.
            # Compare against the updated session value so a newly generated
            # rubric is immediately available for review on the same rerun.
            if rfq_file and uploaded_digest != st.session_state.get("custom_rfq_digest", ""):
                has_matching_rubric = False
                st.warning("This RFQ differs from the one used to create the current rubric. Generate criteria again.")
            if has_matching_rubric:
                st.info(st.session_state.get("custom_rfq_weighting_note", "AI-suggested weights; review before evaluation."))
                version = st.session_state.get("custom_rfq_version", 1)
                editor_key = f"wizard_rfq_criteria_{active_digest[:10]}_{version}"
                draft = (st.session_state.get("wizard_criteria")
                         if st.session_state.get("wizard_criteria_source_digest") == active_digest
                         else st.session_state.custom_rfq_criteria)
                custom_edited = st.data_editor(draft, use_container_width=True, hide_index=True, num_rows="fixed",
                                               column_config={"criterion_id": st.column_config.NumberColumn(disabled=True),
                                                              "name": st.column_config.TextColumn("Criterion", required=True, help="Short name for an independently scored procurement requirement."),
                                                              "description": st.column_config.TextColumn("What the evaluator checks", width="large", required=True, help="Specify evidence and minimum requirements the proposal will be assessed against."),
                                                              "weight": st.column_config.NumberColumn("Weight %", min_value=0.0, max_value=100.0, step=0.5, help="Importance of the criterion; all weights must sum to 100%."),
                                                              "max_score": st.column_config.NumberColumn("Max score", min_value=1.0, max_value=100.0, step=1.0, help="Maximum score available for this criterion."),
                                                              "weight_rationale": st.column_config.TextColumn("Why this weight", width="large", help="Explain the procurement rationale for the suggested percentage.")}, key=editor_key)
                criteria = []
                for row in custom_edited:
                    item = {key: row[key] for key in ("criterion_id", "name", "description", "weight", "max_score")}
                    item["weight_rationale"] = row.get("weight_rationale", "")
                    criteria.append(item)
                active_weight = sum(float(row["weight"]) for row in criteria)
                valid_criteria = bool(criteria) and abs(active_weight - 100.0) <= 0.01
                st.caption(f"Custom rubric total: **{active_weight:g}%** · Run-specific; it does not overwrite the floor-mat rubric.")
                back_col, next_col = st.columns(2)
                if back_col.button("← Back to setup", key="wizard_step2_back_custom"):
                    st.session_state.wizard_step = 1
                    st.rerun()
                if next_col.button("Continue to supplier proposals  →", type="primary", disabled=not valid_criteria, key="wizard_step2_next_custom"):
                    st.session_state.wizard_criteria = criteria
                    st.session_state.wizard_criteria_source_digest = active_digest
                    st.session_state.wizard_analysis_context = {"mode": "custom_rfq", "criteria_source": "LLM-drafted from uploaded RFQ; reviewed in wizard",
                                                               "rfq_document": st.session_state.get("custom_rfq_name", "uploaded RFQ"),
                                                               "rfq_sha256": active_digest}
                    st.session_state.wizard_step = 3
                    st.rerun()
                if not valid_criteria:
                    st.warning(f"Criteria weights must total exactly 100% (currently {active_weight:g}%).")
            else:
                back_col, _ = st.columns(2)
                if back_col.button("← Back to setup", key="wizard_step2_back_no_rubric"):
                    st.session_state.wizard_step = 1
                    st.rerun()

    elif wizard_step == 3:
        st.markdown("<div class='section-label'>Step 3 / Add supplier proposals</div>", unsafe_allow_html=True)
        st.caption("Add at least two supplier proposal PDFs. The bundled supplier set is available for the floor-mat exercise.")
        if analysis_mode == "Current floor-mat rubric":
            demo_mode = st.toggle("Use the five bundled fictional proposals", value=True, key="wizard_demo_mode",
                                  help="Use the supplied synthetic Indian automotive proposals instead of uploading files.")
            if demo_mode:
                st.info("Five fictional Indian automotive suppliers will be compared using the current floor-mat rubric.")
                entries = [{"supplier_name": name, "submission_date": submitted, "experience_rating": rating,
                            "file_name": filename, "bytes": (ROOT / "sample_proposals" / filename).read_bytes()}
                           for name, filename, submitted, rating in SAMPLES]
            else:
                files = st.file_uploader("Supplier proposal PDFs", type=["pdf"], accept_multiple_files=True, key="wizard_current_supplier_files",
                                         help="Select two or more searchable supplier proposal PDFs.")
                previous_entries = st.session_state.get("wizard_entries", [])
                previous_source = st.session_state.get("wizard_proposal_source", "")
                entries = (supplier_upload_form("wizard_current", files) if files else
                           previous_entries if previous_source == "uploads" else [])
        else:
            files = st.file_uploader("Supplier proposal PDFs", type=["pdf"], accept_multiple_files=True, key="wizard_custom_supplier_files",
                                     help="Select two or more searchable supplier proposal PDFs.")
            previous_entries = st.session_state.get("wizard_entries", [])
            previous_source = st.session_state.get("wizard_proposal_source", "")
            entries = (supplier_upload_form("wizard_custom", files) if files else
                       previous_entries if previous_source == "uploads" else [])
        if entries:
            st.success(f"{len(entries)} supplier proposal(s) are ready.")
        elif not (analysis_mode == "Current floor-mat rubric" and st.session_state.get("wizard_demo_mode", True)):
            st.info("Select at least two PDFs and save supplier details to continue.")
        back_col, next_col = st.columns(2)
        if back_col.button("← Back to rubric", key="wizard_step3_back"):
            st.session_state.wizard_step = 2
            st.rerun()
        if next_col.button("Continue to review  →", type="primary", disabled=len(entries) < 2, key="wizard_step3_next"):
            st.session_state.wizard_entries = entries
            st.session_state.wizard_proposal_source = (
                "demo" if analysis_mode == "Current floor-mat rubric" and st.session_state.get("wizard_demo_mode", True)
                else "uploads"
            )
            st.session_state.wizard_step = 4
            st.rerun()

    elif wizard_step == 4:
        st.markdown("<div class='section-label'>Step 4 / Review and run comparison</div>", unsafe_allow_html=True)
        criteria = st.session_state.get("wizard_criteria", [])
        entries = st.session_state.get("wizard_entries", [])
        analysis_context = st.session_state.get("wizard_analysis_context", {})
        provider = st.session_state.get("sidebar_provider", "OpenRouter")
        model = st.session_state.get("active_model", "")
        api_key = st.session_state.get("active_api_key", "")
        criterion_frame = [{"Criterion": c["name"], "Weight": f"{float(c['weight']):g}%", "Evaluation focus": c["description"]}
                           for c in criteria]
        supplier_frame = [{"Supplier": e["supplier_name"], "Proposal": e["file_name"],
                           "Submission date": e["submission_date"], "Experience / 10": e["experience_rating"]}
                          for e in entries]
        rubric_col, supplier_col = st.columns(2)
        with rubric_col:
            st.markdown("### Rubric snapshot")
            st.dataframe(criterion_frame, use_container_width=True, hide_index=True)
        with supplier_col:
            st.markdown("### Supplier batch")
            st.dataframe(supplier_frame, use_container_width=True, hide_index=True)
        st.caption(f"Evaluator: {provider} · {model} · {len(criteria)} criteria · {len(entries)} suppliers")
        back_col, run_col = st.columns(2)
        if back_col.button("← Back to suppliers", key="wizard_step4_back"):
            st.session_state.wizard_step = 3
            st.rerun()
        run = run_col.button("✦ Run supplier comparison", type="primary",
                             disabled=not criteria or len(entries) < 2 or not api_key or not model.strip(),
                             use_container_width=True, key="wizard_run_analysis")
        if run:
            if len({str(c["name"]).strip().casefold() for c in criteria}) != len(criteria):
                st.error("Criterion names must be unique in the rubric.")
            elif len({e["supplier_name"].casefold() for e in entries}) != len(entries):
                st.error("Supplier names must be unique within a batch.")
            elif not all(e["supplier_name"] and e["bytes"] for e in entries):
                st.error("Each supplier needs a name and readable proposal PDF.")
            else:
                analyze_batch(entries, provider, api_key, model, criteria, analysis_context)
        if st.session_state.latest_result:
            st.divider()
            show_results(st.session_state.latest_result)

elif page == "Run history":
    st.markdown("<div class='section-label'>Saved evaluation runs</div>", unsafe_allow_html=True)
    runs = db.list_runs()
    if not runs:
        st.info("Completed runs will appear here.")
    else:
        selected_id = st.selectbox("Select an RFP run", [r["rfp_run_id"] for r in runs],
                                   help="Choose a saved supplier evaluation to reopen its ranking and evidence.")
        payload = db.load_run(selected_id)
        if payload:
            payload["warnings"] = []
            show_results(payload)

elif page == "How it works":
    st.markdown("<div class='section-label'>A transparent, human-reviewable pipeline</div>", unsafe_allow_html=True)
    st.caption("Language models help interpret proposal evidence. The score calculation and ranking remain explicit and deterministic.")
    st.markdown("""
    <div class="info-grid">
      <div class="info-card"><div class="icon">01</div><strong>Set the rubric</strong><span>Criteria and weights are saved to SQLite. The active weights must total exactly 100%.</span></div>
      <div class="info-card"><div class="icon">02</div><strong>Collect proposals</strong><span>Upload searchable PDFs or load the built-in sample batch. Add supplier metadata for comparison.</span></div>
      <div class="info-card"><div class="icon">03</div><strong>Extract & review</strong><span>PDF text is extracted, then OpenRouter or Cohere evaluates one proposal at a time using the rubric.</span></div>
      <div class="info-card"><div class="icon">04</div><strong>Validate the response</strong><span>Scores are normalized to the rubric. Missing or invalid values produce warnings and safe defaults.</span></div>
      <div class="info-card"><div class="icon">05</div><strong>Compare consistently</strong><span>Python calculates weighted scores, criterion benchmarks, relative performance, PPI and tie-breaks.</span></div>
      <div class="info-card"><div class="icon">06</div><strong>Validate & approve</strong><span>An analyst checks every supplier, acknowledges warnings, records feedback and approves before the run enters history.</span></div>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("Scoring and data handling details"):
        st.markdown("""
        - **Absolute score:** sum of criterion score divided by maximum score, multiplied by the criterion weight.
        - **Peer Performance Index:** criterion-relative performance against the best valid score in this run, weighted across criteria.
        - **Ranking:** PPI descending, then earlier submission, higher experience rating, and supplier name.
        - **Provider:** the selected OpenRouter or Cohere API receives proposal text and the active rubric for scoring.
        - **Credential:** entered in the left-side password field and excluded from saved run records and JSON exports.
        - **Human review:** AI results remain session drafts until an analyst reviews each supplier and approves with written feedback.
        - **Evidence check:** criterion excerpts are checked against proposal text; failed checks are flagged for manual verification and warning acknowledgement.
        - **Persistence:** evaluation history is stored in the local SQLite database; hosting platforms may not preserve local files between deployments.
        """)

