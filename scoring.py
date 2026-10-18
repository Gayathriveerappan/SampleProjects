"""Deterministic normalization, peer benchmarking, and ranking."""
from __future__ import annotations

from datetime import date
import re
from typing import Any


def _evidence_is_grounded(evidence: str, source_text: str) -> bool:
    """Conservatively flag whether an excerpt can be located in source text."""
    if not evidence.strip() or not source_text.strip():
        return False
    normalize = lambda value: re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()
    excerpt = normalize(evidence)
    source = normalize(source_text)
    if len(excerpt) < 20:
        return excerpt in source
    if excerpt in source:
        return True
    tokens = [token for token in excerpt.split() if len(token) > 2]
    if len(tokens) < 5:
        return False
    matched = sum(1 for token in set(tokens) if token in source)
    return matched / len(set(tokens)) >= 0.8


def normalize_scorecard(raw: dict[str, Any], criteria: list[dict[str, Any]], supplier_name: str,
                        source_text: str = "") -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    if not isinstance(raw, dict):
        raw = {}
        warnings.append(f"{supplier_name}: response was not a JSON object; all criteria defaulted to zero.")
    rows = raw.get("criteria", [])
    by_id: dict[int, dict[str, Any]] = {}
    expected_ids = {int(c["criterion_id"]) for c in criteria}
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                try:
                    cid = int(row.get("criterion_id"))
                    if cid not in expected_ids:
                        warnings.append(f"{supplier_name}: ignored unexpected criterion ID {cid}.")
                    elif cid in by_id:
                        warnings.append(f"{supplier_name}: duplicate result for criterion ID {cid}; first result retained.")
                    else:
                        by_id[cid] = row
                except (TypeError, ValueError):
                    warnings.append(f"{supplier_name}: ignored a criterion result with an invalid ID.")
    else:
        warnings.append(f"{supplier_name}: criteria field was malformed; missing scores defaulted to zero.")

    normalized = []
    for criterion in criteria:
        cid = int(criterion["criterion_id"])
        row = by_id.get(cid)
        if row is None:
            warnings.append(f"{supplier_name}: missing {criterion['name']} score; defaulted to zero.")
            row = {}
        maximum = float(criterion["max_score"])
        if row and "max_score" in row:
            try:
                returned_maximum = float(row["max_score"])
                if returned_maximum != maximum:
                    warnings.append(f"{supplier_name}: ignored mismatched maximum for {criterion['name']}; rubric maximum {maximum:g} was applied.")
            except (TypeError, ValueError):
                warnings.append(f"{supplier_name}: ignored invalid maximum for {criterion['name']}; rubric maximum {maximum:g} was applied.")
        try:
            score = float(row.get("score", 0))
            if not (score == score and abs(score) != float("inf")):
                raise ValueError
        except (TypeError, ValueError):
            score = 0.0
            warnings.append(f"{supplier_name}: invalid {criterion['name']} score; defaulted to zero.")
        clipped = min(max(score, 0.0), maximum)
        if clipped != score:
            warnings.append(f"{supplier_name}: {criterion['name']} score clipped to 0-{maximum:g}.")
        justification = row.get("justification", "")
        evidence = row.get("evidence", "")
        if not isinstance(justification, str):
            justification = ""
            warnings.append(f"{supplier_name}: malformed {criterion['name']} justification removed.")
        if not isinstance(evidence, str):
            evidence = ""
            warnings.append(f"{supplier_name}: malformed {criterion['name']} evidence removed.")
        evidence = evidence[:2000]
        evidence_verified = _evidence_is_grounded(evidence, source_text)
        if not evidence_verified:
            warnings.append(f"{supplier_name}: {criterion['name']} evidence could not be verified against the proposal text; analyst review required.")
        normalized.append({"criterion_id": cid, "name": criterion["name"], "score": round(clipped, 2),
                           "max_score": maximum, "weight": float(criterion["weight"]),
                           "justification": justification[:1500], "evidence": evidence,
                           "evidence_verified": evidence_verified})
    raw_supplier = raw.get("supplier_name")
    if raw_supplier and str(raw_supplier).strip().casefold() != supplier_name.casefold():
        warnings.append(f"{supplier_name}: response named a different supplier; displayed supplier identity comes from the uploaded batch.")
    risks = raw.get("risks", [])
    if not isinstance(risks, list):
        risks = []
        warnings.append(f"{supplier_name}: malformed risk list removed.")
    risks = [str(risk).strip()[:500] for risk in risks if str(risk).strip()][:20]
    return {"supplier_name": supplier_name, "criteria": normalized,
            "risks": risks,
            "overall_summary": str(raw.get("overall_summary", ""))[:3000]}, warnings


def calculate_and_rank(suppliers: list[dict[str, Any]], criteria: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total_weight = sum(float(c["weight"]) for c in criteria)
    if not criteria or abs(total_weight - 100.0) > 0.01:
        raise ValueError("Active criterion weights must total 100%.")
    benchmark = {}
    for c in criteria:
        cid = int(c["criterion_id"])
        benchmark[cid] = max((next(r["score"] for r in s["scorecard"]["criteria"] if r["criterion_id"] == cid)
                              for s in suppliers), default=0.0)
    for supplier in suppliers:
        details, absolute, ppi = [], 0.0, 0.0
        for c in criteria:
            cid = int(c["criterion_id"])
            item = next(r for r in supplier["scorecard"]["criteria"] if r["criterion_id"] == cid)
            score, best, weight = item["score"], benchmark[cid], float(c["weight"])
            absolute += (score / float(c["max_score"])) * weight
            relative = (score / best * 100.0) if best > 0 else 0.0
            ppi += relative * weight / total_weight
            details.append({**item, "benchmark": best, "gap": round(score - best, 2),
                            "relative_performance_pct": round(relative, 2)})
        supplier["absolute_score"] = round(absolute, 2)
        supplier["ppi"] = round(ppi, 2)
        supplier["scorecard"]["criteria"] = details
    # Dates are ISO YYYY-MM-DD. Ranking is deterministic and independent of model output.
    ranked = sorted(suppliers, key=lambda s: (-s["ppi"], s["submission_date"],
                                               -float(s["experience_rating"]), s["supplier_name"].casefold()))
    for rank, supplier in enumerate(ranked, 1):
        supplier["final_rank"] = rank
        supplier["tie_break_explanation"] = (
            "Sorted by PPI descending, submission date ascending, experience rating descending, then supplier name ascending."
        )
    return ranked
