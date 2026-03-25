#!/usr/bin/env python3
"""Backfill abstracts for existing GA images.

Sources (checked in order, combined):
1. Sidecar JSON: semantic_references.L3[0], description, main_finding
2. Graph narratives from ga_graphs: narrative node names + syntheses
3. Metadata fields: executive_summary_fr, main_finding

Run:
    python scripts/backfill_abstracts.py
"""

import json
import os
import sys

# Add parent dir to path so we can import db, etc.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import yaml
from db import get_db, init_db

BASE = os.path.join(os.path.dirname(__file__), "..")


def load_sidecar(filename: str) -> dict:
    """Load sidecar JSON for a GA image filename."""
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    sidecar_path = os.path.join(BASE, "ga_library", stem + ".json")
    if os.path.exists(sidecar_path):
        try:
            with open(sidecar_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def extract_graph_narratives(ga_image_id: int) -> list[str]:
    """Extract narrative node names + syntheses from the latest graph."""
    db = get_db()
    row = db.execute(
        "SELECT graph_yaml FROM ga_graphs WHERE ga_image_id = ? ORDER BY id DESC LIMIT 1",
        (ga_image_id,)
    ).fetchone()
    db.close()
    if not row or not row[0]:
        return []

    try:
        graph = yaml.safe_load(row[0])
    except Exception:
        return []

    nodes = graph.get("nodes", [])
    parts = []
    for n in nodes:
        if n.get("node_type") != "narrative":
            continue
        name = n.get("name", "")
        synthesis = n.get("synthesis", "")
        if synthesis:
            parts.append(f"{name}: {synthesis}" if name else synthesis)
        elif name:
            parts.append(name)
    return parts


def build_abstract(ga_row: dict, sidecar: dict, narratives: list[str]) -> str | None:
    """Combine all available sources into a structured abstract."""
    parts = []

    # Title
    title = sidecar.get("title", "") or ga_row.get("title", "")
    if title:
        parts.append(f"Title: {title}")

    # Main finding
    main_finding = sidecar.get("main_finding", "")
    if main_finding:
        parts.append(f"Finding: {main_finding}")

    # Executive summary
    exec_summary = sidecar.get("executive_summary_fr", "")
    if exec_summary:
        parts.append(f"Summary: {exec_summary}")

    # Semantic reference L3 (first entry)
    sem_refs = sidecar.get("semantic_references", {})
    if isinstance(sem_refs, dict):
        l3 = sem_refs.get("L3_detailed", sem_refs.get("L3", []))
        if isinstance(l3, list) and l3:
            parts.append(f"Key insight: {l3[0]}")

    # Description fallback
    if not main_finding and not exec_summary:
        desc = sidecar.get("description", "") or ga_row.get("description", "")
        if desc:
            parts.append(f"Description: {desc}")

    # Narrative nodes from graph
    if narratives:
        parts.append("Narratives:\n" + "\n".join(f"- {n}" for n in narratives))

    if not parts:
        return None

    return "\n".join(parts)


def main():
    init_db()
    db = get_db()
    rows = db.execute("SELECT * FROM ga_images").fetchall()
    db.close()

    total = len(rows)
    skipped = 0
    filled = 0
    no_data = 0

    for row in rows:
        row_dict = dict(row)
        ga_id = row_dict["id"]
        filename = row_dict["filename"]

        # Skip if abstract already set
        if row_dict.get("abstract"):
            skipped += 1
            continue

        sidecar = load_sidecar(filename)
        narratives = extract_graph_narratives(ga_id)
        abstract = build_abstract(row_dict, sidecar, narratives)

        if abstract:
            db2 = get_db()
            db2.execute("UPDATE ga_images SET abstract = ? WHERE id = ?", (abstract, ga_id))
            db2.commit()
            db2.close()
            filled += 1
            print(f"  [+] {filename} -> {len(abstract)} chars")
        else:
            no_data += 1

    print(f"\nDone: {total} total, {filled} filled, {skipped} skipped (already set), {no_data} no data")


if __name__ == "__main__":
    main()
