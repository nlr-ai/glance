"""SciSense Telegram Bot — GA analysis via chat commands."""

import os
import json
import time
import logging
import requests
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [TG] %(message)s")
log = logging.getLogger("tg_bot")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ENV = os.path.join(_HERE, ".env")
if os.path.exists(_ENV):
    with open(_ENV) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)

TOKEN = os.environ.get("TG_BOT_TOKEN", "")
API = f"https://api.telegram.org/bot{TOKEN}"
GLANCE_URL = os.environ.get("GLANCE_URL", "https://glance.scisense.fr")

# ── Per-chat state (in-memory, resets on restart) ──
chat_state = {}  # chat_id -> {"ga_slug": ..., "ga_id": ..., "last_command": ...}


COMMANDS = {
    "/start": "Message de bienvenue",
    "/help": "Liste des commandes",
    "/analyze": "Analyser un GA (envoyer une image)",
    "/vision": "Re-analyser le GA (Gemini Vision)",
    "/channels": "Analyser les 70 canaux visuels",
    "/advise": "Demander des améliorations (+ intention)",
    "/duck": "Explorer le GA créativement (+ question)",
    "/health": "Vérifier les routes de transmission",
    "/sim": "Simuler la lecture (System 1 — 5s)",
    "/improve": "Auto-améliorer (1 tour complet)",
    "/search": "Chercher un GA dans la library",
    "/status": "Statut du service",
}


def send(chat_id, text, parse_mode="Markdown", reply_to=None):
    """Send a message."""
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    try:
        resp = requests.post(f"{API}/sendMessage", json=payload, timeout=10)
        return resp.json()
    except Exception as e:
        log.error(f"Send failed: {e}")
        return {}


def set_commands():
    """Register bot commands menu with Telegram."""
    cmds = [{"command": k.lstrip("/"), "description": v} for k, v in COMMANDS.items()]
    requests.post(f"{API}/setMyCommands", json={"commands": cmds})
    log.info(f"Registered {len(cmds)} commands")


def get_state(chat_id):
    return chat_state.get(chat_id, {})


def set_state(chat_id, **kwargs):
    if chat_id not in chat_state:
        chat_state[chat_id] = {}
    chat_state[chat_id].update(kwargs)


def call_tool(tool_name, ga_slug, text_input=None):
    """Call a GLANCE tool endpoint."""
    url = f"{GLANCE_URL}/analyze/tool/{tool_name}/{ga_slug}"
    body = {"text": text_input} if text_input else {}
    try:
        resp = requests.post(url, json=body, timeout=120)
        if resp.status_code == 200:
            return resp.json()
        return {"error": resp.json().get("detail", f"HTTP {resp.status_code}")}
    except Exception as e:
        return {"error": str(e)}


def call_improve(ga_slug):
    """Call the improve endpoint."""
    url = f"{GLANCE_URL}/analyze/improve/{ga_slug}"
    try:
        resp = requests.post(url, timeout=120)
        if resp.status_code == 200:
            return resp.json()
        return {"error": resp.json().get("detail", f"HTTP {resp.status_code}")}
    except Exception as e:
        return {"error": str(e)}


