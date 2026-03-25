"""PRAW-based Reddit poller with per-sub filtering.

Monitors configured subreddits, detects posts matching filter criteria,
and routes them to the reaction pipeline (alert human for comment) or
ingestion pipeline (extract GA from linked paper, add to Leaderboard).

Supports dry-run mode (no Reddit API credentials needed) for development.

CLI:
    python reddit_poller.py [--once] [--sub dataisugly] [--dry-run]
"""

import os
import re
import sys
import json
import time
import sqlite3
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

import yaml

logger = logging.getLogger(__name__)

BASE = Path(__file__).parent
CONFIG_PATH = BASE / "ingestion_config.yaml"
DB_PATH = BASE / "ingestion.db"

# ── Academic detection ────────────────────────────────────────────────────

ACADEMIC_SIGNALS = [
    r'\bdoi\b', r'10\.\d{4,}/', r'pubmed', r'pmc\d+',
    r'nature\.com', r'sciencedirect', r'pnas\.org', r'cell\.com',
    r'springer', r'wiley', r'mdpi\.com', r'frontiersin\.org',
    r'plos', r'bmj\.com', r'lancet', r'jama', r'nejm\.org',
    r'\bpeer.reviewed\b', r'\bpublished\b', r'\bjournal\b',
    r'\bfigure from\b', r'\bpaper\b',
]

_ACADEMIC_PATTERN = re.compile(
    '|'.join(ACADEMIC_SIGNALS), re.IGNORECASE
)


def is_academic(text: str) -> bool:
    """Return True if the text contains academic signals."""
    return bool(_ACADEMIC_PATTERN.search(text))


# ── Config loading ────────────────────────────────────────────────────────

def load_config(path: Path = CONFIG_PATH) -> dict:
    """Load ingestion config from YAML, expanding env vars."""
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    # Expand ${ENV_VAR} patterns
    def _expand(match):
        var = match.group(1)
        return os.environ.get(var, match.group(0))

    raw = re.sub(r'\$\{(\w+)\}', _expand, raw)
    return yaml.safe_load(raw)


# ── SQLite state tracking ────────────────────────────────────────────────

def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Initialize SQLite DB for poll state tracking."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS poll_state (
            sub TEXT PRIMARY KEY,
            last_polled_utc TEXT,
            last_post_id TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_posts (
            post_id TEXT PRIMARY KEY,
            sub TEXT,
            title TEXT,
            url TEXT,
            score INTEGER,
            pipeline TEXT,
            processed_at TEXT,
            result TEXT
        )
    """)
    conn.commit()
    return conn


def get_last_polled(conn: sqlite3.Connection, sub: str) -> str | None:
    """Get the last-polled post ID for a sub."""
    row = conn.execute(
        "SELECT last_post_id FROM poll_state WHERE sub = ?", (sub,)
    ).fetchone()
    return row[0] if row else None


def set_last_polled(conn: sqlite3.Connection, sub: str, post_id: str):
    """Update last-polled state for a sub."""
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO poll_state (sub, last_polled_utc, last_post_id)
        VALUES (?, ?, ?)
        ON CONFLICT(sub) DO UPDATE SET
            last_polled_utc = excluded.last_polled_utc,
            last_post_id = excluded.last_post_id
    """, (sub, now, post_id))
    conn.commit()


def is_seen(conn: sqlite3.Connection, post_id: str) -> bool:
    """Check if we've already processed this post."""
    row = conn.execute(
        "SELECT 1 FROM seen_posts WHERE post_id = ?", (post_id,)
    ).fetchone()
    return row is not None


