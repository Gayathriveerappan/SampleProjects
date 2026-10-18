"""SQLite persistence for evaluation criteria and RFP runs."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent / "data" / "rfp_evaluation.db"

DEFAULT_CRITERIA = [
    ("Product & Tooling Capability", "Fitment design, TPE process, tooling, retention features, and production readiness.", 25.0, 10.0),
    ("Quality & Compliance", "Material consistency, dimensional checks, traceability, and quality controls.", 25.0, 10.0),
    ("Commercial Value", "Set price, tooling charges, taxes, freight, assumptions, and total cost clarity.", 20.0, 10.0),
    ("Delivery & Capacity", "Tooling lead time, samples, pilot, monthly capacity, and delivery reliability.", 20.0, 10.0),
    ("Warranty & Supplier Support", "Warranty terms, defect response, replacement process, and account support.", 10.0, 10.0),
]


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def initialize() -> None:
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS evaluation_criteria (
            criterion_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            weight REAL NOT NULL CHECK(weight >= 0),
            max_score REAL NOT NULL CHECK(max_score > 0),
            is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1))
        );
        CREATE TABLE IF NOT EXISTS rfp_runs (
            rfp_run_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            criteria_snapshot TEXT NOT NULL,
            full_result_json TEXT
        );
        CREATE TABLE IF NOT EXISTS supplier_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rfp_run_id TEXT NOT NULL REFERENCES rfp_runs(rfp_run_id) ON DELETE CASCADE,
            supplier_name TEXT NOT NULL,
            submission_date TEXT NOT NULL,
            experience_rating REAL NOT NULL,
            absolute_score REAL NOT NULL,
            ppi REAL NOT NULL,
            final_rank INTEGER NOT NULL,
            result_json TEXT NOT NULL,
            UNIQUE(rfp_run_id, supplier_name)
        );
        CREATE INDEX IF NOT EXISTS idx_supplier_runs ON supplier_results(rfp_run_id);
        """)
        columns = {row[1] for row in con.execute("PRAGMA table_info(rfp_runs)")}
        if "full_result_json" not in columns:
            con.execute("ALTER TABLE rfp_runs ADD COLUMN full_result_json TEXT")
        count = con.execute("SELECT COUNT(*) FROM evaluation_criteria").fetchone()[0]
        if count == 0:
            con.executemany(
                "INSERT INTO evaluation_criteria(name, description, weight, max_score, is_active) VALUES (?, ?, ?, ?, 1)",
                DEFAULT_CRITERIA,
            )
        else:
            rows = con.execute("SELECT criterion_id, name, weight, is_active FROM evaluation_criteria ORDER BY criterion_id").fetchall()
            legacy_names = ["Technical Capability", "Implementation Plan", "Commercial Value",
                            "Security & Compliance", "Support & Experience"]
            legacy_weights = [30.0, 20.0, 20.0, 20.0, 10.0]
            if ([row["name"] for row in rows] == legacy_names
                    and [float(row["weight"]) for row in rows] == legacy_weights
                    and all(int(row["is_active"]) == 1 for row in rows)):
                for row, criterion in zip(rows, DEFAULT_CRITERIA):
                    con.execute("UPDATE evaluation_criteria SET name=?, description=?, weight=? WHERE criterion_id=?",
                                (criterion[0], criterion[1], criterion[2], row["criterion_id"]))


def get_criteria(active_only: bool = False) -> list[dict[str, Any]]:
    query = "SELECT criterion_id, name, description, weight, max_score, is_active FROM evaluation_criteria"
    if active_only:
        query += " WHERE is_active=1"
    query += " ORDER BY criterion_id"
    with connect() as con:
        return [dict(row) for row in con.execute(query).fetchall()]


def save_criteria(criteria: list[dict[str, Any]]) -> None:
    with connect() as con:
        for item in criteria:
            con.execute(
                "UPDATE evaluation_criteria SET name=?, description=?, weight=?, max_score=?, is_active=? WHERE criterion_id=?",
                (item["name"].strip(), item["description"].strip(), float(item["weight"]),
                 float(item["max_score"]), int(bool(item["is_active"])), int(item["criterion_id"])),
            )


def save_run(run_id: str, provider: str, model: str, criteria: list[dict[str, Any]],
             suppliers: list[dict[str, Any]], full_result: dict[str, Any]) -> None:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with connect() as con:
        con.execute(
            "INSERT INTO rfp_runs(rfp_run_id, created_at, status, provider, model, criteria_snapshot, full_result_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, created_at, full_result.get("status", "approved"), provider, model, json.dumps(criteria, ensure_ascii=False),
             json.dumps(full_result, ensure_ascii=False)),
        )
        con.executemany(
            """INSERT INTO supplier_results
               (rfp_run_id, supplier_name, submission_date, experience_rating, absolute_score, ppi, final_rank, result_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [(run_id, s["supplier_name"], s["submission_date"], s["experience_rating"],
              s["absolute_score"], s["ppi"], s["final_rank"], json.dumps(s, ensure_ascii=False)) for s in suppliers],
        )


def list_runs() -> list[dict[str, Any]]:
    with connect() as con:
        return [dict(row) for row in con.execute(
            "SELECT rfp_run_id, created_at, status, provider, model FROM rfp_runs ORDER BY created_at DESC"
        ).fetchall()]


def load_run(run_id: str) -> dict[str, Any] | None:
    with connect() as con:
        run = con.execute("SELECT * FROM rfp_runs WHERE rfp_run_id=?", (run_id,)).fetchone()
        if not run:
            return None
        if run["full_result_json"]:
            return json.loads(run["full_result_json"])
        rows = con.execute(
            "SELECT result_json FROM supplier_results WHERE rfp_run_id=? ORDER BY final_rank", (run_id,)
        ).fetchall()
        return {**dict(run), "criteria": json.loads(run["criteria_snapshot"]),
                "suppliers": [json.loads(row["result_json"]) for row in rows]}
