# Build and runbook: Agentic RFP Evaluation

This document describes the complete workflow for the mini-project, including design choices, setup, operation, demonstration, and deployment handoff. Requirements inside the classroom brief are represented below; credentials are collected only through the interactive UI as requested.

## 1. Goal and procurement boundary

Build an AI-assisted procurement evaluation workspace. The model judges proposal content against a configurable rubric and cites support from the document. Python owns score normalization, all arithmetic, peer comparisons, deterministic tie-breaks, and ranking. Model output is decision support and requires buyer review before an award.

The exercise sources a four-piece TPE floor-mat set for a fictional small hatchback. The five India-based supplier names, locations, prices, and company claims are fictional and prepared only for demonstration; they are not independently verified. See `procurement_brief.md` and `procurement_rfp.pdf` for the five-page buyer RFP and `sample_proposals/` for five four-page synthetic responses.

## 2. Architecture

```text
Streamlit interface
  ├── Criteria editor ─────────── SQLite evaluation_criteria
  ├── PDF intake + metadata
  ├── Workflow orchestrator
  │     ├── pypdf text extraction
  │     ├── OpenRouter / Cohere adapter ── criterion JSON + evidence
  │     ├── Python validation and normalization
  │     ├── Python scoring, peer benchmarks, and stable ranking
  │     └── SQLite run + complete supplier scorecards
  └── Leaderboard, detail view, history, JSON download
```

The provider adapters use OpenRouter's Chat Completions endpoint and Cohere's v2 Chat endpoint. Active criteria are read from SQLite at the beginning of each run and inserted into each proposal prompt. No LLM is asked to compare suppliers or assign final rank.

## 3. Files and responsibilities

1. `app.py` renders the dark interactive interface, handles proposal upload and metadata, extracts PDF text, coordinates the steps, and presents results.
2. `db.py` creates/updates SQLite tables, seeds example criteria, and stores complete run payloads and supplier rows.
3. `llm.py` builds evidence-only prompts, calls the selected provider, and parses JSON responses.
4. `scoring.py` handles invalid score data, peer calculations, and deterministic ordering.
5. `procurement_brief.md` defines the detailed RFP, product and synthetic Indian sourcing scenario.
6. `create_rfp_pdf.py` creates the formatted five-page buyer RFP PDF.
7. `create_sample_proposals.py` creates five fictional four-page supplier proposals in `sample_proposals/`.
7. `create_sample_run.py` rebuilds the sample JSON without a provider call.
8. `sample_run.json` illustrates the final export shape.

## 4. Setup

1. Install Python 3.10+.
2. Open a terminal in the project folder.
3. Create a virtual environment: `python -m venv .venv`.
4. Activate it (`.venv\\Scripts\\Activate.ps1` in Windows PowerShell; `source .venv/bin/activate` on macOS/Linux).
5. Install: `python -m pip install -r requirements.txt`.
6. Optional: regenerate the documents using `python create_rfp_pdf.py` and `python create_sample_proposals.py` (these generators use ReportLab).
7. Optional: rebuild the illustrative export using `python create_sample_run.py`.
8. Start: `streamlit run app.py`.

On first launch, `db.initialize()` creates `data/rfp_evaluation.db` and seeds Product & Tooling Capability (25%), Quality & Compliance (25%), Commercial Value (20%), Delivery & Capacity (20%), and Warranty & Supplier Support (10%). The criteria screen permits edits and activation changes; active weights must sum to 100% before evaluation.

## 5. Evaluation workflow

1. **Setup:** load active criteria and weights from SQLite.
2. **Input:** upload multiple quotations or choose the five bundled fictional floor-mat proposals. Record supplier name, submission date, and historical experience rating out of 10.
3. **Batch:** generate one `RFP-YYYYMMDD-XXXXXXXX` run ID.
4. **Extract:** read PDF text with `pypdf`; stop if a PDF has no usable text (scan-only documents require OCR).
5. **Evaluate:** reload active criteria; build a prompt for one supplier at a time; call the UI-selected OpenRouter or Cohere provider.
6. **Validate:** parse JSON; match active criteria by ID; default missing or malformed scores to zero; clip out-of-range scores; keep warnings.
7. **Score:** compute weighted absolute scores for all suppliers.
8. **Benchmark:** for each criterion, find the highest score observed in the batch and calculate each supplier's gap and relative percentage.
9. **Rank:** calculate PPI and sort with the mandated stable tie-break order.
10. **Persist:** store the run and full response data under one run ID.
11. **Present:** show leaderboard, evidence and explanations, run details, and download the full JSON.

