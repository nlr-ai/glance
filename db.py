"""GLANCE database — SQLite, zero dependencies beyond stdlib."""

import sqlite3
import os
import json
import re

DB_PATH = os.environ.get("GLANCE_DB_PATH", os.path.join(os.path.dirname(__file__), "data", "glance.db"))


def slugify(text: str) -> str:
    """Generate a URL-friendly slug from a filename or text.

    Strips image extensions, lowercases, replaces underscores/spaces with hyphens,
    removes non-alphanumeric characters (except hyphens), and collapses runs.
    """
    text = text.lower().strip()
    text = re.sub(r'\.(png|jpg|jpeg|webp)$', '', text)
    text = re.sub(r'[_\s]+', '-', text)
    text = re.sub(r'[^a-z0-9-]', '', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text

SCHEMA = """
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    token TEXT UNIQUE NOT NULL,
    clinical_domain TEXT NOT NULL,
    experience_years TEXT,
    data_literacy TEXT NOT NULL,
    grade_familiar INTEGER DEFAULT 0,
    colorblind_status TEXT DEFAULT 'unknown',
    input_mode TEXT DEFAULT 'text',
    referred_by TEXT,
    handle TEXT
);

CREATE TABLE IF NOT EXISTS ga_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    domain TEXT NOT NULL DEFAULT 'med',
    version TEXT,
    is_control INTEGER DEFAULT 0,
    correct_product TEXT,
    products TEXT,
    title TEXT,
    description TEXT,
    slug TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS analysis_leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    email TEXT NOT NULL,
    ga_image_id INTEGER,
    source TEXT DEFAULT 'analyze',
    paid INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL,
    ga_image_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    exposure_ms INTEGER DEFAULT 5000,
    q1_text TEXT,
    q1_time_ms INTEGER,
    q2_choice TEXT,
    q2_time_ms INTEGER,
    q3_choice TEXT,
    q3_time_ms INTEGER,
    s9a_pass INTEGER,
    s9a_score REAL DEFAULT 0.0,
    s9b_pass INTEGER,
    s9c_pass INTEGER,
    s9c_score REAL DEFAULT 0.0,
    glance_score REAL DEFAULT 0.0,
    speed_accuracy TEXT,
    q4_text TEXT,
    ab_group TEXT,
    tab_switched INTEGER DEFAULT 0,
    exposure_actual_ms INTEGER,
    q1_first_keystroke_ms INTEGER,
    q1_last_keystroke_ms INTEGER,
    exposure_mode TEXT DEFAULT 'spotlight',
    stream_position INTEGER,
    stream_length INTEGER,
    stream_selected_id TEXT,
    s10_hit INTEGER,
    q1_input_mode TEXT DEFAULT 'text',
    q1_raw_transcript TEXT,
    stimulus_condition TEXT DEFAULT 'nude',
    stimulus_text TEXT,
    stimulus_frame TEXT,
    stimulus_image_width INTEGER,
    screen_width INTEGER,
    screen_height INTEGER,
    device_pixel_ratio REAL,
    user_agent TEXT,
    screen_is_mobile INTEGER,
    stream_target_dwell_ms INTEGER,
    stream_scroll_type TEXT DEFAULT 'inertial_flick',
    stream_flick_seed TEXT,
    stream_feed_style TEXT,
    stream_target_enter_ts REAL,
    stream_target_exit_ts REAL,
    exposure_valid INTEGER DEFAULT 1,
    q1_edit_distance INTEGER,
    q1_audio_path TEXT,
    q1_first_utterance_ms INTEGER,
    q1_last_utterance_ms INTEGER,
    q1_word_count INTEGER,
    q1_filtered_text TEXT,
    q1_filter_ratio REAL,
    s9a_raw REAL,
    q4_dimension_id TEXT,
    q4_pattern TEXT,
    q4_response TEXT,
    q4_rt INTEGER,
    q5_dimension_id TEXT,
    q5_pattern TEXT,
    q5_response TEXT,
    q5_rt INTEGER,
    rejection_reason TEXT,
    stream_show_title INTEGER DEFAULT 1,
    s2_transcript TEXT,
    s2_duration_ms INTEGER,
    s2_chunks TEXT,
    s2_node_coverage TEXT,
    code_version TEXT,
    FOREIGN KEY (participant_id) REFERENCES participants(id),
    FOREIGN KEY (ga_image_id) REFERENCES ga_images(id),
    UNIQUE(participant_id, ga_image_id)
);
"""


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    # Migrate: add System 2 columns if missing (for existing DBs)
    _migrate_add_columns(conn, "tests", [
        ("s2_transcript", "TEXT"),
        ("s2_duration_ms", "INTEGER"),
        ("s2_chunks", "TEXT"),
        ("s2_node_coverage", "TEXT"),
    ])
    # Migrate: add code_version column if missing (for existing DBs)
    _migrate_add_columns(conn, "tests", [
        ("code_version", "TEXT"),
    ])
    # Migrate: add referral column if missing (for existing DBs)
    _migrate_add_columns(conn, "participants", [
        ("referred_by", "TEXT"),
    ])
    # Migrate: add paid column to analysis_leads if missing
    _migrate_add_columns(conn, "analysis_leads", [
        ("paid", "INTEGER DEFAULT 0"),
    ])
    # Migrate: add handle column for pseudonymous display names
    _migrate_add_columns(conn, "participants", [
        ("handle", "TEXT"),
    ])
    # Migrate: add slug column to ga_images
    _migrate_add_columns(conn, "ga_images", [
        ("slug", "TEXT"),
    ])
    # Ensure slug UNIQUE index exists (safe if already there)
    try:
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_ga_images_slug ON ga_images(slug)")
        conn.commit()
    except Exception:
        pass
    # Generate slugs for any images that don't have one yet
    _backfill_slugs(conn)
    conn.close()


def _migrate_add_columns(conn, table: str, columns: list[tuple[str, str]]):
    """Add columns to a table if they don't already exist."""
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    for col_name, col_type in columns:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
    conn.commit()


def _backfill_slugs(conn):
    """Generate slugs for any ga_images rows that don't have one yet."""
    rows = conn.execute("SELECT id, filename FROM ga_images WHERE slug IS NULL").fetchall()
    if not rows:
        return
    # Collect existing slugs to handle collisions
    existing = {r[0] for r in conn.execute("SELECT slug FROM ga_images WHERE slug IS NOT NULL").fetchall()}
    for row in rows:
        base_slug = slugify(row[1])  # row[1] = filename
        slug = base_slug
        counter = 2
        while slug in existing:
            slug = f"{base_slug}-{counter}"
            counter += 1
        existing.add(slug)
        conn.execute("UPDATE ga_images SET slug = ? WHERE id = ?", (slug, row[0]))
    conn.commit()


def _generate_unique_slug(conn, filename: str) -> str:
    """Generate a unique slug for a new ga_images entry."""
    base_slug = slugify(filename)
    slug = base_slug
    counter = 2
    while True:
        existing = conn.execute(
            "SELECT 1 FROM ga_images WHERE slug = ?", (slug,)
        ).fetchone()
        if not existing:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def get_image_by_slug(slug: str):
    """Return a single GA image row by slug."""
    db = get_db()
    row = db.execute("SELECT * FROM ga_images WHERE slug = ?", (slug,)).fetchone()
    db.close()
    return dict(row) if row else None


def create_participant(token, clinical_domain, experience_years, data_literacy, grade_familiar, colorblind_status, input_mode="text", referred_by=None):
    db = get_db()
    db.execute(
        """INSERT INTO participants
           (token, clinical_domain, experience_years, data_literacy, grade_familiar, colorblind_status, input_mode, referred_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (token, clinical_domain, experience_years, data_literacy, grade_familiar, colorblind_status, input_mode, referred_by),
    )
    db.commit()
    pid = db.execute("SELECT id FROM participants WHERE token = ?", (token,)).fetchone()["id"]
    db.close()
    return pid


def get_participant_by_token(token):
    db = get_db()
    row = db.execute("SELECT * FROM participants WHERE token = ?", (token,)).fetchone()
    db.close()
    return dict(row) if row else None


def add_ga_image(filename, domain="med", version=None, is_control=False,
                 correct_product=None, products=None, title=None, description=None):
    db = get_db()
    slug = _generate_unique_slug(db, filename)
    db.execute(
        """INSERT INTO ga_images (filename, domain, version, is_control, correct_product, products, title, description, slug)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (filename, domain, version, int(is_control), correct_product,
         json.dumps(products) if products else None, title, description, slug),
    )
    db.commit()
    db.close()


def get_next_image(participant_id):
    """Pick next unseen image for this participant."""
    db = get_db()
    seen = db.execute(
        "SELECT ga_image_id FROM tests WHERE participant_id = ?", (participant_id,)
    ).fetchall()
    seen_ids = [r["ga_image_id"] for r in seen]

    if seen_ids:
        placeholders = ",".join("?" * len(seen_ids))
        row = db.execute(
            f"SELECT * FROM ga_images WHERE id NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT 1",
            seen_ids,
        ).fetchone()
    else:
        row = db.execute("SELECT * FROM ga_images ORDER BY RANDOM() LIMIT 1").fetchone()

    db.close()
    return dict(row) if row else None


def save_test(participant_id, ga_image_id, q1_text, q1_time_ms,
              q2_choice, q2_time_ms, q3_choice, q3_time_ms,
              s9a_pass, s9b_pass, s9c_pass, q4_text="", ab_group=None,
              s9c_score=0.0, glance_score=0.0, speed_accuracy=None,
              s9a_score=0.0,
              tab_switched=0, exposure_actual_ms=None,
              q1_first_keystroke_ms=None, q1_last_keystroke_ms=None,
              exposure_mode="spotlight", stream_position=None,
              stream_length=None, stream_selected_id=None, s10_hit=None,
              q1_input_mode="text", q1_raw_transcript=None,
              screen_width=None, screen_height=None,
              device_pixel_ratio=None, user_agent=None,
              screen_is_mobile=None,
              stream_target_dwell_ms=None,
              stream_scroll_type="inertial_flick", stream_flick_seed=None,
              stream_feed_style=None,
              stream_target_enter_ts=None, stream_target_exit_ts=None,
              exposure_valid=1,
              stimulus_frame=None, stimulus_image_width=None,
              q1_edit_distance=None, q1_audio_path=None,
              q1_first_utterance_ms=None, q1_last_utterance_ms=None,
              q1_word_count=None,
              q1_filtered_text=None, q1_filter_ratio=None,
              s9a_raw=None,
              q4_dimension_id=None, q4_pattern=None,
              q4_response=None, q4_rt=None,
              q5_dimension_id=None, q5_pattern=None,
              q5_response=None, q5_rt=None,
              stream_show_title=1,
              code_version=None):
    db = get_db()
    cursor = db.execute(
        """INSERT INTO tests
           (participant_id, ga_image_id, q1_text, q1_time_ms,
            q2_choice, q2_time_ms, q3_choice, q3_time_ms,
            s9a_pass, s9a_score, s9b_pass, s9c_pass, s9c_score, glance_score,
            speed_accuracy, q4_text, ab_group,
            tab_switched, exposure_actual_ms,
            q1_first_keystroke_ms, q1_last_keystroke_ms,
            exposure_mode, stream_position, stream_length,
            stream_selected_id, s10_hit,
            q1_input_mode, q1_raw_transcript,
            screen_width, screen_height, device_pixel_ratio,
            user_agent, screen_is_mobile,
            stream_target_dwell_ms,
            stream_scroll_type, stream_flick_seed, stream_feed_style,
            stream_target_enter_ts, stream_target_exit_ts,
            exposure_valid,
            stimulus_frame, stimulus_image_width,
            q1_edit_distance, q1_audio_path,
            q1_first_utterance_ms, q1_last_utterance_ms, q1_word_count,
            q1_filtered_text, q1_filter_ratio,
            s9a_raw,
            q4_dimension_id, q4_pattern, q4_response, q4_rt,
            q5_dimension_id, q5_pattern, q5_response, q5_rt,
            stream_show_title, code_version)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (participant_id, ga_image_id, q1_text, q1_time_ms,
         q2_choice, q2_time_ms, q3_choice, q3_time_ms,
         int(s9a_pass), float(s9a_score), int(s9b_pass), int(s9c_pass),
         s9c_score, glance_score, speed_accuracy, q4_text, ab_group,
         int(tab_switched), exposure_actual_ms,
         q1_first_keystroke_ms, q1_last_keystroke_ms,
         exposure_mode, stream_position, stream_length,
         stream_selected_id, s10_hit,
         q1_input_mode, q1_raw_transcript,
         screen_width, screen_height, device_pixel_ratio,
         user_agent, screen_is_mobile,
         stream_target_dwell_ms,
         stream_scroll_type, stream_flick_seed, stream_feed_style,
         stream_target_enter_ts, stream_target_exit_ts,
         int(exposure_valid) if exposure_valid is not None else 1,
         stimulus_frame, stimulus_image_width,
         q1_edit_distance, q1_audio_path,
         q1_first_utterance_ms, q1_last_utterance_ms, q1_word_count,
         q1_filtered_text, q1_filter_ratio,
         s9a_raw,
         q4_dimension_id, q4_pattern, q4_response, q4_rt,
         q5_dimension_id, q5_pattern, q5_response, q5_rt,
         int(stream_show_title), code_version),
    )
    test_id = cursor.lastrowid
    db.commit()
    db.close()
    return test_id


def update_test_system2(test_id: int, s2_transcript: str, s2_duration_ms: int,
                        s2_chunks: str, s2_node_coverage: str):
    """Update a test row with System 2 deep analysis data."""
    db = get_db()
    db.execute(
        """UPDATE tests SET s2_transcript = ?, s2_duration_ms = ?,
           s2_chunks = ?, s2_node_coverage = ?
           WHERE id = ?""",
        (s2_transcript, s2_duration_ms, s2_chunks, s2_node_coverage, test_id),
    )
    db.commit()
    db.close()


def get_test(test_id):
    db = get_db()
    row = db.execute(
        """SELECT t.*, g.filename, g.domain, g.correct_product, g.title,
                  g.description, g.products, g.is_control, g.version
           FROM tests t JOIN ga_images g ON t.ga_image_id = g.id
           WHERE t.id = ?""",
        (test_id,),
    ).fetchone()
    db.close()
    return dict(row) if row else None


def get_stats(ga_image_id=None):
    db = get_db()
    if ga_image_id:
        row = db.execute(
            """SELECT COUNT(*) as total, AVG(s9a_pass)*100 as pct_s9a,
                      AVG(s9b_pass)*100 as pct_s9b, AVG(s9c_pass)*100 as pct_s9c,
                      AVG(q2_time_ms) as avg_q2_time
               FROM tests WHERE ga_image_id = ?""",
            (ga_image_id,),
        ).fetchone()
    else:
        row = db.execute(
            """SELECT COUNT(*) as total, AVG(s9a_pass)*100 as pct_s9a,
                      AVG(s9b_pass)*100 as pct_s9b, AVG(s9c_pass)*100 as pct_s9c,
                      AVG(q2_time_ms) as avg_q2_time
               FROM tests""",
        ).fetchone()
    db.close()
    return dict(row) if row else {}


def get_all_tests():
    db = get_db()
    rows = db.execute(
        """SELECT t.id, t.created_at, t.s9a_pass, t.s9a_score,
                  t.s9b_pass, t.s9c_pass,
                  t.s9c_score, t.glance_score, t.speed_accuracy,
                  t.q1_text, t.q2_choice, t.q3_choice,
                  t.q1_time_ms, t.q2_time_ms, t.q3_time_ms,
                  t.participant_id, t.ab_group,
                  t.tab_switched, t.exposure_actual_ms,
                  t.q1_first_keystroke_ms, t.q1_last_keystroke_ms,
                  t.exposure_mode, t.stream_position, t.stream_length,
                  t.stream_selected_id, t.s10_hit,
                  t.q1_input_mode, t.q1_raw_transcript,
                  t.q1_filter_ratio,
                  t.stream_show_title,
                  t.rejection_reason,
                  t.stimulus_frame, t.stimulus_image_width,
                  t.screen_is_mobile,
                  t.stream_scroll_type, t.stream_flick_seed,
                  t.stream_feed_style,
                  t.stream_target_enter_ts, t.stream_target_exit_ts,
                  t.exposure_valid,
                  t.q1_edit_distance, t.q1_audio_path,
                  t.q1_first_utterance_ms, t.q1_last_utterance_ms,
                  t.q1_word_count,
                  t.s9a_raw,
                  t.q4_dimension_id, t.q4_pattern, t.q4_response, t.q4_rt,
                  t.q5_dimension_id, t.q5_pattern, t.q5_response, t.q5_rt,
                  t.code_version,
                  p.clinical_domain, p.data_literacy,
                  g.title, g.domain, g.version, g.correct_product, g.is_control
           FROM tests t
           JOIN participants p ON t.participant_id = p.id
           JOIN ga_images g ON t.ga_image_id = g.id
           ORDER BY t.created_at DESC""",
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_image_count():
    db = get_db()
    row = db.execute("SELECT COUNT(*) as c FROM ga_images").fetchone()
    db.close()
    return row["c"]


def get_all_images():
    db = get_db()
    rows = db.execute("SELECT * FROM ga_images ORDER BY id").fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_tests_by_quadrant(quadrant_fn):
    """Group all tests by profile quadrant.

    Args:
        quadrant_fn: callable(clinical_domain, data_literacy) -> quadrant string

    Returns: dict mapping quadrant -> list of test dicts
    """
    tests = get_all_tests()
    buckets = {}
    for t in tests:
        q = quadrant_fn(t.get("clinical_domain", ""), t.get("data_literacy", ""))
        buckets.setdefault(q, []).append(t)
    return buckets


def get_tests_for_participant(participant_id: int):
    """Return all tests for a specific participant, with image data joined."""
    db = get_db()
    rows = db.execute(
        """SELECT t.id, t.created_at, t.glance_score,
                  t.q1_text, t.q2_choice, t.q3_choice,
                  t.s9a_pass, t.s9b_pass, t.s9c_pass,
                  t.q2_time_ms, t.speed_accuracy,
                  t.exposure_mode, t.tab_switched,
                  g.id AS ga_image_id, g.filename, g.title,
                  g.domain, g.correct_product, g.is_control
           FROM tests t
           JOIN ga_images g ON t.ga_image_id = g.id
           WHERE t.participant_id = ?
           ORDER BY t.created_at DESC""",
        (participant_id,),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_tests_for_image(ga_image_id: int):
    """Return all tests for a specific GA image, with participant and image data."""
    db = get_db()
    rows = db.execute(
        """SELECT t.*, p.clinical_domain, p.data_literacy,
                  g.title, g.domain, g.version, g.correct_product, g.is_control
           FROM tests t
           JOIN participants p ON t.participant_id = p.id
           JOIN ga_images g ON t.ga_image_id = g.id
           WHERE t.ga_image_id = ?
           ORDER BY t.created_at DESC""",
        (ga_image_id,),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_image_by_id(ga_image_id: int):
    """Return a single GA image row by id."""
    db = get_db()
    row = db.execute("SELECT * FROM ga_images WHERE id = ?", (ga_image_id,)).fetchone()
    db.close()
    return dict(row) if row else None


def get_landing_stats() -> dict:
    """Return stats needed for the landing page.

    Returns:
        {
            "total_participants": int,
            "total_tests": int,
            "total_gas": int,
            "total_domains": int,
            "avg_glance": float or None,
            "top_gas": list of dicts (top 5 by avg glance_score),
            "domain_counts": dict mapping domain -> n_gas,
            "best_ga": dict or None,
        }
    """
    db = get_db()

    total_participants = db.execute("SELECT COUNT(*) as c FROM participants").fetchone()["c"]
    total_tests = db.execute("SELECT COUNT(*) as c FROM tests").fetchone()["c"]
    total_gas = db.execute("SELECT COUNT(*) as c FROM ga_images").fetchone()["c"]
    total_domains = db.execute("SELECT COUNT(DISTINCT domain) as c FROM ga_images").fetchone()["c"]

    avg_row = db.execute("SELECT AVG(glance_score) as avg_g FROM tests WHERE glance_score IS NOT NULL").fetchone()
    avg_glance = round(avg_row["avg_g"], 4) if avg_row["avg_g"] is not None else None

    top_rows = db.execute(
        """SELECT g.id, g.filename, g.domain, g.title, g.slug,
                  AVG(t.glance_score) as avg_glance,
                  COUNT(t.id) as n_tests
           FROM ga_images g
           JOIN tests t ON t.ga_image_id = g.id
           WHERE t.glance_score IS NOT NULL
           GROUP BY g.id
           ORDER BY avg_glance DESC
           LIMIT 5"""
    ).fetchall()
    top_gas = [dict(r) for r in top_rows]

    domain_rows = db.execute(
        "SELECT domain, COUNT(*) as n_gas FROM ga_images GROUP BY domain ORDER BY n_gas DESC"
    ).fetchall()
    domain_counts = {r["domain"]: r["n_gas"] for r in domain_rows}

    best_ga = top_gas[0] if top_gas else None

    db.close()

    return {
        "total_participants": total_participants,
        "total_tests": total_tests,
        "total_gas": total_gas,
        "total_domains": total_domains,
        "avg_glance": avg_glance,
        "top_gas": top_gas,
        "domain_counts": domain_counts,
        "best_ga": best_ga,
    }


def get_example_ga() -> dict | None:
    """Return the GA with the most tests, or None if no tests exist.

    Returns dict with id, filename, domain, title, n_tests.
    """
    db = get_db()
    row = db.execute(
        """SELECT g.id, g.filename, g.domain, g.title, g.slug,
                  COUNT(t.id) as n_tests
           FROM ga_images g
           JOIN tests t ON t.ga_image_id = g.id
           GROUP BY g.id
           ORDER BY n_tests DESC
           LIMIT 1"""
    ).fetchone()
    db.close()
    return dict(row) if row else None


def get_referral_count(referral_code: str) -> int:
    """Count how many participants were referred by a given referral code."""
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) as c FROM participants WHERE referred_by = ?",
        (referral_code,),
    ).fetchone()
    db.close()
    return row["c"] if row else 0


def get_top_referrers(limit: int = 20) -> list[dict]:
    """Return top referrers ranked by number of successful referrals.

    Each entry: {referral_code, n_referrals, referrer_domain, referrer_handle}.
    """
    db = get_db()
    rows = db.execute(
        """SELECT p.referred_by AS referral_code,
                  COUNT(*) AS n_referrals,
                  (SELECT pp.clinical_domain FROM participants pp
                   WHERE SUBSTR(pp.token, 1, 8) = p.referred_by
                   LIMIT 1) AS referrer_domain,
                  (SELECT pp.id FROM participants pp
                   WHERE SUBSTR(pp.token, 1, 8) = p.referred_by
                   LIMIT 1) AS referrer_id
           FROM participants p
           WHERE p.referred_by IS NOT NULL AND p.referred_by != ''
           GROUP BY p.referred_by
           ORDER BY n_referrals DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    db.close()

    result = [dict(r) for r in rows]

    # Attach handles for referrers
    referrer_ids = [r["referrer_id"] for r in result if r.get("referrer_id")]
    if referrer_ids:
        from handles import get_handle_map
        handle_map = get_handle_map(referrer_ids)
        for r in result:
            rid = r.get("referrer_id")
            r["referrer_handle"] = handle_map.get(rid, None) if rid else None
    else:
        for r in result:
            r["referrer_handle"] = None

    return result


def save_analysis_lead(email: str, ga_image_id: int | None = None, source: str = "analyze", paid: int = 0) -> int:
    """Save an email lead from the analyze flow. Returns the lead id."""
    db = get_db()
    cursor = db.execute(
        "INSERT INTO analysis_leads (email, ga_image_id, source, paid) VALUES (?, ?, ?, ?)",
        (email, ga_image_id, source, paid),
    )
    lead_id = cursor.lastrowid
    db.commit()
    db.close()
    return lead_id
