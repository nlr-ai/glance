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


# ── GA OG Card — TV NEWS BANNER style (V3) ──────────────────────────

import json as _json


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


def _banner_verdict(score_pct: int) -> tuple[str, tuple[int, int, int]]:
    """Return (verdict_label, banner_bg_color_rgb) for the score tier.

    Bold solid colors — TV news authority, not neon subtlety:
        >=80  LIMPIDE     solid green   #059669
        60-79 FLUIDE      solid teal    #0D9488
        40-59 ACCESSIBLE  solid amber   #D97706
        20-39 BRUMEUX     solid orange  #EA580C
        10-19 OPAQUE      solid red     #DC2626
        <10   ILLISIBLE   solid dark-red #991B1B
    """
    if score_pct >= 80:
        return "LIMPIDE", (5, 150, 105)       # #059669
    elif score_pct >= 60:
        return "FLUIDE", (13, 148, 136)        # #0D9488
    elif score_pct >= 40:
        return "ACCESSIBLE", (217, 119, 6)     # #D97706
    elif score_pct >= 20:
        return "BRUMEUX", (234, 88, 12)        # #EA580C
    elif score_pct >= 10:
        return "OPAQUE", (220, 38, 38)         # #DC2626
    else:
        return "ILLISIBLE", (153, 27, 27)      # #991B1B


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


