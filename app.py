"""GLANCE Premier Regard — FastAPI server."""

GLANCE_VERSION = "0.9.1"

import os
import json
import re
import uuid
import random
import time
import logging

import yaml
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db import get_db, init_db, create_participant, get_participant_by_token
from db import get_next_image, save_test, get_test, get_stats
from db import get_all_tests, get_image_count, get_all_images, add_ga_image
from db import get_image_by_id, get_image_by_slug, get_tests_for_image, get_tests_for_participant, get_landing_stats, get_example_ga
from db import get_referral_count, get_top_referrers, save_analysis_lead
from db import get_latest_graph, get_reading_sims, save_graph
from db import create_auth_token, verify_auth_token, get_user_gas, add_designer, swap_ga_image, get_image_iteration
from scoring import score_test, classify_speed_accuracy
from analytics import (
    compute_aggregate_stats,
    compute_profile_quadrant,
    compute_stats_by_quadrant,
    compute_speed_accuracy_distribution,
    compute_ab_delta,
    compute_ab_fluency_delta,
    compute_s10_rate,
    compute_fluency_score,
    get_leaderboard_data,
    get_domain_leaderboard,
    get_ga_detail_stats,
    get_score_distributions,
    get_domain_rank,
    get_admin_analytics,
    compute_kpi_evolution,
    get_participant_percentile,
    get_participant_ranking_comprehension,
    get_participant_ranking_contribution,
)
from config_loader import get_constant
from cards import generate_test_card, generate_dashboard_card, generate_default_card, generate_ga_og_card
from i18n import t as _t, get_lang
from archetype import classify_ga, classify_from_vision_metadata, ARCHETYPES
from archetype_icons import ARCHETYPE_SVGS

BASE = os.path.dirname(__file__)

app = FastAPI(title="GLANCE — Premier Regard")
templates = Jinja2Templates(directory=os.path.join(BASE, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE, "static")), name="static")
app.mount("/ga", StaticFiles(directory=os.path.join(BASE, "ga_library")), name="ga")

# Make t() available in all Jinja2 templates as a global function
templates.env.globals["t"] = _t
templates.env.globals["archetype_svgs"] = ARCHETYPE_SVGS
templates.env.globals["GLANCE_VERSION"] = GLANCE_VERSION

with open(os.path.join(BASE, "config.yaml"), encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)


# ── i18n middleware: detect language, set cookie when ?lang= is used ──

class I18nMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        lang = get_lang(request)
        request.state.lang = lang
        response = await call_next(request)
        # Persist language choice via cookie when explicitly set via URL param
        if request.query_params.get("lang") in ("fr", "en"):
            response.set_cookie("glance_lang", request.query_params["lang"],
                                max_age=86400 * 365, httponly=True)
        # Persist referral code via cookie so it survives through onboard flow
        ref_param = request.query_params.get("ref", "")
        if ref_param and len(ref_param) <= 8:
            response.set_cookie("glance_ref", ref_param,
                                max_age=86400 * 30, httponly=True)
        return response

app.add_middleware(I18nMiddleware)


@app.on_event("startup")
def startup():
    init_db()
    _seed_images()
    # Preload semantic model to avoid slow first submission
    try:
        from semantic import load_model
        load_model()
    except Exception:
        pass  # Model loading is optional — keyword fallback works


def _seed_images():
    """Seed GA images from ga_library/ if DB is empty."""
    if get_image_count() > 0:
        return
    lib = os.path.join(BASE, "ga_library")
    for fname in os.listdir(lib):
        if fname.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            meta_path = os.path.join(lib, fname.rsplit(".", 1)[0] + ".json")
            meta = {}
            if os.path.exists(meta_path):
                with open(meta_path, encoding="utf-8") as f:
                    meta = json.load(f)
            add_ga_image(
                filename=fname,
                domain=meta.get("domain", "med"),
                version=meta.get("version"),
                is_control=meta.get("is_control", False),
                correct_product=meta.get("correct_product"),
                products=meta.get("products"),
                title=meta.get("title", fname),
                description=meta.get("description"),
            )


def _get_participant(request: Request):
    token = request.cookies.get("glance_token")
    if not token:
        return None
    return get_participant_by_token(token)


def _lang(request: Request) -> str:
    """Get language for this request (set by I18nMiddleware)."""
    return getattr(request.state, "lang", "fr")


def _resolve_ga(ga_id_or_slug: str):
    """Resolve a GA identifier — try slug first, then numeric ID fallback.

    Returns (image_dict, numeric_id) or (None, None).
    """
    # Try slug lookup first
    image = get_image_by_slug(ga_id_or_slug)
    if image:
        return image, image["id"]
    # Fallback: try parsing as numeric ID
    try:
        numeric_id = int(ga_id_or_slug)
        image = get_image_by_id(numeric_id)
        if image:
            return image, numeric_id
    except (ValueError, TypeError):
        pass
    return None, None


# ── Routes ────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    lang = _lang(request)
    landing = get_landing_stats()

    # Build domain list with labels from config
    domain_list = []
    for domain_key, n_gas in landing["domain_counts"].items():
        label = CONFIG["domains"].get(domain_key, {}).get("label", domain_key)
        domain_list.append({"key": domain_key, "label": label, "n_gas": n_gas})

    # Enrich top_gas with archetype info for score badges on cards
    for ga in landing.get("top_gas", []):
        if ga.get("avg_glance") is not None:
            sidecar_ga = _load_sidecar(ga.get("filename", ""))
            ga_scores = {
                "s10": 0.0, "s9b": 0.0, "s2_coverage": 0.0,
                "drift": 0.0, "warp": 0.0,
                "word_count": sidecar_ga.get("word_count", 0),
                "spin_detected": False,
            }
            # Try to get real test stats for richer classification
            try:
                ga_detail = get_ga_detail_stats(ga["id"])
                ga_scores["s10"] = ga_detail.get("avg_s9a", 0.0)
                ga_scores["s9b"] = ga_detail.get("avg_s9b", 0.0)
                ga_scores["s2_coverage"] = ga_detail.get("avg_s2_coverage", 0.0)
            except Exception:
                pass
            arch_result = classify_ga(ga_scores)
            ga["archetype"] = arch_result["archetype"]
            ga["archetype_info"] = arch_result["archetype_info"]
            ga["archetype_source"] = "measured"
        else:
            ga["archetype"] = None
            ga["archetype_info"] = None
            ga["archetype_source"] = None

    # Example GA analysis for the demo section
    example = _build_example_data()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "lang": lang,
        "landing": landing,
        "domain_list": domain_list,
        "example": example,
        "og_title": "GLANCE — Testez votre oeil scientifique en 2 minutes",
        "og_description": "47 GAs, 15 domaines. Le premier benchmark de compréhension des Graphical Abstracts. Gratuit.",
    })


def _build_example_data() -> dict:
    """Build example GA analysis data for the landing page demo section.

    Tries to load real data from the GA with the most tests.
    Falls back to hardcoded example values if no test data exists.
    """
    from scoring import score_glance_composite

    fallback = {
        "has_real_data": False,
        "ga_filename": "immunomod_v10_wireframe.png",
        "ga_title": "Immunomodulateurs RTIs",
        "ga_id": None,
        "ga_domain": "med",
        "n_tests": 12,
        "s9a": 0.67,
        "s9b": 0.17,
        "s9c": 0.0,
        "fluency": 0.22,
        "s2_coverage": 0.58,
        "glance": 0.0,
        "recommendation": "Remplacez les surfaces par des barres — vos lecteurs comprendront ~20% mieux.",
    }
    fallback["glance"] = round(score_glance_composite(
        fallback["s9a"], fallback["s9b"], fallback["s9c"]
    ), 4)

    try:
        example_ga = get_example_ga()
    except Exception:
        return fallback

    if not example_ga or example_ga.get("n_tests", 0) == 0:
        return fallback

    ga_id = example_ga["id"]
    detail = get_ga_detail_stats(ga_id)
    if detail.get("n_tests", 0) == 0:
        return fallback

    s9b_val = detail.get("avg_s9b", 0)
    s9c_val = detail.get("avg_s9c", 0)
    glance_val = detail.get("avg_glance", 0)

    if s9b_val < 0.5:
        reco = "Le produit principal n'est pas identifie — simplifiez la hierarchie visuelle."
    elif s9c_val < 0.3:
        reco = "L'insight cle se perd — ajoutez un element de preuve visuel."
    elif glance_val < 0.7:
        reco = "Le message passe partiellement — reduisez la charge cognitive du design."
    else:
        reco = "Ce GA communique efficacement — bon equilibre entre clarte et densite."

    return {
        "has_real_data": True,
        "ga_filename": example_ga.get("filename", ""),
        "ga_title": example_ga.get("title", ""),
        "ga_id": ga_id,
        "ga_domain": example_ga.get("domain", "med"),
        "n_tests": detail.get("n_tests", 0),
        "s9a": round(detail.get("avg_s9a", 0), 2),
        "s9b": round(detail.get("avg_s9b", 0), 2),
        "s9c": round(detail.get("avg_s9c", 0), 2),
        "fluency": round(detail.get("fluency_normalized", detail.get("avg_fluency", 0)), 2),
        "s2_coverage": round(detail.get("avg_s2_coverage", 0), 2),
        "glance": round(glance_val, 4),
        "recommendation": reco,
    }


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    lang = _lang(request)
    return templates.TemplateResponse("privacy.html", {
        "request": request,
        "lang": lang,
        "og_title": "Politique de confidentialité — GLANCE",
        "og_description": "Comment GLANCE protège vos données. Aucun nom, email ou IP collecté.",
    })


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request):
    lang = _lang(request)
    return templates.TemplateResponse("terms.html", {
        "request": request,
        "lang": lang,
        "og_title": "Conditions d'utilisation — GLANCE",
        "og_description": "Conditions d'utilisation de la plateforme GLANCE par SciSense.",
    })


# ── Auth (magic link) ─────────────────────────────────────────────────


def _get_glance_user(request: Request) -> str | None:
    """Return the logged-in user's email from cookie, or None."""
    return request.cookies.get("glance_user")


@app.get("/auth/login", response_class=HTMLResponse)
def auth_login(request: Request):
    lang = _lang(request)
    sent = request.query_params.get("sent", "")
    error = request.query_params.get("error", "")
    return templates.TemplateResponse("auth_login.html", {
        "request": request,
        "lang": lang,
        "glance_user": _get_glance_user(request),
        "sent": sent,
        "error": error,
        "og_title": "Connexion — GLANCE",
        "og_description": "Connectez-vous a GLANCE pour retrouver vos Graphical Abstracts.",
    })


@app.post("/auth/send-link")
async def auth_send_link(request: Request, email: str = Form(...)):
    """Generate a magic link token and send it via Telegram + console."""
    email = email.strip().lower()
    if not email or "@" not in email:
        return RedirectResponse(url="/auth/login?error=email", status_code=303)

    token = create_auth_token(email)
    base_url = os.environ.get("GLANCE_BASE_URL", "https://glance.scisense.fr")
    magic_link = f"{base_url}/auth/verify?token={token}"

    # Always log to console
    logger = logging.getLogger("auth")
    logger.info(f"[AUTH] Magic link for {email}: {magic_link}")

    # Send via Telegram if bot token is available
    tg_bot_token = os.environ.get("TG_BOT_TOKEN", "")
    tg_chat_id = os.environ.get("TG_ADMIN_CHAT_ID", "")
    if tg_bot_token and tg_chat_id:
        try:
            import urllib.request
            tg_payload = json.dumps({
                "chat_id": tg_chat_id,
                "text": f"GLANCE login link for {email}:\n{magic_link}",
                "parse_mode": "HTML",
            }).encode("utf-8")
            tg_req = urllib.request.Request(
                f"https://api.telegram.org/bot{tg_bot_token}/sendMessage",
                data=tg_payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(tg_req, timeout=10)
        except Exception as e:
            logger.warning(f"TG magic link send failed: {e}")

    return RedirectResponse(url="/auth/login?sent=1", status_code=303)


@app.get("/auth/verify")
def auth_verify(request: Request, token: str = ""):
    """Verify magic link token, set session cookie, redirect to profile."""
    if not token:
        return RedirectResponse(url="/auth/login?error=missing", status_code=303)

    email = verify_auth_token(token)
    if not email:
        return RedirectResponse(url="/auth/login?error=expired", status_code=303)

    response = RedirectResponse(url="/profile", status_code=303)
    response.set_cookie(
        "glance_user",
        email,
        max_age=86400 * 30,  # 30 days
        httponly=True,
        samesite="lax",
    )
    return response


@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    lang = _lang(request)
    glance_user = _get_glance_user(request)
    if not glance_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    user_gas = get_user_gas(glance_user)

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "lang": lang,
        "glance_user": glance_user,
        "user_gas": user_gas,
        "og_title": "Mon profil — GLANCE",
        "og_description": "Retrouvez vos Graphical Abstracts analyses sur GLANCE.",
    })


@app.get("/auth/logout")
def auth_logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("glance_user")
    return response


@app.get("/pricing", response_class=HTMLResponse)
def pricing(request: Request):
    lang = _lang(request)
    return templates.TemplateResponse("pricing.html", {
        "request": request,
        "lang": lang,
        "glance_user": _get_glance_user(request),
        "og_title": "Offres GLANCE — SciSense",
        "og_description": "Du test gratuit à l'audit complet — choisissez votre niveau d'analyse GLANCE.",
    })


@app.get("/onboard", response_class=HTMLResponse)
def onboard(request: Request):
    lang = _lang(request)
    return templates.TemplateResponse("onboard.html", {
        "request": request,
        "lang": lang,
        "config": CONFIG,
        "og_title": "GLANCE — Inscription rapide",
        "og_description": "Rejoignez GLANCE : le benchmark de compréhension des Graphical Abstracts scientifiques. 2 minutes, gratuit.",
    })


@app.post("/onboard")
def onboard_submit(
    request: Request,
    clinical_domain: str = Form(...),
    experience_years: str = Form(""),
    data_literacy: str = Form(...),
    grade_familiar: int = Form(0),
    colorblind_status: str = Form("unknown"),
    input_mode: str = Form("text"),
):
    token = str(uuid.uuid4())
    # Capture referral code from query param or cookie
    ref = request.query_params.get("ref", "") or request.cookies.get("glance_ref", "")
    ref = ref.strip()[:8] if ref else None
    create_participant(token, clinical_domain, experience_years,
                       data_literacy, grade_familiar, colorblind_status,
                       input_mode=input_mode, referred_by=ref)
    lang = _lang(request)
    response = RedirectResponse(url=f"/test?lang={lang}", status_code=303)
    response.set_cookie("glance_token", token, httponly=True,
                        max_age=get_constant("cookie_max_age_seconds", 2592000))
    return response


def _load_leurres():
    """Load leurre metadata from ga_library/leurres/leurres.json."""
    leurres_path = os.path.join(BASE, "ga_library", "leurres", "leurres.json")
    if not os.path.exists(leurres_path):
        return []
    with open(leurres_path, encoding="utf-8") as f:
        data = json.load(f)
    leurres = data.get("leurres", [])
    # Handle both old format (list of strings) and new format (list of dicts)
    result = []
    for item in leurres:
        if isinstance(item, str):
            result.append({"filename": item, "title": "", "author": "", "journal": "", "likes": 0, "comments": 0})
        else:
            result.append(item)
    return result


