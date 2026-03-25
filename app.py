"""GLANCE Premier Regard — FastAPI server."""

import os
import json
import re
import uuid
import random

import yaml
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db import get_db, init_db, create_participant, get_participant_by_token
from db import get_next_image, save_test, get_test, get_stats
from db import get_all_tests, get_image_count, get_all_images, add_ga_image
from db import get_image_by_id, get_tests_for_image
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
)
from config_loader import get_constant

BASE = os.path.dirname(__file__)

app = FastAPI(title="GLANCE — Premier Regard")
templates = Jinja2Templates(directory=os.path.join(BASE, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE, "static")), name="static")
app.mount("/ga", StaticFiles(directory=os.path.join(BASE, "ga_library")), name="ga")

with open(os.path.join(BASE, "config.yaml"), encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)


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


# ── Routes ────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/onboard", response_class=HTMLResponse)
def onboard(request: Request):
    return templates.TemplateResponse("onboard.html", {"request": request, "config": CONFIG})


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
    create_participant(token, clinical_domain, experience_years,
                       data_literacy, grade_familiar, colorblind_status,
                       input_mode=input_mode)
    response = RedirectResponse(url="/test", status_code=303)
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

    image = get_next_image(participant["id"])
    if not image:
        return templates.TemplateResponse("complete.html", {"request": request})

    domain = image["domain"]
    questions = CONFIG["domains"].get(domain, CONFIG["domains"]["generic"])
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
    )
    return RedirectResponse(url=f"/reveal/{test_id}", status_code=303)


@app.get("/reveal/{test_id}", response_class=HTMLResponse)
def reveal(request: Request, test_id: int):
    participant = _get_participant(request)
    if not participant:
        return RedirectResponse(url="/onboard")

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

    return templates.TemplateResponse("reveal.html", {
        "request": request,
        "test": test,
        "stats": stats,
        "has_more": has_more,
        "glance_score": round(glance_score, 2),
        "glance_label": glance_label,
        "speed_accuracy": speed_acc,
        "s9a_score": round(float(s9a_score), 3),
        "s10_hit": s10_hit,
        "fluency_score": round(fluency, 4),
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

    return templates.TemplateResponse("spin.html", {
        "request": request,
        "control": control,
        "vec": vec,
        "products": products,
        "q2_text": questions["q2"],
    })


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    stats = get_stats()
    tests = get_all_tests()
    images = get_all_images()

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

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
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
    })


# ── Leaderboard routes ────────────────────────────────────────────────


@app.get("/leaderboard", response_class=HTMLResponse)
def leaderboard(request: Request):
    domain_config = CONFIG.get("domains", {})
    data = get_leaderboard_data(domain_config)
    domains = sorted(
        data.items(),
        key=lambda kv: (kv[1]["avg_score"] is not None, kv[1]["avg_score"] or 0),
        reverse=True,
    )
    return templates.TemplateResponse("leaderboard.html", {
        "request": request,
        "domains": domains,
    })


@app.get("/leaderboard/{domain}", response_class=HTMLResponse)
def leaderboard_domain(request: Request, domain: str):
    domain_config = CONFIG.get("domains", {})
    data = get_domain_leaderboard(domain, domain_config)
    if not data:
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")
    return templates.TemplateResponse("leaderboard_domain.html", {
        "request": request,
        "domain": domain,
        "data": data,
    })


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

    # 1. What the GA shows
    if description:
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
def ga_detail(request: Request, ga_id: int):
    """GA detail page with executive summary, study reference, and analysis."""
    image = get_image_by_id(ga_id)
    if not image:
        raise HTTPException(status_code=404, detail="GA not found")

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

    return templates.TemplateResponse("ga_detail.html", {
        "request": request,
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
    })


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    """Admin analytics dashboard — platform-wide metrics and charts."""
    analytics = get_admin_analytics()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "analytics": analytics,
        "analytics_json": json.dumps(analytics, ensure_ascii=False),
    })