def generate_ga_og_card(image: dict, avg_glance: float | None,
                        n_tests: int, domain_label: str = "") -> bytes:
    """Generate a 1200x630 OG card — TV NEWS BANNER design (V3).

    Layout:
        Top ~490px: GA image (contain-fit, dark background, dot-grid texture)
        Bottom 140px: Unified opaque banner (bold tier color) with:
            Row 1: SCORE GLANCE label | score% | verdict | domain pill
            Row 2: Standard subtitle line
            Row 3: Paper title (italic, truncated)
        Left accent: 6px white stripe on banner left edge

    Score sources (priority): real tests > sidecar predicted_score > "?"

    Args:
        image: dict from ga_images table (filename, domain, title, etc.)
        avg_glance: average GLANCE score 0.0-1.0, or None if no tests
        n_tests: number of tests for this GA
        domain_label: human-readable domain label (e.g. "BIOLOGY")

    Returns:
        PNG bytes.
    """
    BG = (15, 23, 42)  # #0F172A — dark slate
    BANNER_H = 140
    ACCENT_W = 6       # left white accent stripe

    img = Image.new("RGB", (CARD_W, CARD_H), BG)
    draw = ImageDraw.Draw(img)

    # Image zone height (no decorative texture — every pixel must communicate)
    image_zone_h = CARD_H - BANNER_H  # 490px

    # ── Resolve score ──
    score_pct, score_source = _resolve_score(image, avg_glance, n_tests)
    has_score = score_pct is not None

    if has_score:
        verdict_label, banner_color = _banner_verdict(score_pct)
    else:
        verdict_label = "PAS ENCORE EVALUE"
        banner_color = (55, 65, 81)  # #374151 — dark gray

    # ── Load and fit GA image — CONTAIN (full image, no crop) ──
    ga_path = os.path.join(BASE, "ga_library", image.get("filename", ""))
    if os.path.exists(ga_path):
        try:
            ga_img = Image.open(ga_path).convert("RGB")
            src_w, src_h = ga_img.size

            # Contain-fit: scale to fit within card width x image_zone_h
            scale = min(CARD_W / src_w, image_zone_h / src_h)
            new_w = int(src_w * scale)
            new_h = int(src_h * scale)
            ga_img = ga_img.resize((new_w, new_h), Image.LANCZOS)

            # Center the image in the available zone
            paste_x = (CARD_W - new_w) // 2
            paste_y = (image_zone_h - new_h) // 2
            img.paste(ga_img, (paste_x, paste_y))
        except Exception:
            pass

    # ── UNIFIED BANNER — opaque, bold color, bottom 140px ──
    banner_y = CARD_H - BANNER_H  # 490

    # Solid opaque banner background
    draw.rectangle(
        [(0, banner_y), (CARD_W, CARD_H)],
        fill=banner_color,
    )

    # Left accent stripe — 6px solid white, full banner height
    draw.rectangle(
        [(0, banner_y), (ACCENT_W, CARD_H)],
        fill=(255, 255, 255),
    )

    # ── Row 1 (main line) — SCORE GLANCE | score% | verdict | domain pill ──
    row1_y = banner_y + 14
    text_x = ACCENT_W + 20  # after the white stripe + padding

    # "SCORE GLANCE" — small caps authority label
    font_label = _get_font(18, bold=True)
    draw.text((text_x, row1_y + 6), "SCORE GLANCE", fill=(255, 255, 255), font=font_label)

    # Measure "SCORE GLANCE" width
    label_bbox = draw.textbbox((text_x, row1_y + 6), "SCORE GLANCE", font=font_label)
    label_right = label_bbox[2]

    # Score percentage — giant Impact font
    font_score_big = _get_impact_font(72)
    if has_score:
        score_text = f"{score_pct}%:"
    else:
        score_text = "?:"
    score_x = label_right + 24
    draw.text((score_x, row1_y - 16), score_text,
              fill=(255, 255, 255), font=font_score_big)

    # Measure score text width
    score_bbox = draw.textbbox((score_x, row1_y - 16), score_text, font=font_score_big)
    score_right = score_bbox[2]

    # Verdict — the judgment DROPS after the colon
    font_verdict_big = _get_impact_font(48)
    verdict_x = score_right + 16
    draw.text((verdict_x, row1_y + 4), verdict_label,
              fill=(255, 255, 255), font=font_verdict_big)

    # Domain pill badge (right side of row 1)
    domain_text = domain_label.upper() if domain_label else ""
    if domain_text:
        font_domain = _get_font(14, bold=True)
        d_bbox = draw.textbbox((0, 0), domain_text, font=font_domain)
        d_text_w = d_bbox[2] - d_bbox[0]
        d_text_h = d_bbox[3] - d_bbox[1]
        pill_pad_x = 14
        pill_pad_y = 6
        pill_w = d_text_w + pill_pad_x * 2
        pill_h = d_text_h + pill_pad_y * 2
        pill_x = CARD_W - 24 - pill_w
        pill_y = row1_y + 12
        # White outline pill
        _draw_rounded_rect(
            draw,
            (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
            radius=pill_h // 2,
            outline=(255, 255, 255),
            width=2,
        )
        draw.text((pill_x + pill_pad_x, pill_y + pill_pad_y),
                  domain_text, fill=(255, 255, 255), font=font_domain)

    # ── Archetype icon (between verdict and domain pill) ──
    if has_score:
        # Resolve archetype from sidecar
        sidecar_path = os.path.join(BASE, "ga_library",
            os.path.splitext(image.get("filename", ""))[0] + ".json")
        archetype_key = None
        if os.path.exists(sidecar_path):
            try:
                import json
                with open(sidecar_path) as sf:
                    sidecar = json.load(sf)
                archetype_key = sidecar.get("glance_archetype", sidecar.get("archetype"))
            except Exception:
                pass
        if archetype_key:
            icon_path = os.path.join(BASE, "static", "icons", f"archetype_{archetype_key}.png")
            if os.path.exists(icon_path):
                try:
                    arch_icon = Image.open(icon_path).convert("RGBA")
                    arch_icon = arch_icon.resize((32, 32), Image.LANCZOS)
                    # Place after verdict
                    verdict_bbox = draw.textbbox((verdict_x, row1_y + 4), verdict_label, font=font_verdict_big)
                    icon_x = verdict_bbox[2] + 16
                    icon_y = row1_y + 12
                    img.paste(arch_icon, (icon_x, icon_y), arch_icon)
                except Exception:
                    pass

    # ── Row 2 (subtitle) — standard description ──
    row2_y = row1_y + 62
    font_subtitle = _get_font(16)
    subtitle = "\u25c9 Standard de comprehension visuelle en 5 secondes"
    draw.text((text_x, row2_y), subtitle,
              fill=(255, 255, 255, 200), font=font_subtitle)

    # ── Row 3 (paper title) — italic, lighter, truncated ──
    row3_y = row2_y + 26
    title = image.get("title", "") or image.get("filename", "")
    font_title = _get_italic_font(14)
    if title:
        # Truncate to fit within banner width minus margins
        max_title_w = CARD_W - text_x - 30
        display_title = f'"{title}"'
        while True:
            t_bbox = draw.textbbox((0, 0), display_title, font=font_title)
            if t_bbox[2] - t_bbox[0] <= max_title_w or len(display_title) <= 10:
                break
            # Chop from the inner text, keep closing quote
            display_title = display_title[:len(display_title) - 4] + '..."'
        draw.text((text_x, row3_y), display_title,
                  fill=(220, 220, 220), font=font_title)

    # DOI / source (right side of row 3, if available)
    doi = image.get("doi", "")
    if doi and has_score:
        font_doi = _get_font(12)
        doi_display = doi if len(doi) <= 40 else doi[:37] + "..."
        doi_bbox = draw.textbbox((0, 0), doi_display, font=font_doi)
        doi_w = doi_bbox[2] - doi_bbox[0]
        draw.text((CARD_W - 24 - doi_w, row3_y + 2), doi_display,
                  fill=(200, 200, 200), font=font_doi)

    # ── Export to PNG bytes ──
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()