## 6. Formulas and rules

For supplier `s`, criterion `c`, criterion score `x`, maximum `m`, and weight `w` (percentage points):

- **Absolute weighted score (out of 100):** `Σ((x / m) × w)`.
- **Criterion benchmark:** maximum valid `x` across suppliers for criterion `c`.
- **Criterion gap:** `x - benchmark` (zero for the leader, negative for other suppliers).
- **Relative performance:** `(x / benchmark) × 100`; if the benchmark is zero, the relative percentage is zero.
- **PPI:** `Σ(relative_performance × w) / Σ(w)` for active criteria (a weighted average in percent).
- **Ranking:** PPI descending → earlier submission date → higher historical experience rating → supplier name ascending (case-insensitive). Sequential ranks are assigned only after this sort.

All numbers shown by the UI use the normalized scorecard; raw LLM values never determine rank directly.

## 7. Credentials and data handling

1. The operator selects a provider, enters an API key in a masked UI field, and supplies a model name.
2. The key is sent to the provider adapter only when **Evaluate proposals** is selected. It is not stored in a config file, database, or export.
3. Proposal text is sent to that provider for scoring. Confirm data-sharing authorization before uploading confidential proposals.
4. Uploaded bytes and key are held by the live app session while the workflow runs; clear the session or close the tab when finished.
5. Local SQLite holds criteria and evaluation outputs. The DB is Git-ignored. Community Cloud local files are not durable; select an external managed database for persistent production history.

Never commit API keys or a populated `data/rfp_evaluation.db` file.

## 8. Demo script

### Successful run

1. Start the app and leave the five default criteria active (weights total 100%).
2. Toggle **Use the five bundled fictional proposals**.
3. Select OpenRouter or Cohere; enter a key in the password field and confirm a model available to the account.
4. Click **Evaluate proposals**. The progress/status messages show independent supplier reviews.
5. Review rank, absolute score, PPI, criterion benchmarks, gap, relative percent, evidence, justification, and warnings.
6. Download the completed JSON and inspect the saved run in **Run history**.

### Validation / error demonstration

- For a local development demonstration, use a provider mock or an invalid/malformed JSON fixture in `llm.evaluate` and confirm missing criterion rows default to zero with warnings and out-of-range scores clip to the maximum. Do not send fabricated requests with a real credential.
- Use an invalid model or blank credential to show a provider failure. The app stops before saving an incomplete run.
- Upload a scan-only image PDF to demonstrate the extraction error. Convert it to searchable text with OCR before a successful analysis.

The project includes manual demonstration steps; no live provider call is made during setup because it requires the operator's private API key.

## 9. Deployment handoff

1. Put the contents of this project folder in a GitHub repository.
2. Verify `data/rfp_evaluation.db`, `.env`, and any provider secrets are not committed.
3. Connect the repository to Streamlit Community Cloud and select `app.py` as the entrypoint.
4. Confirm the included `requirements.txt` installs and the sample PDFs are present.
5. Share the resulting public Streamlit URL after checking the app with the intended account and provider.

This workspace contains a deployment-ready source project, but publishing has not been performed. Community Cloud local SQLite history can disappear, so use managed persistence for a real procurement system.

## 10. Acceptance checklist

- [x] Streamlit UI with editable active criteria and weight total display.
- [x] Multiple PDF supplier input and metadata; bundled five-supplier synthetic India sourcing batch.
- [x] OpenRouter and Cohere provider choice; run-time masked key entry.
- [x] Dynamic prompt includes each active criterion; JSON-only, evidence-grounded instruction.
- [x] Validation warnings and normalized bounded criterion scores.
- [x] Python-only weighted scores, peer benchmarks, relative performance, PPI, and deterministic tie-breaks.
- [x] SQLite storage of criteria, batch metadata, and complete scorecard result.
- [x] Leaderboard, scorecard, run history, warnings, and JSON download.
- [x] Detailed five-page fictional buyer RFP and five fictional four-page supplier proposal PDFs with deliberately varied strengths, prices, schedules, and gaps.
- [x] Beginner-friendly procurement brief for a molded automotive floor-mat set.
- [x] Setup, formulas, operation, demo, and deployment documented.