def _build_flux_feed(target_image, flux_config):
    """Build the ordered feed for flux mode.

    Returns (feed_items, target_position_0indexed) where feed_items is
    a list of dicts with 'filename' and 'path' keys.

    Uses stratified sampling to guarantee diverse content_type representation:
    one leurre per content_type bucket first, then fill remaining slots randomly.
    """
    n_items = flux_config.get("n_items", 6)
    n_leurres = n_items - 1  # one slot is the target

    all_leurres = _load_leurres()
    if len(all_leurres) < n_leurres:
        # Not enough leurres — use what we have
        selected = all_leurres[:]
    else:
        # Stratified sampling: one per content_type bucket, then fill
        buckets = {}
        for l in all_leurres:
            ct = l.get("content_type", "paper")
            buckets.setdefault(ct, []).append(l)

        selected = []
        used_ids = set()
        # Pick one from each bucket (shuffled order)
        bucket_keys = list(buckets.keys())
        random.shuffle(bucket_keys)
        for key in bucket_keys:
            if len(selected) >= n_leurres:
                break
            pick = random.choice(buckets[key])
            selected.append(pick)
            used_ids.add(pick["filename"])

        # Fill remaining slots from all leurres (excluding already picked)
        remaining = [l for l in all_leurres if l["filename"] not in used_ids]
        if remaining and len(selected) < n_leurres:
            fill_count = n_leurres - len(selected)
            selected.extend(random.sample(remaining, min(fill_count, len(remaining))))

        # Shuffle final selection so bucket order isn't visible
        random.shuffle(selected)

    # Build leurre items (served from /ga/leurres/)
    leurre_items = [
        {
            "filename": l["filename"],
            "path": f"/ga/leurres/{l['filename']}",
            "title": l.get("title", ""),
            "author": l.get("author", ""),
            "journal": l.get("journal", ""),
            "likes": l.get("likes", 0),
            "comments": l.get("comments", 0),
            "content_type": l.get("content_type", "paper"),
            "pfp": l.get("pfp", ""),
        }
        for l in selected
    ]

    # Target item (served from /ga/)
    target_item = {
        "filename": target_image["filename"],
        "path": f"/ga/{target_image['filename']}",
        "title": target_image.get("title", ""),
        "author": "Research Team",
        "journal": "Scientific Journal",
        "likes": random.randint(30, 200),
        "comments": random.randint(5, 40),
        "content_type": "paper",
        "pfp": "",
    }

    # Determine target position
    pos_cfg = flux_config.get("target_position", "random")
    if pos_cfg == "random":
        target_pos = random.randint(0, len(leurre_items))  # 0 to n_leurres inclusive
    else:
        target_pos = max(0, min(int(pos_cfg) - 1, len(leurre_items)))

    # Insert target at position
    feed = leurre_items[:]
    feed.insert(target_pos, target_item)

    return feed, target_pos


@app.get("/test", response_class=HTMLResponse)
def test_page(request: Request):
    participant = _get_participant(request)
    if not participant:
        return RedirectResponse(url="/onboard")

    lang = _lang(request)

    image = get_next_image(participant["id"])
    if not image:
        return templates.TemplateResponse("complete.html", {"request": request, "lang": lang})

    domain = image["domain"]
    domain_cfg = CONFIG["domains"].get(domain, CONFIG["domains"]["generic"])
    # Select language-appropriate questions: use q1_en/q2_en/q3_en if EN, else default
    if lang == "en" and "q1_en" in domain_cfg:
        questions = {
            "q1": domain_cfg["q1_en"],
            "q2": domain_cfg["q2_en"],
            "q3": domain_cfg["q3_en"],
            "q3_choices": domain_cfg.get("q3_choices_en", domain_cfg["q3_choices"]),
            "label": domain_cfg.get("label_en", domain_cfg["label"]),
        }
    else:
        questions = domain_cfg
    products = json.loads(image["products"]) if image["products"] else []

    # Check if this is the participant's first test (for briefing skip)
    from db import get_db
    _db = get_db()
    test_count = _db.execute(
        "SELECT COUNT(*) as c FROM tests WHERE participant_id = ?",
        (participant["id"],)
    ).fetchone()["c"]
    _db.close()
    first_test = test_count == 0

    # Load OCR words from sidecar JSON for STT keyword hints
    ocr_words = []
    meta_path = os.path.join(BASE, "ga_library",
                             image["filename"].rsplit(".", 1)[0] + ".json")
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as mf:
            sidecar_meta = json.load(mf)
            ocr_words = sidecar_meta.get("ocr_words", [])

    # Check if flux mode is enabled
    flux_config = CONFIG.get("flux", {})
    if flux_config.get("enabled", False):
        feed_items, target_pos = _build_flux_feed(image, flux_config)

        # Build selection thumbnails: target + 2 random distractors
        distractor_filenames = [
            item["filename"] for item in feed_items
            if item["filename"] != image["filename"]
        ]
        n_distractors = min(2, len(distractor_filenames))
        selected_distractors = random.sample(distractor_filenames, n_distractors)

        selection_thumbs = [
            {"filename": image["filename"], "path": f"/ga/{image['filename']}"}
        ]
        for fname in selected_distractors:
            selection_thumbs.append(
                {"filename": fname, "path": f"/ga/leurres/{fname}"}
            )
        random.shuffle(selection_thumbs)

        return templates.TemplateResponse("test_flux.html", {
            "request": request,
            "lang": lang,
            "image": image,
            "questions": questions,
            "products": products,
            "feed_items": feed_items,
            "target_position": target_pos,
            "target_filename": image["filename"],
            "item_duration_ms": flux_config.get("item_duration_ms", 4000),
            "scroll_transition_ms": flux_config.get("scroll_transition_ms", 300),
            "selection_thumbs": selection_thumbs,
            "input_mode": participant.get("input_mode", "text"),
            "first_test": first_test,
            "show_title": flux_config.get("show_title", True),
            "ocr_words": ocr_words,
        })

    # Focused mode (original)
    return templates.TemplateResponse("test.html", {
        "request": request,
        "lang": lang,
        "image": image,
        "questions": questions,
        "products": products,
        "timer_ms": CONFIG["timer"]["exposure_ms"],
        "countdown_s": CONFIG["timer"]["countdown_seconds"],
        "input_mode": participant.get("input_mode", "text"),
        "ocr_words": ocr_words,
    })


@app.post("/submit")
def submit_test(
    request: Request,
    ga_image_id: int = Form(...),
    q1_text: str = Form(""),
    q1_time_ms: int = Form(0),
    q2_choice: str = Form(""),
    q2_time_ms: int = Form(0),
    q3_choice: str = Form(""),
    q3_time_ms: int = Form(0),
    q4_text: str = Form(""),
    tab_switched: int = Form(0),
    exposure_actual_ms: int = Form(0),
    q1_first_keystroke_ms: int = Form(0),
    q1_last_keystroke_ms: int = Form(0),
    exposure_mode: str = Form("spotlight"),
    stream_position: int = Form(0),
    stream_length: int = Form(0),
    stream_selected_id: str = Form(""),
    target_filename: str = Form(""),
    q1_input_mode: str = Form("text"),
    q1_raw_transcript: str = Form(""),
    screen_width: int = Form(0),
    screen_height: int = Form(0),
    device_pixel_ratio: float = Form(0.0),
    user_agent: str = Form(""),
    stream_target_dwell_ms: int = Form(0),
):
    participant = _get_participant(request)
    if not participant:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Score
    from db import get_db
    db = get_db()
    image = db.execute("SELECT * FROM ga_images WHERE id = ?", (ga_image_id,)).fetchone()
    db.close()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Build GA metadata for semantic S9a scoring
    ga_metadata = dict(image)
    if ga_metadata.get("products") and isinstance(ga_metadata["products"], str):
        ga_metadata["products"] = json.loads(ga_metadata["products"])

    # Load semantic_references from sidecar JSON if available
    meta_path = os.path.join(BASE, "ga_library",
                             image["filename"].rsplit(".", 1)[0] + ".json")
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as mf:
            sidecar = json.load(mf)
            ga_metadata.update(sidecar)

    scores = score_test(q1_text, q2_choice, q3_choice, image["correct_product"],
                        ga_metadata=ga_metadata, q1_input_mode=q1_input_mode)
    speed_acc = classify_speed_accuracy(scores["s9b"], q2_time_ms)

    # Compute s10_hit: did the participant select the target GA in the thumbnail step?
    # s10_hit = 1 if they picked the target, 0 if they picked a distractor, None if spotlight
    s10_hit = None
    if exposure_mode == "stream" and stream_selected_id:
        actual_target = target_filename or image["filename"]
        s10_hit = 1 if stream_selected_id == actual_target else 0

    # Determine if titles were shown during this test (stream nude mode)
    flux_config = CONFIG.get("flux", {})
    stream_show_title = 1 if flux_config.get("show_title", True) else 0

    test_id = save_test(
        participant["id"], ga_image_id,
        q1_text, q1_time_ms, q2_choice, q2_time_ms, q3_choice, q3_time_ms,
        scores["s9a"], scores["s9b"], scores["s9c"], q4_text,
        s9c_score=scores["s9c_score"],
        glance_score=scores["glance_score"],
        speed_accuracy=speed_acc,
        s9a_score=scores["s9a_score"],
        tab_switched=tab_switched,
        exposure_actual_ms=exposure_actual_ms or None,
        q1_first_keystroke_ms=q1_first_keystroke_ms or None,
        q1_last_keystroke_ms=q1_last_keystroke_ms or None,
        exposure_mode=exposure_mode,
        stream_position=stream_position or None,
        stream_length=stream_length or None,
        stream_selected_id=stream_selected_id or None,
        s10_hit=s10_hit,
        q1_input_mode=q1_input_mode,
        q1_raw_transcript=q1_raw_transcript or None,
        screen_width=screen_width or None,
        screen_height=screen_height or None,
        device_pixel_ratio=device_pixel_ratio or None,
        user_agent=user_agent or None,
        stream_target_dwell_ms=stream_target_dwell_ms or None,
        q1_filtered_text=scores.get("q1_filtered_text"),
        q1_filter_ratio=scores.get("q1_filter_ratio"),
        stream_show_title=stream_show_title,
        code_version=GLANCE_VERSION,
    )
    return RedirectResponse(url=f"/reveal/{test_id}", status_code=303)


@app.get("/reveal/{test_id}", response_class=HTMLResponse)
def reveal(request: Request, test_id: int):
    participant = _get_participant(request)
    if not participant:
        return RedirectResponse(url="/onboard")
    lang = _lang(request)

    test = get_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    stats = get_stats(test["ga_image_id"])
    has_more = get_next_image(participant["id"]) is not None

    # Compute GLANCE composite and speed-accuracy for this test (may be stored, but
    # also compute from raw data for tests created before the migration)
    from scoring import score_s9c_graduated, score_glance_composite
    s9c_score = test.get("s9c_score") or score_s9c_graduated(test.get("q3_choice", ""))
    glance_score = test.get("glance_score") or score_glance_composite(
        float(test.get("s9a_pass", 0)),
        float(test.get("s9b_pass", 0)),
        s9c_score,
    )
    speed_acc = test.get("speed_accuracy") or classify_speed_accuracy(
        test.get("s9b_pass", False), test.get("q2_time_ms", 0)
    )

    # Label per S2b_Mathematics.md section 7
    glance_threshold = get_constant("glance_pass_threshold", 0.70)
    glance_label = "Décodage réussi" if glance_score >= glance_threshold else "Le design n'a pas survécu au transfert"

    s9a_score = test.get("s9a_score") or 0.0

    # s10_hit: True (hit), False (miss), None (spotlight mode — treat as hit for display)
    raw_s10 = test.get("s10_hit")
    if raw_s10 is None:
        s10_hit = True  # spotlight mode: always show score card
    else:
        s10_hit = bool(raw_s10)

    # Compute fluency score for display
    fluency = compute_fluency_score(bool(test.get("s9b_pass")), test.get("q2_time_ms", 0))

    # Compute participant percentile among all testers
    participant_percentile = get_participant_percentile(participant["id"])

    # OG meta for sharing (includes percentile rank)
    score_pct = round(glance_score * 100)
    og_title = f"Mon score GLANCE : {score_pct}% — meilleur que {participant_percentile}% des testeurs"
    og_desc = (f"Mon score GLANCE : {score_pct}% — meilleur que {participant_percentile}% "
               f"des testeurs ! Teste ton oeil sur glance.scisense.fr")
    og_image = f"https://glance.scisense.fr/card/{test_id}.png"

    return templates.TemplateResponse("reveal.html", {
        "request": request,
        "lang": lang,
        "test": test,
        "stats": stats,
        "has_more": has_more,
        "glance_score": round(glance_score, 2),
        "glance_label": glance_label,
        "speed_accuracy": speed_acc,
        "s9a_score": round(float(s9a_score), 3),
        "s10_hit": s10_hit,
        "fluency_score": round(fluency, 4),
        "participant_percentile": participant_percentile,
        "og_title": og_title,
        "og_description": og_desc,
        "og_image": og_image,
    })


@app.get("/reject/{test_id}")
def reject_reason(test_id: int, reason: str = ""):
    """Store the rejection reason for an S10 miss — first-class B2B metric."""
    if reason:
        db = get_db()
        db.execute("UPDATE tests SET rejection_reason = ? WHERE id = ?", (reason, test_id))
        db.commit()
        db.close()
    return RedirectResponse(url="/test", status_code=303)


