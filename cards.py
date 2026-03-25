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


# ── GA OG Card (GA image + GLANCE score badge overlay) ───────────────


def _score_badge_colors(score_pct: int) -> tuple[tuple, tuple]:
    """Return (color_start, color_end) gradient pair for the score badge."""
    if score_pct >= 80:
        return (16, 185, 129), (5, 150, 105)       # green #10b981 -> #059669
    elif score_pct >= 60:
        return (132, 204, 22), (101, 163, 13)       # yellow-green #84cc16 -> #65a30d
    elif score_pct >= 40:
        return (245, 158, 11), (217, 119, 6)        # amber #f59e0b -> #d97706
    else:
        return (239, 68, 68), (220, 38, 38)         # red #ef4444 -> #dc2626


def _score_verdict(score_pct: int) -> str:
    """Return descriptive French verdict for score."""
    if score_pct >= 90:
        return "LIMPIDE"
    elif score_pct >= 80:
        return "FLUIDE"
    elif score_pct >= 70:
        return "ACCESSIBLE"
    elif score_pct >= 60:
        return "BRUMEUX"
    elif score_pct >= 40:
        return "OPAQUE"
    else:
        return "ILLISIBLE"


def _draw_score_badge(img: Image.Image, score_pct: int, cx: int, cy: int,
                      radius: int = 100):
    """Draw a visually stunning circular score badge with glow effect.

    Args:
        img: target RGBA image to composite onto
        cx, cy: center position of badge
        radius: badge radius in pixels
        score_pct: 0-100 integer
    """
    color_start, color_end = _score_badge_colors(score_pct)
    badge_size = radius * 2 + 60  # extra for glow
    badge = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    center = badge_size // 2

    # Outer glow: large blurred circle
    glow_color = (*color_start, 80)
    bd.ellipse(
        (center - radius - 20, center - radius - 20,
         center + radius + 20, center + radius + 20),
        fill=glow_color,
    )
    badge = badge.filter(ImageFilter.GaussianBlur(radius=18))
    bd = ImageDraw.Draw(badge)

    # Main circle with gradient effect (radial approximation via concentric rings)
    for r_offset in range(radius, 0, -1):
        t = 1.0 - (r_offset / radius)
        cr = int(color_start[0] + (color_end[0] - color_start[0]) * t)
        cg = int(color_start[1] + (color_end[1] - color_start[1]) * t)
        cb = int(color_start[2] + (color_end[2] - color_start[2]) * t)
        bd.ellipse(
            (center - r_offset, center - r_offset,
             center + r_offset, center + r_offset),
            fill=(cr, cg, cb, 240),
        )

    # Inner highlight (subtle lighter ring at top)
    highlight_r = radius - 8
    for i in range(6):
        alpha = int(40 - i * 6)
        bd.arc(
            (center - highlight_r + i, center - highlight_r + i,
             center + highlight_r - i, center - highlight_r + radius // 2),
            start=200, end=340,
            fill=(*TEXT_COLOR, alpha), width=2,
        )

    # Score text
    font_score = _get_font(72 if score_pct < 100 else 62, bold=True)
    score_text = f"{score_pct}%"
    s_bbox = bd.textbbox((0, 0), score_text, font=font_score)
    s_w = s_bbox[2] - s_bbox[0]
    s_h = s_bbox[3] - s_bbox[1]
    bd.text(
        (center - s_w // 2, center - s_h // 2 - 14),
        score_text, fill=(255, 255, 255, 255), font=font_score,
    )

    # Verdict text below score
    verdict = _score_verdict(score_pct)
    font_verdict = _get_font(18, bold=True)
    v_bbox = bd.textbbox((0, 0), verdict, font=font_verdict)
    v_w = v_bbox[2] - v_bbox[0]
    bd.text(
        (center - v_w // 2, center + s_h // 2 - 6),
        verdict, fill=(255, 255, 255, 200), font=font_verdict,
    )

    # Paste badge onto main image
    paste_x = cx - badge_size // 2
    paste_y = cy - badge_size // 2
    img.paste(badge, (paste_x, paste_y), badge)


def generate_ga_og_card(image: dict, avg_glance: float | None,
                        n_tests: int, domain_label: str = "") -> bytes:
    """Generate a 1200x630 OG card: GA image background + GLANCE score badge.

    Args:
        image: dict from ga_images table (filename, domain, title, etc.)
        avg_glance: average GLANCE score 0.0-1.0, or None if no tests
        n_tests: number of tests for this GA
        domain_label: human-readable domain label (e.g. "MEDICAL")

    Returns:
        PNG bytes.
    """
    canvas = Image.new("RGBA", (CARD_W, CARD_H), (20, 20, 30, 255))

    # ── Load and fit GA image ──
    ga_path = os.path.join(BASE, "ga_library", image.get("filename", ""))
    if os.path.exists(ga_path):
        try:
            ga_img = Image.open(ga_path).convert("RGBA")
            # Scale to fill 1200x630, center-crop
            src_w, src_h = ga_img.size
            scale = max(CARD_W / src_w, CARD_H / src_h)
            new_w = int(src_w * scale)
            new_h = int(src_h * scale)
            ga_img = ga_img.resize((new_w, new_h), Image.LANCZOS)
            # Center crop
            left = (new_w - CARD_W) // 2
            top = (new_h - CARD_H) // 2
            ga_img = ga_img.crop((left, top, left + CARD_W, top + CARD_H))
            canvas.paste(ga_img, (0, 0), ga_img)
        except Exception:
            pass

    draw = ImageDraw.Draw(canvas)

    # ── Bottom gradient overlay for text readability ──
    gradient_h = 280
    for y in range(CARD_H - gradient_h, CARD_H):
        progress = (y - (CARD_H - gradient_h)) / gradient_h
        # Ease-in curve for smoother gradient
        alpha = int(220 * (progress ** 1.5))
        draw.line([(0, y), (CARD_W, y)], fill=(15, 23, 42, alpha))

    # ── Top-left: subtle dark overlay + GLANCE branding ──
    # Top gradient for branding readability
    top_grad_h = 80
    for y in range(top_grad_h):
        progress = 1.0 - (y / top_grad_h)
        alpha = int(160 * (progress ** 2))
        draw.line([(0, y), (CARD_W, y)], fill=(15, 23, 42, alpha))

    font_brand = _get_font(28, bold=True)
    # Shadow
    draw.text((32, 22), "GLANCE", fill=(0, 0, 0, 120), font=font_brand)
    draw.text((30, 20), "GLANCE", fill=(255, 255, 255, 230), font=font_brand)

    # ── Top-right: domain badge pill ──
    if domain_label:
        font_domain = _get_font(15, bold=True)
        d_text = domain_label.upper()
        d_bbox = draw.textbbox((0, 0), d_text, font=font_domain)
        d_w = d_bbox[2] - d_bbox[0] + 28
        d_h = d_bbox[3] - d_bbox[1] + 16
        d_x = CARD_W - 30 - d_w
        d_y = 20
        # Pill background
        draw.rounded_rectangle(
            (d_x, d_y, d_x + d_w, d_y + d_h),
            radius=d_h // 2,
            fill=(15, 23, 42, 180),
        )
        draw.text(
            (d_x + 14, d_y + 6), d_text,
            fill=(255, 255, 255, 220), font=font_domain,
        )

    # ── Score badge or "EN ATTENTE" badge ──
    if n_tests > 0 and avg_glance is not None:
        score_pct = round(avg_glance * 100)
        # Position: bottom-right area
        badge_cx = CARD_W - 160
        badge_cy = CARD_H - 180
        _draw_score_badge(canvas, score_pct, badge_cx, badge_cy, radius=95)

        # Number of tests below badge
        draw = ImageDraw.Draw(canvas)  # refresh after paste
        font_tests = _get_font(14)
        tests_text = f"{n_tests} test{'s' if n_tests > 1 else ''}"
        t_bbox = draw.textbbox((0, 0), tests_text, font=font_tests)
        t_w = t_bbox[2] - t_bbox[0]
        draw.text(
            (badge_cx - t_w // 2, badge_cy + 110),
            tests_text, fill=(255, 255, 255, 160), font=font_tests,
        )
    else:
        # No test data: "EN ATTENTE" gray badge
        draw = ImageDraw.Draw(canvas)
        badge_w, badge_h = 220, 80
        badge_x = CARD_W - 30 - badge_w
        badge_y = CARD_H - 30 - badge_h
        draw.rounded_rectangle(
            (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
            radius=16,
            fill=(100, 116, 139, 200),
        )
        font_wait = _get_font(24, bold=True)
        wait_text = "EN ATTENTE"
        w_bbox = draw.textbbox((0, 0), wait_text, font=font_wait)
        w_w = w_bbox[2] - w_bbox[0]
        w_h = w_bbox[3] - w_bbox[1]
        draw.text(
            (badge_x + (badge_w - w_w) // 2,
             badge_y + (badge_h - w_h) // 2),
            wait_text, fill=(255, 255, 255, 220), font=font_wait,
        )

    # ── GA title (bottom-left, over gradient) ──
    draw = ImageDraw.Draw(canvas)
    title = image.get("title", "") or image.get("filename", "")
    if title:
        font_title = _get_font(22, bold=True)
        # Truncate
        display_title = title if len(title) <= 70 else title[:67] + "..."
        # Shadow
        draw.text((32, CARD_H - 62), display_title,
                  fill=(0, 0, 0, 150), font=font_title)
        draw.text((30, CARD_H - 64), display_title,
                  fill=(255, 255, 255, 230), font=font_title)

    # ── CTA line ──
    font_cta = _get_font(13)
    cta = "glance.scisense.fr"
    draw.text((30, CARD_H - 30), cta, fill=(255, 255, 255, 120), font=font_cta)

    # Convert to RGB for PNG output
    output = Image.new("RGB", (CARD_W, CARD_H), (15, 23, 42))
    output.paste(canvas, (0, 0), canvas)

    buf = io.BytesIO()
    output.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()
