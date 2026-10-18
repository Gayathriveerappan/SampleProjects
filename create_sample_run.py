"""Rebuild the illustrative JSON export without making provider API calls."""
import json
from datetime import datetime, timezone
from pathlib import Path

from db import DEFAULT_CRITERIA
from scoring import calculate_and_rank

ROOT = Path(__file__).parent
names = ["BharatMold Components", "Deccan Polymer Works", "Narmada Auto Plastics",
         "Kaveri Trim Systems", "Eastern Mobility Components"]
filenames = ["bharatmold_components.pdf", "deccan_polymer_works.pdf", "narmada_auto_plastics.pdf",
             "kaveri_trim_systems.pdf", "eastern_mobility_components.pdf"]
dates = ["2026-10-12", "2026-10-10", "2026-10-11", "2026-10-09", "2026-10-13"]
experience = [8.0, 4.5, 7.5, 9.0, 6.5]
scores = [[9, 9, 6, 7, 8], [7, 6, 10, 9, 5], [8, 8, 8, 8, 8], [7, 8, 7, 7, 9], [8, 7, 7, 5, 7]]
evidence = [
    ["3.5 mm TPE; 10 mm edge; reinforced heel zone; fit checked to supplied template.",
     "12-point fitment checklist, first-article report, and batch traceability.",
     "INR 1,185/set plus INR 6,50,000 tooling; freight and GST stated separately.",
     "30 days to approved sample; 12,000 sets/month capacity.",
     "12-month warranty; containment plan within 3 business days."],
    ["2.5 mm TPE blend and basic texture; compound grade and tolerances not specified.",
     "Visual inspection and one sample fit check; no written control plan included.",
     "INR 790/set plus INR 2,50,000 tooling; freight to be confirmed.",
     "14 days to first sample; 7,000 sets/month capacity.",
     "6-month warranty; claim timing and freight responsibility are not committed."],
    ["3.0 mm virgin TPE, raised edge, anti-slip ribs, and retention windows.",
     "First-article approval, hourly sampling, batch labels, and 20-set pilot gate.",
     "INR 965/set plus INR 3,80,000 tooling; GST and estimated freight stated.",
     "21 days to approved sample; 10,000 sets/month capacity.",
     "12-month warranty; initial containment within 48 hours."],
    ["3.2 mm TPE, ribbed underside, and heel reinforcement; grade finalized later.",
     "Incoming inspection, digital production records, and first-article sign-off.",
     "INR 1,045/set plus INR 4,20,000 tooling; freight terms specified by order size.",
     "24 days after fitment data; 15,000 sets/month capacity.",
     "18-month warranty; 24-hour claim response and named account contact."],
    ["3.4 mm TPE with raised edge and two hardness options; retention to be confirmed.",
     "Batch tracking, visual inspection of every mat, and shift-level dimensional sampling.",
     "INR 990/set plus INR 3,10,000 tooling; GST and freight stated separately.",
     "40 days to first sample; 8,000 sets/month capacity.",
     "12-month warranty; replacement target within 10 working days after claim approval."],
]
summaries = [
    "Strong tooling and quality documentation with a premium quote and moderate schedule.",
    "Lowest set price and quick sample start, with weak quality evidence and limited experience.",
    "Balanced price and schedule with a well-defined sample, pilot, and support process.",
    "Strong supplier experience, capacity, and warranty service; tooling and quality detail are less complete.",
    "Useful material and inspection detail at a competitive price, offset by the longest sample schedule."
]
risks = [
    ["Independent material test reports are not attached."],
    ["Compound grade, inspection frequencies, traceability format, and warranty process need agreement."],
    ["Compound certificate and approved fitment template should be confirmed before tooling release."],
    ["Dimensional limits, sample frequency, and number of tool corrections remain open."],
    ["Interstate sample transit leaves little schedule buffer; formal corrective-action timing is absent."]
]

criteria = [{"criterion_id": index, "name": item[0], "description": item[1], "weight": item[2],
             "max_score": item[3], "is_active": 1} for index, item in enumerate(DEFAULT_CRITERIA, 1)]
suppliers = []
for i, name in enumerate(names):
    rows = []
    for j, criterion in enumerate(criteria):
        rows.append({"criterion_id": criterion["criterion_id"], "name": criterion["name"],
                     "score": scores[i][j], "max_score": criterion["max_score"],
                     "weight": criterion["weight"], "justification": evidence[i][j], "evidence": evidence[i][j]})
    suppliers.append({"supplier_name": name, "submission_date": dates[i], "experience_rating": experience[i],
                      "source_file": filenames[i], "scorecard": {"supplier_name": name, "criteria": rows,
                      "risks": risks[i], "overall_summary": summaries[i]}})

ranked = calculate_and_rank(suppliers, criteria)
payload = {"rfp_run_id": "RFP-20261018-DEMO0001", "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "status": "completed", "provider": "Illustrative fixture - no live API call",
           "model": "Hand-authored sample scorecards", "criteria": criteria, "suppliers": ranked,
           "warnings": [], "business_rules": {
               "absolute_score": "sum((score / max_score) * weight)",
               "criterion_benchmark": "highest valid score for that criterion in this run",
               "relative_performance_pct": "score / benchmark * 100; 0 when benchmark is 0",
               "ppi": "weighted average of criterion relative-performance percentages",
               "tie_break_order": ["PPI descending", "submission date ascending",
                                   "experience rating descending", "supplier name ascending"]}}
(ROOT / "sample_run.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(ROOT / "sample_run.json")
