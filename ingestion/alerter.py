"""Send alerts for reaction opportunities and ingestion events.

Currently supports:
    - JSON lines file (alerts.jsonl) — always on
    - stdout printing — configurable
    - Telegram bot API — planned, not yet active
    - Weekly report generation

All posting is HUMAN ONLY — this pipeline NEVER posts to Reddit automatically.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BASE = Path(__file__).parent
DEFAULT_ALERTS_PATH = BASE / "alerts.jsonl"


class Alerter:
    """Multi-channel alert dispatcher."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        alerts_cfg = self.config.get("alerts", {})
        ingestion_cfg = self.config.get("ingestion", {})

        self.stdout_enabled = alerts_cfg.get("stdout", True)
        self.jsonl_enabled = alerts_cfg.get("jsonl", True)
        self.telegram_enabled = alerts_cfg.get("telegram_enabled", False)
        self.telegram_chat_id = alerts_cfg.get("telegram_chat_id")

        alerts_path = ingestion_cfg.get("alerts_path", str(DEFAULT_ALERTS_PATH))
        self.alerts_path = Path(alerts_path)
        if not self.alerts_path.is_absolute():
            self.alerts_path = BASE / self.alerts_path

    def send(self, alert: dict):
        """Dispatch an alert to all enabled channels.

        Args:
            alert: dict with at minimum:
                - type: "reaction_opportunity" | "ga_ingested" | "weekly_report"
                - sub: subreddit name
                - title: post title
                Plus any additional context fields.
        """
        # Ensure timestamp
        if "timestamp" not in alert:
            alert["timestamp"] = datetime.now(timezone.utc).isoformat()

        # JSONL file
        if self.jsonl_enabled:
            self._write_jsonl(alert)

        # stdout
        if self.stdout_enabled:
            self._print_alert(alert)

        # Telegram
        if self.telegram_enabled:
            self._send_telegram(alert)

    def _write_jsonl(self, alert: dict):
        """Append alert to JSONL file."""
        try:
            with open(self.alerts_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write alert to {self.alerts_path}: {e}")

    def _print_alert(self, alert: dict):
        """Print alert to stdout in human-readable format."""
        alert_type = alert.get("type", "unknown")
        sub = alert.get("sub", "?")
        title = alert.get("title", "?")

        if alert_type == "reaction_opportunity":
            template = alert.get("template", "?")
            responder = alert.get("responder", "?")
            score = alert.get("score", 0)
            url = alert.get("url", "")
            print(
                f"\n{'='*70}\n"
                f"  REACTION OPPORTUNITY\n"
                f"  Sub: r/{sub} | Score: {score}\n"
                f"  Title: {title}\n"
                f"  URL: {url}\n"
                f"  Template: {template} | Responder: {responder}\n"
                f"{'='*70}\n"
            )
        elif alert_type == "ga_ingested":
            ga_path = alert.get("ga_path", "?")
            shadow = alert.get("shadow_mode", True)
            url = alert.get("url", "")
            print(
                f"\n{'='*70}\n"
                f"  GA INGESTED {'(SHADOW)' if shadow else '(LIVE)'}\n"
                f"  Sub: r/{sub}\n"
                f"  Title: {title}\n"
                f"  URL: {url}\n"
                f"  Saved: {ga_path}\n"
                f"{'='*70}\n"
            )
        elif alert_type == "weekly_report":
            print(
                f"\n{'='*70}\n"
                f"  WEEKLY REPORT\n"
                f"  {json.dumps(alert, indent=2)}\n"
                f"{'='*70}\n"
            )
        else:
            print(f"[ALERT] {alert_type}: {json.dumps(alert)}")

    def _send_telegram(self, alert: dict):
        """Send alert via Telegram Bot API."""
        import os

        if not self.telegram_chat_id:
            logger.warning("Telegram enabled but no chat_id configured")
            return

        bot_token = os.environ.get("TG_BOT_TOKEN", "")
        if not bot_token:
            logger.warning("TG_BOT_TOKEN not set, skipping Telegram alert")
            return

        # Format message
        alert_type = alert.get("type", "unknown")
        sub = alert.get("sub", "?")
        title = alert.get("title", "?")
        url = alert.get("url", "")

        if alert_type == "reaction_opportunity":
            template = alert.get("template", "?")
            msg = (
                f"*GLANCE Reaction Opportunity*\n\n"
                f"r/{sub} | Score: {alert.get('score', 0)}\n"
                f"{title}\n\n"
                f"Template: {template}\n"
                f"{url}"
            )
        elif alert_type == "ga_ingested":
            shadow = alert.get("shadow_mode", True)
            msg = (
                f"*GLANCE GA Ingested* {'(shadow)' if shadow else '(live)'}\n\n"
                f"r/{sub}\n"
                f"{title}\n\n"
                f"{url}"
            )
        else:
            msg = f"*GLANCE Alert*\n{json.dumps(alert, indent=2)}"

        try:
            import requests
            resp = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": self.telegram_chat_id,
                    "text": msg,
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                logger.info(f"[TELEGRAM] Alert sent to {self.telegram_chat_id}")
            else:
                logger.warning(f"[TELEGRAM] Send failed ({resp.status_code}): {resp.text[:200]}")
        except Exception as e:
            logger.error(f"[TELEGRAM] Send error: {e}")

    def generate_weekly_report(self) -> dict:
        """Generate a weekly summary from the alerts JSONL file.

        Returns:
            dict with counts and details of the past week's activity.
        """
        report = {
            "type": "weekly_report",
            "period_end": datetime.now(timezone.utc).isoformat(),
            "reactions_detected": 0,
            "gas_ingested": 0,
            "duplicates_skipped": 0,
            "subs_active": set(),
            "top_posts": [],
        }

        if not self.alerts_path.exists():
            return report

        try:
            with open(self.alerts_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        alert = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    alert_type = alert.get("type", "")
                    if alert_type == "reaction_opportunity":
                        report["reactions_detected"] += 1
                    elif alert_type == "ga_ingested":
                        report["gas_ingested"] += 1

                    sub = alert.get("sub")
                    if sub:
                        report["subs_active"].add(sub)
        except Exception as e:
            logger.error(f"Error reading alerts file: {e}")

        # Convert set to list for JSON serialization
        report["subs_active"] = sorted(report["subs_active"])

        return report