def mark_seen(conn: sqlite3.Connection, post_id: str, sub: str,
              title: str, url: str, score: int, pipeline: str, result: str):
    """Mark a post as processed."""
    conn.execute("""
        INSERT OR IGNORE INTO seen_posts
        (post_id, sub, title, url, score, pipeline, processed_at, result)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (post_id, sub, title, url, score, pipeline,
          datetime.now(timezone.utc).isoformat(), result))
    conn.commit()


# ── Post filtering ────────────────────────────────────────────────────────

def matches_filters(post: dict, source: dict) -> bool:
    """Check if a post matches the source's filter criteria.

    Args:
        post: dict with keys: title, selftext, score, link_flair_text, url
        source: dict from config sources list
    """
    # Min score
    if post.get("score", 0) < source.get("min_score", 0):
        return False

    # Flair filter (if specified, post must match one)
    required_flairs = source.get("flairs", [])
    if required_flairs:
        post_flair = (post.get("link_flair_text") or "").strip()
        if not any(f.lower() in post_flair.lower() for f in required_flairs):
            return False

    # Keyword filter (if specified, post must contain at least one)
    keywords = source.get("keywords", [])
    if keywords:
        combined = (post.get("title", "") + " " + post.get("selftext", "")).lower()
        if not any(kw.lower() in combined for kw in keywords):
            return False

    # Academic filter
    if source.get("require_academic", False):
        combined = (
            post.get("title", "") + " " +
            post.get("selftext", "") + " " +
            post.get("url", "")
        )
        if not is_academic(combined):
            return False

    return True


# ── Pipeline routing ──────────────────────────────────────────────────────

def route_to_reaction(post: dict, source: dict, config: dict):
    """Route a post to the reaction pipeline (alert human)."""
    from .alerter import Alerter

    alerter = Alerter(config=config)
    alert = {
        "type": "reaction_opportunity",
        "sub": source["sub"],
        "title": post["title"],
        "url": post["url"],
        "score": post.get("score", 0),
        "template": source.get("template"),
        "responder": source.get("responder"),
        "post_id": post["id"],
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }
    alerter.send(alert)
    return "alerted"


def route_to_ingestion(post: dict, source: dict, config: dict):
    """Route a post to the ingestion pipeline (extract GA)."""
    from .ga_extractor import extract_ga_from_url
    from .dedup import ImageDedup

    url = post.get("url", "")
    if not url:
        logger.warning(f"Post {post['id']} has no URL, skipping ingestion")
        return "no_url"

    # Try to extract GA from the linked URL
    try:
        result = extract_ga_from_url(url)
    except Exception as e:
        logger.warning(f"GA extraction failed for {url}: {e}")
        return f"extraction_failed: {e}"

    if result is None:
        logger.info(f"No GA found at {url}")
        return "no_ga_found"

    image_bytes = result["image_bytes"]
    metadata = result["metadata"]

    # Dedup check
    dedup = ImageDedup(db_path=Path(config["ingestion"]["db_path"]))
    if dedup.is_duplicate(image_bytes):
        logger.info(f"Duplicate GA from {url}, skipping")
        return "duplicate"

    # Register in dedup DB
    dedup.register(image_bytes, url, post["id"])

    # Save to ga_library with JSON sidecar
    ga_dir = Path(BASE).parent / config["ingestion"].get("ga_library_dir", "../ga_library")
    ga_dir = ga_dir.resolve()
    ga_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename from metadata
    safe_title = re.sub(r'[^\w\s-]', '', metadata.get("title", "untitled")[:60])
    safe_title = re.sub(r'\s+', '_', safe_title).strip('_').lower()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    base_name = f"reddit_{source['sub']}_{safe_title}_{timestamp}"

    # Determine extension from content type
    ext = "png"
    if metadata.get("content_type"):
        ct = metadata["content_type"]
        if "jpeg" in ct or "jpg" in ct:
            ext = "jpg"
        elif "webp" in ct:
            ext = "webp"

    img_path = ga_dir / f"{base_name}.{ext}"
    json_path = ga_dir / f"{base_name}.json"

    # Write image
    with open(img_path, "wb") as f:
        f.write(image_bytes)

    # Build sidecar JSON (matching existing ga_library format)
    sidecar = {
        "domain": source.get("sub", "reddit"),
        "version": base_name,
        "title": metadata.get("title", ""),
        "source": metadata.get("authors", "Reddit") if metadata.get("authors") else f"r/{source['sub']}",
        "doi": metadata.get("doi", ""),
        "figure": "Graphical Abstract",
        "is_control": False,
        "bloc": source.get("sub", "reddit"),
        "target_sub": f"r/{source['sub']}",
        "expected_archetype": "Variable",
        "reddit_post_id": post["id"],
        "reddit_url": post["url"],
        "shadow_mode": config["ingestion"].get("shadow_mode", True),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }

    # Add semantic references if we have metadata
    if metadata.get("title"):
        sidecar["semantic_references"] = {
            "L1": [w for w in metadata["title"].split()[:6] if len(w) > 3],
            "L2": [metadata.get("title", "")],
            "L3": [metadata.get("title", "")],
        }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sidecar, f, indent=2, ensure_ascii=False)

    logger.info(f"Ingested GA: {img_path}")

    # Optional: run vision scorer and archetype classification
    try:
        _score_and_classify(image_bytes, img_path.name, json_path, sidecar)
    except Exception as e:
        logger.warning(f"Scoring/classification failed (non-blocking): {e}")

    # Alert about new ingestion
    from .alerter import Alerter
    alerter = Alerter(config=config)
    alerter.send({
        "type": "ga_ingested",
        "sub": source["sub"],
        "title": post["title"],
        "url": post["url"],
        "ga_path": str(img_path),
        "shadow_mode": config["ingestion"].get("shadow_mode", True),
        "post_id": post["id"],
        "detected_at": datetime.now(timezone.utc).isoformat(),
    })

    return "ingested"


def _score_and_classify(image_bytes: bytes, filename: str,
                        json_path: Path, sidecar: dict):
    """Run vision scorer and archetype classifier on extracted GA.

    Non-blocking — failures here don't stop the ingestion pipeline.
    """
    # Import from parent package
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from vision_scorer import analyze_ga_image
    from archetype import classify_from_vision_metadata

    # Score with Gemini Vision
    result = analyze_ga_image(image_bytes, filename)
    metadata = result.get("metadata", {})

    # Classify archetype
    archetype_result = classify_from_vision_metadata(metadata)

    # Update sidecar with scores
    sidecar["vision_metadata"] = metadata
    sidecar["archetype"] = archetype_result.get("archetype", "unknown")
    sidecar["archetype_confidence"] = archetype_result.get("confidence", 0)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sidecar, f, indent=2, ensure_ascii=False)

    logger.info(f"Scored+classified: {filename} -> {sidecar['archetype']}")


# ── Main poller ───────────────────────────────────────────────────────────

class RedditPoller:
    """PRAW-based Reddit poller with per-sub filtering.

    In dry-run mode, logs what it would do without making Reddit API calls.
    """

    def __init__(self, config: dict | None = None, db_path: Path | None = None):
        self.config = config or load_config()
        self.db_path = db_path or Path(
            self.config.get("ingestion", {}).get("db_path", str(DB_PATH))
        )
        if not self.db_path.is_absolute():
            self.db_path = BASE / self.db_path
        self.conn = init_db(self.db_path)
        self.dry_run = self.config.get("polling", {}).get("dry_run", True)
        self._reddit = None

    @property
    def reddit(self):
        """Lazy-init PRAW Reddit instance."""
        if self._reddit is None:
            if self.dry_run:
                logger.info("Dry-run mode: no Reddit API connection")
                return None
            try:
                import praw
                reddit_cfg = self.config.get("reddit", {})
                self._reddit = praw.Reddit(
                    client_id=reddit_cfg.get("client_id", ""),
                    client_secret=reddit_cfg.get("client_secret", ""),
                    user_agent=reddit_cfg.get("user_agent", "GLANCE/1.0"),
                    username=reddit_cfg.get("username"),
                    password=reddit_cfg.get("password"),
                )
                logger.info(f"Connected to Reddit as {self._reddit.user.me()}")
            except ImportError:
                logger.error("praw not installed. Install with: pip install praw")
                raise
            except Exception as e:
                logger.error(f"Reddit connection failed: {e}")
                raise
        return self._reddit

    def poll_source(self, source: dict) -> list[dict]:
        """Poll a single subreddit source. Returns list of matched posts."""
        sub_name = source["sub"]
        max_posts = self.config.get("polling", {}).get("max_posts_per_poll", 25)

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would poll r/{sub_name} "
                        f"(pipeline={source['pipeline']}, "
                        f"min_score={source.get('min_score', 0)}, "
                        f"require_academic={source.get('require_academic', False)})")
            return []

        reddit = self.reddit
        if reddit is None:
            return []

        subreddit = reddit.subreddit(sub_name)
        matched = []

        try:
            for submission in subreddit.new(limit=max_posts):
                post = {
                    "id": submission.id,
                    "title": submission.title,
                    "selftext": submission.selftext or "",
                    "url": submission.url,
                    "score": submission.score,
                    "link_flair_text": submission.link_flair_text,
                    "created_utc": submission.created_utc,
                    "permalink": f"https://reddit.com{submission.permalink}",
                    "num_comments": submission.num_comments,
                }

                # Skip already-seen posts
                if is_seen(self.conn, post["id"]):
                    continue

                # Apply filters
                if matches_filters(post, source):
                    matched.append(post)
                    logger.info(f"Matched: r/{sub_name} — {post['title'][:80]}")

        except Exception as e:
            logger.error(f"Error polling r/{sub_name}: {e}")

        return matched

    def process_matches(self, matches: list[dict], source: dict):
        """Route matched posts to appropriate pipeline."""
        pipeline = source.get("pipeline", "ingestion")

        for post in matches:
            try:
                if pipeline == "reaction":
                    result = route_to_reaction(post, source, self.config)
                else:
                    result = route_to_ingestion(post, source, self.config)

                mark_seen(self.conn, post["id"], source["sub"],
                          post["title"], post["url"], post.get("score", 0),
                          pipeline, result)
                logger.info(f"Processed: {post['id']} -> {result}")

            except Exception as e:
                logger.error(f"Error processing {post['id']}: {e}")
                mark_seen(self.conn, post["id"], source["sub"],
                          post["title"], post["url"], post.get("score", 0),
                          pipeline, f"error: {e}")

    def poll_all(self, sub_filter: str | None = None):
        """Poll all configured sources (or just one if sub_filter is set)."""
        sources = self.config.get("sources", [])

        for source in sources:
            if sub_filter and source["sub"] != sub_filter:
                continue

            logger.info(f"Polling r/{source['sub']}...")
            matches = self.poll_source(source)

            if matches:
                self.process_matches(matches, source)
                # Update last-polled with most recent post
                set_last_polled(self.conn, source["sub"], matches[0]["id"])

            logger.info(f"r/{source['sub']}: {len(matches)} matches")

    def run_loop(self, sub_filter: str | None = None):
        """Run continuous polling loop."""
        interval = self.config.get("polling", {}).get("interval_seconds", 300)
        logger.info(f"Starting poll loop (interval={interval}s, "
                    f"dry_run={self.dry_run})")

        while True:
            try:
                self.poll_all(sub_filter=sub_filter)
            except KeyboardInterrupt:
                logger.info("Poll loop stopped by user")
                break
            except Exception as e:
                logger.error(f"Poll cycle error: {e}")

            logger.info(f"Sleeping {interval}s until next poll...")
            try:
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Poll loop stopped by user")
                break


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="GLANCE Reddit Poller — monitor subreddits for GA opportunities"
    )
    parser.add_argument("--once", action="store_true",
                        help="Poll once and exit (no loop)")
    parser.add_argument("--sub", type=str, default=None,
                        help="Only poll this specific subreddit")
    parser.add_argument("--dry-run", action="store_true",
                        help="Force dry-run mode (no Reddit API)")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to config YAML")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config_path = Path(args.config) if args.config else CONFIG_PATH
    config = load_config(config_path)

    if args.dry_run:
        config.setdefault("polling", {})["dry_run"] = True

    poller = RedditPoller(config=config)

    if args.once:
        poller.poll_all(sub_filter=args.sub)
    else:
        poller.run_loop(sub_filter=args.sub)


if __name__ == "__main__":
    main()
