"""GLANCE pseudonymous handle generator.

Produces deterministic, dataviz-themed Reddit-style handles from participant
tokens (UUIDs). Format: @AdjectiveChartTerm or @AdjectiveChartTerm42 on collision.

The hash of the token selects adjective + noun. The handle is stored in the
DB on first generation so it stays stable forever.
"""

import hashlib

# ── Word pools ────────────────────────────────────────────────────────────

ADJECTIVES = [
    "Rugged", "Crooked", "Blurry", "Tiny", "Wobbly", "Sharp", "Sleek",
    "Crisp", "Fuzzy", "Bold", "Broken", "Smooth", "Stacked", "Nested",
    "Clipped", "Dashed", "Dotted", "Hollow", "Solid", "Chunky", "Slim",
    "Wide", "Narrow", "Dense", "Sparse", "Tangled", "Clean", "Noisy",
    "Faded", "Vivid", "Subtle", "Bright", "Dim", "Flat", "Deep",
    "Tilted", "Skewed", "Warped", "Shifted", "Stretched",
]

NOUNS = [
    "Piechart", "Barchart", "Scatterplot", "Histogram", "Heatmap",
    "Boxplot", "Trendline", "Errorbar", "Axis", "Legend", "Gridline",
    "Tooltip", "Datapoint", "Outlier", "Baseline", "Gradient", "Contour",
    "Mosaic", "Treemap", "Sparkline", "Violin", "Ridgeline", "Sunburst",
    "Sankey", "Waffle", "Bubble", "Funnel", "Gauge", "Donut", "Radar",
    "Waterfall", "Candlestick", "Choropleth", "Isoline", "Cartogram",
    "Dendrogram", "Lollipop", "Stripplot", "Hexbin", "Rosechart",
]

# Total unique base combos: 40 * 40 = 1600
# With 2-digit suffix for collisions: 1600 * 100 = 160,000


def _hash_token(token: str) -> int:
    """Return a stable integer hash from a token string."""
    return int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)


def generate_handle(token: str) -> str:
    """Generate a deterministic @AdjectiveNoun handle from a token.

    The same token always produces the same base handle. No @ prefix
    in the stored value (added at display time).
    """
    h = _hash_token(token)
    adj = ADJECTIVES[h % len(ADJECTIVES)]
    noun = NOUNS[(h // len(ADJECTIVES)) % len(NOUNS)]
    return f"{adj}{noun}"


def generate_unique_handle(token: str, existing_handles: set[str]) -> str:
    """Generate a handle that doesn't collide with existing ones.

    First tries the base AdjectiveNoun form. If taken, appends 2-digit
    numbers (02-99) derived from the hash until a unique one is found.
    """
    base = generate_handle(token)
    if base not in existing_handles:
        return base

    h = _hash_token(token)
    # Try suffixed variants
    for i in range(2, 100):
        # Mix the suffix deterministically with the hash
        candidate = f"{base}{(h + i) % 100:02d}"
        if candidate not in existing_handles:
            return candidate

    # Fallback: use raw hash digits (astronomically unlikely to reach here)
    return f"{base}{h % 10000:04d}"


def ensure_handle(participant_id: int, token: str) -> str:
    """Get or create a stable handle for a participant.

    Checks the DB first. If no handle stored, generates one (collision-safe)
    and persists it. Returns the handle string (without @ prefix).
    """
    from db import get_db

    db = get_db()

    # Check if handle already exists
    row = db.execute(
        "SELECT handle FROM participants WHERE id = ?", (participant_id,)
    ).fetchone()

    if row and row["handle"]:
        db.close()
        return row["handle"]

    # Generate collision-free handle
    existing = db.execute(
        "SELECT handle FROM participants WHERE handle IS NOT NULL"
    ).fetchall()
    existing_handles = {r["handle"] for r in existing}

    handle = generate_unique_handle(token, existing_handles)

    # Persist
    db.execute(
        "UPDATE participants SET handle = ? WHERE id = ?",
        (handle, participant_id),
    )
    db.commit()
    db.close()

    return handle


def get_handle_map(participant_ids: list[int]) -> dict[int, str]:
    """Bulk-fetch or generate handles for a list of participant IDs.

    Returns dict mapping participant_id -> handle string.
    Generates and persists handles for any participants missing one.
    """
    if not participant_ids:
        return {}

    from db import get_db

    db = get_db()

    placeholders = ",".join("?" * len(participant_ids))
    rows = db.execute(
        f"SELECT id, token, handle FROM participants WHERE id IN ({placeholders})",
        participant_ids,
    ).fetchall()

    # Collect existing handles for collision detection
    all_handles_rows = db.execute(
        "SELECT handle FROM participants WHERE handle IS NOT NULL"
    ).fetchall()
    existing_handles = {r["handle"] for r in all_handles_rows}

    result = {}
    to_update = []

    for r in rows:
        pid = r["id"]
        if r["handle"]:
            result[pid] = r["handle"]
        else:
            handle = generate_unique_handle(r["token"], existing_handles)
            existing_handles.add(handle)
            result[pid] = handle
            to_update.append((handle, pid))

    # Bulk persist new handles
    if to_update:
        for handle, pid in to_update:
            db.execute(
                "UPDATE participants SET handle = ? WHERE id = ?",
                (handle, pid),
            )
        db.commit()

    db.close()
    return result