@app.get("/spin", response_class=HTMLResponse)
def spin_page(request: Request):
    """Proposition C landing: zero-friction spin reveal.

    Picks a random CONTROL GA (area/pie encoding), shows it for 5s,
    asks Q2 only, then reveals Stevens beta ~0.7 explanation with
    side-by-side comparison to the VEC bar chart version.
    """
    db = get_db()
    # Pick a random control image
    control_row = db.execute(
        "SELECT * FROM ga_images WHERE is_control = 1 ORDER BY RANDOM() LIMIT 1"
    ).fetchone()
    if not control_row:
        db.close()
        raise HTTPException(status_code=503, detail="No control images in library")
    control = dict(control_row)

    # Find the corresponding VEC version: same correct_product + domain, not control
    vec_row = db.execute(
        """SELECT * FROM ga_images
           WHERE is_control = 0
             AND correct_product = ?
             AND domain = ?
           LIMIT 1""",
        (control["correct_product"], control["domain"]),
    ).fetchone()
    db.close()

    vec = dict(vec_row) if vec_row else None
    products = json.loads(control["products"]) if control["products"] else []

    # Get the domain-specific Q2 text
    domain = control["domain"]
    questions = CONFIG["domains"].get(domain, CONFIG["domains"]["generic"])

    lang = _lang(request)
    q2_key = "q2_en" if lang == "en" and "q2_en" in questions else "q2"
    return templates.TemplateResponse("spin.html", {
        "request": request,
        "lang": lang,
        "control": control,
        "vec": vec,
        "products": products,
        "q2_text": questions[q2_key],
    })


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    lang = _lang(request)
    stats = get_stats()
    tests = get_all_tests()
    images = get_all_images()

    # Enrich tests with pseudonymous handles
    from handles import get_handle_map
    test_pids = list({t["participant_id"] for t in tests if t.get("participant_id")})
    if test_pids:
        hmap = get_handle_map(test_pids)
        for t in tests:
            t["handle"] = hmap.get(t.get("participant_id"), "Anonymous")

    # Rich analytics from S2b_Mathematics.md
    agg = compute_aggregate_stats(tests)
    quadrant_stats = compute_stats_by_quadrant(tests)
    speed_dist = compute_speed_accuracy_distribution(tests)

    # A/B delta if both groups exist
    tests_control = [t for t in tests if t.get("is_control")]
    tests_vec = [t for t in tests if not t.get("is_control")]
    ab_delta = compute_ab_delta(tests_control, tests_vec) if tests_control and tests_vec else None
    ab_fluency = compute_ab_fluency_delta(tests_control, tests_vec) if tests_control and tests_vec else None

    # Invalidation rate (tab switch) per S2b_Mathematics.md section 3
    n_total = len(tests)
    n_invalid = sum(1 for t in tests if t.get("tab_switched"))
    invalidation_rate = (n_invalid / n_total * 100) if n_total > 0 else 0.0

    # Stream vs Spotlight split
    tests_stream = [t for t in tests if t.get("exposure_mode") == "stream"]
    tests_spotlight = [t for t in tests if t.get("exposure_mode") != "stream"]
    stream_stats = compute_aggregate_stats(tests_stream) if tests_stream else None
    spotlight_stats = compute_aggregate_stats(tests_spotlight) if tests_spotlight else None

    # S10 saillance rate (stream mode only) per S2b_Mathematics.md section 8
    s10_stats = compute_s10_rate(tests)

    # Week-over-week KPI evolution indicators
    kpi_evo = compute_kpi_evolution(tests)

    # Current participant's test history (if logged in via cookie)
    participant = _get_participant(request)
    my_tests = []
    if participant:
        my_tests = get_tests_for_participant(participant["id"])

    # OG meta for sharing
    n_tests = len(tests)
    glance_avg = round(agg.get("mean_glance", 0) * 100) if agg.get("mean_glance") else 0
    og_title = f"Dashboard GLANCE — {glance_avg}% score moyen"
    og_desc = f"{n_tests} GAs testés. Score moyen {glance_avg}%."

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "lang": lang,
        "stats": stats,
        "tests": tests,
        "images": images,
        "agg": agg,
        "quadrant_stats": quadrant_stats,
        "speed_dist": speed_dist,
        "ab_delta": ab_delta,
        "invalidation_rate": round(invalidation_rate, 1),
        "stream_stats": stream_stats,
        "spotlight_stats": spotlight_stats,
        "s10_stats": s10_stats,
        "ab_fluency": ab_fluency,
        "kpi_evo": kpi_evo,
        "participant": participant,
        "my_tests": my_tests,
        "og_title": og_title,
        "og_description": og_desc,
    })


# ── Invite route ────────────────────────────────────────────────────────


@app.get("/invite", response_class=HTMLResponse)
def invite_page(request: Request):
    """Invite colleagues page — viral growth through email, LinkedIn, WhatsApp."""
    participant = _get_participant(request)
    lang = _lang(request)

    # Build participant stats for personalized messages
    referral_code = ""
    score_pct = 0
    n_tests = 0
    n_referrals = 0

    if participant:
        referral_code = participant["token"][:8]
        n_referrals = get_referral_count(referral_code)

        # Get participant's average score
        db = get_db()
        row = db.execute(
            """SELECT AVG(glance_score) as avg_score, COUNT(*) as n
               FROM tests WHERE participant_id = ?""",
            (participant["id"],),
        ).fetchone()
        db.close()
        if row and row["avg_score"] is not None:
            score_pct = round(row["avg_score"] * 100)
            n_tests = row["n"]

    # Ambassador badge threshold
    is_ambassador = n_referrals >= 5

    return templates.TemplateResponse("invite.html", {
        "request": request,
        "lang": lang,
        "referral_code": referral_code,
        "score_pct": score_pct,
        "n_tests": n_tests,
        "n_referrals": n_referrals,
        "is_ambassador": is_ambassador,
        "has_participant": participant is not None,
        "og_title": "Invitez vos collegues sur GLANCE",
        "og_description": "GLANCE a besoin de testeurs de tous profils. Le premier benchmark des Graphical Abstracts scientifiques.",
    })


# ── Leaderboard routes ────────────────────────────────────────────────


@app.get("/leaderboard", response_class=HTMLResponse)
def leaderboard(request: Request):
    lang = _lang(request)
    domain_config = CONFIG.get("domains", {})
    data = get_leaderboard_data(domain_config)
    # Filter out user_upload and domains with 0 GAs
    domains = sorted(
        [(k, v) for k, v in data.items() if k != "user_upload" and v["n_gas"] > 0],
        key=lambda kv: kv[1]["n_gas"],
        reverse=True,
    )
    # Build domain pills for inter-domain navigation (also filtered)
    all_domains = [
        {"key": k, "label": v["label"], "n_gas": v["n_gas"],
         "emoji": v.get("emoji", ""), "color": v.get("color", "#71717a")}
        for k, v in domains
    ]
    # Global stats for hero section
    total_gas = sum(v["n_gas"] for _, v in domains)
    total_domains = len(domains)
    all_display_scores = []
    for _, v in domains:
        if v.get("avg_display_score") is not None:
            all_display_scores.append(v["avg_display_score"])
        elif v.get("avg_score") is not None:
            all_display_scores.append(v["avg_score"])
    avg_score_global = round(sum(all_display_scores) / len(all_display_scores) * 100) if all_display_scores else None

    return templates.TemplateResponse("leaderboard.html", {
        "request": request,
        "lang": lang,
        "domains": domains,
        "all_domains": all_domains,
        "total_gas": total_gas,
        "total_domains": total_domains,
        "avg_score_global": avg_score_global,
        "og_title": "GLANCE Leaderboard — Classement des Graphical Abstracts",
        "og_description": "Découvrez quels GAs scientifiques communiquent le mieux, classés par domaine.",
    })


@app.get("/leaderboard/{domain}", response_class=HTMLResponse)
def leaderboard_domain(request: Request, domain: str):
    lang = _lang(request)
    domain_config = CONFIG.get("domains", {})
    data = get_domain_leaderboard(domain, domain_config)
    if not data:
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")

    # Enrich each GA with archetype data for leaderboard display
    for ga in data.get("gas", []):
        if ga.get("avg_glance") is not None:
            lb_scores = {
                "s10": ga.get("avg_s9a", 0.0) or 0.0,
                "s9b": ga.get("avg_s9b", 0.0) or 0.0,
                "s2_coverage": ga.get("avg_s2_coverage", 0.0) or 0.0,
                "drift": 0.0,
                "warp": 0.0,
                "word_count": 0,
                "spin_detected": False,
            }
            # Try loading sidecar for word_count
            sidecar_lb = _load_sidecar(ga.get("filename", ""))
            lb_scores["word_count"] = sidecar_lb.get("word_count", 0)
            lb_result = classify_ga(lb_scores)
            ga["archetype_emoji"] = lb_result["archetype_info"]["emoji"]
            ga["archetype_name"] = lb_result["archetype_info"]["name_fr"]
            ga["archetype_key"] = lb_result["archetype"]
            ga["archetype_info"] = lb_result["archetype_info"]
            ga["archetype_source"] = "measured"
        else:
            # Try vision-based approximation
            sidecar_lb = _load_sidecar(ga.get("filename", ""))
            vision_meta = {}
            if sidecar_lb.get("word_count") is not None or sidecar_lb.get("chart_type"):
                vision_meta = {
                    "word_count": sidecar_lb.get("word_count", 0),
                    "hierarchy_clear": sidecar_lb.get("hierarchy_clear", False),
                    "chart_type": sidecar_lb.get("chart_type", "other"),
                }
            if vision_meta:
                lb_result = classify_from_vision_metadata(vision_meta)
                ga["archetype_emoji"] = lb_result["archetype_info"]["emoji"]
                ga["archetype_name"] = lb_result["archetype_info"]["name_fr"]
                ga["archetype_key"] = lb_result["archetype"]
                ga["archetype_info"] = lb_result["archetype_info"]
                ga["archetype_source"] = "predicted"
            else:
                ga["archetype_emoji"] = ""
                ga["archetype_name"] = ""
                ga["archetype_key"] = None
                ga["archetype_info"] = None
                ga["archetype_source"] = None

    # OG meta for sharing
    domain_label = data.get("label", domain)
    n_gas = data.get("n_gas", 0)
    avg_score = data.get("avg_score")
    avg_pct = round(avg_score * 100) if avg_score is not None else 0
    og_title = f"GLANCE — Classement {domain_label}"
    og_desc = f"{n_gas} Graphical Abstracts classés en {domain_label}. Score moyen : {avg_pct}%."

    # Build domain pills for inter-domain navigation
    all_lb_data = get_leaderboard_data(domain_config)
    all_domains_sorted = sorted(
        all_lb_data.items(),
        key=lambda kv: kv[1]["n_gas"],
        reverse=True,
    )
    all_domains = [
        {"key": k, "label": v["label"], "n_gas": v["n_gas"],
         "emoji": v.get("emoji", ""), "color": v.get("color", "#71717a")}
        for k, v in all_domains_sorted
    ]

    return templates.TemplateResponse("leaderboard_domain.html", {
        "request": request,
        "lang": lang,
        "domain": domain,
        "data": data,
        "all_domains": all_domains,
        "og_title": og_title,
        "og_description": og_desc,
    })


# ── Participant ranking routes ──────────────────────────────────────


@app.get("/participants", response_class=HTMLResponse)
def participants(request: Request):
    lang = _lang(request)
    comprehension = get_participant_ranking_comprehension(min_tests=3)
    contribution = get_participant_ranking_contribution()
    top_referrers = get_top_referrers(limit=20)

    n_participants = len(contribution)
    n_qualified = len(comprehension)

    return templates.TemplateResponse("participants.html", {
        "request": request,
        "lang": lang,
        "comprehension": comprehension,
        "contribution": contribution,
        "top_referrers": top_referrers,
        "n_participants": n_participants,
        "n_qualified": n_qualified,
        "og_title": "GLANCE — Classement des participants",
        # TODO: unhide when N >= 10 — hidden because ~2 participants looks bad
        "og_description": "Classement par comprehension et contribution.",
    })


@app.get("/players", response_class=HTMLResponse)
def players_redirect(request: Request):
    """Legacy redirect: /players -> /participants."""
    return RedirectResponse(url="/participants", status_code=301)


# ── GA Detail helpers ─────────────────────────────────────────────────


def _load_sidecar(filename: str) -> dict:
    """Load the JSON sidecar for a GA image (if it exists)."""
    stem = filename.rsplit(".", 1)[0]
    meta_path = os.path.join(BASE, "ga_library", stem + ".json")
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _extract_study_reference(sidecar: dict, image: dict) -> dict:
    """Extract study reference info from sidecar data.

    Returns dict with keys: text, url (or None), title_short.
    """
    ref = {"text": "", "url": None, "title_short": ""}

    # Try to extract reference from OCR text (usually the last line)
    ocr_text = sidecar.get("ocr_text", "")
    if ocr_text:
        lines = [l.strip() for l in ocr_text.strip().split("\n") if l.strip()]
        for line in reversed(lines):
            if re.search(
                r'(?:et\s+al|Source|doi|DOI|NEJM|Nature|Lancet|JAMA|Science|BMJ'
                r'|NeurIPS|AJPH|Cochrane|PLoS|PNAS|Cell)',
                line, re.IGNORECASE,
            ):
                ref["text"] = re.sub(r'^Source\s*:\s*', '', line).strip()
                break

    # Extract author+year from title patterns like "(Cuijpers et al., 2020)"
    title = sidecar.get("title", "") or image.get("title", "")
    if title:
        m = re.search(r'\(([^)]*(?:et\s+al\.?)?[^)]*\d{4}[^)]*)\)', title)
        if m:
            ref["title_short"] = m.group(1)

    # Fallback: use the title if no reference found from OCR
    if not ref["text"] and title:
        ref["text"] = title

    # Check for DOI or URL in sidecar
    for key in ("doi", "url", "paper_url", "link"):
        val = sidecar.get(key, "")
        if val:
            if val.startswith("10.") and not val.startswith("http"):
                ref["url"] = f"https://doi.org/{val}"
            elif val.startswith("http"):
                ref["url"] = val
            break

    return ref


def _detect_chart_type(sidecar: dict) -> str:
    """Detect the visual encoding type from OCR/sidecar data."""
    ocr = (sidecar.get("ocr_text", "") + " " + sidecar.get("raw_ocr_text", "")).lower()
    desc = (sidecar.get("description", "") or "").lower()
    combined = ocr + " " + desc

    if any(w in combined for w in ["pie", "camembert", "secteur"]):
        return "diagramme circulaire (camembert)"
    if any(w in combined for w in ["scatter", "nuage", "dispersion"]):
        return "nuage de points"
    if any(w in combined for w in ["line chart", "courbe", "trend", "tendance"]):
        return "graphique en courbe"
    if any(w in combined for w in ["heatmap", "carte de chaleur"]):
        return "carte de chaleur"
    if any(w in combined for w in ["wireframe", "infographic", "infographie", "schema"]):
        return "infographie"
    if any(w in combined for w in ["bar", "barre", "longueur", "length"]):
        return "diagramme en barres"
    return "diagramme en barres"


def _generate_ga_abstract(sidecar: dict, image: dict) -> str:
    """Generate a brief abstract of the GA's information content.

    Not the paper abstract — describes what data the GA presents,
    what comparison it shows, and what visual encoding it uses.
    """
    parts = []

    title = sidecar.get("title", "") or image.get("title", "")
    description = sidecar.get("description", "") or image.get("description", "")
    products = sidecar.get("products", [])
    domain = sidecar.get("domain", "") or image.get("domain", "")
    chart_type = _detect_chart_type(sidecar)

    domain_labels = {
        "med": "medical", "epidemiology": "epidemiologique",
        "tech": "technologique", "neuroscience": "neurosciences",
        "psychology": "psychologie", "nutrition": "nutrition",
        "policy": "politiques publiques", "economics": "economique",
        "education": "education", "ecology": "ecologie",
        "climate": "climat", "energy": "energie",
        "transport": "transport", "agriculture": "agriculture",
        "materials": "materiaux",
    }

    if description:
        parts.append(description)
    elif title:
        parts.append(f"Ce graphique presente les donnees de : {title}.")

    if products and len(products) > 1:
        prod_list = ", ".join(products[:-1]) + " et " + products[-1]
        parts.append(f"Il compare {len(products)} elements : {prod_list}.")

    parts.append(f"Encodage visuel : {chart_type}.")

    if domain:
        label = domain_labels.get(domain, domain)
        parts.append(f"Domaine : {label}.")

    return " ".join(parts)


