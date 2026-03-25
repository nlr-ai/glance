"""Image deduplication via SHA-256 hash.

Prevents the same GA image from being ingested multiple times,
even if discovered from different Reddit posts or subreddits.

Uses SQLite for persistent hash storage.
"""

import hashlib
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BASE = Path(__file__).parent
DEFAULT_DB_PATH = BASE / "ingestion.db"


class ImageDedup:
    """SHA-256 based image deduplication backed by SQLite."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self._init_table()

    def _init_table(self):
        """Create the dedup table if it doesn't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ingested_images (
                hash TEXT PRIMARY KEY,
                source_url TEXT,
                reddit_post_id TEXT,
                created_at TEXT
            )
        """)
        self.conn.commit()

    @staticmethod
    def _hash(image_bytes: bytes) -> str:
        """Compute SHA-256 hash of image bytes."""
        return hashlib.sha256(image_bytes).hexdigest()

    def is_duplicate(self, image_bytes: bytes) -> bool:
        """Check if an image has already been ingested.

        Args:
            image_bytes: Raw image data

        Returns:
            True if a matching hash exists in the database
        """
        h = self._hash(image_bytes)
        row = self.conn.execute(
            "SELECT 1 FROM ingested_images WHERE hash = ?", (h,)
        ).fetchone()
        if row:
            logger.debug(f"Duplicate detected: {h[:16]}...")
            return True
        return False

    def register(self, image_bytes: bytes, source_url: str,
                 reddit_post_id: str = ""):
        """Register a new image hash in the database.

        Args:
            image_bytes: Raw image data
            source_url: URL where the image was found
            reddit_post_id: Reddit post ID that linked to this image
        """
        h = self._hash(image_bytes)
        now = datetime.now(timezone.utc).isoformat()
        try:
            self.conn.execute("""
                INSERT INTO ingested_images (hash, source_url, reddit_post_id, created_at)
                VALUES (?, ?, ?, ?)
            """, (h, source_url, reddit_post_id, now))
            self.conn.commit()
            logger.info(f"Registered image: {h[:16]}... from {source_url}")
        except sqlite3.IntegrityError:
            logger.debug(f"Hash already registered: {h[:16]}...")

    def count(self) -> int:
        """Return the number of registered images."""
        row = self.conn.execute(
            "SELECT COUNT(*) FROM ingested_images"
        ).fetchone()
        return row[0] if row else 0

    def lookup(self, image_bytes: bytes) -> dict | None:
        """Look up metadata for an image hash.

        Returns:
            dict with source_url, reddit_post_id, created_at — or None
        """
        h = self._hash(image_bytes)
        row = self.conn.execute(
            "SELECT source_url, reddit_post_id, created_at "
            "FROM ingested_images WHERE hash = ?", (h,)
        ).fetchone()
        if row:
            return {
                "hash": h,
                "source_url": row[0],
                "reddit_post_id": row[1],
                "created_at": row[2],
            }
        return None

    def close(self):
        """Close the database connection."""
        self.conn.close()
