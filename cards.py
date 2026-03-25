"""GLANCE OG Image Card Generator — PIL-based server-side PNG rendering.

Generates 1200x630 social sharing cards for:
  - /card/{test_id}.png — single test result card
  - /card/dashboard/{participant_token}.png — overall participant dashboard card
  - /og/ga/{ga_id}.png — GA detail page OG card (GA image + GLANCE score badge)

Uses system fonts (Inter/Segoe UI/Arial) with GLANCE dark theme.
"""

import io
import math
import os
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Theme constants (match style.css design tokens) ──────────────────
BG_COLOR = (15, 23, 42)            # --bg: #0f172a
SURFACE_COLOR = (30, 41, 59)       # --surface: #1e293b
BORDER_COLOR = (51, 65, 85)        # --border: #334155
TEXT_COLOR = (226, 232, 240)       # --text: #e2e8f0
TEXT_MUTED = (148, 163, 184)       # --text-muted: #94a3b8
TEXT_DIM = (100, 116, 139)         # --text-dim: #64748b
PRIMARY = (59, 130, 246)           # --primary: #3b82f6
PASS_COLOR = (34, 197, 94)         # --pass: #22c55e
FAIL_COLOR = (239, 68, 68)         # --fail: #ef4444
WARN_COLOR = (234, 179, 8)        # amber-500
TEAL = (13, 148, 136)             # teal-600
GOLD = (251, 191, 36)             # amber-400 — top 10% percentile

CARD_W = 1200
CARD_H = 630

BASE = os.path.dirname(__file__)

# ── Font loading ─────────────────────────────────────────────────────

# Try system fonts in priority order
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/Inter-SemiBold.ttf",
    "C:/Windows/Fonts/Inter-Medium.ttf",
    "C:/Windows/Fonts/Inter-Regular.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    # Linux paths (for Render deployment)
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