def _generate_executive_summary(sidecar: dict, image: dict, detail: dict,
                                recommendations: dict | None) -> str:
    """Generate a 3-4 sentence executive summary in French.

    Combines: what the GA shows, key GLANCE finding, top recommendation, verdict.
    """
    sentences = []

    description = sidecar.get("description", "") or image.get("description", "")
    title = sidecar.get("title", "") or image.get("title", "")
    gemini_summary = sidecar.get("executive_summary_fr", "")

    # 1. What the GA shows (prefer Gemini summary for AI-analyzed uploads)
    if gemini_summary:
        sentences.append(gemini_summary)
    elif description:
        sentences.append(description)
    elif title:
        sentences.append(f"Ce GA presente : {title}.")

    # 2. Key GLANCE finding
    n_tests = detail.get("n_tests", 0)
    if n_tests > 0:
        pct = round(detail.get("avg_glance", 0) * 100)
        s9a_pct = round(detail.get("avg_s9a", 0) * 100)
        s9b_pct = round(detail.get("avg_s9b", 0) * 100)
        s9c_pct = round(detail.get("avg_s9c", 0) * 100)
        s2_pct = round(detail.get("avg_s2_coverage", 0) * 100)

        dims = {
            "recall (S9a)": s9a_pct,
            "hierarchie (S9b)": s9b_pct,
            "actionabilite (S9c)": s9c_pct,
            "couverture nodale (S2)": s2_pct,
        }
        weakest_name, weakest_val = min(dims.items(), key=lambda x: x[1])
        strongest_name, strongest_val = max(dims.items(), key=lambda x: x[1])

        sentences.append(
            f"Sur {n_tests} test{'s' if n_tests > 1 else ''}, ce GA obtient "
            f"{pct}% en score GLANCE composite, avec {strongest_val}% en "
            f"{strongest_name} mais seulement {weakest_val}% en {weakest_name}."
        )
    else:
        sentences.append("Aucun test n'a encore ete soumis pour ce GA.")

    # 3. Top recommendation
    if recommendations and recommendations.get("recommendations"):
        top_rec = recommendations["recommendations"][0]
        fix_text = top_rec.get("fix", "")
        impact = top_rec.get("impact", "")
        rec_sentence = f"Recommandation principale : {fix_text}"
        if impact:
            rec_sentence += f" ({impact})"
        rec_sentence += "."
        sentences.append(rec_sentence)

    # 4. Overall verdict
    if n_tests > 0:
        pct = round(detail.get("avg_glance", 0) * 100)
        threshold = get_constant("glance_pass_threshold", 0.70)
        threshold_pct = round(threshold * 100)
        if pct >= threshold_pct:
            sentences.append(
                f"Verdict : decodage reussi — le design franchit le seuil de {threshold_pct}%."
            )
        elif pct >= 50:
            sentences.append(
                f"Verdict : partiellement decode — le design est en dessous du seuil "
                f"de {threshold_pct}%, des ameliorations ciblees sont necessaires."
            )
        else:
            sentences.append(
                f"Verdict : le design n'a pas survecu au transfert — score bien en dessous "
                f"du seuil de {threshold_pct}%."
            )

    return " ".join(sentences)


# ── GA Detail route ───────────────────────────────────────────────────


@app.get("/ga-detail/{ga_id}", response_class=HTMLResponse)
def ga_detail(request: Request, ga_id: str):
    """GA detail page with executive summary, study reference, and analysis."""
    lang = _lang(request)
    image, numeric_id = _resolve_ga(ga_id)
    if not image:
        raise HTTPException(status_code=404, detail="GA not found")

    # Redirect numeric IDs to canonical slug URL (301 for SEO)
    if image.get("slug") and ga_id != image["slug"]:
        return RedirectResponse(url=f"/ga-detail/{image['slug']}", status_code=301)

    ga_id = numeric_id  # use numeric ID for all downstream lookups

    # Compute detailed stats for this GA
    detail = get_ga_detail_stats(ga_id)

    # Domain rank and percentile
    domain = image["domain"]
    domain_rank = get_domain_rank(ga_id, domain)
    domain_label = CONFIG["domains"].get(domain, {}).get("label", domain)
    domain_rank["domain_label"] = domain_label

    # Score distributions across ALL GAs (global position)
    distributions = get_score_distributions()

    # Load sidecar metadata
    sidecar = _load_sidecar(image["filename"])

    # GLANCE pass threshold
    glance_threshold = get_constant("glance_pass_threshold", 0.70)

    # Recommendations (from recommender if GA graph exists)
    recommendations = None
    stem = image["filename"].rsplit(".", 1)[0]
    graph_candidates = [
        os.path.join(BASE, "ga_library", stem + ".yaml"),
        os.path.join(BASE, "data", stem + "_ga_graph.yaml"),
        os.path.join(BASE, "data", stem.replace("_control", "") + "_ga_graph.yaml"),
    ]
    for ga_graph_path in graph_candidates:
        if os.path.exists(ga_graph_path):
            try:
                from recommender import analyze_ga
                recommendations = analyze_ga(ga_graph_path)
            except Exception:
                pass
            break

    # Archetype classification
    archetype_result = None
    if detail.get("n_tests", 0) > 0:
        # Measured archetype from real test data
        # Compute drift and warp from S2 node coverage
        s2_node_means = detail.get("s2_node_means", {})
        if s2_node_means:
            node_scores = list(s2_node_means.values())
            mean_cov = sum(node_scores) / len(node_scores) if node_scores else 0.0
            # drift = average distance from system-wide mean
            drift_val = (sum(abs(s - mean_cov) for s in node_scores) / len(node_scores)
                         if node_scores else 0.0)
            # warp = coefficient of variation (sigma / mu)
            if mean_cov > 0 and len(node_scores) > 1:
                variance = sum((s - mean_cov) ** 2 for s in node_scores) / len(node_scores)
                warp_val = (variance ** 0.5) / mean_cov
            else:
                warp_val = 0.0
        else:
            drift_val = 0.0
            warp_val = 0.0

        archetype_scores = {
            "s10": detail.get("avg_s9a", 0.0),
            "s9b": detail.get("avg_s9b", 0.0),
            "s2_coverage": detail.get("avg_s2_coverage", 0.0),
            "drift": drift_val,
            "warp": warp_val,
            "word_count": sidecar.get("word_count", 0),
            "spin_detected": False,
        }
        archetype_result = classify_ga(archetype_scores)
        archetype_result["source"] = "measured"
    else:
        # Predicted archetype from vision metadata (if sidecar has it)
        vision_meta = {}
        if sidecar.get("word_count") is not None or sidecar.get("chart_type"):
            vision_meta = {
                "word_count": sidecar.get("word_count", 0),
                "hierarchy_clear": sidecar.get("hierarchy_clear", False),
                "chart_type": sidecar.get("chart_type", "other"),
            }
        # Also check batch_vision_results for this GA
        if not vision_meta:
            try:
                vision_path = os.path.join(BASE, "exports", "batch_vision_results.json")
                if os.path.exists(vision_path):
                    with open(vision_path, encoding="utf-8") as vf:
                        vision_data = json.load(vf)
                    for vr in vision_data.get("results", []):
                        if vr.get("filename") == image["filename"]:
                            vision_meta = {
                                "word_count": vr.get("word_count", 0),
                                "hierarchy_clear": vr.get("hierarchy_clear", False),
                                "chart_type": vr.get("chart_type", "other"),
                            }
                            break
            except Exception:
                pass
        if vision_meta:
            archetype_result = classify_from_vision_metadata(vision_meta)
            archetype_result["source"] = "predicted"

    # A/B pair lookup (same correct_product + domain, opposite is_control)
    pair_image = None
    pair_stats = None
    db = get_db()
    pair_row = db.execute(
        """SELECT * FROM ga_images
           WHERE correct_product = ? AND domain = ? AND is_control != ? AND id != ?
           LIMIT 1""",
        (image.get("correct_product"), domain, image.get("is_control", 0), ga_id),
    ).fetchone()
    db.close()
    if pair_row:
        pair_image = dict(pair_row)
        pair_stats = get_ga_detail_stats(pair_image["id"])

    # S2 node labels from sidecar semantic_references (dict of level -> list)
    s2_node_labels = {}
    sem_refs = sidecar.get("semantic_references", {})
    if isinstance(sem_refs, dict):
        for level_key, refs in sem_refs.items():
            if isinstance(refs, list):
                for i, ref_text in enumerate(refs):
                    node_id = f"{level_key}_{i}"
                    s2_node_labels[node_id] = ref_text
    elif isinstance(sem_refs, list):
        for ref in sem_refs:
            nid = ref.get("id", "")
            s2_node_labels[nid] = ref.get("label", ref.get("text", nid))

    # Generate new sections
    study_ref = _extract_study_reference(sidecar, image)
    ga_abstract = _generate_ga_abstract(sidecar, image)
    executive_summary = _generate_executive_summary(sidecar, image, detail, recommendations)

    # Email gate: DISABLED — user_upload GAs are never locked
    is_user_upload = (image.get("domain") == "user_upload")
    is_locked = False
    # admin_pwd = os.environ.get("GLANCE_ADMIN_PWD", "glance")
    admin_pwd = os.environ.get("GLANCE_ADMIN_PWD", "glance")
    is_admin = (request.query_params.get("pwd", "") == admin_pwd)
    # if is_user_upload and not is_admin:
    #     unlock_cookie = request.cookies.get(f"glance_unlock_{ga_id}")
    #     is_locked = not bool(unlock_cookie)

    # Stripe availability (graceful degradation: hide payment option if not configured)
    from payments import is_stripe_configured
    stripe_enabled = is_stripe_configured()

    # OG meta for sharing
    ga_title = image.get("title", image.get("filename", "GA"))
    n_tests = detail.get("n_tests", 0)
    avg_glance = detail.get("avg_glance", 0)
    avg_s9b = detail.get("avg_s9b", 0)
    score_pct = round(avg_glance * 100) if avg_glance else 0
    s9b_pct = round(avg_s9b * 100) if avg_s9b else 0
    verdict = "Décodage réussi" if avg_glance and avg_glance >= glance_threshold else "Design à améliorer"
    og_title = f"{ga_title} — Score GLANCE {score_pct}%"
    og_desc = f"Analyse détaillée : S9b {s9b_pct}%, {n_tests} tests. {verdict}."
    og_image = f"https://glance.scisense.fr/og/ga/{ga_id}.png"

    # Canonical share slug (prefer slug, fallback to numeric id)
    share_slug = image.get("slug") or str(ga_id)

    # Dynamic share text — use sim data when available
    share_text_dynamic = None
    try:
        _lg = get_latest_graph(ga_id)
        if _lg:
            _sims = get_reading_sims(graph_id=_lg["id"])
            _s1 = next((s for s in _sims if s["mode"] == "system1"), None)
            if _s1:
                _visited = _s1.get("nodes_visited", 0) or 0
                _total = _s1.get("nodes_total", 0) or 0
                _coverage = _s1.get("narrative_coverage", 0) or 0
                _verdict = _s1.get("complexity_verdict", "")
                _skipped = _s1.get("nodes_skipped", 0) or 0
                _dead = _s1.get("dead_space_count", 0) or 0
                _pct_read = round(_visited / max(_total, 1) * 100)
                _narr_pct = round(_coverage * 100)

                # Build share text — narrative coverage is the headline
                share_text_dynamic = (
                    f"Que voient vos lecteurs en 5 secondes sur votre Graphical Abstract ?\n\n"
                    f"{_narr_pct}% des messages scientifiques transmis.\n\n"
                    f"Testez le vôtre →")
    except Exception:
        pass

    if share_text_dynamic:
        og_desc = share_text_dynamic

    # Expose drift / warp / spin for the perceptual profile report card
    if detail.get("n_tests", 0) > 0:
        perceptual_drift = drift_val
        perceptual_warp = warp_val
        perceptual_spin = archetype_scores.get("spin_detected", False)
    else:
        perceptual_drift = None
        perceptual_warp = None
        perceptual_spin = None

    # ── Graphs history for evolution chart ──
    graphs_history = []
    try:
        db_hist = get_db()
        rows = db_hist.execute("""
            SELECT g.id, g.graph_type, g.created_at, g.node_count, g.link_count,
                   g.avg_effectiveness, g.anti_pattern_count,
                   rs.narrative_coverage, rs.budget_pressure, rs.complexity_verdict,
                   rs.nodes_visited, rs.nodes_total
            FROM ga_graphs g
            LEFT JOIN reading_simulations rs ON rs.graph_id = g.id AND rs.mode = 'system1'
            WHERE g.ga_image_id = ?
            ORDER BY g.id ASC
        """, (ga_id,)).fetchall()
        db_hist.close()
        graphs_history = [dict(r) for r in rows]
    except Exception:
        pass

    # ── Graph overlay SVG + scanpath data ──
    overlay_svg = None
    scanpath_json = "null"
    try:
        latest_graph = get_latest_graph(ga_id)
        if latest_graph:
            sims = get_reading_sims(graph_id=latest_graph["id"])
            sim_s1 = next((s for s in sims if s["mode"] == "system1"), None)
            if sim_s1:
                from graph_renderer import render_overlay_svg
                from reader_sim import simulate_reading
                # Re-run sim from stored graph to get full result (DB only stores stats)
                graph_dict = latest_graph["graph"]
                sim_full = simulate_reading(graph_dict, total_ticks=50, mode="system1")
                overlay_svg = render_overlay_svg(graph_dict, sim_full, 900, 600)
                scanpath_json = json.dumps(sim_full.get("scanpath", []))
    except Exception as e:
        logger.warning(f"Overlay SVG failed for ga {ga_id}: {e}")

    return templates.TemplateResponse("ga_detail.html", {
        "request": request,
        "lang": lang,
        "image": image,
        "detail": detail,
        "domain_rank": domain_rank,
        "distributions": distributions,
        "sidecar": sidecar,
        "glance_threshold": glance_threshold,
        "recommendations": recommendations,
        "pair_image": pair_image,
        "pair_stats": pair_stats,
        "s2_node_labels": s2_node_labels,
        "executive_summary": executive_summary,
        "study_ref": study_ref,
        "ga_abstract": ga_abstract,
        "archetype": archetype_result,
        "is_locked": is_locked,
        "is_user_upload": is_user_upload,
        "stripe_enabled": stripe_enabled,
        "og_title": og_title,
        "og_description": og_desc,
        "og_image": og_image,
        "perceptual_drift": perceptual_drift,
        "perceptual_warp": perceptual_warp,
        "perceptual_spin": perceptual_spin,
        "share_slug": share_slug,
        "ga_id": ga_id,
        "is_admin": is_admin,
        "overlay_svg": overlay_svg,
        "scanpath_json": scanpath_json,
        "graphs_history": graphs_history,
        "graphs_history_json": json.dumps(graphs_history),
        "iteration": get_image_iteration(ga_id),
    })


# ── Note mon GA (Analyze) routes ──────────────────────────────────────

logger = logging.getLogger(__name__)


