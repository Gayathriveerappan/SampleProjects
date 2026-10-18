from __future__ import annotations

import json
from html import escape
import hashlib
import uuid
from datetime import date, datetime, timezone
from io import BytesIO
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

import db
from llm import COHERE_DEFAULT_MODEL, OPENROUTER_DEFAULT_MODEL, evaluate, generate_criteria
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
.section-label { color:#e9eaf1; font-size:17px; font-weight:700; margin:10px 0 12px; }
div.stButton > button[kind="primary"] { background:linear-gradient(95deg,#8a63f6,#5dcfb1); color:#11131a; border:0; font-weight:800; border-radius:10px; }
div.stButton > button { border-radius:10px; transition:transform .18s ease,box-shadow .18s ease; }
div.stButton > button:hover { transform:translateY(-1px); box-shadow:0 8px 22px rgba(117,91,222,.18); border-color:rgba(167,139,250,.55); }
.note { border-left:2px solid var(--mint); background:rgba(113,224,194,.06); padding:10px 13px; color:#bbc7ce; font-size:12px; border-radius:0 9px 9px 0; }
.status-strip { display:flex; flex-wrap:wrap; gap:8px; margin:0 0 20px; }
.status-chip { border:1px solid var(--line); background:rgba(255,255,255,.025); border-radius:30px; padding:6px 10px; color:#b8c0d0; font:10px 'DM Mono',monospace; }
.status-chip b { color:#e8e9ef; font-weight:500; }
.stepper { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; margin:0 0 22px; }
.step { padding:10px 12px; border-radius:12px; background:rgba(255,255,255,.025); border:1px solid var(--line); color:#939bad; font-size:11px; }
.step span { color:var(--mint); font:11px 'DM Mono',monospace; margin-right:7px; }
.step.active { border-color:rgba(167,139,250,.4); background:rgba(167,139,250,.09); color:#f1edff; }
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
@media (max-width:700px) { .hero h1 { font-size:29px; } .stepper { grid-template-columns:repeat(2,minmax(0,1fr)); } .leader-item { grid-template-columns:minmax(90px,1fr) 2fr 45px; gap:7px; } }
</style>
""", unsafe_allow_html=True)

db.initialize()
if "latest_result" not in st.session_state:
    st.session_state.latest_result = None

with st.sidebar:
    st.markdown("<div class='eyebrow'>✦ PROCUREMENT INTELLIGENCE</div>", unsafe_allow_html=True)
    st.markdown("## Sourcing Studio")
    st.caption("An evidence-led workspace for confident sourcing")
    st.divider()
    st.markdown("### Your workspace")
    page = st.radio("Navigate", ["New evaluation", "Run history", "How it works"], label_visibility="collapsed")
    st.divider()
    active = db.get_criteria(active_only=True)
    active_weight = sum(float(c["weight"]) for c in active)
    st.metric("Active criteria", len(active))
    st.metric("Weight allocation", f"{active_weight:g}%")
    if active_weight == 100:
        st.caption("● Rubric ready · weights are balanced")
    else:
        st.caption("○ Balance active weights to 100% to run an evaluation.")

st.markdown("""
<div class="hero"><div class="eyebrow">AGENTIC RFP EVALUATION · PROCUREMENT WORKSPACE</div>
<h1>Find the best fit.<br>Back it with evidence.</h1>
<p>Bring supplier proposals together, evaluate them against your rubric, and make the trade-offs easy to see.</p></div>
<div class="status-strip"><div class="status-chip">◉ <b>LLM-assisted</b> evaluation</div><div class="status-chip">◉ <b>Evidence-linked</b> scorecards</div><div class="status-chip">◉ <b>SQLite</b> run history</div><div class="status-chip">◉ <b>Runtime-only</b> API key</div></div>
""", unsafe_allow_html=True)

active_step = {"New evaluation": "03" if st.session_state.latest_result else "01", "Run history": "04", "How it works": "02"}[page]
st.markdown(f"""
<div class="stepper">
 <div class="step {'active' if active_step == '01' else ''}"><span>01</span>Prepare the batch</div>
 <div class="step {'active' if active_step == '02' else ''}"><span>02</span>LLM review</div>
 <div class="step {'active' if active_step == '03' else ''}"><span>03</span>Compare evidence</div>
 <div class="step {'active' if active_step == '04' else ''}"><span>04</span>Saved run history</div>
</div>
""", unsafe_allow_html=True)


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
                supplier_name = x.text_input("Supplier name", value=Path(file.name).stem.replace("_", " ").title(), key=f"{prefix}_name_{i}")
                submitted = y.date_input("Submission date", value=date.today(), key=f"{prefix}_date_{i}")
                rating = z.number_input("Historical experience / 10", min_value=0.0, max_value=10.0, value=5.0, step=0.5, key=f"{prefix}_rating_{i}")
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


def analyze_batch(entries: list[dict], provider: str, key: str, model: str, criteria: list[dict],
                  analysis_context: dict | None = None) -> None:
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
                   "analysis_context": analysis_context or {"mode": "current_rubric"},
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
    bars = []
    for s in suppliers:
        width = max(0, min(100, float(s["absolute_score"])))
        bars.append(f"<div class='leader-item'><span>{escape(s['supplier_name'])}</span><div class='leader-track'><div class='leader-fill' style='width:{width:.1f}%'></div></div><span class='leader-score'>{s['absolute_score']:.1f}</span></div>")
    st.markdown("<div class='soft-card'>" + "".join(bars) + "</div>", unsafe_allow_html=True)
    st.markdown("### Ranked shortlist")
    st.dataframe([{"Rank": s["final_rank"], "Supplier": s["supplier_name"], "Absolute score": s["absolute_score"],
                   "PPI": f"{s['ppi']:.2f}%", "Submission date": s["submission_date"],
                   "Experience / 10": s["experience_rating"]} for s in suppliers],
                 use_container_width=True, hide_index=True)
    chosen = st.selectbox("Explore a supplier scorecard", [s["supplier_name"] for s in suppliers], key="scorecard_select")
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
    st.download_button("↓ Download complete result as JSON", json.dumps(payload, indent=2, ensure_ascii=False),
                       file_name=f"{payload['rfp_run_id'].lower()}.json", mime="application/json", type="primary")


if page == "New evaluation":
    st.markdown("<div class='section-label'>01 / Choose an evaluation path</div>", unsafe_allow_html=True)
    analysis_mode = st.radio("Evaluation mode", ["Current floor-mat rubric", "Customize from an RFQ"], key="analysis_mode")
    st.caption("Start with the bundled floor-mat exercise and existing weights, or upload your own buyer RFQ to generate a reviewable custom rubric.")

    st.markdown("<div class='section-label'>02 / Connect your evaluator</div>", unsafe_allow_html=True)
    st.markdown("<div class='note'>🔐 Enter a provider key for this session. For a custom RFQ, the selected model first proposes criteria and weightage, then evaluates each supplier proposal.</div>", unsafe_allow_html=True)
    provider = st.selectbox("AI provider", ["OpenRouter", "Cohere"], key="analysis_provider")
    default_model = OPENROUTER_DEFAULT_MODEL if provider == "OpenRouter" else COHERE_DEFAULT_MODEL
    if provider == "OpenRouter":
        st.caption("OpenRouter · use a model enabled for your account.")
    else:
        st.caption("Cohere · use a Cohere Chat model enabled for your account.")
    model = st.text_input("Model", value=default_model, key="analysis_model", help="Replace the default with a model available to your account.")
    api_key = st.text_input(f"{provider} API key", type="password", placeholder="Paste key for this run", key="runtime_api_key")
    st.caption("Credentials are supplied at run time and are not saved in SQLite or exported with the results.")
    provider_ready = bool(api_key and model.strip())

    entries = []
    criteria = []
    analysis_context = {"mode": "current_rubric", "criteria_source": "Current floor-mat rubric; edited parameters reviewed in UI"}
    active_weight = 0.0

    if analysis_mode == "Current floor-mat rubric":
        st.markdown("<div class='section-label'>03 / Current evaluation criteria</div>", unsafe_allow_html=True)
        st.caption("The current floor-mat rubric and weights remain the starting point. Edit and save only if you want to update this existing rubric.")
        all_criteria = db.get_criteria()
        edited = st.data_editor(all_criteria, use_container_width=True, hide_index=True, num_rows="fixed",
                                column_config={"criterion_id": st.column_config.NumberColumn(disabled=True),
                                               "name": st.column_config.TextColumn("Criterion", required=True),
                                               "description": st.column_config.TextColumn("What to inspect", width="large"),
                                               "weight": st.column_config.NumberColumn("Weight %", min_value=0.0, max_value=100.0, step=1.0),
                                               "max_score": st.column_config.NumberColumn("Max score", min_value=1.0, max_value=100.0, step=1.0),
                                               "is_active": st.column_config.CheckboxColumn("Active")}, key="criteria_editor")
        current_criteria = [dict(row) for row in edited if row["is_active"]]
        active_weight = sum(float(row["weight"]) for row in current_criteria)
        ca, cb = st.columns([1, 3])
        if ca.button("Save current rubric", key="save_criteria"):
            try:
                db.save_criteria(edited)
                st.success("Current rubric saved to SQLite.")
                st.rerun()
            except Exception:
                st.error("Could not save criteria. Check that criterion names are unique.")
        cb.caption(f"Active weight total: **{active_weight:g}%**")
        criteria = current_criteria

        st.markdown("<div class='section-label'>04 / Choose proposals</div>", unsafe_allow_html=True)
        st.markdown("<div class='info-grid'><div class='info-card'><div class='icon'>✦</div><strong>Current sample batch</strong><span>Five fictional Indian suppliers quoting the same automotive floor mat.</span></div><div class='info-card'><div class='icon'>↥</div><strong>Your own proposals</strong><span>Upload supplier PDFs to compare them with the current floor-mat rubric.</span></div><div class='info-card'><div class='icon'>⌕</div><strong>Evidence stays visible</strong><span>Review the extracted support behind each criterion score.</span></div></div>", unsafe_allow_html=True)
        demo_mode = st.toggle("Use the five bundled fictional proposals", value=True, key="current_demo_mode")
        if demo_mode:
            st.info("The bundled exercise data is fictional and intended for demonstration.")
            for name, filename, submitted, rating in SAMPLES:
                entries.append({"supplier_name": name, "submission_date": submitted, "experience_rating": rating,
                                "file_name": filename, "bytes": (ROOT / "sample_proposals" / filename).read_bytes()})
        else:
            proposal_files = st.file_uploader("Upload supplier proposal PDFs", type=["pdf"], accept_multiple_files=True,
                                               key="current_proposal_files", help="Upload two or more text-readable PDF responses.")
            if proposal_files:
                st.caption(f"{len(proposal_files)} proposal file(s) selected.")
                entries = supplier_upload_form("current", proposal_files)
        analysis_context = {"mode": "current_rubric", "criteria_source": "Current floor-mat rubric; edited parameters reviewed in UI",
                            "rfq_document": "Bundled fictional floor-mat RFP"}

    else:
        st.markdown("<div class='section-label'>03 / Upload the buyer RFQ</div>", unsafe_allow_html=True)
        st.markdown("<div class='info-grid'><div class='info-card'><div class='icon'>01</div><strong>Upload the requirement</strong><span>Provide a searchable RFQ PDF or UTF-8 text file. Scanned PDFs need OCR first.</span></div><div class='info-card'><div class='icon'>02</div><strong>Generate a draft rubric</strong><span>The chosen LLM extracts evaluation dimensions and suggests weights totalling 100%.</span></div><div class='info-card'><div class='icon'>03</div><strong>Review before scoring</strong><span>Edit the generated criteria and weightage before comparing supplier responses.</span></div></div>", unsafe_allow_html=True)
        rfq_file = st.file_uploader("Upload buyer RFQ", type=["pdf", "txt"], key="custom_rfq_file")
        rfq_digest = hashlib.sha256(rfq_file.getvalue()).hexdigest() if rfq_file else ""
        has_matching_rubric = bool(rfq_digest and st.session_state.get("custom_rfq_digest") == rfq_digest
                                   and st.session_state.get("custom_rfq_criteria"))
        generate_clicked = st.button("✦ Generate criteria and weightage from RFQ", type="primary",
                                     disabled=not rfq_file or not provider_ready, key="generate_rfq_criteria",
                                     use_container_width=True)
        if generate_clicked:
            try:
                document_text = rfq_text(rfq_file)
                with st.spinner(f"{provider} is reading the RFQ and drafting evaluation criteria…"):
                    generated, weighting_note = generate_criteria(provider, api_key, model.strip(), document_text)
                st.session_state.custom_rfq_digest = rfq_digest
                st.session_state.custom_rfq_name = rfq_file.name
                st.session_state.custom_rfq_criteria = generated
                st.session_state.custom_rfq_weighting_note = weighting_note
                st.session_state.custom_rfq_version = st.session_state.get("custom_rfq_version", 0) + 1
                has_matching_rubric = True
                st.success("Draft rubric generated. Review every criterion and weight before continuing.")
            except Exception as exc:
                st.error(f"Could not generate the RFQ rubric: {exc}")
        if rfq_file and not has_matching_rubric:
            st.warning("Generate or regenerate the criteria for the currently selected RFQ before uploading supplier proposals.")
        if has_matching_rubric:
            st.markdown("<div class='section-label'>04 / Review generated criteria and weights</div>", unsafe_allow_html=True)
            st.info(st.session_state.get("custom_rfq_weighting_note", "AI-proposed weights; review before evaluation."))
            version = st.session_state.get("custom_rfq_version", 1)
            criteria_editor_key = f"rfq_criteria_editor_{rfq_digest[:10]}_{version}"
            custom_edited = st.data_editor(st.session_state.custom_rfq_criteria, use_container_width=True,
                                           hide_index=True, num_rows="fixed",
                                           column_config={"criterion_id": st.column_config.NumberColumn(disabled=True),
                                                          "name": st.column_config.TextColumn("Criterion", required=True),
                                                          "description": st.column_config.TextColumn("What the evaluator checks", width="large", required=True),
                                                          "weight": st.column_config.NumberColumn("Weight %", min_value=0.0, max_value=100.0, step=0.5),
                                                          "max_score": st.column_config.NumberColumn("Max score", min_value=1.0, max_value=100.0, step=1.0),
                                                          "weight_rationale": st.column_config.TextColumn("Why this weight", width="large")},
                                           key=criteria_editor_key)
            criteria = []
            for row in custom_edited:
                item = {key: row[key] for key in ("criterion_id", "name", "description", "weight", "max_score")}
                item["weight_rationale"] = row.get("weight_rationale", "")
                criteria.append(item)
            active_weight = sum(float(row["weight"]) for row in criteria)
            st.caption(f"Custom rubric total: **{active_weight:g}%** · These weights apply to this RFQ run and do not overwrite the current sample rubric.")
            st.markdown("<div class='section-label'>05 / Upload supplier proposals</div>", unsafe_allow_html=True)
            proposal_files = st.file_uploader("Upload two or more supplier proposal PDFs", type=["pdf"],
                                               accept_multiple_files=True, key="custom_proposal_files")
            if proposal_files:
                st.caption(f"{len(proposal_files)} proposal file(s) selected.")
                entries = supplier_upload_form("custom", proposal_files)
            analysis_context = {"mode": "custom_rfq", "criteria_source": "LLM-drafted from uploaded RFQ; reviewed in UI",
                                "rfq_document": st.session_state.get("custom_rfq_name", rfq_file.name),
                                "rfq_sha256": rfq_digest}

    st.markdown("<div class='section-label'>06 / Run the comparison</div>", unsafe_allow_html=True)
    valid_criteria = bool(criteria) and abs(active_weight - 100.0) <= 0.01
    if not valid_criteria:
        st.warning(f"Evaluation criteria must be present and total exactly 100% (currently {active_weight:g}%).")
    if not entries:
        st.caption("Choose the bundled proposals or upload supplier proposals and save their details to enable the run.")
    run = st.button("✦  Evaluate supplier proposals", type="primary",
                    disabled=not valid_criteria or len(entries) < 2 or not provider_ready,
                    use_container_width=True)
    if run:
        if len({entry["supplier_name"].casefold() for entry in entries}) != len(entries):
            st.error("Supplier names must be unique within a batch.")
        elif not all(entry["supplier_name"] and len(entry["bytes"]) > 0 for entry in entries):
            st.error("Each supplier needs a name and a readable PDF.")
        else:
            analyze_batch(entries, provider, api_key, model.strip(), criteria, analysis_context)

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
    st.markdown("<div class='section-label'>A transparent, human-reviewable pipeline</div>", unsafe_allow_html=True)
    st.caption("Language models help interpret proposal evidence. The score calculation and ranking remain explicit and deterministic.")
    st.markdown("""
    <div class="info-grid">
      <div class="info-card"><div class="icon">01</div><strong>Set the rubric</strong><span>Criteria and weights are saved to SQLite. The active weights must total exactly 100%.</span></div>
      <div class="info-card"><div class="icon">02</div><strong>Collect proposals</strong><span>Upload searchable PDFs or load the built-in sample batch. Add supplier metadata for comparison.</span></div>
      <div class="info-card"><div class="icon">03</div><strong>Extract & review</strong><span>PDF text is extracted, then OpenRouter or Cohere evaluates one proposal at a time using the rubric.</span></div>
      <div class="info-card"><div class="icon">04</div><strong>Validate the response</strong><span>Scores are normalized to the rubric. Missing or invalid values produce warnings and safe defaults.</span></div>
      <div class="info-card"><div class="icon">05</div><strong>Compare consistently</strong><span>Python calculates weighted scores, criterion benchmarks, relative performance, PPI and tie-breaks.</span></div>
      <div class="info-card"><div class="icon">06</div><strong>Save & inspect</strong><span>Scorecards, cited proposal evidence, risks and run details are available for human review and JSON export.</span></div>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("Scoring and data handling details"):
        st.markdown("""
        - **Absolute score:** sum of criterion score divided by maximum score, multiplied by the criterion weight.
        - **Peer Performance Index:** criterion-relative performance against the best valid score in this run, weighted across criteria.
        - **Ranking:** PPI descending, then earlier submission, higher experience rating, and supplier name.
        - **Provider:** the selected OpenRouter or Cohere API receives proposal text and the active rubric for scoring.
        - **Credential:** entered in a password field for the run and excluded from saved run records and JSON exports.
        - **Persistence:** evaluation history is stored in the local SQLite database; hosting platforms may not preserve local files between deployments.
        """)