def search_ga(query):
    """Search GA library by name."""
    from db import get_db
    db = get_db()
    rows = db.execute(
        "SELECT slug, title, filename FROM ga_images WHERE title LIKE ? OR filename LIKE ? LIMIT 10",
        (f"%{query}%", f"%{query}%")
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def format_tool_result(tool, data):
    """Format a tool result as Telegram message."""
    if "error" in data:
        return f"*Erreur ({tool}):* {data['error']}"

    if tool == "vision":
        return (f"*Vision* — Graph #{data.get('graph_id')}\n"
                f"Nodes: {data.get('node_count')} | Links: {data.get('link_count')}\n"
                f"Mots: {data.get('word_count')} | Hierarchie: {'oui' if data.get('hierarchy_clear') else 'non'}\n"
                f"_{data.get('summary', '')}_")

    elif tool == "channels":
        txt = (f"*Channels* — {data.get('channels_used')}/{data.get('channels_total')} utilises\n"
               f"Avg effectiveness: {data.get('avg_effectiveness', 0):.0%}\n"
               f"Anti-patterns: {data.get('anti_pattern_count', 0)}")
        for ap in data.get("anti_patterns", [])[:5]:
            txt += f"\n  - {ap.get('type')}: {ap.get('node')} — {ap.get('issue', '')[:60]}"
        return txt

    elif tool == "advise":
        if data.get("action") == "no_changes":
            return f"*Advise* — {data.get('message', 'Aucun changement.')}"
        txt = f"*Advise* — {data.get('n_changes', 0)} changements"
        for c in data.get("changes", [])[:5]:
            txt += f"\n  - *{c.get('node')}*: {c.get('change', '')[:60]}"
        return txt

    elif tool == "rubber_duck":
        return f"*Duck* — Q: _{data.get('question')}_\n\n{data.get('response', '')[:2000]}"

    elif tool == "health":
        score = data.get("overall_score", 0)
        return (f"*Health* — Score: {score:.0%}\n"
                f"Spaces: {data.get('n_spaces')} | Things: {data.get('n_things')} | Narratives: {data.get('n_narratives')}\n"
                f"Orphan things: {len(data.get('orphan_things', []))} | Orphan spaces: {len(data.get('orphan_spaces', []))}")

    elif tool == "reader_sim":
        txt = (f"*Lecture simulee* — {data.get('verdict')}\n"
               f"Pression: {data.get('pressure', 0):.2f}x | "
               f"Visites: {data.get('visited')}/{data.get('total')} | "
               f"Couverture: {data.get('narrative_coverage', 0):.0%}\n"
               f"Zones mortes: {data.get('dead_spaces', 0)} | Orphelins: {data.get('orphan_narratives', 0)}")
        narr = data.get("narrative_text", "")
        if narr:
            txt += f"\n\n_{narr[:1500]}_"
        return txt

    elif tool == "improve":
        if data.get("action") == "initial_analysis":
            return f"*Analyse initiale* — {data.get('message')}"
        txt = f"*Auto-amelioration* — {data.get('n_changes', 0)} changements"
        for c in data.get("changes", [])[:5]:
            txt += f"\n  - *{c.get('node')}*: {c.get('change', '')[:60]}"
        if data.get("sim_s1"):
            s = data["sim_s1"]
            txt += f"\n\n{s.get('verdict')} — couverture {(s.get('narrative_coverage') or 0):.0%}"
        return txt

    return f"*{tool}*\n```\n{json.dumps(data, indent=2, ensure_ascii=False)[:1500]}\n```"


def handle_message(msg):
    """Route incoming messages to the right handler."""
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()
    user = msg.get("from", {})
    username = user.get("username", user.get("first_name", "?"))
    msg_id = msg.get("message_id")

    log.info(f"@{username} ({chat_id}): {text[:80]}")
    state = get_state(chat_id)
    slug = state.get("ga_slug")

    # ── Commands ──

    if text.startswith("/start"):
        send(chat_id,
             "*Bienvenue sur SciSense GLANCE*\n\n"
             "Envoyez-moi un Graphical Abstract (image) et je l'analyserai.\n\n"
             "Tapez /help pour voir toutes les commandes.")
        return

    if text.startswith("/help"):
        lines = ["*Commandes disponibles:*\n"]
        for cmd, desc in COMMANDS.items():
            lines.append(f"{cmd} — {desc}")
        if slug:
            lines.append(f"\n_GA actif: {slug}_")
        else:
            lines.append(f"\n_Aucun GA actif — envoyez une image ou /search_")
        send(chat_id, "\n".join(lines))
        return

    if text.startswith("/status"):
        send(chat_id, f"*GLANCE* est en ligne\nSite: {GLANCE_URL}\nBot: @scisense\\_bot")
        return

    if text.startswith("/search"):
        query = text.replace("/search", "").strip()
        if not query:
            send(chat_id, "Usage: `/search immunomod`", reply_to=msg_id)
            return
        results = search_ga(query)
        if not results:
            send(chat_id, f"Aucun GA trouve pour '{query}'.")
            return
        lines = [f"*Resultats pour '{query}':*\n"]
        for r in results:
            title = r.get("title", r.get("filename", "?"))[:50]
            s = r.get("slug", "")
            lines.append(f"  `{s}` — {title}")
        lines.append(f"\nPour selectionner: `/analyze {results[0]['slug']}`")
        send(chat_id, "\n".join(lines))
        return

    if text.startswith("/analyze"):
        arg = text.replace("/analyze", "").strip()
        if arg:
            # Select existing GA by slug
            set_state(chat_id, ga_slug=arg)
            send(chat_id, f"GA actif: `{arg}`\nUtilisez /vision, /channels, /sim, etc.", reply_to=msg_id)
        else:
            send(chat_id, "Envoyez une image de GA, ou `/analyze <slug>` pour selectionner un existant.", reply_to=msg_id)
        return

    # ── Tool commands (require active GA) ──

    tool_map = {
        "/vision": ("vision", False),
        "/channels": ("channels", False),
        "/advise": ("advise", True),
        "/duck": ("rubber_duck", True),
        "/health": ("health", False),
        "/sim": ("reader_sim", False),
    }

    for cmd, (tool, needs_text) in tool_map.items():
        if text.startswith(cmd):
            if not slug:
                send(chat_id, "Aucun GA actif. Envoyez une image ou `/analyze <slug>`.", reply_to=msg_id)
                return
            text_input = text.replace(cmd, "").strip() if needs_text else None
            if needs_text and not text_input:
                placeholder = "intention d'amelioration" if tool == "advise" else "question"
                send(chat_id, f"Usage: `{cmd} <{placeholder}>`", reply_to=msg_id)
                return
            send(chat_id, f"_{tool} en cours..._", reply_to=msg_id)
            result = call_tool(tool, slug, text_input)
            send(chat_id, format_tool_result(tool, result))
            return

    if text.startswith("/improve"):
        if not slug:
            send(chat_id, "Aucun GA actif. Envoyez une image ou `/analyze <slug>`.", reply_to=msg_id)
            return
        send(chat_id, "_Auto-amelioration en cours..._", reply_to=msg_id)
        result = call_improve(slug)
        send(chat_id, format_tool_result("improve", result))
        return

    # ── Photo upload ──
    if "photo" in msg:
        send(chat_id,
             "Image recue. L'analyse via Telegram arrive bientot.\n"
             f"En attendant: {GLANCE_URL}/analyze", reply_to=msg_id)
        return

    # ── Free text → route to advise or duck if GA is active ──
    if slug and text and not text.startswith("/"):
        # Heuristic: questions → duck, statements → advise
        if "?" in text or text.lower().startswith(("qu", "comment", "pourquoi", "est-ce")):
            send(chat_id, "_Exploration en cours..._", reply_to=msg_id)
            result = call_tool("rubber_duck", slug, text)
            send(chat_id, format_tool_result("rubber_duck", result))
        else:
            send(chat_id, "_Analyse de votre intention..._", reply_to=msg_id)
            result = call_tool("advise", slug, text)
            send(chat_id, format_tool_result("advise", result))
        return

    # ── Fallback ──
    send(chat_id, "Tapez /help pour voir les commandes.", reply_to=msg_id)


def poll():
    """Long-poll for updates."""
    set_commands()
    offset = 0
    log.info("Bot @scisense_bot listening...")

    while True:
        try:
            resp = requests.get(f"{API}/getUpdates", params={
                "offset": offset,
                "timeout": 30,
            }, timeout=35)
            data = resp.json()

            if not data.get("ok"):
                log.warning(f"API error: {data}")
                time.sleep(5)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                if "message" in update:
                    try:
                        handle_message(update["message"])
                    except Exception as e:
                        log.error(f"Handler error: {e}")

        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            log.error(f"Poll error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: TG_BOT_TOKEN not set")
        exit(1)
    poll()