@app.get("/analyze", response_class=HTMLResponse)
def analyze_page(request: Request, ga: str = ""):
    """Show the GA upload/analysis page.

    If ?ga=<slug> is provided, show the GA image + tool panel instead of the
    upload dropzone. This lets users continue working on an already-uploaded GA.
    """
    lang = _lang(request)
    active_ga = None
    overlay_svg = None
    scanpath_json = "null"
    if ga:
        active_ga = get_image_by_slug(ga)
        if active_ga:
            try:
                _lg = get_latest_graph(active_ga["id"])
                if _lg:
                    _sims = get_reading_sims(graph_id=_lg["id"])
                    _s1 = next((s for s in _sims if s["mode"] == "system1"), None)
                    if _s1:
                        from graph_renderer import render_overlay_svg
                        from reader_sim import simulate_reading
                        graph_dict = _lg["graph"]
                        sim_full = simulate_reading(graph_dict, total_ticks=50, mode="system1")
                        overlay_svg = render_overlay_svg(graph_dict, sim_full, 900, 600)
                        scanpath_json = json.dumps(sim_full.get("scanpath", []))
            except Exception as e:
                logger.warning(f"Analyze overlay failed: {e}")

    graphs_history = []
    if active_ga:
        try:
            db_hist = get_db()
            rows = db_hist.execute("""
                SELECT g.id, g.graph_type, g.created_at, g.node_count, g.link_count,
                       g.avg_effectiveness, g.anti_pattern_count,
                       rs.narrative_coverage, rs.budget_pressure, rs.complexity_verdict,
                       rs.nodes_visited, rs.nodes_total
                FROM ga_graphs g
                LEFT JOIN reading_simulations rs ON rs.graph_id = g.id AND rs.mode = 'system1'
                WHERE g.ga_image_id = ?
                ORDER BY g.id ASC
            """, (active_ga["id"],)).fetchall()
            db_hist.close()
            graphs_history = [dict(r) for r in rows]
        except Exception:
            pass

    sim_stats = None
    narrative_text = None
    if active_ga:
        try:
            _lg2 = get_latest_graph(active_ga["id"])
            if _lg2:
                _sims2 = get_reading_sims(graph_id=_lg2["id"])
                _s1_2 = next((s for s in _sims2 if s["mode"] == "system1"), None)
                if _s1_2:
                    sim_stats = {
                        "narrative_coverage": _s1_2.get("narrative_coverage"),
                        "nodes_visited": _s1_2.get("nodes_visited"),
                        "nodes_total": _s1_2.get("nodes_total"),
                        "nodes_skipped": _s1_2.get("nodes_skipped"),
                        "complexity_verdict": _s1_2.get("complexity_verdict"),
                        "dead_space_count": _s1_2.get("dead_space_count"),
                        "budget_pressure": _s1_2.get("budget_pressure"),
                    }
                    narrative_text = _s1_2.get("narrative_text", "")
        except Exception:
            pass

    return templates.TemplateResponse("analyze.html", {
        "request": request,
        "lang": lang,
        "active_ga": active_ga,
        "overlay_svg": overlay_svg,
        "scanpath_json": scanpath_json,
        "sim_stats": sim_stats,
        "narrative_text": narrative_text,
        "graphs_history": graphs_history,
        "graphs_history_json": json.dumps(graphs_history),
        "og_title": "Analyse ton Graphical Abstract — GLANCE",
        "og_description": "Depose ton Graphical Abstract et recois une analyse IA en 30 secondes : score, archetype, forces, faiblesses, recommandations.",
    })


