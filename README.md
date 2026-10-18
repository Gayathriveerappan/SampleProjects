# Sourcing Studio — Agentic RFP Evaluation

A classroom procurement analysis app that evaluates supplier RFP PDFs against an editable rubric, compares suppliers, calculates deterministic rankings, and keeps evidence visible at every step.

The bundled exercise sources a simple, four-piece TPE automotive floor-mat set for a fictional small hatchback. The buyer RFP is documented in [procurement_brief.md](procurement_brief.md) and as a five-page PDF at `procurement_rfp.pdf`. Five fictional India-based component manufacturers submit distinct, four-page INR proposals. Supplier identities and all quote details are synthetic, not real companies or market offers.

The previous software-vendor sample PDFs are retained in `sample_proposals/legacy_software_demo/` for reference; the app's bundled batch uses only the five floor-mat proposals.

## Start locally

1. Install Python 3.10 or newer.
2. From this folder, create and activate a virtual environment.
3. Install dependencies: `pip install -r requirements.txt`.
4. Start the app: `streamlit run app.py`.
5. Open **New evaluation**. **Current floor-mat rubric** keeps the existing criteria and can run the bundled five-supplier demo. **Customize from an RFQ** accepts a searchable buyer RFQ PDF or UTF-8 text file.
6. For a custom run, choose OpenRouter or Cohere and enter the API key at runtime. Generate the draft criteria and weights, review/edit them until the total is 100%, then upload two or more supplier proposal PDFs.
7. Enter supplier names, dates and experience ratings, then run the comparison. Review the leaderboard, rubric snapshot, scorecards and evidence; download the complete JSON if needed.

The project seeds five active criteria into `data/rfp_evaluation.db` on first run. The active weights must total 100%. Criteria and completed runs are stored in local SQLite. The database is ignored by Git.

## API keys

Keys are entered at run time in the UI, passed to the selected provider adapter, and are not written to SQLite, `.env`, Streamlit config, or JSON exports. The password field exists in the active Streamlit session memory. Do not use a shared device for confidential proposal analysis. This project sends proposal text to the provider selected by the operator; use only documents you are authorized to share with that provider.

## What the project does

- Uses a responsive dark workspace with a workflow stepper, sample-batch onboarding cards, a visual ranked comparison, and tabbed evidence/risk/run-detail views.
- Offers a separate custom-RFQ path: an uploaded buyer RFQ is sent to the selected OpenRouter/Cohere model to draft a 4–8 criterion rubric with suggested weights, which the user can edit before supplier scoring. Custom rubric edits are saved with that run and do not overwrite the current floor-mat criteria.
- Extracts text from selectable PDFs with `pypdf`; scanned PDFs need OCR before upload.
- Calls OpenRouter Chat Completions or Cohere v2 Chat once per supplier with the current active rubric.
- Requests evidence-based JSON, parses the response, fills missing criteria with zero, clips scores to the allowed range, and records validation warnings.
- Calculates weighted absolute score, best peer score per criterion, score gap, relative performance percentage, and weighted Peer Performance Index (PPI) in Python.
- Sorts by PPI descending, submission date ascending, experience rating descending, and supplier name ascending.
- Persists the full result and supplier scorecards in one SQLite RFP run, then offers complete JSON download.

## Repository map

| File | Responsibility |
|---|---|
| `app.py` | Streamlit UI, orchestration, extraction, result views, and JSON download |
| `db.py` | SQLite schema, criterion seed, and persistence |
| `llm.py` | OpenRouter and Cohere HTTP adapters; prompts; JSON parsing |
| `scoring.py` | Deterministic normalization, benchmarks, PPI, and ranking |
| `procurement_brief.md` | Detailed buyer RFP: scope, product specification, quality, delivery, commercial response, evaluation and submission instructions |
| `procurement_rfp.pdf` | Five-page formatted copy of the fictional buyer RFP |
| `create_rfp_pdf.py` | Rebuilds the buyer RFP PDF |
| `create_sample_proposals.py` | Rebuilds five four-page synthetic supplier proposals |
| `create_sample_run.py` | Rebuilds an illustrative JSON scorecard without calling an LLM |
| `sample_proposals/` | Five fictional, text-readable India-based supplier responses (4 pages each) |
| `data/` | Local SQLite database, created at runtime and excluded from Git |
| `sample_run.json` | Illustrative completed-run export |
| `BUILD_STEPS.md` | End-to-end implementation and demonstration guide |

## Deploy to Streamlit Community Cloud

Create a GitHub repository containing this folder's files, then create an app on Streamlit Community Cloud with `app.py` as the entrypoint. `requirements.txt` sits alongside the entrypoint. The five sample PDFs must be committed with the source. Community Cloud does not guarantee persistence of local file storage, so the SQLite run history can be deleted by the platform; use a managed database for durable production history. See [Streamlit's data connection guidance](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data) and [deployment steps](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

The app is prepared for deployment but has not been published: publishing requires a GitHub repository and a Streamlit Community Cloud account.

## Provider endpoints

- OpenRouter: [Chat Completions API](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request)
- Cohere: [v2 Chat API](https://docs.cohere.com/reference/chat)

