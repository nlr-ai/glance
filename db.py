"""GLANCE database — SQLite, zero dependencies beyond stdlib."""

import sqlite3
import os
import json

DB_PATH = os.environ.get("GLANCE_DB_PATH", os.path.join(os.path.dirname(__file__), "data", "glance.db"))

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
    input_mode TEXT DEFAULT 'text'
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
    description TEXT
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
    conn.close()


def _migrate_add_columns(conn, table: str, columns: list[tuple[str, str]]):
    """Add columns to a table if they don't already exist."""
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    for col_name, col_type in columns:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
    conn.commit()


def create_participant(token, clinical_domain, experience_years, data_literacy, grade_familiar, colorblind_status, input_mode="text"):
    db = get_db()
    db.execute(
        """INSERT INTO participants
           (token, clinical_domain, experience_years, data_literacy, grade_familiar, colorblind_status, input_mode)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (token, clinical_domain, experience_years, data_literacy, grade_familiar, colorblind_status, input_mode),
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
    db.execute(
        """INSERT INTO ga_images (filename, domain, version, is_control, correct_product, products, title, description)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (filename, domain, version, int(is_control), correct_product,
         json.dumps(products) if products else None, title, description),
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
              stream_show_title=1):
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
            stream_show_title)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
         int(stream_show_title)),
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
