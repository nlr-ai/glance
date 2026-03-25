"""GLANCE Reddit Auto-Ingest Runner.

Unified pipeline that:
1. Polls configured subreddits for posts with images
2. Downloads GA images from posts (i.redd.it, imgur, direct image URLs)
3. Deduplicates via SHA-256 (check against ga_images.image_hash in DB)
4. For new GAs: save to ga_library/reddit/, create ga_images DB entry,
   call save_graph() which auto-triggers sim + health + overlay
5. Sends Telegram alert for each new GA found

Rate limits: 2s between Reddit API calls, 6s between Gemini calls.

CLI:
    python -m ingestion.run_ingest --subreddit dataisugly --limit 10
    python -m ingestion.run_ingest --all --limit 5
"""

import os
import re
import sys
import time
import hashlib
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Ensure parent dir is on path for imports (vision_scorer, db, etc.)
GLANCE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GLANCE_ROOT))

logger = logging.getLogger("ingest")

# ── .env loading ─────────────────────────────────────────────────────────

_env_path = GLANCE_ROOT / ".env"
if _env_path.exists():
    with open(_env_path, encoding="utf-8") as _ef:
        for _line in _ef:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                k, v = _line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# ── Constants ────────────────────────────────────────────────────────────

REDDIT_DELAY = 2.0   # seconds between Reddit API calls
GEMINI_DELAY = 6.0   # seconds between Gemini Vision calls

IMAGE_URL_PATTERNS = [
    re.compile(r'https?://i\.redd\.it/\S+\.(png|jpg|jpeg|gif|webp)', re.I),
    re.compile(r'https?://(?:i\.)?imgur\.com/\S+\.(png|jpg|jpeg|gif|webp)', re.I),
    re.compile(r'https?://\S+\.(png|jpg|jpeg|webp)(?:\?\S*)?$', re.I),
]

# Subreddit configs — override pipeline to "image_ingest" for direct image posts
SUBREDDIT_DEFAULTS = {
    "dataisugly":        {"domain": "datavis", "is_control": True,  "min_score": 5},
    "dataisbeautiful":   {"domain": "datavis", "is_control": False, "min_score": 20},
    "medicalwriters":    {"domain": "med",     "is_control": False, "min_score": 3},
    "academicpublishing":{"domain": "sci",     "is_control": False, "min_score": 3},
    "bioinformatics":    {"domain": "bio",     "is_control": False, "min_score": 5},
}


# ── Helpers ──────────────────────────────────────────────────────────────

def _is_image_url(url: str) -> bool:
    """Check if URL points directly to an image."""
    if not url:
        return False
    for pat in IMAGE_URL_PATTERNS:
        if pat.match(url):
            return True
    return False