@app.post("/analyze/submit")
async def analyze_submit(request: Request, file: UploadFile = File(...), public: str = Form("")):
    """Process uploaded GA image through the vision pipeline.

    1. Save uploaded image to ga_library/user_uploads/
    2. Send to Gemini Vision -> get L3 graph
    3. Save graph YAML
    4. Run recommender on the graph
    5. Create a ga_images entry in DB
    6. Redirect to /ga-detail/{new_id}
    """
    is_public = 1 if public else 0

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    allowed_exts = {"png", "jpg", "jpeg", "webp", "pdf"}
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporte : .{ext}. Utilisez PNG, JPG, WebP, ou PDF.",
        )

    # Read file bytes
    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 20 Mo)")

    # Auto-resize large images to max 2000px (reduces Gemini latency + cost)
    if ext in ("png", "jpg", "jpeg", "webp") and len(image_bytes) > 2 * 1024 * 1024:
        try:
            from PIL import Image as PILImage
            import io
            img = PILImage.open(io.BytesIO(image_bytes))
            if img.width > 2000:
                ratio = 2000 / img.width
                img = img.resize((2000, int(img.height * ratio)), PILImage.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="PNG", optimize=True)
                image_bytes = buf.getvalue()
                logger.info(f"Resized to 2000px ({len(image_bytes)//1024}KB)")
        except Exception as e:
            logger.warning(f"Auto-resize failed: {e}")

    # Handle PDF: extract largest image
    if ext == "pdf":
        from analyze import extract_ga_from_pdf
        extracted = extract_ga_from_pdf(image_bytes)
        if not extracted:
            raise HTTPException(
                status_code=400,
                detail="Impossible d'extraire une image du PDF. Uploadez directement le GA en PNG/JPG.",
            )
        image_bytes = extracted
        ext = "png"  # extracted image is raw, treat as PNG

    # ── Dedup: check if this image was already uploaded ──
    import hashlib
    img_hash = hashlib.sha256(image_bytes).hexdigest()
    db_dup = get_db()
    existing = db_dup.execute(
        "SELECT id, slug FROM ga_images WHERE image_hash = ?", (img_hash,)
    ).fetchone()
    db_dup.close()
    if existing:
        # Same image already analyzed — add this user as designer
        glance_user = _get_glance_user(request)
        designer_id = glance_user or request.cookies.get("glance_session", str(int(time.time())))
        add_designer(existing["id"], designer_id)
        # Restore image file if missing (lost during deploy)
        ex_db = get_db()
        ex_row = ex_db.execute("SELECT filename FROM ga_images WHERE id = ?", (existing["id"],)).fetchone()
        ex_db.close()
        if ex_row:
            ex_path = os.path.join(BASE, "ga_library", ex_row[0])
            if not os.path.exists(ex_path):
                os.makedirs(os.path.dirname(ex_path), exist_ok=True)
                with open(ex_path, "wb") as f:
                    f.write(image_bytes)
                logger.info(f"Restored missing image: {ex_path}")
                # Also persist to /var/data/
                persist_dir = os.path.join(os.environ.get("GLANCE_DATA_DIR", os.path.join(BASE, "ga_library")), "user_uploads")
                os.makedirs(persist_dir, exist_ok=True)
                with open(os.path.join(persist_dir, os.path.basename(ex_row[0])), "wb") as f:
                    f.write(image_bytes)
        redirect_key = existing["slug"] or str(existing["id"])
        return RedirectResponse(url=f"/analyze?ga={redirect_key}", status_code=303)

    # Save uploaded image to ga_library/user_uploads/
    timestamp = int(time.time())
    safe_name = re.sub(r'[^\w\-.]', '_', file.filename)
    upload_filename = f"user_uploads/{timestamp}_{safe_name}"
    # Store on persistent disk (/var/data/) AND local ga_library/ for serving
    persist_dir = os.path.join(os.environ.get("GLANCE_DATA_DIR", os.path.join(BASE, "ga_library")), "user_uploads")
    local_dir = os.path.join(BASE, "ga_library", "user_uploads")
    os.makedirs(persist_dir, exist_ok=True)
    os.makedirs(local_dir, exist_ok=True)
    # Save to persistent disk
    persist_path = os.path.join(persist_dir, f"{timestamp}_{safe_name}")
    with open(persist_path, "wb") as f:
        f.write(image_bytes)
    # Also save to local ga_library for immediate serving
    upload_path = os.path.join(BASE, "ga_library", upload_filename)
    with open(upload_path, "wb") as f:
        f.write(image_bytes)

    # Send to Gemini Vision
    try:
        from vision_scorer import analyze_ga_image
        result = analyze_ga_image(image_bytes, filename=file.filename)
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur d'analyse IA : {str(e)}. Reessayez ou contactez le support.",
        )

    graph = result["graph"]
    metadata = result.get("metadata", {})
    graph_path = result["saved_path"]

    # Run recommender on the saved graph
    recommendations = None
    try:
        from recommender import analyze_ga
        recommendations = analyze_ga(graph_path)
    except Exception as e:
        logger.warning(f"Recommender failed: {e}")

    # Derive title from analysis metadata
    main_finding = metadata.get("main_finding", "")
    executive_summary = metadata.get("executive_summary_fr", "")
    title = main_finding[:80] if main_finding else file.filename

    # Create ga_images entry in DB
    description = executive_summary or main_finding or ""
    ga_id = None
    ga_slug = None
    try:
        from db import _generate_unique_slug, slugify
        db = get_db()
        slug = _generate_unique_slug(db, upload_filename)
        db.execute(
            """INSERT INTO ga_images
               (filename, domain, version, is_control, correct_product, products, title, description, slug, image_hash, public)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                upload_filename,
                "user_upload",
                f"user_{timestamp}",
                0,
                None,
                None,
                title,
                description,
                slug,
                img_hash,
                is_public,  # from checkbox — 0=private, 1=public
            ),
        )
        db.commit()
        ga_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        ga_slug = slug

        # Build and store abstract from analysis metadata
        abstract_parts = []
        if title:
            abstract_parts.append(f"Title: {title}")
        if main_finding:
            abstract_parts.append(f"Finding: {main_finding}")
        if executive_summary:
            abstract_parts.append(f"Summary: {executive_summary}")
        if abstract_parts:
            abstract_text = "\n".join(abstract_parts)
            db.execute("UPDATE ga_images SET abstract = ? WHERE id = ?", (abstract_text, ga_id))
            db.commit()

        db.close()
    except Exception as e:
        logger.error(f"DB insert failed: {e}")
        raise HTTPException(status_code=500, detail="Erreur base de donnees")

    # Add logged-in user as designer of this new GA
    glance_user = _get_glance_user(request)
    if glance_user and ga_id:
        add_designer(ga_id, glance_user)

    # Persist graph in DB → triggers async reader sim S1+S2 + health + overlay
    try:
        graph_id = save_graph(graph, ga_image_id=ga_id, graph_type="vision",
                              source="analyze_upload", yaml_path=graph_path)
        logger.info(f"Graph saved for GA {ga_id} (graph {graph_id}) — async sim launched")
    except Exception as e:
        logger.warning(f"save_graph failed (non-blocking): {e}")
        graph_id = None

    # Launch auto-improve loop in background (channels + advise)
    import threading
    def _auto_improve_bg(ga_img_id, img_path, g_path):
        """Background: run channel analysis + 1 improve turn after upload."""
        try:
            # Step 1: Channel analysis (enriches the graph)
            time.sleep(5)  # wait for initial sim to complete
            from channel_analyzer import analyze_ga_channels
            enriched = analyze_ga_channels(img_path, g_path, prior_graph=True)
            if enriched:
                save_graph(enriched, ga_image_id=ga_img_id,
                           graph_type="enriched", source="auto_post_upload")
                logger.info(f"Auto-enriched GA {ga_img_id}")

            # Step 2: One improve turn (advise based on sim + channels)
            time.sleep(4)
            from db import get_latest_graph as _glg, get_reading_sims as _grs
            latest = _glg(ga_img_id)
            if latest:
                sims = _grs(graph_id=latest["id"])
                s1 = next((s for s in sims if s["mode"] == "system1"), None)
                intent = ""
                if s1 and s1.get("narrative_text"):
                    intent = s1["narrative_text"]
                    prompts = json.loads(s1.get("prompts_json", "[]"))
                    if prompts:
                        intent += "\n\n" + "\n".join(f"- {p}" for p in prompts[:3])
                if not intent:
                    intent = "Proposer des ameliorations de clarte visuelle."

                _tmp = os.path.join(BASE, "data", f"autoimp_{ga_img_id}_{int(time.time())}.yaml")
                os.makedirs(os.path.dirname(_tmp), exist_ok=True)
                with open(_tmp, "w", encoding="utf-8") as f:
                    yaml.dump(latest["graph"], f, default_flow_style=False, allow_unicode=True)
                try:
                    from ga_advisor import advise
                    advised = advise(img_path, _tmp, intent, prior_graph=True)
                    if advised:
                        save_graph(advised, ga_image_id=ga_img_id,
                                   graph_type="advised", source="auto_post_upload")
                        logger.info(f"Auto-advised GA {ga_img_id}")
                finally:
                    try: os.remove(_tmp)
                    except: pass
        except Exception as e:
            logger.warning(f"Auto-improve bg failed for GA {ga_img_id}: {e}")

    t = threading.Thread(target=_auto_improve_bg,
                         args=(ga_id, upload_path, graph_path), daemon=True)
    t.start()

    # Save sidecar JSON with analysis metadata (for ga_detail page)
    sidecar_path = os.path.join(
        BASE, "ga_library",
        upload_filename.rsplit(".", 1)[0] + ".json" if "." in upload_filename else upload_filename + ".json",
    )
    sidecar_data = {
        "domain": "user_upload",
        "title": title,
        "description": description,
        "executive_summary_fr": executive_summary,
        "main_finding": main_finding,
        "chart_type": metadata.get("chart_type", "mixed"),
        "word_count": metadata.get("word_count", 0),
        "visual_channels_used": metadata.get("visual_channels_used", []),
        "dominant_encoding": metadata.get("dominant_encoding", ""),
        "hierarchy_clear": metadata.get("hierarchy_clear", False),
        "accessibility_issues": metadata.get("accessibility_issues", []),
        "color_count": metadata.get("color_count", 0),
        "has_legend": metadata.get("has_legend", False),
        "figure_text_ratio": metadata.get("figure_text_ratio", 0.5),
        "source": "gemini_vision",
        "analyzed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        os.makedirs(os.path.dirname(sidecar_path), exist_ok=True)
        with open(sidecar_path, "w", encoding="utf-8") as f:
            json.dump(sidecar_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Sidecar save failed: {e}")

    # Also copy the graph YAML to ga_library/ so ga_detail can find it
    ga_yaml_dest = os.path.join(
        BASE, "ga_library",
        upload_filename.rsplit(".", 1)[0] + ".yaml" if "." in upload_filename else upload_filename + ".yaml",
    )
    try:
        import shutil
        shutil.copy2(graph_path, ga_yaml_dest)
    except Exception as e:
        logger.warning(f"Graph YAML copy failed: {e}")

    # Redirect back to /analyze with the GA active (tools ready)
    redirect_key = ga_slug or ga_id
    return RedirectResponse(url=f"/analyze?ga={redirect_key}", status_code=303)


@app.post("/analyze/swap-image/{ga_slug}")
async def analyze_swap_image(ga_slug: str, file: UploadFile = File(...)):
    """Swap the image on an existing GA, preserving the graph as prior_graph.

    The old image is recorded in image_history. The existing graph is kept
    and used as prior_graph for re-analysis with the new image.
    """
    image = get_image_by_slug(ga_slug)
    if not image:
        raise HTTPException(status_code=404, detail="GA not found")

    ga_id = image["id"]

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    allowed_exts = {"png", "jpg", "jpeg", "webp"}
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporte : .{ext}. Utilisez PNG, JPG, ou WebP.",
        )

    # Read file bytes
    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 20 Mo)")

    # Auto-resize large images to max 2000px
    if len(image_bytes) > 2 * 1024 * 1024:
        try:
            from PIL import Image as PILImage
            import io
            img = PILImage.open(io.BytesIO(image_bytes))
            if img.width > 2000:
                ratio = 2000 / img.width
                img = img.resize((2000, int(img.height * ratio)), PILImage.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="PNG", optimize=True)
                image_bytes = buf.getvalue()
                ext = "png"
                logger.info(f"Swap: resized to 2000px ({len(image_bytes)//1024}KB)")
        except Exception as e:
            logger.warning(f"Auto-resize failed on swap: {e}")

    # Compute hash for the new image
    import hashlib
    img_hash = hashlib.sha256(image_bytes).hexdigest()

    # Save new image file
    timestamp = int(time.time())
    safe_name = re.sub(r'[^\w\-.]', '_', file.filename)
    upload_filename = f"user_uploads/{timestamp}_{safe_name}"
    persist_dir = os.path.join(os.environ.get("GLANCE_DATA_DIR", os.path.join(BASE, "ga_library")), "user_uploads")
    local_dir = os.path.join(BASE, "ga_library", "user_uploads")
    os.makedirs(persist_dir, exist_ok=True)
    os.makedirs(local_dir, exist_ok=True)
    persist_path = os.path.join(persist_dir, f"{timestamp}_{safe_name}")
    with open(persist_path, "wb") as f:
        f.write(image_bytes)
    upload_path = os.path.join(BASE, "ga_library", upload_filename)
    with open(upload_path, "wb") as f:
        f.write(image_bytes)

    # Get existing graph BEFORE swapping (this is the prior_graph)
    existing_graph = get_latest_graph(ga_id)
    prior_graph_dict = existing_graph["graph"] if existing_graph else None

    # Swap the image in DB (preserves graph, records history)
    iteration = swap_ga_image(ga_id, upload_filename, new_image_hash=img_hash)
    logger.info(f"Image swapped for GA {ga_id} ({ga_slug}) — iteration {iteration}")

    # Re-analyze with prior_graph so Gemini extends rather than starts fresh
    import threading

    def _swap_reanalyze_bg(ga_img_id, img_path, prior_graph):
        """Background: re-analyze swapped image using existing graph as prior."""
        try:
            from vision_scorer import analyze_ga_image
            with open(img_path, "rb") as f:
                img_bytes = f.read()
            result = analyze_ga_image(
                img_bytes,
                filename=os.path.basename(img_path),
                prior_graph=prior_graph if prior_graph else True,
            )
            graph = result["graph"]
            graph_id = save_graph(graph, ga_image_id=ga_img_id,
                                  graph_type="vision", source="image_swap")
            logger.info(f"Swap re-analysis for GA {ga_img_id}: graph {graph_id}")

            # Auto-improve: channels + advise (same as initial upload)
            time.sleep(5)
            from channel_analyzer import analyze_ga_channels
            graph_path = result.get("saved_path", "")
            if graph_path and os.path.exists(graph_path):
                enriched = analyze_ga_channels(img_path, graph_path, prior_graph=True)
                if enriched:
                    save_graph(enriched, ga_image_id=ga_img_id,
                               graph_type="enriched", source="swap_auto_enrich")
                    logger.info(f"Swap auto-enriched GA {ga_img_id}")

            time.sleep(4)
            from db import get_latest_graph as _glg, get_reading_sims as _grs
            latest = _glg(ga_img_id)
            if latest:
                sims = _grs(graph_id=latest["id"])
                s1 = next((s for s in sims if s["mode"] == "system1"), None)
                intent = ""
                if s1 and s1.get("narrative_text"):
                    intent = s1["narrative_text"]
                if not intent:
                    intent = "Proposer des ameliorations de clarte visuelle."
                _tmp = os.path.join(BASE, "data", f"swap_adv_{ga_img_id}_{int(time.time())}.yaml")
                os.makedirs(os.path.dirname(_tmp), exist_ok=True)
                with open(_tmp, "w", encoding="utf-8") as f:
                    yaml.dump(latest["graph"], f, default_flow_style=False, allow_unicode=True)
                try:
                    from ga_advisor import advise
                    advised = advise(img_path, _tmp, intent, prior_graph=True)
                    if advised:
                        save_graph(advised, ga_image_id=ga_img_id,
                                   graph_type="advised", source="swap_auto_advise")
                        logger.info(f"Swap auto-advised GA {ga_img_id}")
                finally:
                    try:
                        os.remove(_tmp)
                    except OSError:
                        pass
        except Exception as e:
            logger.warning(f"Swap re-analysis failed for GA {ga_img_id}: {e}")

    t = threading.Thread(target=_swap_reanalyze_bg,
                         args=(ga_id, upload_path, prior_graph_dict), daemon=True)
    t.start()

    return RedirectResponse(url=f"/analyze?ga={ga_slug}", status_code=303)


@app.get("/analyze/poll/{ga_slug}")
async def analyze_poll_state(ga_slug: str):
    """Poll the current analysis state for a GA. Used by frontend to update without refresh."""
    image = get_image_by_slug(ga_slug)
    if not image:
        return JSONResponse({"status": "not_found"}, status_code=404)

    ga_id = image["id"]
    latest = get_latest_graph(ga_id)
    if not latest:
        return JSONResponse({"status": "pending", "message": "Analyse en cours..."})

    sims = get_reading_sims(graph_id=latest["id"])
    s1 = next((s for s in sims if s["mode"] == "system1"), None)

    state = {
        "status": "ready",
        "graph_id": latest["id"],
        "graph_type": latest.get("graph_type", "vision"),
        "node_count": latest.get("node_count"),
        "link_count": latest.get("link_count"),
    }

    if s1:
        state["sim"] = {
            "verdict": s1.get("complexity_verdict"),
            "pressure": s1.get("budget_pressure"),
            "visited": s1.get("nodes_visited"),
            "total": s1.get("nodes_total"),
            "coverage": s1.get("narrative_coverage"),
            "dead_spaces": s1.get("dead_space_count"),
            "narrative_text": s1.get("narrative_text", ""),
        }
        # Overlay SVG
        try:
            from graph_renderer import render_overlay_svg
            from reader_sim import simulate_reading
            graph_dict = latest["graph"]
            sim_full = simulate_reading(graph_dict, total_ticks=50, mode="system1")
            state["overlay_svg"] = render_overlay_svg(graph_dict, sim_full, 900, 600)
            state["scanpath"] = sim_full.get("scanpath", [])
        except Exception:
            pass

    return JSONResponse(state)



@app.get("/analyze/activity/{ga_slug}")
async def analyze_activity(ga_slug: str):
    """Activity log for a GA — what ran, when, results."""
    image = get_image_by_slug(ga_slug)
    if not image:
        return JSONResponse({"error": "not_found"}, status_code=404)
    ga_id = image["id"]
    db = get_db()
    graphs = [dict(r) for r in db.execute(
        "SELECT id, graph_type, source, created_at, node_count, link_count, avg_effectiveness, anti_pattern_count FROM ga_graphs WHERE ga_image_id = ? ORDER BY id", (ga_id,)
    ).fetchall()]
    sims = [dict(r) for r in db.execute(
        "SELECT id, graph_id, mode, created_at, complexity_verdict, budget_pressure, nodes_visited, nodes_total, narrative_coverage, dead_space_count FROM reading_simulations WHERE ga_image_id = ? ORDER BY id", (ga_id,)
    ).fetchall()]
    db.close()
    events = []
    for g in graphs:
        events.append({"type": "graph", "time": g["created_at"], "icon": "📊",
            "title": f"Graph {g['graph_type']} ({g['source']})", "detail": f"{g['node_count']} nodes, {g['link_count']} links"})
    for s in sims:
        events.append({"type": "sim", "time": s["created_at"], "icon": "👀" if s["mode"] == "system1" else "🔍",
            "title": f"Lecture {'5s' if s['mode'] == 'system1' else '90s'} — {s['complexity_verdict']}",
            "detail": f"{s['nodes_visited']}/{s['nodes_total']} lus, {round((s['narrative_coverage'] or 0)*100)}% messages"})
    events.sort(key=lambda e: e.get("time", ""))
    return JSONResponse({"ga_id": ga_id, "total_events": len(events), "timeline": events})


@app.post("/analyze/improve/{ga_slug}")
async def analyze_improve(ga_slug: str, pwd: str = ""):
    """Run one improvement turn on a GA. Returns JSON with turn results."""
    # admin_pwd = os.environ.get("GLANCE_ADMIN_PWD", "glance")
    # if pwd != admin_pwd:
    #     raise HTTPException(status_code=403, detail="Admin password required")

    # 1. Look up GA
    image = get_image_by_slug(ga_slug)
    if not image:
        raise HTTPException(status_code=404, detail="GA not found")

    ga_id = image["id"]
    filename = image["filename"]
    image_path = os.path.join(BASE, "ga_library", filename)

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="GA image file not found")

    # 2. Get latest graph
    latest = get_latest_graph(ga_id)

    if not latest:
        # No graph yet — run initial analysis
        try:
            from vision_scorer import analyze_ga_image
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            result = analyze_ga_image(image_bytes, filename=filename)
            graph = result["graph"]
            graph_id = save_graph(graph, ga_image_id=ga_id, graph_type="vision", source="improve_initial")
            # Wait for async sim
            time.sleep(3)
            return JSONResponse({
                "turn": 0,
                "action": "initial_analysis",
                "graph_id": graph_id,
                "node_count": len(graph.get("nodes", [])),
                "link_count": len(graph.get("links", [])),
                "message": "Analyse initiale completee. Cliquez a nouveau pour ameliorer.",
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Initial analysis failed: {str(e)}")

    # 3. Build intent from latest sim + graph data
    graph = latest["graph"]
    graph_id = latest["id"]
    _tmp_dir = os.path.join(BASE, "data")
    os.makedirs(_tmp_dir, exist_ok=True)
    graph_path_tmp = os.path.join(_tmp_dir, f"improve_{ga_slug}_{int(time.time())}.yaml")

    # Save graph to temp file for advisor
    with open(graph_path_tmp, "w", encoding="utf-8") as f:
        yaml.dump(graph, f, default_flow_style=False, allow_unicode=True)

    # Get sim results
    sims = get_reading_sims(graph_id=graph_id)
    sim_s1 = next((s for s in sims if s["mode"] == "system1"), None)
    sim_s2 = next((s for s in sims if s["mode"] == "system2"), None)

    intent_parts = []

    if sim_s1 and sim_s1.get("narrative_text"):
        intent_parts.append("## Lecture simulee (System 1 — 5s)\n" + sim_s1["narrative_text"])

        s1_cov = sim_s1.get("narrative_coverage", 0) or 0
        s2_cov = (sim_s2.get("narrative_coverage", 0) or 0) if sim_s2 else 0
        if s2_cov > s1_cov + 0.2:
            intent_parts.append(
                f"En 90 secondes (System 2), la couverture narrative monte a {s2_cov:.0%} "
                f"(vs {s1_cov:.0%} en 5s).")

        sim_prompts = json.loads(sim_s1.get("prompts_json", "[]"))
        if sim_prompts:
            intent_parts.append("## Axes d'amelioration\n" + "\n".join(f"- {p}" for p in sim_prompts[:3]))

    # Anti-pattern diagnosis
    anti_patterns = graph.get("metadata", {}).get("channel_analysis", {}).get("anti_patterns", [])
    if anti_patterns:
        ap_text = "\n".join(f"- {ap.get('type')}: {ap.get('node_id', '')} — {ap.get('issue', '')}"
                           for ap in anti_patterns[:5])
        intent_parts.append("## Anti-patterns detectes\n" + ap_text)

    if not intent_parts:
        intent_parts.append("Analyser le graph actuel et proposer des ameliorations de clarte visuelle.")

    intent = "\n\n".join(intent_parts)

    # 4. Call advisor
    try:
        from ga_advisor import advise
        advised = advise(image_path, graph_path_tmp, intent, prior_graph=True)
    except Exception as e:
        # Clean up temp file
        try:
            os.remove(graph_path_tmp)
        except OSError:
            pass
        raise HTTPException(status_code=500, detail=f"Advisor failed: {str(e)}")

    # Clean up temp file
    try:
        os.remove(graph_path_tmp)
    except OSError:
        pass

    if not advised:
        return JSONResponse({
            "turn": "N/A",
            "action": "no_changes",
            "message": "L'advisor n'a propose aucun changement.",
        })

    # 5. Count changes
    changes = [n for n in advised.get("nodes", []) if n.get("_change")]

    # 6. Save improved graph (triggers async sim + health)
    new_graph_id = save_graph(advised, ga_image_id=ga_id, graph_type="advised", source="improve_manual")

    # 7. Wait briefly for async sim
    time.sleep(3)

    # 8. Get new sim results
    new_sims = get_reading_sims(graph_id=new_graph_id)
    new_s1 = next((s for s in new_sims if s["mode"] == "system1"), None)

    # Build response
    response_data = {
        "action": "improved",
        "graph_id": new_graph_id,
        "prev_graph_id": graph_id,
        "changes": [{"node": c.get("name", ""), "change": c.get("_change", "")} for c in changes],
        "n_changes": len(changes),
        "node_count": len(advised.get("nodes", [])),
        "link_count": len(advised.get("links", [])),
    }

    if new_s1:
        response_data["sim_s1"] = {
            "verdict": new_s1.get("complexity_verdict"),
            "pressure": new_s1.get("budget_pressure"),
            "visited": new_s1.get("nodes_visited"),
            "total": new_s1.get("nodes_total"),
            "skipped": new_s1.get("nodes_skipped"),
            "narrative_coverage": new_s1.get("narrative_coverage"),
            "narrative_text": new_s1.get("narrative_text", ""),
        }

    # Compare with previous
    if sim_s1:
        response_data["prev_sim_s1"] = {
            "verdict": sim_s1.get("complexity_verdict"),
            "pressure": sim_s1.get("budget_pressure"),
            "narrative_coverage": sim_s1.get("narrative_coverage"),
        }

    return JSONResponse(response_data)


@app.post("/analyze/tool/{tool_name}/{ga_slug}")
async def analyze_tool(tool_name: str, ga_slug: str, request: Request, pwd: str = ""):
    """Run a specific analysis tool on a GA. Returns JSON.

    Freemium: 3 free tool calls per GA. After that, payment or email required.
    Free tools (no Gemini cost): health, reader_sim — always free.
    """
    FREE_TOOLS = {"health", "reader_sim", "reader_sim_s2"}  # pure math, no API cost
    FREE_CALLS_PER_GA = 6

    image = get_image_by_slug(ga_slug)
    if not image:
        raise HTTPException(status_code=404, detail="GA not found")

    ga_id = image["id"]
    filename = image["filename"]
    image_path = os.path.join(BASE, "ga_library", filename)

    # ── Freemium gate: 3 free Gemini calls per GA, unlimited for free tools ──
    if tool_name not in FREE_TOOLS:
        cookie_key = f"glance_calls_{ga_id}"
        calls_used = int(request.cookies.get(cookie_key, "0"))
        # Admin bypass
        admin_pwd = os.environ.get("GLANCE_ADMIN_PWD", "glance")
        is_admin = (pwd == admin_pwd)
        # Unlock cookie (paid users)
        is_unlocked = bool(request.cookies.get(f"glance_unlock_{ga_id}"))

        if calls_used >= FREE_CALLS_PER_GA and not is_admin and not is_unlocked:
            return JSONResponse({
                "error": "free_limit",
                "message": f"Vous avez utilisé vos {FREE_CALLS_PER_GA} analyses gratuites pour ce GA.",
                "calls_used": calls_used,
                "limit": FREE_CALLS_PER_GA,
            }, status_code=402)

    # Get optional text input from request body
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    text_input = body.get("text", "")
    node_id = body.get("node_id", "")

    # Prepend node context for tools that use text_input
    if node_id and tool_name in ("advise", "rubber_duck"):
        if text_input:
            text_input = f"Focus on node '{node_id}': {text_input}"
        else:
            text_input = f"Improve node '{node_id}' specifically."

    # Get latest graph
    latest = get_latest_graph(ga_id)
    graph = latest["graph"] if latest else None
    graph_id = latest["id"] if latest else None

    # Save graph to temp file if needed
    graph_path_tmp = None
    if graph:
        _tmp_dir = os.path.join(BASE, "data")
        os.makedirs(_tmp_dir, exist_ok=True)
        graph_path_tmp = os.path.join(_tmp_dir, f"tool_{ga_slug}_{int(time.time())}.yaml")
        with open(graph_path_tmp, "w", encoding="utf-8") as f:
            yaml.dump(graph, f, default_flow_style=False, allow_unicode=True)

    try:
        if tool_name == "vision":
            from vision_scorer import analyze_ga_image
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            result = analyze_ga_image(image_bytes, filename=filename,
                                      prior_graph=graph if graph else True)
            new_graph = result["graph"]
            new_graph_id = save_graph(new_graph, ga_image_id=ga_id,
                                     graph_type="vision", source="tool_vision")
            meta = result.get("metadata", {})
            return JSONResponse({
                "tool": "vision",
                "graph_id": new_graph_id,
                "node_count": len(new_graph.get("nodes", [])),
                "link_count": len(new_graph.get("links", [])),
                "summary": meta.get("executive_summary_fr", ""),
                "word_count": meta.get("word_count", 0),
                "hierarchy_clear": meta.get("hierarchy_clear", False),
            })

        elif tool_name == "channels":
            if not graph_path_tmp:
                raise HTTPException(status_code=400, detail="No graph yet — run vision first")
            from channel_analyzer import analyze_ga_channels
            enriched = analyze_ga_channels(image_path, graph_path_tmp, prior_graph=True)
            ca = enriched.get("metadata", {}).get("channel_analysis", {})
            aps = enriched.get("metadata", {}).get("anti_patterns", [])
            # Save enriched graph
            new_graph_id = save_graph(enriched, ga_image_id=ga_id,
                                     graph_type="enriched", source="tool_channels")
            return JSONResponse({
                "tool": "channels",
                "graph_id": new_graph_id,
                "channels_used": ca.get("channels_used", 0),
                "channels_total": ca.get("total_channels_analyzed", 0),
                "avg_effectiveness": round(ca.get("avg_effectiveness", 0), 3),
                "anti_patterns": [{"type": a.get("type"), "node": a.get("node_id", ""),
                                   "issue": a.get("issue", "")} for a in aps[:10]],
                "anti_pattern_count": len(aps),
            })

        elif tool_name == "advise":
            if not graph_path_tmp:
                raise HTTPException(status_code=400, detail="No graph yet — run vision first")
            if not text_input:
                text_input = "Proposer des améliorations de clarté visuelle."
            from ga_advisor import advise
            advised = advise(image_path, graph_path_tmp, text_input, prior_graph=True)
            if not advised:
                return JSONResponse({"tool": "advise", "action": "no_changes",
                                     "message": "Aucun changement proposé."})
            changes = [n for n in advised.get("nodes", []) if n.get("_change")]
            new_graph_id = save_graph(advised, ga_image_id=ga_id,
                                     graph_type="advised", source="tool_advise")
            return JSONResponse({
                "tool": "advise",
                "graph_id": new_graph_id,
                "intent": text_input,
                "changes": [{"node": c.get("name", ""), "change": c.get("_change", "")}
                           for c in changes],
                "n_changes": len(changes),
            })

        elif tool_name == "rubber_duck":
            if not graph_path_tmp:
                raise HTTPException(status_code=400, detail="No graph yet — run vision first")
            if not text_input:
                text_input = "Qu'est-ce qui capte l'attention en premier dans ce GA ?"
            from ga_rubber_duck import rubber_duck
            duck_result = rubber_duck(image_path, graph_path_tmp, text_input, prior_graph=True)
            return JSONResponse({
                "tool": "rubber_duck",
                "question": text_input,
                "response": duck_result if isinstance(duck_result, str) else yaml.dump(duck_result, allow_unicode=True),
            })

        elif tool_name == "health":
            if not graph:
                raise HTTPException(status_code=400, detail="No graph yet — run vision first")
            from graph_health import check_transmission_health
            health = check_transmission_health(graph)
            return JSONResponse({
                "tool": "health",
                "overall_score": health.get("overall_score", 0),
                "n_spaces": health.get("n_spaces", 0),
                "n_things": health.get("n_things", 0),
                "n_narratives": health.get("n_narratives", 0),
                "orphan_things": health.get("orphan_things", []),
                "orphan_spaces": health.get("orphan_spaces", []),
                "narratives": health.get("narratives", []),
                "prompts": health.get("prompts", []),
            })

        elif tool_name == "reader_sim":
            if not graph:
                raise HTTPException(status_code=400, detail="No graph yet — run vision first")
            from reader_sim import simulate_reading, generate_reading_narrative
            sim = simulate_reading(graph, total_ticks=50, mode="system1")
            narrative = generate_reading_narrative(sim, graph)
            return JSONResponse({
                "tool": "reader_sim",
                "verdict": sim["stats"]["complexity_verdict"],
                "pressure": sim["stats"]["budget_pressure"],
                "visited": sim["stats"]["unique_nodes_visited"],
                "total": sim["stats"]["total_things"],
                "skipped": sim["stats"]["nodes_skipped"],
                "narrative_coverage": sim["stats"]["narrative_coverage"],
                "dead_spaces": sim["stats"]["dead_space_count"],
                "orphan_narratives": sim["stats"]["orphan_narrative_count"],
                "narrative_text": narrative,
                "recommendations": sim.get("recommendations", []),
            })

        elif tool_name == "reader_sim_s2":
            if not graph:
                raise HTTPException(status_code=400, detail="No graph yet — run vision first")
            from reader_sim import simulate_reading, generate_reading_narrative
            sim = simulate_reading(graph, total_ticks=900, mode="system2")
            narrative = generate_reading_narrative(sim, graph)
            return JSONResponse({
                "tool": "reader_sim_s2",
                "verdict": sim["stats"]["complexity_verdict"],
                "pressure": sim["stats"]["budget_pressure"],
                "visited": sim["stats"]["unique_nodes_visited"],
                "total": sim["stats"]["total_things"],
                "skipped": sim["stats"]["nodes_skipped"],
                "narrative_coverage": sim["stats"]["narrative_coverage"],
                "dead_spaces": sim["stats"]["dead_space_count"],
                "orphan_narratives": sim["stats"]["orphan_narrative_count"],
                "narrative_text": narrative,
                "recommendations": sim.get("recommendations", []),
            })

        elif tool_name == "deepen":
            if not graph:
                raise HTTPException(status_code=400, detail="No graph yet — run vision first")
            from deepen import deepen as run_deepen
            max_depth = body.get("max_depth", 1)
            stats = run_deepen(ga_image_id=ga_id, max_depth=max_depth,
                               image_path=image_path)
            return JSONResponse({
                "tool": "deepen",
                "graph_id": stats["graph_id"],
                "depth": stats["depth"],
                "root_nodes": stats["root_nodes"],
                "total_nodes": stats["total_nodes"],
                "total_links": stats["total_links"],
                "spaces_deepened": stats["spaces_deepened"],
                "resolution": stats["resolution"],
            })

        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{tool_name} failed: {str(e)}")
    finally:
        # Clean up temp file
        if graph_path_tmp:
            try:
                os.remove(graph_path_tmp)
            except OSError:
                pass

    # Should not reach here — all branches return above.
    # But if we do reach here somehow, return a generic success.
    return JSONResponse({"tool": tool_name, "status": "ok"})


@app.post("/analyze/deepen/{ga_slug}")
async def analyze_deepen(ga_slug: str, pwd: str = "", max_depth: int = 1):
    """Deepen the analysis of a GA by analyzing each space at higher resolution.

    Each space with a bbox is cropped and re-analyzed by Gemini Vision.
    The child nodes are merged into the parent graph with containment links.

    Args:
        ga_slug: GA slug or numeric ID
        pwd: admin password (required — deepen uses multiple Gemini calls)
        max_depth: how many levels to recurse (1 = analyze each space once)
    """
    admin_pwd = os.environ.get("GLANCE_ADMIN_PWD", "glance")
    if pwd != admin_pwd:
        raise HTTPException(status_code=403, detail="Admin password required")

    image, ga_id = _resolve_ga(ga_slug)
    if not image:
        raise HTTPException(status_code=404, detail="GA not found")

    max_depth = min(max_depth, 3)  # cap recursion

    image_path = os.path.join(BASE, "ga_library", image["filename"])
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="GA image file not found")

    try:
        from deepen import deepen as run_deepen
        stats = run_deepen(ga_image_id=ga_id, max_depth=max_depth,
                           image_path=image_path)
        return JSONResponse({
            "status": "ok",
            "ga_slug": ga_slug,
            **stats,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deepen failed: {str(e)}")


@app.post("/analyze/extract-claims")
async def analyze_extract_claims(request: Request):
    """Extract structured claims from a paper abstract using Gemini.

    Accepts JSON body: {"abstract": "text...", "context": "optional..."}
    Returns claims classified by data family + suggested GA narratives.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    abstract_text = body.get("abstract", "").strip()
    if not abstract_text:
        raise HTTPException(status_code=400, detail="'abstract' field is required")

    context = body.get("context", None)

    try:
        from claim_extractor import extract_claims
        result = extract_claims(abstract_text, context=context)
        return JSONResponse(result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claim extraction failed: {str(e)}")


@app.post("/admin/batch-analyze")
async def admin_batch_analyze(pwd: str = "", batch_size: int = 5):
    """Launch background batch analysis on GAs without graphs.

    Fires a background thread that processes `batch_size` GAs at a time
    (default 5). Returns immediately with the list of GAs queued.
    Check /admin for progress (graphs table).
    """
    admin_pwd = os.environ.get("GLANCE_ADMIN_PWD", "glance")
    if pwd != admin_pwd:
        raise HTTPException(status_code=403, detail="Admin password required")

    batch_size = min(batch_size, 20)  # cap at 20 per call

    db = get_db()
    images = db.execute("""
        SELECT i.id, i.filename, i.slug, i.title
        FROM ga_images i
        LEFT JOIN ga_graphs g ON g.ga_image_id = i.id
        WHERE g.id IS NULL
        ORDER BY i.id
        LIMIT ?
    """, (batch_size,)).fetchall()
    total_remaining = db.execute("""
        SELECT COUNT(*) FROM ga_images i
        LEFT JOIN ga_graphs g ON g.ga_image_id = i.id
        WHERE g.id IS NULL
    """).fetchone()[0]
    db.close()

    if not images:
        return JSONResponse({"status": "done", "message": "All GAs already have graphs.", "remaining": 0})

    queued = [{"ga_id": img["id"], "slug": img["slug"], "title": img["title"]} for img in images]

    # Fire and forget — background thread
    import threading

    def _batch_worker(image_list):
        from vision_scorer import analyze_ga_image
        _log = logging.getLogger("batch")
        for img in image_list:
            ga_id = img["id"]
            filename = img["filename"]
            image_path = os.path.join(BASE, "ga_library", filename)
            if not os.path.exists(image_path):
                _log.warning(f"Batch: {filename} not found, skipping")
                continue
            try:
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                # Use existing graph as prior_graph if available
                existing = get_latest_graph(ga_id)
                prior = existing["graph"] if existing else True
                result = analyze_ga_image(image_bytes, filename=filename,
                                          prior_graph=prior)
                graph_id = save_graph(result["graph"], ga_image_id=ga_id,
                                     graph_type="vision", source="batch_analyze")
                _log.info(f"Batch: GA {ga_id} ({img['slug']}) → graph {graph_id}"
                          f"{' (prior_graph used)' if existing else ''}")
            except Exception as e:
                _log.warning(f"Batch: GA {ga_id} failed: {e}")
            time.sleep(6)  # gentle rate limit

    t = threading.Thread(target=_batch_worker, args=([dict(img) for img in images],), daemon=True)
    t.start()

    return JSONResponse({
        "status": "started",
        "queued": len(queued),
        "remaining_after": total_remaining - len(queued),
        "batch": queued,
        "message": f"Batch de {len(queued)} GAs lancé en background. Check /admin pour voir les résultats.",
    })


@app.post("/admin/ingest-reddit")
async def admin_ingest_reddit(pwd: str = "", subreddit: str = "dataisugly", limit: int = 10):
    """Trigger Reddit ingestion for a subreddit. Runs in background.

    Polls the subreddit for image posts, deduplicates via SHA-256,
    saves new GAs to ga_library/reddit/, creates DB entries,
    runs vision scoring, and sends Telegram alerts.
    """
    admin_pwd = os.environ.get("GLANCE_ADMIN_PWD", "glance")
    if pwd != admin_pwd:
        raise HTTPException(status_code=403, detail="Admin password required")

    limit = min(limit, 50)  # cap at 50 per call

    import threading
    from ingestion.run_ingest import ingest_subreddit

    def _ingest_worker(sub, n):
        _log = logging.getLogger("ingest.admin")
        try:
            stats = ingest_subreddit(sub, limit=n)
            _log.info(f"Reddit ingest done: {stats}")
        except Exception as e:
            _log.error(f"Reddit ingest failed for r/{sub}: {e}")

    t = threading.Thread(target=_ingest_worker, args=(subreddit, limit), daemon=True)
    t.start()

    return JSONResponse({
        "status": "started",
        "subreddit": subreddit,
        "limit": limit,
        "message": f"Reddit ingestion for r/{subreddit} (limit={limit}) launched in background.",
    })


@app.post("/analyze/unlock/{ga_id}")
async def unlock_analysis(ga_id: int, email: str = Form(...)):
    """Capture email lead and unlock the full analysis for this GA."""
    # Validate email minimally
    email = email.strip()
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Email invalide")

    # Save email lead
    save_analysis_lead(email=email, ga_image_id=ga_id, source="analyze")

    # Resolve slug for redirect
    image = get_image_by_id(ga_id)
    redirect_key = image["slug"] if image and image.get("slug") else str(ga_id)

    # Set unlock cookie (30 days) and redirect back
    response = RedirectResponse(url=f"/ga-detail/{redirect_key}", status_code=303)
    response.set_cookie(
        f"glance_unlock_{ga_id}",
        "1",
        max_age=86400 * 30,
        httponly=True,
    )
    return response


# ── Stripe Checkout routes ────────────────────────────────────────────


@app.post("/checkout/{product}/{ga_id}")
async def create_checkout(request: Request, product: str, ga_id: int):
    """Create Stripe Checkout and redirect to payment page."""
    from payments import create_checkout_session, PRODUCTS, is_stripe_configured

    if not is_stripe_configured():
        raise HTTPException(status_code=503, detail="Paiement indisponible")

    if product not in PRODUCTS:
        raise HTTPException(status_code=400, detail="Produit inconnu")

    # Resolve slug for cancel URL
    image = get_image_by_id(ga_id)
    redirect_key = image["slug"] if image and image.get("slug") else str(ga_id)

    base_url = str(request.base_url).rstrip("/")
    success_url = f"{base_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}&ga_id={ga_id}"
    cancel_url = f"{base_url}/ga-detail/{redirect_key}"

    checkout_url = create_checkout_session(product, ga_id, success_url, cancel_url)
    return RedirectResponse(url=checkout_url, status_code=303)


@app.get("/checkout/success")
async def checkout_success(request: Request, session_id: str, ga_id: int):
    """Handle successful payment — unlock the analysis."""
    from payments import verify_session

    result = verify_session(session_id)

    # Resolve slug for redirect
    image = get_image_by_id(ga_id)
    redirect_key = image["slug"] if image and image.get("slug") else str(ga_id)

    if result["paid"]:
        # Save to DB as paid lead
        save_analysis_lead(
            email=result["email"] or "",
            ga_image_id=ga_id,
            source="stripe",
            paid=1,
        )

        # Set unlock cookie (1 year)
        response = RedirectResponse(url=f"/ga-detail/{redirect_key}", status_code=303)
        response.set_cookie(
            f"glance_unlock_{ga_id}",
            "paid",
            httponly=True,
            max_age=86400 * 365,
        )
        return response

    # Payment not completed — redirect back without unlocking
    return RedirectResponse(url=f"/ga-detail/{redirect_key}", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, pwd: str = ""):
    """Admin analytics dashboard — password-protected."""
    admin_pwd = os.environ.get("GLANCE_ADMIN_PWD", "glance")
    if pwd != admin_pwd:
        return HTMLResponse(
            content='<html><body style="background:#0f172a;color:#fff;display:flex;align-items:center;'
            'justify-content:center;height:100vh;font-family:system-ui;">'
            '<form><input name="pwd" type="password" placeholder="Mot de passe admin" '
            'style="padding:12px 20px;border-radius:8px;border:1px solid #334155;background:#1e293b;'
            'color:#fff;font-size:1rem;"><button type="submit" style="padding:12px 20px;'
            'border-radius:8px;border:none;background:#0d9488;color:#fff;margin-left:8px;'
            'cursor:pointer;font-size:1rem;">Entrer</button></form></body></html>',
            status_code=200,
        )
    analytics = get_admin_analytics()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "analytics": analytics,
        "analytics_json": json.dumps(analytics, ensure_ascii=False),
        "hide_lang_switcher": True,
    })