_FONT_BOLD_CANDIDATES = [
    "C:/Windows/Fonts/Inter-SemiBold.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


@lru_cache(maxsize=32)
def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a TrueType font at the given size, with fallback chain."""
    candidates = _FONT_BOLD_CANDIDATES if bold else _FONT_CANDIDATES
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    # Ultimate fallback
    return ImageFont.load_default()


def _score_color(score: float) -> tuple[int, int, int]:
    """Return color based on score value (0.0-1.0)."""
    if score >= 0.70:
        return PASS_COLOR
    elif score >= 0.40:
        return WARN_COLOR
    else:
        return FAIL_COLOR


def _verdict_text(score: float) -> str:
    """Return French verdict string based on score."""
    if score >= 0.70:
        return "Ce GA communique efficacement"
    elif score >= 0.40:
        return "Ce GA est partiellement decode"
    else:
        return "Ce GA perd trop d'info en scroll"


def _draw_rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple, radius: int,
                        fill=None, outline=None, width: int = 1):
    """Draw a rounded rectangle (PIL compatibility helper)."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _load_thumbnail(filename: str, max_size: tuple = (200, 200)) -> Image.Image | None:
    """Load and resize a GA thumbnail image."""
    path = os.path.join(BASE, "ga_library", filename)
    if not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        img.thumbnail(max_size, Image.LANCZOS)
        return img
    except Exception:
        return None


# ── Card generators ──────────────────────────────────────────────────

def _percentile_color(pctl: int) -> tuple[int, int, int]:
    """Return color for percentile badge: gold top 10%, teal top 50%, white rest."""
    if pctl >= 90:
        return GOLD
    elif pctl >= 50:
        return TEAL
    else:
        return TEXT_MUTED


def _percentile_text(pctl: int) -> str:
    """Return French percentile label."""
    if pctl >= 90:
        return f"Top {100 - pctl}%"
    return f"Meilleur que {pctl}% des testeurs"


def generate_test_card(test: dict, participant_percentile: int = 0) -> bytes:
    """Generate a 1200x630 PNG card for a single test result.

    Args:
        test: dict from get_test() — includes glance_score, filename, domain, title, etc.
        participant_percentile: 0-100 percentile rank among all testers.

    Returns:
        PNG bytes.
    """
    img = Image.new("RGB", (CARD_W, CARD_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    score = float(test.get("glance_score", 0))
    score_pct = round(score * 100)
    color = _score_color(score)
    verdict = _verdict_text(score)
    domain = test.get("domain", "")
    title = test.get("title", "") or test.get("filename", "")

    # ── Background accent stripe ──
    draw.rectangle([(0, 0), (CARD_W, 6)], fill=PRIMARY)

    # ── GLANCE logo / title (top left) ──
    font_logo = _get_font(42, bold=True)
    font_sub = _get_font(18)
    draw.text((60, 40), "GLANCE", fill=TEXT_COLOR, font=font_logo)
    draw.text((60, 92), "Premier Regard — SciSense", fill=TEXT_MUTED, font=font_sub)

    # ── GA thumbnail (left side, vertically centered) ──
    thumb = _load_thumbnail(test.get("filename", ""), max_size=(240, 280))
    thumb_x = 60
    thumb_y = 160
    if thumb:
        # Draw a subtle border/frame
        tw, th = thumb.size
        frame_pad = 4
        _draw_rounded_rect(
            draw,
            (thumb_x - frame_pad, thumb_y - frame_pad,
             thumb_x + tw + frame_pad, thumb_y + th + frame_pad),
            radius=8, fill=SURFACE_COLOR, outline=BORDER_COLOR, width=2
        )
        # Paste thumbnail
        if thumb.mode == "RGBA":
            img.paste(thumb, (thumb_x, thumb_y), thumb)
        else:
            img.paste(thumb, (thumb_x, thumb_y))
        content_left = thumb_x + tw + 50
    else:
        content_left = 60

    # ── Score (big number, right of thumbnail) ──
    font_score = _get_font(120, bold=True)
    font_pct = _get_font(48, bold=True)
    score_text = str(score_pct)
    score_x = content_left + 20
    score_y = 170

    draw.text((score_x, score_y), score_text, fill=color, font=font_score)

    # Measure score text width to place "%" after it
    score_bbox = draw.textbbox((score_x, score_y), score_text, font=font_score)
    pct_x = score_bbox[2] + 5
    draw.text((pct_x, score_y + 30), "%", fill=color, font=font_pct)

    # ── Score label ──
    font_label = _get_font(20)
    draw.text((score_x, score_y + 140), "Score GLANCE composite", fill=TEXT_MUTED, font=font_label)

    # ── Percentile rank (below score label) ──
    if participant_percentile > 0:
        font_pctl = _get_font(22, bold=True)
        pctl_text = _percentile_text(participant_percentile)
        pctl_color = _percentile_color(participant_percentile)
        draw.text((score_x, score_y + 168), pctl_text, fill=pctl_color, font=font_pctl)
        verdict_y_offset = 210
    else:
        verdict_y_offset = 180

    # ── Verdict (below score / percentile) ──
    font_verdict = _get_font(26, bold=True)
    verdict_y = score_y + verdict_y_offset
    draw.text((score_x, verdict_y), verdict, fill=color, font=font_verdict)

    # ── Domain badge (top right) ──
    if domain:
        font_domain = _get_font(16, bold=True)
        domain_label = domain.upper()
        d_bbox = draw.textbbox((0, 0), domain_label, font=font_domain)
        d_w = d_bbox[2] - d_bbox[0] + 24
        d_h = d_bbox[3] - d_bbox[1] + 14
        d_x = CARD_W - 60 - d_w
        d_y = 50
        _draw_rounded_rect(draw, (d_x, d_y, d_x + d_w, d_y + d_h),
                           radius=6, fill=SURFACE_COLOR, outline=BORDER_COLOR)
        draw.text((d_x + 12, d_y + 5), domain_label, fill=TEXT_MUTED, font=font_domain)

    # ── GA title (truncated, below domain badge area, right side) ──
    if title and len(title) > 5:
        font_title = _get_font(16)
        # Truncate if too long
        display_title = title if len(title) <= 60 else title[:57] + "..."
        title_x = CARD_W - 60
        # Right-align
        t_bbox = draw.textbbox((0, 0), display_title, font=font_title)
        t_w = t_bbox[2] - t_bbox[0]
        draw.text((title_x - t_w, 90), display_title, fill=TEXT_DIM, font=font_title)

    # ── Sub-scores bar (bottom area) ──
    bar_y = 480
    font_bar = _get_font(15, bold=True)
    font_bar_val = _get_font(22, bold=True)
    sub_scores = [
        ("Recall (S9a)", float(test.get("s9a_score", test.get("s9a_pass", 0)))),
        ("Hierarchie (S9b)", float(test.get("s9b_pass", 0))),
        ("Actionabilite (S9c)", float(test.get("s9c_score", test.get("s9c_pass", 0)))),
    ]

    bar_start_x = content_left + 20
    bar_spacing = 200
    for i, (label, val) in enumerate(sub_scores):
        bx = bar_start_x + i * bar_spacing
        val_text = f"{round(val * 100)}%" if val <= 1.0 else f"{round(val)}%"
        draw.text((bx, bar_y), label, fill=TEXT_DIM, font=font_bar)
        draw.text((bx, bar_y + 22), val_text, fill=_score_color(val), font=font_bar_val)

    # ── CTA (bottom center) ──
    font_cta = _get_font(20, bold=True)
    cta_text = "Teste ton oeil -> glance.scisense.fr"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=font_cta)
    cta_w = cta_bbox[2] - cta_bbox[0]
    cta_x = (CARD_W - cta_w) // 2
    cta_y = CARD_H - 50
    draw.text((cta_x, cta_y), cta_text, fill=TEAL, font=font_cta)

    # ── Bottom border accent ──
    draw.rectangle([(0, CARD_H - 6), (CARD_W, CARD_H)], fill=PRIMARY)

    # Export to PNG bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()


def generate_dashboard_card(participant: dict, tests: list[dict],
                            participant_percentile: int = 0) -> bytes:
    """Generate a 1200x630 PNG card for a participant's overall dashboard.

    Args:
        participant: dict with token, clinical_domain, etc.
        tests: list of test dicts for this participant.
        participant_percentile: 0-100 percentile rank among all testers.

    Returns:
        PNG bytes.
    """
    img = Image.new("RGB", (CARD_W, CARD_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    n_tests = len(tests)
    if n_tests > 0:
        avg_score = sum(float(t.get("glance_score", 0)) for t in tests) / n_tests
    else:
        avg_score = 0.0
    avg_pct = round(avg_score * 100)
    color = _score_color(avg_score)

    domain = participant.get("clinical_domain", "")

    # ── Top accent ──
    draw.rectangle([(0, 0), (CARD_W, 6)], fill=PRIMARY)

    # ── GLANCE header ──
    font_logo = _get_font(42, bold=True)
    font_sub = _get_font(18)
    draw.text((60, 40), "GLANCE", fill=TEXT_COLOR, font=font_logo)
    draw.text((60, 92), "Premier Regard — Tableau de bord", fill=TEXT_MUTED, font=font_sub)

    # ── Overall score (centered, big) ──
    font_score = _get_font(140, bold=True)
    font_pct = _get_font(56, bold=True)
    score_text = str(avg_pct)
    s_bbox = draw.textbbox((0, 0), score_text, font=font_score)
    s_w = s_bbox[2] - s_bbox[0]
    p_bbox = draw.textbbox((0, 0), "%", font=font_pct)
    p_w = p_bbox[2] - p_bbox[0]
    total_w = s_w + p_w + 5

    score_x = (CARD_W - total_w) // 2
    score_y = 160

    draw.text((score_x, score_y), score_text, fill=color, font=font_score)
    draw.text((score_x + s_w + 5, score_y + 35), "%", fill=color, font=font_pct)

    # ── Label ──
    font_label = _get_font(22)
    label_text = "Score GLANCE moyen"
    l_bbox = draw.textbbox((0, 0), label_text, font=font_label)
    l_w = l_bbox[2] - l_bbox[0]
    draw.text(((CARD_W - l_w) // 2, score_y + 160), label_text, fill=TEXT_MUTED, font=font_label)

    # ── Percentile rank (centered, below label) ──
    if participant_percentile > 0:
        font_pctl = _get_font(24, bold=True)
        pctl_text = _percentile_text(participant_percentile)
        pctl_color = _percentile_color(participant_percentile)
        pctl_bbox = draw.textbbox((0, 0), pctl_text, font=font_pctl)
        pctl_w = pctl_bbox[2] - pctl_bbox[0]
        draw.text(((CARD_W - pctl_w) // 2, score_y + 190), pctl_text,
                  fill=pctl_color, font=font_pctl)

    # ── Stats row (tests count + domain) ──
    stats_y = 420
    font_stat_label = _get_font(16)
    font_stat_val = _get_font(28, bold=True)

    # Number of tests
    stat_x1 = CARD_W // 2 - 200
    draw.text((stat_x1, stats_y), "Tests completes", fill=TEXT_DIM, font=font_stat_label)
    draw.text((stat_x1, stats_y + 24), str(n_tests), fill=TEXT_COLOR, font=font_stat_val)

    # Domain
    stat_x2 = CARD_W // 2 + 50
    draw.text((stat_x2, stats_y), "Domaine", fill=TEXT_DIM, font=font_stat_label)
    draw.text((stat_x2, stats_y + 24), domain or "General", fill=TEXT_COLOR, font=font_stat_val)

    # ── Best score badge ──
    if n_tests > 0:
        best = max(float(t.get("glance_score", 0)) for t in tests)
        best_pct = round(best * 100)
        stat_x3 = CARD_W // 2 + 300
        draw.text((stat_x3, stats_y), "Meilleur score", fill=TEXT_DIM, font=font_stat_label)
        draw.text((stat_x3, stats_y + 24), f"{best_pct}%",
                  fill=_score_color(best), font=font_stat_val)

    # ── Verdict line ──
    font_verdict = _get_font(24, bold=True)
    if n_tests == 0:
        verdict = "Aucun test complete"
        v_color = TEXT_DIM
    elif avg_score >= 0.70:
        verdict = "Expert en decodage visuel"
        v_color = PASS_COLOR
    elif avg_score >= 0.40:
        verdict = "Oeil en cours d'entrainement"
        v_color = WARN_COLOR
    else:
        verdict = "Le scroll cache l'essentiel"
        v_color = FAIL_COLOR

    v_bbox = draw.textbbox((0, 0), verdict, font=font_verdict)
    v_w = v_bbox[2] - v_bbox[0]
    draw.text(((CARD_W - v_w) // 2, 510), verdict, fill=v_color, font=font_verdict)

    # ── CTA ──
    font_cta = _get_font(20, bold=True)
    cta_text = "Teste ton oeil -> glance.scisense.fr"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=font_cta)
    cta_w = cta_bbox[2] - cta_bbox[0]
    draw.text(((CARD_W - cta_w) // 2, CARD_H - 50), cta_text, fill=TEAL, font=font_cta)

    # ── Bottom accent ──
    draw.rectangle([(0, CARD_H - 6), (CARD_W, CARD_H)], fill=PRIMARY)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()


def generate_default_card() -> bytes:
    """Generate a default/fallback card when test is not found."""
    img = Image.new("RGB", (CARD_W, CARD_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (CARD_W, 6)], fill=PRIMARY)
    draw.rectangle([(0, CARD_H - 6), (CARD_W, CARD_H)], fill=PRIMARY)

    font_logo = _get_font(52, bold=True)
    font_sub = _get_font(24)
    font_cta = _get_font(28, bold=True)

    # Centered GLANCE logo
    t_bbox = draw.textbbox((0, 0), "GLANCE", font=font_logo)
    t_w = t_bbox[2] - t_bbox[0]
    draw.text(((CARD_W - t_w) // 2, 200), "GLANCE", fill=TEXT_COLOR, font=font_logo)

    sub = "Premier Regard — SciSense"
    s_bbox = draw.textbbox((0, 0), sub, font=font_sub)
    s_w = s_bbox[2] - s_bbox[0]
    draw.text(((CARD_W - s_w) // 2, 270), sub, fill=TEXT_MUTED, font=font_sub)

    desc = "Teste ta comprehension des Graphical Abstracts en 5 secondes"
    d_bbox = draw.textbbox((0, 0), desc, font=font_sub)
    d_w = d_bbox[2] - d_bbox[0]
    draw.text(((CARD_W - d_w) // 2, 330), desc, fill=TEXT_DIM, font=font_sub)

    cta = "glance.scisense.fr"
    c_bbox = draw.textbbox((0, 0), cta, font=font_cta)
    c_w = c_bbox[2] - c_bbox[0]
    draw.text(((CARD_W - c_w) // 2, 440), cta, fill=TEAL, font=font_cta)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()


# ── GA OG Card — MULTI-CHANNEL VERDICT STAMP design (V5) ─────────────

import json as _json
import random as _random

from PIL import ImageEnhance

# Impact / Arial Black font candidates for bold score display
_FONT_IMPACT_CANDIDATES = [
    "C:/Windows/Fonts/impact.ttf",
    "C:/Windows/Fonts/ariblk.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    # Linux fallbacks
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]

_FONT_ITALIC_CANDIDATES = [
    "C:/Windows/Fonts/ariali.ttf",
    "C:/Windows/Fonts/Inter-Regular.ttf",
    # Linux fallbacks
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
]


@lru_cache(maxsize=8)
def _get_impact_font(size: int) -> ImageFont.FreeTypeFont:
    """Load Impact/Arial Black font (or bold fallback) for score display."""
    for path in _FONT_IMPACT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


@lru_cache(maxsize=8)
def _get_italic_font(size: int) -> ImageFont.FreeTypeFont:
    """Load italic font for paper title display."""
    for path in _FONT_ITALIC_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ── Tier key resolution ─────────────────────────────────────────────

def _get_tier_key(score_pct: int) -> str:
    """Return the tier key string for a given score percentage."""
    if score_pct >= 80:
        return 'limpide'
    elif score_pct >= 60:
        return 'clair'
    elif score_pct >= 40:
        return 'ambigu'
    elif score_pct >= 20:
        return 'confus'
    elif score_pct >= 10:
        return 'obscur'
    else:
        return 'incomprehensible'


# ── Multi-channel tier parameter dicts ──────────────────────────────

# Channel 1: COLOR (gradient start, gradient end)
TIER_COLORS = {
    'limpide':    ((5, 150, 105),  (4, 120, 87)),
    'clair':     ((13, 148, 136), (15, 118, 110)),
    'ambigu': ((217, 119, 6),  (180, 83, 9)),
    'confus':    ((234, 88, 12),  (194, 65, 12)),
    'obscur':     ((220, 38, 38),  (185, 28, 28)),
    'incomprehensible':  ((153, 27, 27),  (127, 29, 29)),
}

# Channel 2: ROTATION (degrees, positive = CCW in PIL)
TIER_ROTATION = {
    'incomprehensible':  -7,
    'obscur':     -5,
    'confus':    -3,
    'ambigu': -2,
    'clair':     -1,
    'limpide':     0,
}

# Channel 3: STAMP SIZE (width, height)
TIER_STAMP_SIZE = {
    'incomprehensible':  (320, 210),
    'obscur':     (290, 190),
    'confus':    (260, 175),
    'ambigu': (250, 170),
    'clair':     (270, 175),
    'limpide':    (310, 200),
}

# Channel 6: TYPOGRAPHY — score number font size
TIER_SCORE_FONT = {
    'incomprehensible':  72,
    'obscur':     64,
    'confus':    56,
    'ambigu': 52,
    'clair':     56,
    'limpide':    64,
}

# Channel 7: SPEED LINES — count
TIER_SPEED_LINES = {
    'incomprehensible':  6,
    'obscur':     4,
    'confus':    2,
    'ambigu': 1,
    'clair':     2,
    'limpide':    4,
}

# Channel 8: EMOTION ICON
TIER_ICONS = {
    'incomprehensible':  '\u26a0',   # warning
    'obscur':     '\u2717',   # fail X
    'confus':    '\u2193',   # down arrow
    'ambigu': '\u2192',   # right arrow
    'clair':     '\u2191',   # up arrow
    'limpide':    '\u2605',   # star
}

# Verdict labels (same as V4 but organized)
TIER_VERDICT = {
    'limpide':    'LIMPIDE',
    'clair':     'CLAIR',
    'ambigu':    'AMBIGU',
    'confus':    'CONFUS',
    'obscur':    'OBSCUR',
    'incomprehensible':  'INCOMPRÉHENSIBLE',
}


def _stamp_verdict(score_pct: int) -> tuple[str, tuple[int, int, int], tuple[int, int, int]]:
    """Return (verdict_label, gradient_start_rgb, gradient_end_rgb) for the score tier."""
    tier = _get_tier_key(score_pct)
    return TIER_VERDICT[tier], TIER_COLORS[tier][0], TIER_COLORS[tier][1]


def _resolve_score(image: dict, avg_glance: float | None,
                   n_tests: int) -> tuple[int | None, str]:
    """Resolve the best available score for a GA, with source label.

    Priority:
        1. Real test data (avg_glance) when n_tests > 0
        2. Predicted score from sidecar JSON (predicted_score field)
        3. Fallback: None

    Returns:
        (score_pct or None, source_label)
    """
    # 1. Real test data
    if n_tests > 0 and avg_glance is not None:
        return round(avg_glance * 100), f"{n_tests} test{'s' if n_tests > 1 else ''}"

    # 2. Sidecar JSON predicted_score
    filename = image.get("filename", "")
    if filename:
        stem = filename.rsplit(".", 1)[0]
        sidecar_path = os.path.join(BASE, "ga_library", stem + ".json")
        if os.path.exists(sidecar_path):
            try:
                with open(sidecar_path, encoding="utf-8") as f:
                    sidecar = _json.load(f)
                ps = sidecar.get("predicted_score")
                if ps is not None:
                    return int(ps), "score predit"
                # Try archetype approximated_scores.s9b
                approx = sidecar.get("approximated_scores", {})
                s9b = approx.get("s9b")
                if s9b is not None:
                    return round(float(s9b) * 100), "score approx."
            except Exception:
                pass

    # 3. Fallback
    return None, ""


def _add_noise_texture(img: Image.Image, intensity: int = 12):
    """Add subtle noise/stipple texture to an RGBA image for a printed feel."""
    pixels = img.load()
    w, h = img.size
    rng = _random.Random(42)
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a < 10:
                continue
            noise = rng.randint(-intensity, intensity)
            r = max(0, min(255, r + noise))
            g = max(0, min(255, g + noise))
            b = max(0, min(255, b + noise))
            pixels[x, y] = (r, g, b, a)


def _draw_speed_lines(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                      stamp_w: int, stamp_h: int, tier: str):
    """Draw tier-varying speed lines radiating outward from the stamp.

    LIMPIDE uses golden lines (#FFD700). All others use white.
    Count varies by tier — more for extreme scores (both ends).
    """
    n_lines = TIER_SPEED_LINES.get(tier, 2)
    line_color = (255, 215, 0, 50) if tier == 'limpide' else (255, 255, 255, 38)

    # Base line templates — we pick n_lines from this pool
    all_lines = [
        (-stamp_w // 2 - 10, -stamp_h // 4,     -stamp_w // 2 - 55, -stamp_h // 4 - 12),
        (-stamp_w // 2 - 8,  stamp_h // 6,       -stamp_w // 2 - 48, stamp_h // 6 + 8),
        (stamp_w // 2 + 10,  -stamp_h // 3,      stamp_w // 2 + 50,  -stamp_h // 3 - 10),
        (stamp_w // 2 + 12,  stamp_h // 5,       stamp_w // 2 + 58,  stamp_h // 5 + 6),
        (-stamp_w // 2 - 15, -stamp_h // 2 + 10, -stamp_w // 2 - 60, -stamp_h // 2 - 5),
        (stamp_w // 2 + 8,   -stamp_h // 6,      stamp_w // 2 + 52,  -stamp_h // 6 - 4),
    ]

    for i in range(min(n_lines, len(all_lines))):
        sx, sy, ex, ey = all_lines[i]
        draw.line(
            [(cx + sx, cy + sy), (cx + ex, cy + ey)],
            fill=line_color,
            width=2 if tier in ('incomprehensible', 'limpide') else 1,
        )


def _apply_ga_treatment(ga_img: Image.Image, tier: str) -> Image.Image:
    """Apply tier-varying visual treatment to the GA background image.

    Channel 4: GA IMAGE TREATMENT
        Low scores: desaturate (gray/washed out = "hard to understand")
        NOT blur (opaque ≠ blurry) and NOT darken (hiding the GA defeats the purpose)
        High scores: saturate + brighten (crystal clear, vibrant)
    """
    if tier == 'incomprehensible':
        # Strong desaturation — almost grayscale. "My brain can't process this"
        ga_img = ImageEnhance.Color(ga_img).enhance(0.15)
        ga_img = ImageEnhance.Brightness(ga_img).enhance(0.85)
    elif tier == 'obscur':
        # Partial desaturation — washed out, dull. "I can see it but can't understand"
        ga_img = ImageEnhance.Color(ga_img).enhance(0.35)
        ga_img = ImageEnhance.Brightness(ga_img).enhance(0.9)
    elif tier == 'confus':
        # Slight desaturation — muted colors. "Not clear enough"
        ga_img = ImageEnhance.Color(ga_img).enhance(0.65)
    elif tier == 'ambigu':
        pass  # Normal — no treatment
    elif tier == 'clair':
        ga_img = ImageEnhance.Color(ga_img).enhance(1.15)
        ga_img = ImageEnhance.Brightness(ga_img).enhance(1.05)
    elif tier == 'limpide':
        ga_img = ImageEnhance.Color(ga_img).enhance(1.3)
        ga_img = ImageEnhance.Brightness(ga_img).enhance(1.1)
        # Subtle sparkle crystals — scattered transparent bright dots
        import random
        sparkle = Image.new("RGBA", ga_img.size, (0, 0, 0, 0))
        sp_draw = ImageDraw.Draw(sparkle)
        rng = random.Random(42)  # deterministic
        w, h = ga_img.size
        for _ in range(25):
            sx = rng.randint(20, w - 20)
            sy = rng.randint(20, h - 20)
            size = rng.randint(2, 5)
            alpha = rng.randint(40, 90)
            sp_draw.ellipse(
                [sx - size, sy - size, sx + size, sy + size],
                fill=(255, 255, 255, alpha),
            )
            # Cross sparkle lines
            sp_draw.line([(sx - size * 2, sy), (sx + size * 2, sy)],
                         fill=(255, 255, 255, alpha // 2), width=1)
            sp_draw.line([(sx, sy - size * 2), (sx, sy + size * 2)],
                         fill=(255, 255, 255, alpha // 2), width=1)
        ga_img = Image.alpha_composite(ga_img.convert("RGBA"), sparkle).convert("RGB")

    return ga_img


# Reaction smileys per tier — viewer's COMPREHENSION reaction, not emotion
TIER_REACTION = {
    'incomprehensible': '🫠',    # melting brain — "what am I looking at"
    'obscur':    '❓',     # question mark — "I don't get it"
    'confus':   '🤔',    # thinking — "I think I get it... maybe"
    'ambigu': '💡',   # lightbulb — "ah I see"
    'clair':    '✅',     # check — "got it, clear"
    'limpide':   '🤯',    # mind blown — "I understood everything instantly"
}


def _build_stamp_v5(score_pct: int, score_source: str, tier: str,
                    verdict_label: str, grad_start: tuple, grad_end: tuple,
                    archetype_icon: Image.Image | None = None) -> Image.Image:
    """Build the floating verdict stamp as an RGBA image — V5 multi-channel.

    Varies stamp size, score font size, texture, and emotion icon by tier.
    Includes the explanation line: "X% du message compris en 5s".

    Returns an RGBA Image on a padded transparent canvas.
    """
    STAMP_W, STAMP_H = TIER_STAMP_SIZE[tier]
    PAD = 80  # extra space for rotation + shadow (larger stamps need more)
    canvas_w = STAMP_W + PAD * 2
    canvas_h = STAMP_H + PAD * 2

    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    # ── Stamp gradient background with rounded corners ──
    stamp_img = Image.new("RGBA", (STAMP_W, STAMP_H), (0, 0, 0, 0))

    # Build gradient layer masked to rounded rect
    grad_layer = Image.new("RGBA", (STAMP_W, STAMP_H), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(grad_layer)
    for row in range(STAMP_H):
        t = row / max(1, STAMP_H - 1)
        r = int(grad_start[0] + (grad_end[0] - grad_start[0]) * t)
        g = int(grad_start[1] + (grad_end[1] - grad_start[1]) * t)
        b = int(grad_start[2] + (grad_end[2] - grad_start[2]) * t)
        grad_draw.line([(0, row), (STAMP_W - 1, row)], fill=(r, g, b, 255))

    mask = Image.new("L", (STAMP_W, STAMP_H), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (STAMP_W - 1, STAMP_H - 1)], radius=14, fill=255)
    grad_layer.putalpha(mask)
    stamp_img = Image.alpha_composite(
        Image.new("RGBA", (STAMP_W, STAMP_H), (0, 0, 0, 0)),
        grad_layer,
    )

    # ── Channel 5: TEXTURE ON STAMP ──
    if tier == 'incomprehensible':
        # Heavy diagonal warning stripes + thick lines
        stripe_layer = Image.new("RGBA", (STAMP_W, STAMP_H), (0, 0, 0, 0))
        stripe_draw = ImageDraw.Draw(stripe_layer)
        stripe_spacing = 14
        for offset in range(-STAMP_H, STAMP_W + STAMP_H, stripe_spacing):
            stripe_draw.line(
                [(offset, 0), (offset + STAMP_H, STAMP_H)],
                fill=(0, 0, 0, 40),
                width=8,
            )
        stripe_layer.putalpha(mask)
        stamp_img = Image.alpha_composite(stamp_img, stripe_layer)
        _add_noise_texture(stamp_img, intensity=16)
    elif tier in ('obscur', 'confus'):
        # Medium noise grain
        _add_noise_texture(stamp_img, intensity=12)
    elif tier == 'limpide':
        # Clean + subtle shimmer (white highlight gradient on top half)
        shimmer = Image.new("RGBA", (STAMP_W, STAMP_H), (0, 0, 0, 0))
        shimmer_draw = ImageDraw.Draw(shimmer)
        for row in range(STAMP_H // 3):
            alpha = int(25 * (1.0 - row / (STAMP_H // 3)))
            shimmer_draw.line([(0, row), (STAMP_W - 1, row)],
                              fill=(255, 255, 255, alpha))
        shimmer.putalpha(mask)
        stamp_img = Image.alpha_composite(stamp_img, shimmer)
        _add_noise_texture(stamp_img, intensity=4)
    else:
        # accessible, fluide — light noise
        _add_noise_texture(stamp_img, intensity=8)

    # ── White border ──
    border_draw = ImageDraw.Draw(stamp_img)
    border_width = 4 if tier in ('incomprehensible', 'limpide') else 3
    border_draw.rounded_rectangle(
        [(0, 0), (STAMP_W - 1, STAMP_H - 1)],
        radius=14,
        outline=(255, 255, 255, 220),
        width=border_width,
    )

    # ── Text content inside the stamp ──
    draw = ImageDraw.Draw(stamp_img)

    # "SCORE GLANCE" header (left-aligned) + emotion icon (right-aligned)
    font_header = _get_font(12, bold=True)
    header_text = "S C O R E   G L A N C E"
    h_bbox = draw.textbbox((0, 0), header_text, font=font_header)
    h_w = h_bbox[2] - h_bbox[0]
    header_x = (STAMP_W - h_w) // 2 - 10  # shift left to make room for icon
    draw.text((max(16, header_x), 14), header_text,
              fill=(255, 255, 255, 230), font=font_header)

    # Channel 8: EMOTION ICON — top-right corner of stamp
    icon_char = TIER_ICONS[tier]
    font_icon = _get_font(18, bold=True)
    draw.text((STAMP_W - 30, 10), icon_char,
              fill=(255, 255, 255, 200), font=font_icon)

    # Thin white separator line
    line_y = 34
    line_margin = 20
    draw.line(
        [(line_margin, line_y), (STAMP_W - line_margin, line_y)],
        fill=(255, 255, 255, 180),
        width=1,
    )

    # Channel 6: TYPOGRAPHY — score number with tier-varying font size
    score_font_size = TIER_SCORE_FONT[tier]
    font_score = _get_impact_font(score_font_size)
    score_text = f"{score_pct}%"
    s_bbox = draw.textbbox((0, 0), score_text, font=font_score)
    s_w = s_bbox[2] - s_bbox[0]
    s_h = s_bbox[3] - s_bbox[1]
    score_y = 38
    draw.text(((STAMP_W - s_w) // 2, score_y), score_text,
              fill=(255, 255, 255), font=font_score)

    # Verdict label — bold, below score
    font_verdict = _get_font(26, bold=True)
    v_bbox = draw.textbbox((0, 0), verdict_label, font=font_verdict)
    v_w = v_bbox[2] - v_bbox[0]
    verdict_y = score_y + s_h + 6
    draw.text(((STAMP_W - v_w) // 2, verdict_y), verdict_label,
              fill=(255, 255, 255), font=font_verdict)

    # CRITICAL ADDITION: Explanation line — "X% du message compris en 5s"
    explanation = f"{score_pct}% du message compris en 5s"
    font_explain = _get_font(14, bold=False)
    e_bbox = draw.textbbox((0, 0), explanation, font=font_explain)
    e_w = e_bbox[2] - e_bbox[0]
    explain_y = verdict_y + (v_bbox[3] - v_bbox[1]) + 4
    draw.text(((STAMP_W - e_w) // 2, explain_y), explanation,
              fill=(255, 255, 255, 200), font=font_explain)

    # Source line — small, bottom area
    font_source = _get_font(11, bold=False)
    source_text = f"\u25c9 glance.scisense.fr"
    src_bbox = draw.textbbox((0, 0), source_text, font=font_source)
    src_w = src_bbox[2] - src_bbox[0]
    draw.text(((STAMP_W - src_w) // 2, STAMP_H - 22), source_text,
              fill=(255, 255, 255, 153), font=font_source)

    # ── Tier watermark (subtle) ──
    if tier == 'limpide':
        font_wm = _get_impact_font(80)
        draw.text((STAMP_W - 70, STAMP_H - 90), "\u2713",
                  fill=(255, 255, 255, 20), font=font_wm)
    elif tier in ('incomprehensible', 'obscur'):
        font_wm = _get_impact_font(80)
        draw.text((STAMP_W - 70, STAMP_H - 90), "\u2717",
                  fill=(255, 255, 255, 20), font=font_wm)

    # ── Archetype icon (bottom-right inside stamp) ──
    if archetype_icon is not None:
        icon_resized = archetype_icon.resize((28, 28), Image.LANCZOS)
        stamp_img.paste(icon_resized, (STAMP_W - 38, STAMP_H - 38), icon_resized)

    # ── Place stamp on padded canvas ──
    canvas.paste(stamp_img, (PAD, PAD), stamp_img)

    return canvas


# ── GA OG Card — CIRCULAR SEAL VERDICT STAMP design (V6) ─────────────

# Seal radius per tier
SEAL_RADIUS = {
    'incomprehensible':  160,
    'obscur':     140,
    'confus':    130,
    'ambigu': 120,
    'clair':     130,
    'limpide':    150,
}

# Number of teeth on the seal edge
SEAL_TEETH = {
    'limpide':    24,
    'clair':     20,
    'ambigu': 18,
    'confus':    16,
    'obscur':     14,
    'incomprehensible':  12,
}

# Seal fill colors per tier
SEAL_COLORS = {
    'limpide':    (184, 134, 11),   # #B8860B gold
    'clair':     (13, 148, 136),   # #0D9488 teal
    'ambigu': (217, 119, 6),    # #D97706 amber
    'confus':    (234, 88, 12),    # #EA580C orange
    'obscur':     (220, 38, 38),    # #DC2626 red
    'incomprehensible':  (153, 27, 27),    # #991B1B dark red
}

# Border width per tier
SEAL_BORDER_W = {
    'limpide':    3,
    'clair':     2,
    'ambigu': 2,
    'confus':    2,
    'obscur':     3,
    'incomprehensible':  4,
}

# Rotation (same progression as V5)
SEAL_ROTATION = {
    'limpide':     0,
    'clair':     -2,
    'ambigu': -3,
    'confus':    -4,
    'obscur':     -5,
    'incomprehensible':  -7,
}

# Reaction emoji per tier (comprehension reaction)
SEAL_REACTION = {
    'incomprehensible':  '\U0001fae0',   # melting face
    'obscur':     '\u2753',       # question mark
    'confus':    '\U0001f914',   # thinking face
    'ambigu': '\U0001f4a1',   # lightbulb
    'clair':     '\u2705',       # check
    'limpide':    '\U0001f92f',   # mind blown
}

# Score font size inside seal
SEAL_SCORE_FONT = {
    'incomprehensible':  56,
    'obscur':     52,
    'confus':    48,
    'ambigu': 44,
    'clair':     48,
    'limpide':    56,
}

# Verdict font size
SEAL_VERDICT_FONT = {
    'incomprehensible':  22,
    'obscur':     22,
    'confus':    20,
    'ambigu': 18,
    'clair':     20,
    'limpide':    22,
}

# Certified text for limpide
SEAL_CERTIFIED_TEXT = "CERTIFIE CLAIR"


def _draw_seal_shape(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                     outer_r: int, inner_r: int, n_teeth: int,
                     fill_color: tuple, border_color: tuple,
                     border_width: int = 2,
                     irregular: bool = False, rng=None):
    """Draw a serrated circle (seal/cog shape).

    If irregular=True, randomizes tooth depth for rough worn look.
    """
    points = []
    for i in range(n_teeth * 2):
        angle = math.pi * 2 * i / (n_teeth * 2) - math.pi / 2
        r = outer_r if i % 2 == 0 else inner_r
        if irregular and rng:
            r += rng.uniform(-6, 6)
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=fill_color, outline=border_color)
    # Draw border by drawing outline polygon on top if border_width > 1
    if border_width > 1:
        for bw in range(border_width):
            draw.polygon(points, fill=None, outline=border_color)


def _build_stamp_v6(score_pct: int, score_source: str, tier: str,
                    verdict_label: str, archetype_icon: Image.Image | None = None) -> Image.Image:
    """Build the CIRCULAR SEAL verdict stamp as an RGBA image — V6.

    The seal morphs from a gold "seal of approval" (high scores)
    to a violent "rejection stamp" (low scores).

    Returns an RGBA Image on a padded transparent canvas.
    """
    radius = SEAL_RADIUS[tier]
    n_teeth = SEAL_TEETH[tier]
    seal_color = SEAL_COLORS[tier]
    border_w = SEAL_BORDER_W[tier]
    score_font_size = SEAL_SCORE_FONT[tier]
    verdict_font_size = SEAL_VERDICT_FONT[tier]

    # Tooth depth: outer_r vs inner_r
    tooth_depth = int(radius * 0.08)
    outer_r = radius
    inner_r = radius - tooth_depth

    # Canvas with generous padding for rotation + shadow + splatter
    PAD = 100
    canvas_size = (radius + PAD) * 2
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    cx, cy = canvas_size // 2, canvas_size // 2

    rng = _random.Random(42)

    # ── Ink splatter (ILLISIBLE only — behind everything) ──
    if tier == 'incomprehensible':
        splatter_layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        sp_draw = ImageDraw.Draw(splatter_layer)
        for _ in range(20):
            sx = cx + rng.randint(-radius - 40, radius + 40)
            sy = cy + rng.randint(-radius - 40, radius + 40)
            sr = rng.randint(2, 7)
            sp_draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                            fill=(*seal_color, 80))
        canvas = Image.alpha_composite(canvas, splatter_layer)

    # ── Ink bleed (low scores: draw seal twice with offset at low opacity) ──
    if tier in ('incomprehensible', 'obscur'):
        bleed_layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        bleed_draw = ImageDraw.Draw(bleed_layer)
        irregular = tier == 'incomprehensible'
        bleed_rng = _random.Random(99)
        _draw_seal_shape(bleed_draw, cx + 2, cy + 2,
                         outer_r, inner_r, n_teeth,
                         fill_color=(*seal_color, 50),
                         border_color=(*seal_color, 30),
                         border_width=1,
                         irregular=irregular, rng=bleed_rng)
        canvas = Image.alpha_composite(canvas, bleed_layer)

    # ── Double-stamp bounce (ILLISIBLE only) ──
    if tier == 'incomprehensible':
        bounce_layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        bounce_draw = ImageDraw.Draw(bounce_layer)
        bounce_rng = _random.Random(77)
        _draw_seal_shape(bounce_draw, cx + 4, cy - 3,
                         outer_r - 2, inner_r - 2, n_teeth,
                         fill_color=(*seal_color, 35),
                         border_color=(*seal_color, 25),
                         border_width=1,
                         irregular=True, rng=bounce_rng)
        canvas = Image.alpha_composite(canvas, bounce_layer)

    # ── Main seal shape ──
    seal_layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    seal_draw = ImageDraw.Draw(seal_layer)

    irregular = tier in ('incomprehensible', 'obscur')
    main_rng = _random.Random(42)
    border_color = (255, 255, 255, 220)
    _draw_seal_shape(seal_draw, cx, cy,
                     outer_r, inner_r, n_teeth,
                     fill_color=(*seal_color, 255),
                     border_color=border_color,
                     border_width=border_w,
                     irregular=irregular, rng=main_rng)

    # ── Inner ornamental circle (limpide and fluide only) ──
    if tier in ('limpide', 'clair'):
        inner_ring_r = int(radius * 0.82)
        seal_draw.ellipse(
            [cx - inner_ring_r, cy - inner_ring_r,
             cx + inner_ring_r, cy + inner_ring_r],
            fill=None, outline=(255, 255, 255, 100), width=1)

    # ── Inner decorative dots for limpide (notary-style) ──
    if tier == 'limpide':
        dot_ring_r = int(radius * 0.78)
        n_dots = 36
        for i in range(n_dots):
            angle = math.pi * 2 * i / n_dots - math.pi / 2
            dx = cx + dot_ring_r * math.cos(angle)
            dy = cy + dot_ring_r * math.sin(angle)
            seal_draw.ellipse([dx - 1, dy - 1, dx + 1, dy + 1],
                              fill=(255, 255, 255, 70))

    canvas = Image.alpha_composite(canvas, seal_layer)

    # ── Text content on top of the seal ──
    text_layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    # Layout: icon → "Clarté visuelle : X%" → VERDICT (BIG) → SCORE GLANCE
    # The VERDICT is the hero — biggest text. Score contextualizes it above.

    # -- Pre-measure all text blocks --
    # Top icon
    if tier == 'limpide':
        top_icon = "\u2713"
        font_top_icon = _get_impact_font(28)
    else:
        top_icon = TIER_ICONS.get(tier, '')
        font_top_icon = _get_font(20, bold=True)
    ti_bbox = draw.textbbox((0, 0), top_icon, font=font_top_icon)
    ti_h = ti_bbox[3] - ti_bbox[1]
    ti_w = ti_bbox[2] - ti_bbox[0]

    # Context line: "Clarté visuelle : X%" — small, factual, BEFORE verdict
    context_line = f"Clart\u00e9 visuelle : {score_pct}%"
    font_context = _get_font(13, bold=True)
    ctx_bbox = draw.textbbox((0, 0), context_line, font=font_context)
    ctx_w = ctx_bbox[2] - ctx_bbox[0]
    ctx_h = ctx_bbox[3] - ctx_bbox[1]

    # VERDICT — THE BIGGEST TEXT, the judgment that DROPS
    if tier == 'limpide':
        display_verdict = SEAL_CERTIFIED_TEXT
    else:
        display_verdict = verdict_label
    # Verdict font is BIGGER than score (was inverted)
    font_verdict = _get_impact_font(score_font_size)  # use the big font for verdict
    v_bbox = draw.textbbox((0, 0), display_verdict, font=font_verdict)
    v_w = v_bbox[2] - v_bbox[0]
    v_h = v_bbox[3] - v_bbox[1]

    # Score number — secondary, smaller
    font_score = _get_font(verdict_font_size, bold=True)  # use the smaller font for score
    score_text = f"{score_pct}%"
    s_bbox = draw.textbbox((0, 0), score_text, font=font_score)
    s_w = s_bbox[2] - s_bbox[0]
    s_h = s_bbox[3] - s_bbox[1]

    # Explanation
    explanation = "en 5 secondes"
    explanation2 = ""
    font_explain = _get_font(11, bold=False)
    e_bbox = draw.textbbox((0, 0), explanation, font=font_explain)
    e_h = e_bbox[3] - e_bbox[1]

    # "SCORE GLANCE" footer
    font_bottom = _get_font(9, bold=True)
    bottom_text = "S C O R E   G L A N C E"
    bt_bbox = draw.textbbox((0, 0), bottom_text, font=font_bottom)
    bt_w = bt_bbox[2] - bt_bbox[0]
    bt_h = bt_bbox[3] - bt_bbox[1]

    # Total content height with gaps
    # Order: icon → context ("Clarté visuelle: X%") → VERDICT (BIG) → explanation → footer
    gap1 = 4   # icon → context
    gap2 = 2   # context → verdict
    gap3 = 4   # verdict → explanation
    gap4 = 6   # explanation → footer
    total_h = (ti_h + gap1 +
               ctx_h + gap2 +
               v_h + gap3 +
               e_h + gap4 + bt_h)

    start_y = cy - total_h // 2

    # -- Draw: icon → context → VERDICT → explanation → footer --

    # Top icon
    draw.text((cx - ti_w // 2, start_y),
              top_icon, fill=(255, 255, 255, 230), font=font_top_icon)
    cur_y = start_y + ti_h + gap1

    # Context: "Clarté visuelle : 17%" — small, factual
    draw.text((cx - ctx_w // 2, cur_y),
              context_line, fill=(255, 255, 255, 200), font=font_context)
    cur_y += ctx_h + gap2

    # VERDICT — THE HERO, biggest text
    draw.text((cx - v_w // 2, cur_y),
              display_verdict, fill=(255, 255, 255, 255), font=font_verdict)
    cur_y += v_h + gap3

    # Explanation: "en 5 secondes"
    e_w = draw.textbbox((0, 0), explanation, font=font_explain)[2]
    draw.text((cx - e_w // 2, cur_y),
              explanation, fill=(255, 255, 255, 160), font=font_explain)
    cur_y += e_h + gap4

    # "SCORE GLANCE" footer
    draw.text((cx - bt_w // 2, cur_y),
              bottom_text, fill=(255, 255, 255, 150), font=font_bottom)

    canvas = Image.alpha_composite(canvas, text_layer)

    return canvas


def generate_ga_og_card(image: dict, avg_glance: float | None,
                        n_tests: int, domain_label: str = "",
                        override_score_pct: int | None = None) -> bytes:
    """Generate a 1200x630 OG card — MULTI-CHANNEL VERDICT STAMP (V5).

    8 visual channels vary simultaneously by tier:
        1. Color (gradient)       2. Rotation (stamp tilt)
        3. Stamp size             4. GA image treatment (blur/brighten)
        5. Texture on stamp       6. Typography (score font size)
        7. Speed lines (count)    8. Emotion icon

    Plus: explanation line "X% du message compris en 5 secondes" inside stamp.

    Args:
        image: dict from ga_images table (filename, domain, title, etc.)
        avg_glance: average GLANCE score 0.0-1.0, or None if no tests
        n_tests: number of tests for this GA
        domain_label: human-readable domain label (e.g. "BIOLOGY")
        override_score_pct: if set, forces this score (for testing/simulation)

    Returns:
        PNG bytes.
    """
    img = Image.new("RGBA", (CARD_W, CARD_H), (40, 40, 40, 255))

    # ── Resolve score ──
    if override_score_pct is not None:
        score_pct = override_score_pct
        score_source = "simulation"
        has_score = True
    else:
        score_pct, score_source = _resolve_score(image, avg_glance, n_tests)
        has_score = score_pct is not None

    if has_score:
        tier = _get_tier_key(score_pct)
        verdict_label, grad_start, grad_end = _stamp_verdict(score_pct)
    else:
        tier = 'ambigu'  # neutral fallback for no-score
        verdict_label = "EN ATTENTE"
        grad_start = (55, 65, 81)
        grad_end = (45, 55, 71)

    # ── Load and fit GA image — COVER (full bleed, fills entire card) ──
    ga_path = os.path.join(BASE, "ga_library", image.get("filename", ""))
    ga_loaded = False
    if os.path.exists(ga_path):
        try:
            ga_img = Image.open(ga_path).convert("RGBA")
            src_w, src_h = ga_img.size

            # Cover-fit: scale to fill the entire card (may crop)
            scale = max(CARD_W / src_w, CARD_H / src_h)
            new_w = int(src_w * scale)
            new_h = int(src_h * scale)
            ga_img = ga_img.resize((new_w, new_h), Image.LANCZOS)

            # Center-crop to card dimensions
            crop_x = (new_w - CARD_W) // 2
            crop_y = (new_h - CARD_H) // 2
            ga_img = ga_img.crop((crop_x, crop_y, crop_x + CARD_W, crop_y + CARD_H))

            # Channel 4: GA IMAGE TREATMENT — varies by tier
            if has_score:
                ga_img = _apply_ga_treatment(ga_img, tier)

            # ── Diagonal split: if overlay PNG exists, composite top-left=original, bottom-right=overlay ──
            overlay_path = None
            fn = image.get("filename", "")
            if fn:
                stem = fn.rsplit(".", 1)[0]
                candidate = os.path.join(BASE, "ga_library", stem + "_overlay.png")
                if os.path.exists(candidate):
                    overlay_path = candidate

            if overlay_path:
                try:
                    ov_img = Image.open(overlay_path).convert("RGBA")
                    # Cover-fit overlay to same card dimensions
                    ov_scale = max(CARD_W / ov_img.width, CARD_H / ov_img.height)
                    ov_w = int(ov_img.width * ov_scale)
                    ov_h = int(ov_img.height * ov_scale)
                    ov_img = ov_img.resize((ov_w, ov_h), Image.LANCZOS)
                    ov_cx = (ov_w - CARD_W) // 2
                    ov_cy = (ov_h - CARD_H) // 2
                    ov_img = ov_img.crop((ov_cx, ov_cy, ov_cx + CARD_W, ov_cy + CARD_H))

                    # Diagonal mask: top-left triangle = original GA, bottom-right = overlay
                    diag_mask = Image.new("L", (CARD_W, CARD_H), 0)
                    diag_draw = ImageDraw.Draw(diag_mask)
                    # Bottom-right triangle (white = overlay visible)
                    diag_draw.polygon(
                        [(CARD_W, 0), (CARD_W, CARD_H), (0, CARD_H)],
                        fill=255,
                    )
                    # Composite: paste GA first, then overlay through mask
                    composite = ga_img.copy()
                    composite.paste(ov_img, (0, 0), diag_mask)
                    # Diagonal divider line (subtle white)
                    comp_draw = ImageDraw.Draw(composite)
                    comp_draw.line(
                        [(CARD_W, 0), (0, CARD_H)],
                        fill=(255, 255, 255, 120), width=2,
                    )
                    ga_img = composite
                except Exception:
                    pass  # fallback: use GA image without overlay

            img.paste(ga_img, (0, 0))
            ga_loaded = True
        except Exception:
            pass

    if not ga_loaded:
        # Fallback: dark gradient background
        draw_bg = ImageDraw.Draw(img)
        for row in range(CARD_H):
            t = row / CARD_H
            gray = int(30 + 20 * t)
            draw_bg.line([(0, row), (CARD_W, row)], fill=(gray, gray, gray + 10, 255))

    # ── Slight darkening vignette over the image for readability ──
    vignette = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    vig_draw = ImageDraw.Draw(vignette)
    vig_draw.rectangle([(0, 0), (CARD_W, CARD_H)], fill=(0, 0, 0, 40))
    img = Image.alpha_composite(img, vignette)

    # ── FLOATING VERDICT STAMP ──
    if has_score:
        # Load archetype icon if available
        archetype_icon = None
        sidecar_path = os.path.join(BASE, "ga_library",
            os.path.splitext(image.get("filename", ""))[0] + ".json")
        if os.path.exists(sidecar_path):
            try:
                with open(sidecar_path) as sf:
                    sidecar = _json.load(sf)
                archetype_key = sidecar.get("glance_archetype", sidecar.get("archetype"))
                if archetype_key:
                    icon_path = os.path.join(BASE, "static", "icons",
                                             f"archetype_{archetype_key}.png")
                    if os.path.exists(icon_path):
                        archetype_icon = Image.open(icon_path).convert("RGBA")
            except Exception:
                pass

        stamp_canvas = _build_stamp_v6(
            score_pct, score_source, tier, verdict_label, archetype_icon,
        )

        # Channel 2: ROTATION — varies by tier
        rotation_deg = -SEAL_ROTATION[tier]
        stamp_rotated = stamp_canvas.rotate(
            rotation_deg, expand=True, resample=Image.BICUBIC
        )

        # ── Drop shadow ──
        shadow_offset_x, shadow_offset_y = 6, 8
        shadow_blur_radius = 20
        stamp_alpha = stamp_rotated.split()[3]
        shadow_alpha_blurred = stamp_alpha.filter(
            ImageFilter.GaussianBlur(shadow_blur_radius)
        )
        shadow_color = Image.new("RGBA", stamp_rotated.size, (0, 0, 0, 102))
        shadow_color.putalpha(shadow_alpha_blurred)

        # Position: center-left, slightly above middle
        seal_r = SEAL_RADIUS[tier]
        stamp_cx = CARD_W // 2 - 140
        stamp_cy = CARD_H // 2 - 40
        paste_x = stamp_cx - stamp_rotated.width // 2
        paste_y = stamp_cy - stamp_rotated.height // 2

        # Paste shadow first (offset)
        img.paste(
            shadow_color,
            (paste_x + shadow_offset_x, paste_y + shadow_offset_y),
            shadow_color,
        )

        # Paste the stamp
        img.paste(stamp_rotated, (paste_x, paste_y), stamp_rotated)

        # Channel 7: SPEED LINES — tier-varying count and color
        speed_draw = ImageDraw.Draw(img)
        _draw_speed_lines(speed_draw, stamp_cx, stamp_cy, seal_r * 2, seal_r * 2, tier)

    else:
        # No score: show a muted "?" stamp (unchanged from V4)
        no_stamp_w, no_stamp_h = 280, 180
        no_score_stamp = Image.new("RGBA", (no_stamp_w + 120, no_stamp_h + 120), (0, 0, 0, 0))
        ns_inner = Image.new("RGBA", (no_stamp_w, no_stamp_h), (0, 0, 0, 0))

        ns_mask = Image.new("L", (no_stamp_w, no_stamp_h), 0)
        ns_mask_draw = ImageDraw.Draw(ns_mask)
        ns_mask_draw.rounded_rectangle([(0, 0), (no_stamp_w - 1, no_stamp_h - 1)],
                                       radius=12, fill=255)

        ns_grad = Image.new("RGBA", (no_stamp_w, no_stamp_h), (0, 0, 0, 0))
        ns_grad_draw = ImageDraw.Draw(ns_grad)
        for row in range(no_stamp_h):
            t = row / max(1, no_stamp_h - 1)
            g = int(55 + (45 - 55) * t)
            ns_grad_draw.line([(0, row), (no_stamp_w - 1, row)],
                              fill=(g, g + 10, g + 20, 255))
        ns_grad.putalpha(ns_mask)
        ns_inner = Image.alpha_composite(
            Image.new("RGBA", (no_stamp_w, no_stamp_h), (0, 0, 0, 0)), ns_grad
        )

        _add_noise_texture(ns_inner, intensity=8)

        ns_draw = ImageDraw.Draw(ns_inner)
        ns_draw.rounded_rectangle(
            [(0, 0), (no_stamp_w - 1, no_stamp_h - 1)], radius=12,
            outline=(255, 255, 255, 150), width=3,
        )

        font_h = _get_font(12, bold=True)
        hdr = "S C O R E   G L A N C E"
        hb = ns_draw.textbbox((0, 0), hdr, font=font_h)
        ns_draw.text(((no_stamp_w - (hb[2] - hb[0])) // 2, 14), hdr,
                     fill=(255, 255, 255, 200), font=font_h)
        ns_draw.line([(24, 34), (no_stamp_w - 24, 34)],
                     fill=(255, 255, 255, 140), width=1)

        font_q = _get_impact_font(64)
        qb = ns_draw.textbbox((0, 0), "?", font=font_q)
        ns_draw.text(((no_stamp_w - (qb[2] - qb[0])) // 2, 38), "?",
                     fill=(255, 255, 255), font=font_q)

        font_v = _get_font(28, bold=True)
        vb = ns_draw.textbbox((0, 0), "EN ATTENTE", font=font_v)
        ns_draw.text(((no_stamp_w - (vb[2] - vb[0])) // 2, 110), "EN ATTENTE",
                     fill=(255, 255, 255), font=font_v)

        font_s = _get_font(11)
        st = "\u25c9 glance.scisense.fr"
        sb = ns_draw.textbbox((0, 0), st, font=font_s)
        ns_draw.text(((no_stamp_w - (sb[2] - sb[0])) // 2, 156), st,
                     fill=(255, 255, 255, 130), font=font_s)

        no_score_stamp.paste(ns_inner, (60, 60), ns_inner)
        stamp_rotated = no_score_stamp.rotate(4, expand=True, resample=Image.BICUBIC)

        s_alpha = stamp_rotated.split()[3]
        s_alpha_blur = s_alpha.filter(ImageFilter.GaussianBlur(18))
        shadow_c = Image.new("RGBA", stamp_rotated.size, (0, 0, 0, 80))
        shadow_c.putalpha(s_alpha_blur)

        stamp_cx = CARD_W // 2 - 140
        stamp_cy = CARD_H // 2 - 40
        px = stamp_cx - stamp_rotated.width // 2
        py = stamp_cy - stamp_rotated.height // 2

        img.paste(shadow_c, (px + 6, py + 8), shadow_c)
        img.paste(stamp_rotated, (px, py), stamp_rotated)

    # ── FROSTED GLASS TITLE STRIP (bottom) ──
    strip_h = 50
    strip_y = CARD_H - strip_h

    frost = Image.new("RGBA", (CARD_W, strip_h), (255, 255, 255, 38))
    frost_draw = ImageDraw.Draw(frost)
    frost_draw.line([(0, 0), (CARD_W, 0)], fill=(255, 255, 255, 77), width=1)
    img.paste(frost, (0, strip_y), frost)

    # ── Title strip content ──
    strip_draw = ImageDraw.Draw(img)
    title = image.get("title", "") or image.get("filename", "")
    domain_text = domain_label.upper() if domain_label else ""

    font_strip_title = _get_font(16, bold=True)
    if title:
        max_title_w = CARD_W - 200
        display_title = title
        while True:
            tb = strip_draw.textbbox((0, 0), display_title, font=font_strip_title)
            if tb[2] - tb[0] <= max_title_w or len(display_title) <= 10:
                break
            display_title = display_title[:len(display_title) - 4] + "..."

        title_y = strip_y + (strip_h - (tb[3] - tb[1])) // 2
        strip_draw.text((21, title_y + 1), display_title,
                        fill=(0, 0, 0, 120), font=font_strip_title)
        strip_draw.text((20, title_y), display_title,
                        fill=(255, 255, 255, 230), font=font_strip_title)

    glance_right_margin = 20
    font_glance = _get_font(18, bold=True)
    glance_text = "GLANCE"
    gb = strip_draw.textbbox((0, 0), glance_text, font=font_glance)
    glance_w = gb[2] - gb[0]
    glance_x = CARD_W - glance_right_margin - glance_w
    glance_y = strip_y + (strip_h - (gb[3] - gb[1])) // 2

    strip_draw.text((glance_x + 1, glance_y + 1), glance_text,
                    fill=(0, 0, 0, 100), font=font_glance)
    strip_draw.text((glance_x, glance_y), glance_text,
                    fill=(255, 255, 255, 240), font=font_glance)

    if domain_text:
        font_domain_pill = _get_font(11, bold=True)
        dp_bbox = strip_draw.textbbox((0, 0), domain_text, font=font_domain_pill)
        dp_w = dp_bbox[2] - dp_bbox[0]
        dp_h = dp_bbox[3] - dp_bbox[1]
        pill_pad_x = 8
        pill_pad_y = 4
        pill_total_w = dp_w + pill_pad_x * 2
        pill_total_h = dp_h + pill_pad_y * 2
        pill_x = glance_x - pill_total_w - 14
        pill_y = strip_y + (strip_h - pill_total_h) // 2

        pill_layer = Image.new("RGBA", (pill_total_w, pill_total_h), (0, 0, 0, 0))
        pill_draw = ImageDraw.Draw(pill_layer)
        pill_draw.rounded_rectangle(
            [(0, 0), (pill_total_w - 1, pill_total_h - 1)],
            radius=pill_total_h // 2,
            fill=(255, 255, 255, 50),
            outline=(255, 255, 255, 100),
            width=1,
        )
        img.paste(pill_layer, (pill_x, pill_y), pill_layer)

        strip_draw = ImageDraw.Draw(img)
        strip_draw.text((pill_x + pill_pad_x, pill_y + pill_pad_y),
                        domain_text, fill=(255, 255, 255, 200),
                        font=font_domain_pill)

    # ── Convert to RGB for PNG export ──
    final = img.convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()