def _download_image(url: str, timeout: int = 30) -> bytes | None:
    """Download image bytes from URL. Returns None on failure."""
    import requests
    headers = {
        "User-Agent": "GLANCE/1.0 (reddit GA ingestion)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        ct = resp.headers.get("Content-Type", "")
        data = resp.content
        # Verify it's actually image data
        if ct.startswith("image/") or data[:8] == b'\x89PNG\r\n\x1a\n' or data[:3] == b'\xff\xd8\xff':
            if len(data) < 5000:
                logger.debug(f"Image too small ({len(data)} bytes), skipping: {url}")
                return None
            return data
        logger.debug(f"Not an image (Content-Type: {ct}): {url}")
        return None
    except Exception as e:
        logger.warning(f"Failed to download {url}: {e}")
        return None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _check_hash_in_db(image_hash: str) -> bool:
    """Check if image_hash already exists in ga_images table."""
    from db import get_db
    db = get_db()
    row = db.execute(
        "SELECT 1 FROM ga_images WHERE image_hash = ?", (image_hash,)
    ).fetchone()
    db.close()
    return row is not None


def _check_reddit_post_in_db(post_id: str) -> bool:
    """Check if a reddit post has already been ingested."""
    from db import get_db
    db = get_db()
    row = db.execute(
        "SELECT 1 FROM ga_images WHERE reddit_post_id = ?", (post_id,)
    ).fetchone()
    db.close()
    return row is not None


def _send_telegram_alert(message: str):
    """Send a Telegram alert using the bot token from .env."""
    import requests as req
    bot_token = os.environ.get("TG_BOT_TOKEN", "")
    chat_id = os.environ.get("TG_ADMIN_CHAT_ID", "")
    if not bot_token or not chat_id:
        logger.debug("TG_BOT_TOKEN or TG_ADMIN_CHAT_ID not set, skipping TG alert")
        return
    try:
        resp = req.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.warning(f"TG alert failed ({resp.status_code}): {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"TG alert error: {e}")


def _get_image_extension(data: bytes, url: str) -> str:
    """Detect image extension from magic bytes or URL."""
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return "png"
    if data[:3] == b'\xff\xd8\xff':
        return "jpg"
    if data[:4] == b'RIFF' and len(data) > 12 and data[8:12] == b'WEBP':
        return "webp"
    # Fallback: from URL
    for ext in ("png", "jpg", "jpeg", "webp", "gif"):
        if f".{ext}" in url.lower():
            return "jpg" if ext == "jpeg" else ext
    return "png"


# ── Core ingest function ─────────────────────────────────────────────────

def ingest_subreddit(subreddit: str, limit: int = 10, dry_run: bool = False) -> dict:
    """Poll a subreddit for image posts and ingest new GAs.

    Args:
        subreddit: subreddit name (without r/)
        limit: max posts to fetch
        dry_run: if True, log but don't write anything

    Returns:
        dict with counts: checked, skipped_no_image, skipped_duplicate,
        skipped_seen, ingested, errors
    """
    stats = {
        "subreddit": subreddit,
        "checked": 0,
        "skipped_no_image": 0,
        "skipped_duplicate": 0,
        "skipped_seen": 0,
        "ingested": 0,
        "scored": 0,
        "errors": 0,
    }

    # ── 1. Connect to Reddit via PRAW ────────────────────────────────
    import requests as req

    user_agent = os.environ.get("REDDIT_USER_AGENT", "GLANCE/1.0")

    sub_cfg = SUBREDDIT_DEFAULTS.get(subreddit, {"domain": "misc", "is_control": False, "min_score": 0})
    ga_dir = GLANCE_ROOT / "ga_library" / "reddit"
    ga_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Polling r/{subreddit} (limit={limit}) via public JSON API...")

    # ── 2. Fetch posts via public JSON (no credentials needed) ───────
    try:
        api_url = f"https://old.reddit.com/r/{subreddit}/new.json?limit={limit}"
        resp = req.get(api_url, headers={"User-Agent": user_agent}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        posts = [child["data"] for child in data.get("data", {}).get("children", [])]
    except Exception as e:
        logger.error(f"Failed to fetch r/{subreddit}: {e}")
        return stats

    for post in posts:
        stats["checked"] += 1
        post_id = post.get("id", "")
        title = post.get("title", "")
        url = post.get("url", "")
        score = post.get("score", 0)

        # Rate limit between Reddit API interactions
        time.sleep(REDDIT_DELAY)

        # ── 3. Filter: must be an image post ─────────────────────────
        if not _is_image_url(url):
            stats["skipped_no_image"] += 1
            logger.debug(f"  Skip (no image): {title[:60]}")
            continue

        # ── 4. Skip if post already ingested ─────────────────────────
        if _check_reddit_post_in_db(post_id):
            stats["skipped_seen"] += 1
            logger.debug(f"  Skip (seen): {post_id}")
            continue

        # ── 5. Download image ────────────────────────────────────────
        image_bytes = _download_image(url)
        if image_bytes is None:
            stats["skipped_no_image"] += 1
            continue

        # ── 6. Dedup via SHA-256 ─────────────────────────────────────
        image_hash = _sha256(image_bytes)
        if _check_hash_in_db(image_hash):
            stats["skipped_duplicate"] += 1
            logger.info(f"  Duplicate hash: {image_hash[:16]}... — {title[:50]}")
            continue

        if dry_run:
            logger.info(f"  [DRY-RUN] Would ingest: {title[:60]} ({url})")
            stats["ingested"] += 1
            continue

        # ── 7. Save image to ga_library/reddit/ ──────────────────────
        ext = _get_image_extension(image_bytes, url)
        filename = f"{subreddit}_{post_id}.{ext}"
        img_path = ga_dir / filename

        try:
            with open(img_path, "wb") as f:
                f.write(image_bytes)
            logger.info(f"  Saved: {img_path.name}")
        except Exception as e:
            logger.error(f"  Failed to save image: {e}")
            stats["errors"] += 1
            continue

        # ── 8. Create ga_images DB entry ─────────────────────────────
        try:
            from db import get_db
            db = get_db()
            # Generate slug
            from db import _generate_unique_slug
            slug = _generate_unique_slug(db, filename)

            db.execute("""
                INSERT INTO ga_images
                (filename, domain, version, is_control, title, slug,
                 source_url, ingestion_source, reddit_post_id, image_hash,
                 shadow, bloc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"reddit/{filename}",
                sub_cfg["domain"],
                f"reddit_{subreddit}",
                int(sub_cfg.get("is_control", False)),
                title[:200],
                slug,
                url,
                "reddit",
                post_id,
                image_hash,
                1,  # shadow mode — not public on leaderboard
                subreddit,
            ))
            db.commit()
            ga_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            db.close()
            logger.info(f"  DB entry created: ga_id={ga_id}, slug={slug}")
        except Exception as e:
            logger.error(f"  Failed to create DB entry: {e}")
            stats["errors"] += 1
            continue

        stats["ingested"] += 1

        # ── 9. Run vision scorer + save_graph ────────────────────────
        try:
            time.sleep(GEMINI_DELAY)  # Rate limit Gemini calls
            from vision_scorer import analyze_ga_image
            from db import save_graph

            result = analyze_ga_image(image_bytes, filename=filename)
            graph = result.get("graph")
            if graph:
                graph_id = save_graph(
                    graph, ga_image_id=ga_id,
                    graph_type="vision", source="reddit_ingest"
                )
                logger.info(f"  Graph saved: graph_id={graph_id} — auto sim+health launched")
                stats["scored"] += 1
            else:
                logger.warning(f"  Vision scorer returned no graph for {filename}")
        except Exception as e:
            logger.warning(f"  Scoring failed (non-blocking): {e}")

        # ── 10. Telegram alert ───────────────────────────────────────
        try:
            _send_telegram_alert(
                f"*New GA from r/{subreddit}*\n"
                f"{title[:120]}\n"
                f"Score: {score} | `{slug}`\n"
                f"{url}"
            )
        except Exception as e:
            logger.debug(f"  TG alert failed: {e}")

    logger.info(
        f"r/{subreddit} done: {stats['checked']} checked, "
        f"{stats['ingested']} ingested, {stats['skipped_duplicate']} dupes, "
        f"{stats['scored']} scored, {stats['errors']} errors"
    )
    return stats


def ingest_all(limit: int = 10, dry_run: bool = False) -> list[dict]:
    """Run ingestion on all configured subreddits.

    Returns list of per-subreddit stats dicts.
    """
    results = []
    for sub_name in SUBREDDIT_DEFAULTS:
        try:
            stats = ingest_subreddit(sub_name, limit=limit, dry_run=dry_run)
            results.append(stats)
        except Exception as e:
            logger.error(f"Failed to ingest r/{sub_name}: {e}")
            results.append({"subreddit": sub_name, "error": str(e)})
    return results


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="GLANCE Reddit Auto-Ingest — poll subreddits for GA images"
    )
    parser.add_argument("--subreddit", "-s", type=str, default=None,
                        help="Specific subreddit to poll (default: all configured)")
    parser.add_argument("--all", action="store_true",
                        help="Poll all configured subreddits")
    parser.add_argument("--limit", "-n", type=int, default=10,
                        help="Max posts to fetch per subreddit (default: 10)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Log what would happen without writing anything")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.subreddit:
        stats = ingest_subreddit(args.subreddit, limit=args.limit, dry_run=args.dry_run)
        print(f"\nResult: {stats}")
    elif args.all or not args.subreddit:
        results = ingest_all(limit=args.limit, dry_run=args.dry_run)
        total_ingested = sum(r.get("ingested", 0) for r in results)
        total_scored = sum(r.get("scored", 0) for r in results)
        print(f"\nAll done: {total_ingested} ingested, {total_scored} scored across {len(results)} subs")
        for r in results:
            print(f"  r/{r.get('subreddit', '?')}: {r}")


if __name__ == "__main__":
    main()