# ── OG Image Card routes ────────────────────────────────────────────

# Simple in-memory cache: test_id -> (png_bytes, glance_score)
_card_cache: dict[int, tuple[bytes, float]] = {}
_dashboard_card_cache: dict[str, bytes] = {}


@app.get("/card/default.png")
def card_default():
    """Return the default GLANCE branding card."""
    png_bytes = generate_default_card()
    return Response(content=png_bytes, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.get("/card/{test_id}.png")
def card_test(test_id: int):
    """Generate a 1200x630 OG image card for a single test result.

    Includes the participant's percentile rank. Short cache TTL
    because percentile shifts as more participants join.
    """
    test = get_test(test_id)
    if not test:
        png_bytes = generate_default_card()
        return Response(content=png_bytes, media_type="image/png",
                        headers={"Cache-Control": "public, max-age=3600"})

    percentile = get_participant_percentile(test["participant_id"])
    png_bytes = generate_test_card(test, participant_percentile=percentile)
    return Response(content=png_bytes, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=600"})


@app.get("/card/dashboard/{participant_token}.png")
def card_dashboard(participant_token: str):
    """Generate a 1200x630 OG image card for a participant's dashboard.

    Includes percentile rank. No in-memory cache — percentile is dynamic.
    """
    participant = get_participant_by_token(participant_token)
    if not participant:
        png_bytes = generate_default_card()
        return Response(content=png_bytes, media_type="image/png",
                        headers={"Cache-Control": "public, max-age=3600"})

    # Get all tests for this participant
    db = get_db()
    rows = db.execute(
        """SELECT t.*, g.filename, g.domain, g.title
           FROM tests t JOIN ga_images g ON t.ga_image_id = g.id
           WHERE t.participant_id = ?
           ORDER BY t.created_at DESC""",
        (participant["id"],),
    ).fetchall()
    db.close()
    tests = [dict(r) for r in rows]

    percentile = get_participant_percentile(participant["id"])
    png_bytes = generate_dashboard_card(participant, tests,
                                         participant_percentile=percentile)
    return Response(content=png_bytes, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=600"})


# ── GA OG Image route ────────────────────────────────────────────────

# In-memory cache: ga_id -> (png_bytes, n_tests)
# Invalidated when n_tests changes (new test submitted)
_ga_og_cache: dict[int, tuple[bytes, int]] = {}


# ── Blog: GA evolution timeline ──

BLOG_VERSIONS = [
    {"v": 1, "title": "Bare bones", "desc": "Title + 3 bars only. No visual context.", "reco": "No visual hierarchy \u2014 bars alone don\u2019t communicate the problem", "score": None},
    {"v": 2, "title": "Add scissors graph", "desc": "Engagement vs Comprehension diverging lines show the gap.", "reco": "No methodological context \u2014 reader doesn\u2019t know what this measures", "score": None},
    {"v": 3, "title": "Visual Spin lens + chronometer", "desc": "Magnifying lens shows data distortion. 5.0s chrono adds the time constraint.", "reco": "Labels overflow \u2014 text competes with visual elements", "score": "~30%"},
    {"v": 4, "title": "Fix layout", "desc": "Labels below bars, axis scale, checkmark, angular accents.", "reco": "Low contrast on pink background \u2014 Comprehension label barely visible", "score": "~50%"},
    {"v": 5, "title": "Boost contrast", "desc": "Stronger red tint, annotations, 6 RCTs \u00b7 538 participants.", "reco": "S9b=0.70 (target \u22650.80), 6/11 nodes high energy", "score": "~60%"},
    {"v": 6, "title": "Gradient shine + multiplier", "desc": "\u00d77.7 multiplier, grid lines, GLANCE bar gradient glow, bigger chrono.", "reco": "Word count 31, engagement energy still 0.9", "score": "70%"},
]


@app.get("/search", response_class=HTMLResponse)
def search_page(request: Request, q: str = ""):
    """Search GAs by title, domain, or description."""
    lang = _lang(request)
    results = []
    if q and len(q) >= 2:
        db = get_db()
        rows = db.execute(
            """SELECT id, filename, slug, title, domain, description
               FROM ga_images
               WHERE public = 1
                 AND (title LIKE ? OR domain LIKE ? OR description LIKE ? OR filename LIKE ?)
               ORDER BY id DESC LIMIT 30""",
            (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")
        ).fetchall()
        db.close()
        results = [dict(r) for r in rows]
    return JSONResponse({
        "query": q,
        "count": len(results),
        "results": [
            {
                "id": r["id"],
                "slug": r.get("slug", str(r["id"])),
                "title": r.get("title", r.get("filename", "")),
                "domain": r.get("domain", ""),
                "url": f"/ga-detail/{r.get('slug', r['id'])}",
            }
            for r in results
        ],
    })


@app.get("/blog", response_class=HTMLResponse)
def blog(request: Request):
    lang = _lang(request)
    return templates.TemplateResponse("blog.html", {
        "request": request,
        "lang": lang,
    })


@app.get("/blog/ga-tests-itself", response_class=HTMLResponse)
def blog_ga_tests_itself(request: Request):
    lang = _lang(request)
    return templates.TemplateResponse("blog_ga_tests_itself.html", {
        "request": request,
        "lang": lang,
        "versions": BLOG_VERSIONS,
    })


@app.get("/blog/reader-simulation", response_class=HTMLResponse)
def blog_reader_sim(request: Request):
    lang = _lang(request)
    return templates.TemplateResponse("blog_reader_simulation.html", {
        "request": request,
        "lang": lang,
    })


@app.get("/blog/7-archetypes", response_class=HTMLResponse)
def blog_archetypes(request: Request):
    lang = _lang(request)
    return templates.TemplateResponse("blog_7_archetypes.html", {
        "request": request,
        "lang": lang,
    })


@app.get("/blog/redesign-ozempic", response_class=HTMLResponse)
def blog_ozempic(request: Request):
    lang = _lang(request)
    return templates.TemplateResponse("blog_redesign_ozempic.html", {
        "request": request,
        "lang": lang,
    })


@app.get("/og/ga/{ga_id}.png")
def og_ga_image(ga_id: int):
    """Generate a 1200x630 OG card for a GA detail page.

    Shows the GA image itself with a GLANCE score badge overlay.
    Cached in memory; invalidated when test count changes.
    """
    image = get_image_by_id(ga_id)
    if not image:
        png_bytes = generate_default_card()
        return Response(content=png_bytes, media_type="image/png",
                        headers={"Cache-Control": "public, max-age=3600"})

    # Compute current stats
    detail = get_ga_detail_stats(ga_id)
    n_tests = detail.get("n_tests", 0)
    avg_glance = detail.get("avg_glance", 0.0) if n_tests > 0 else None

    # Check cache (invalidate if test count changed)
    if ga_id in _ga_og_cache:
        cached_bytes, cached_n = _ga_og_cache[ga_id]
        if cached_n == n_tests:
            return Response(content=cached_bytes, media_type="image/png",
                            headers={"Cache-Control": "public, max-age=3600"})

    # Resolve domain label
    domain = image.get("domain", "")
    domain_label = CONFIG["domains"].get(domain, {}).get("label", domain)

    png_bytes = generate_ga_og_card(image, avg_glance, n_tests, domain_label)
    _ga_og_cache[ga_id] = (png_bytes, n_tests)
    return Response(content=png_bytes, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"})


# ── Scanpath video (animated GIF) ────────────────────────────────────

_gif_cache: dict[str, bytes] = {}


@app.get("/overlay/ga/{ga_slug}.png")
def ga_overlay(ga_slug: str):
    """Serve the graph overlay PNG for a GA (composite: GA image + overlay)."""
    image = get_image_by_slug(ga_slug)
    if not image:
        raise HTTPException(status_code=404, detail="GA not found")

    ga_id = image["id"]
    latest = get_latest_graph(ga_id)

    if not latest:
        raise HTTPException(status_code=404, detail="No graph yet")

    # Try to generate overlay on-the-fly
    try:
        from graph_renderer import render_overlay_png
        from reader_sim import simulate_reading

        image_path = os.path.join(BASE, "ga_library", image["filename"])
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image file not found")

        graph_dict = latest["graph"]
        sim = simulate_reading(graph_dict, total_ticks=50, mode="system1")
        png_path = render_overlay_png(graph_dict, sim, image_path)

        if png_path and os.path.exists(png_path):
            with open(png_path, "rb") as f:
                png_bytes = f.read()
            return Response(content=png_bytes, media_type="image/png",
                            headers={"Cache-Control": "public, max-age=3600"})
    except Exception as e:
        logger.warning(f"Overlay generation failed: {e}")

    raise HTTPException(status_code=500, detail="Overlay generation failed")


@app.get("/video/ga/{ga_slug}.gif")
def ga_video(ga_slug: str):
    """Generate or serve cached animated GIF of the scanpath simulation."""
    # Check cache
    if ga_slug in _gif_cache:
        return Response(content=_gif_cache[ga_slug], media_type="image/gif",
                        headers={"Cache-Control": "public, max-age=3600"})

    image = get_image_by_slug(ga_slug)
    if not image:
        return Response(status_code=404, content=b"GA not found")

    ga_id = image["id"]
    ga_path = os.path.join(BASE, "ga_library", image.get("filename", ""))
    if not os.path.exists(ga_path):
        return Response(status_code=404, content=b"GA image not found")

    # Get latest graph and sim
    latest = get_latest_graph(ga_id)
    if not latest:
        return Response(status_code=404, content=b"No graph available")

    graph_dict = latest.get("graph") or {}
    sims = get_reading_sims(graph_id=latest["id"])
    sim_s1 = next((s for s in sims if s.get("mode") == "system1"), None)
    if not sim_s1:
        return Response(status_code=404, content=b"No simulation available")

    sim_full = sim_s1.get("full_result") or {}

    try:
        from video_generator import generate_scanpath_gif
        gif_bytes = generate_scanpath_gif(graph_dict, sim_full, ga_path)
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        return Response(status_code=500, content=b"Video generation failed")

    if not gif_bytes:
        return Response(status_code=404, content=b"Could not generate video")

    _gif_cache[ga_slug] = gif_bytes
    return Response(content=gif_bytes, media_type="image/gif",
                    headers={"Cache-Control": "public, max-age=3600"})


# ── Changelog ──────────────────────────────────────────────────────────

@app.get("/changelog", response_class=HTMLResponse)
def changelog_page(request: Request):
    """Auto-generated changelog from git log."""
    import subprocess
    lang = _lang(request)
    changelog = []
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--format=%H|%ai|%s", "-50"],
            capture_output=True, text=True, timeout=5, cwd=BASE
        )
        current_day = None
        day_items = []
        for line in result.stdout.strip().split("\n"):
            if not line or "|" not in line:
                continue
            parts = line.split("|", 2)
            if len(parts) < 3:
                continue
            _, date_str, msg = parts
            day = date_str[:10]
            # Determine type from conventional commit prefix
            if msg.startswith("feat"):
                item_type = "feat"
                text = msg.split(":", 1)[-1].strip() if ":" in msg else msg[5:].strip()
            elif msg.startswith("fix"):
                item_type = "fix"
                text = msg.split(":", 1)[-1].strip() if ":" in msg else msg[4:].strip()
            elif msg.startswith("docs"):
                item_type = "docs"
                text = msg.split(":", 1)[-1].strip() if ":" in msg else msg[5:].strip()
            else:
                continue  # skip non-conventional commits
            if day != current_day:
                if current_day and day_items:
                    changelog.append({"date": current_day, "items": day_items})
                current_day = day
                day_items = []
            day_items.append({"type": item_type, "text": text})
        if current_day and day_items:
            changelog.append({"date": current_day, "items": day_items})
    except Exception:
        pass
    return templates.TemplateResponse("changelog.html", {
        "request": request, "lang": lang, "changelog": changelog,
    })


# ── SEO: sitemap.xml + robots.txt ──────────────────────────────────────

@app.get("/sitemap.xml")
def sitemap():
    """Dynamic sitemap for Google indexing."""
    try:
        db = get_db()
        try:
            gas = [dict(r) for r in db.execute(
                "SELECT slug FROM ga_images WHERE public = 1 AND slug IS NOT NULL ORDER BY id DESC"
            ).fetchall()]
        except Exception:
            gas = [dict(r) for r in db.execute(
                "SELECT slug FROM ga_images WHERE domain != 'user_upload' AND slug IS NOT NULL ORDER BY id DESC"
            ).fetchall()]
        try:
            domains = [dict(r) for r in db.execute(
                "SELECT DISTINCT domain FROM ga_images WHERE public = 1"
            ).fetchall()]
        except Exception:
            domains = [dict(r) for r in db.execute(
                "SELECT DISTINCT domain FROM ga_images WHERE domain != 'user_upload'"
            ).fetchall()]
        db.close()
    except Exception as e:
        logger.warning(f"Sitemap DB error: {e}")
        gas = []
        domains = []

    base = "https://glance.scisense.fr"

    urls = []
    # Static pages
    for path, priority, freq in [
        ("/", "1.0", "daily"),
        ("/analyze", "0.9", "daily"),
        ("/leaderboard", "0.8", "daily"),
        ("/blog", "0.7", "weekly"),
        ("/pricing", "0.6", "monthly"),
        ("/blog/ga-tests-itself", "0.6", "monthly"),
        ("/auth/login", "0.5", "monthly"),
    ]:
        urls.append(
            f"<url><loc>{base}{path}</loc><priority>{priority}</priority>"
            f"<changefreq>{freq}</changefreq></url>"
        )

    # Domain pages
    for d in domains:
        domain = d["domain"]
        if domain != "user_upload":
            urls.append(
                f"<url><loc>{base}/leaderboard/{domain}</loc>"
                f"<priority>0.7</priority><changefreq>weekly</changefreq></url>"
            )

    # GA detail pages
    for ga in gas:
        slug = ga["slug"]
        urls.append(
            f"<url><loc>{base}/ga-detail/{slug}</loc>"
            f"<priority>0.6</priority><changefreq>weekly</changefreq></url>"
        )

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "\n".join(urls)
    xml += "\n</urlset>"

    return Response(content=xml, media_type="application/xml")


@app.get("/robots.txt")
def robots():
    """Robots.txt with sitemap reference."""
    return Response(
        content="User-agent: *\nAllow: /\nSitemap: https://glance.scisense.fr/sitemap.xml\n",
        media_type="text/plain",
    )
