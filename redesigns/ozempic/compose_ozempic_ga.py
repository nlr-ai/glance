"""
Parametric GA Compositor — Ozempic/Semaglutide STEP 1 Trial — V2 (High Impact)

Full-canvas architecture:
  Left  (~40%): Transformation circles (before/after weight)
  Center (~24%): Hero "6.2x" callout badge — the biggest element
  Right (~22%): Milestone bars (86%, 69%, 50% thresholds)
  Top: Title + drug name + metadata
  Bottom: Source citation

Message in 3 seconds: "Semaglutide = 6.2x more weight loss. -14.9% vs -2.4%."

Visual metaphor: Two concentric circles show the weight shrinking.
The 6.2x badge dominates the center. Milestone bars show depth of effect.

Reads config/layout.yaml + config/palette.yaml
Produces: output/ozempic_redesign.svg + _full.png + _delivery.png
"""

import yaml
import svgwrite
import os
import sys
import math

# Add scisense root to path for vec_lib import
_SCISENSE_ROOT = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", ".."))
if _SCISENSE_ROOT not in sys.path:
    sys.path.insert(0, _SCISENSE_ROOT)

from scripts.vec_lib import lighten_hex, darken_hex, render_png

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE, "config")
OUT_DIR = os.path.join(BASE, "output")
os.makedirs(OUT_DIR, exist_ok=True)


# ===================================================================
# CONFIG LOADING
# ===================================================================

def load_config():
    config = {}
    for name in ("palette", "layout"):
        path = os.path.join(CONFIG_DIR, f"{name}.yaml")
        with open(path, "r", encoding="utf-8") as f:
            config[name] = yaml.safe_load(f)
    return config


def resolve_color(palette, dotted_key):
    """Resolve a dotted key like 'hero.primary' from palette dict."""
    parts = dotted_key.split(".")
    val = palette
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p, "#888888")
        else:
            return "#888888"
    return val


# ===================================================================
# DRAWING: BACKGROUND (warm-to-cool gradient)
# ===================================================================

def draw_background(dwg, layout, palette, W, H):
    """Full-canvas warm-to-cool gradient with subtle texture."""
    bg = palette["background"]

    # Base gradient: warm cream (left) -> cool mint (right)
    grad_id = "bg_gradient"
    bg_grad = dwg.defs.add(dwg.linearGradient(
        id=grad_id, x1="0%", y1="0%", x2="100%", y2="100%"))
    bg_grad.add_stop_color(0, bg["left"])
    bg_grad.add_stop_color(0.5, bg["overlay"], opacity=0.7)
    bg_grad.add_stop_color(1, bg["right"])
    dwg.add(dwg.rect((0, 0), (W, H), fill=f"url(#{grad_id})"))

    # Subtle radial glow behind the hero callout area (center)
    hero = layout["hero_callout"]
    hcx = int(W * hero["cx_pct"])
    hcy = int(H * hero["cy_pct"])
    rad_id = "hero_radial_glow"
    rad_grad = dwg.defs.add(dwg.radialGradient(
        id=rad_id, cx="50%", cy="50%", r="50%"))
    rad_grad.add_stop_color(0, palette["hero"]["glow"], opacity=0.12)
    rad_grad.add_stop_color(0.6, palette["hero"]["glow"], opacity=0.04)
    rad_grad.add_stop_color(1, palette["hero"]["glow"], opacity=0.0)
    glow_r = 400
    dwg.add(dwg.rect((hcx - glow_r, hcy - glow_r), (glow_r * 2, glow_r * 2),
                      fill=f"url(#{rad_id})"))

    # Top accent line (teal gradient bar)
    accent_grad_id = "top_accent"
    accent_grad = dwg.defs.add(dwg.linearGradient(
        id=accent_grad_id, x1="0%", y1="0%", x2="100%", y2="0%"))
    accent_grad.add_stop_color(0, palette["hero"]["primary"], opacity=0.8)
    accent_grad.add_stop_color(0.5, palette["hero"]["glow"], opacity=0.6)
    accent_grad.add_stop_color(1, palette["hero"]["primary"], opacity=0.3)
    dwg.add(dwg.rect((0, 0), (W, 6), fill=f"url(#{accent_grad_id})"))


# ===================================================================
# DRAWING: TITLE + DRUG NAME + METADATA (Top Band)
# ===================================================================

def draw_title_band(dwg, layout, palette, W, H):
    """Title, drug name, and trial metadata — top-left aligned."""
    font = layout["font"]["family"]

    # STEP 1 Trial
    t = layout["title"]
    tx = int(W * t["x_pct"])
    ty = int(H * t["y_pct"])
    dwg.add(dwg.text(t["text"], insert=(tx, ty),
                     font_size=t["font_size"],
                     font_weight=t["font_weight"],
                     fill=palette["text"]["primary"],
                     font_family=font,
                     text_anchor="start",
                     dominant_baseline="middle"))

    # Semaglutide 2.4 mg (in teal)
    d = layout["drug_name"]
    dx = int(W * d["x_pct"])
    dy = int(H * d["y_pct"])
    dwg.add(dwg.text(d["text"], insert=(dx, dy),
                     font_size=d["font_size"],
                     font_weight=d["font_weight"],
                     fill=palette["text"]["teal"],
                     font_family=font,
                     text_anchor="start",
                     dominant_baseline="middle"))

    # Metadata line
    m = layout["meta"]
    mx = int(W * m["x_pct"])
    my = int(H * m["y_pct"])
    dwg.add(dwg.text(m["text"], insert=(mx, my),
                     font_size=m["font_size"],
                     font_weight=m["font_weight"],
                     fill=palette["text"]["muted"],
                     font_family=font,
                     text_anchor="start",
                     dominant_baseline="middle"))


# ===================================================================
# DRAWING: TRANSFORMATION CIRCLES (Left Area)
# ===================================================================

def draw_transformation_circles(dwg, layout, palette, W, H):
    """Two concentric circles: big (100% baseline) → small (85.1% after).
    The visible ring between them IS the weight loss."""
    tc = layout["transformation"]
    bf = tc["before"]
    af = tc["after"]
    font = layout["font"]["family"]
    condensed = layout["font"]["condensed"]

    # Centers
    bcx = int(W * bf["cx_pct"])
    bcy = int(H * bf["cy_pct"])
    acx = int(W * af["cx_pct"])
    acy = int(H * af["cy_pct"])

    br = bf["radius"]
    ar = af["radius"]

    # --- BEFORE circle (the outer ring = lost weight) ---

    # Subtle shadow behind outer circle
    dwg.add(dwg.circle((bcx + 6, bcy + 6), br + 4,
                       fill=palette["structure"]["card_shadow"], opacity=0.06))

    # Outer circle fill (light slate = the "mass" that was lost)
    dwg.add(dwg.circle((bcx, bcy), br,
                       fill=palette["circles"]["before"],
                       stroke=palette["circles"]["before_stroke"],
                       stroke_width=bf["stroke_width"],
                       opacity=0.6))

    # Cross-hatch texture on the reduction ring (the gap between circles)
    # This makes the "lost weight" zone visually distinct
    clip_id = "reduction_ring_clip"
    clip = dwg.defs.add(dwg.clipPath(id=clip_id))
    # Outer boundary
    clip.add(dwg.circle((bcx, bcy), br))
    # We'll overlay the inner circle on top, so the texture shows only in the ring

    # Diagonal lines in the ring (gives depth/texture to "weight lost" zone)
    ring_group = dwg.g(clip_path=f"url(#{clip_id})")
    stripe_color = palette["circles"]["reduction_fill"]
    n_stripes = 30
    for i in range(n_stripes):
        offset = -br + (2 * br * i / n_stripes)
        x1 = bcx + offset
        y1 = bcy - br
        x2 = bcx + offset + br
        y2 = bcy + br
        ring_group.add(dwg.line((x1, y1), (x2, y2),
                                stroke=stripe_color, stroke_width=3, opacity=0.4))
    dwg.add(ring_group)

    # --- AFTER circle (inner = remaining weight) ---

    # Inner circle gradient (teal, with 3D depth)
    inner_grad_id = "after_circle_grad"
    inner_grad = dwg.defs.add(dwg.radialGradient(
        id=inner_grad_id, cx="40%", cy="35%", r="65%"))
    inner_grad.add_stop_color(0, palette["hero"]["glow"], opacity=0.9)
    inner_grad.add_stop_color(0.4, palette["hero"]["primary"], opacity=0.95)
    inner_grad.add_stop_color(1, palette["hero"]["dark"], opacity=1.0)

    dwg.add(dwg.circle((acx, acy), ar,
                       fill=f"url(#{inner_grad_id})",
                       stroke=palette["circles"]["after_stroke"],
                       stroke_width=af["stroke_width"]))

    # Specular highlight on inner circle (3D effect)
    highlight_grad_id = "circle_highlight"
    hl_grad = dwg.defs.add(dwg.radialGradient(
        id=highlight_grad_id, cx="35%", cy="30%", r="50%"))
    hl_grad.add_stop_color(0, "#FFFFFF", opacity=0.35)
    hl_grad.add_stop_color(1, "#FFFFFF", opacity=0.0)
    dwg.add(dwg.circle((acx, acy), ar * 0.85,
                       fill=f"url(#{highlight_grad_id})"))

    # "85.1%" label inside the inner circle
    dwg.add(dwg.text(af["label"], insert=(acx, acy - 8),
                     font_size=62,
                     font_weight="900",
                     fill=palette["text"]["inverse"],
                     font_family=condensed,
                     text_anchor="middle",
                     dominant_baseline="middle"))

    # "after 68 wk" sub-label
    dwg.add(dwg.text(af["label_sub"], insert=(acx, acy + 36),
                     font_size=22,
                     font_weight="400",
                     fill=palette["text"]["inverse"],
                     font_family=font,
                     text_anchor="middle",
                     dominant_baseline="middle",
                     opacity=0.85))

    # "100%" label above the outer circle
    dwg.add(dwg.text(bf["label"], insert=(bcx, bcy - br - 18),
                     font_size=32,
                     font_weight="700",
                     fill=palette["text"]["secondary"],
                     font_family=font,
                     text_anchor="middle",
                     dominant_baseline="middle"))

    # "baseline" under 100%
    dwg.add(dwg.text(bf["label_sub"], insert=(bcx, bcy - br + 12),
                     font_size=20,
                     font_weight="400",
                     fill=palette["text"]["muted"],
                     font_family=font,
                     text_anchor="middle",
                     dominant_baseline="middle"))

    # --- Reduction callout: "-14.9%" with arrow pointing to the ring ---
    red = tc["reduction"]
    rx = int(W * red["x_pct"])
    ry = int(H * red["y_pct"])

    # The big "-14.9%" number
    dwg.add(dwg.text(red["text"], insert=(rx, ry),
                     font_size=red["font_size"],
                     font_weight=red["font_weight"],
                     fill=palette["hero"]["primary"],
                     font_family=condensed,
                     text_anchor="start",
                     dominant_baseline="middle"))

    # Arrow from label to the ring gap
    arw_sx = int(W * red["arrow_start_x_pct"])
    arw_sy = int(H * red["arrow_start_y_pct"])
    arw_ex = int(W * red["arrow_end_x_pct"])
    arw_ey = int(H * red["arrow_end_y_pct"])

    # Curved arrow path
    mid_x = (arw_sx + arw_ex) / 2 - 20
    mid_y = (arw_sy + arw_ey) / 2 + 30
    path_d = f"M {arw_sx},{arw_sy} Q {mid_x},{mid_y} {arw_ex},{arw_ey}"
    dwg.add(dwg.path(d=path_d, fill="none",
                     stroke=palette["hero"]["primary"],
                     stroke_width=3, stroke_linecap="round",
                     opacity=0.7))

    # Arrowhead
    angle = math.atan2(arw_ey - mid_y, arw_ex - mid_x)
    head_size = 12
    h1x = arw_ex - head_size * math.cos(angle - 0.4)
    h1y = arw_ey - head_size * math.sin(angle - 0.4)
    h2x = arw_ex - head_size * math.cos(angle + 0.4)
    h2y = arw_ey - head_size * math.sin(angle + 0.4)
    dwg.add(dwg.polygon([(arw_ex, arw_ey), (h1x, h1y), (h2x, h2y)],
                        fill=palette["hero"]["primary"], opacity=0.7))


# ===================================================================
# DRAWING: HERO CALLOUT BADGE (Center — "6.2x")
# ===================================================================

def draw_hero_callout(dwg, layout, palette, W, H):
    """The 6.2x callout — the BIGGEST, most unmissable element.
    Dark teal badge with giant white number, outer glow."""
    hc = layout["hero_callout"]
    font = layout["font"]["family"]
    condensed = layout["font"]["condensed"]

    cx = int(W * hc["cx_pct"])
    cy = int(H * hc["cy_pct"])
    bw = hc["badge_width"]
    bh = hc["badge_height"]
    br = hc["badge_radius"]

    bx = cx - bw // 2
    by = cy - bh // 2

    # Outer glow (large soft shadow)
    for i, (dx, dy, op) in enumerate([(0, 0, 0.06), (0, 0, 0.04), (0, 0, 0.03)]):
        expand = (3 - i) * 12
        dwg.add(dwg.rect((bx - expand + dx, by - expand + dy),
                         (bw + expand * 2, bh + expand * 2),
                         fill=palette["accent"]["badge_glow"],
                         rx=br + expand // 2, ry=br + expand // 2,
                         opacity=op))

    # Drop shadow
    dwg.add(dwg.rect((bx + 8, by + 10), (bw, bh),
                      fill=palette["structure"]["card_shadow"],
                      rx=br, ry=br, opacity=0.12))

    # Badge background (dark teal gradient)
    badge_grad_id = "badge_bg_grad"
    badge_grad = dwg.defs.add(dwg.linearGradient(
        id=badge_grad_id, x1="0%", y1="0%", x2="0%", y2="100%"))
    badge_grad.add_stop_color(0, palette["hero"]["primary"])
    badge_grad.add_stop_color(1, palette["hero"]["dark"])
    dwg.add(dwg.rect((bx, by), (bw, bh),
                      fill=f"url(#{badge_grad_id})",
                      rx=br, ry=br))

    # Inner shine (top highlight)
    shine_id = "badge_shine"
    shine_grad = dwg.defs.add(dwg.linearGradient(
        id=shine_id, x1="0%", y1="0%", x2="0%", y2="100%"))
    shine_grad.add_stop_color(0, "#FFFFFF", opacity=0.20)
    shine_grad.add_stop_color(0.3, "#FFFFFF", opacity=0.05)
    shine_grad.add_stop_color(1, "#000000", opacity=0.0)
    # Clip the shine to the badge shape
    shine_clip_id = "badge_shine_clip"
    shine_clip = dwg.defs.add(dwg.clipPath(id=shine_clip_id))
    shine_clip.add(dwg.rect((bx, by), (bw, bh), rx=br, ry=br))
    shine_g = dwg.g(clip_path=f"url(#{shine_clip_id})")
    shine_g.add(dwg.rect((bx, by), (bw, bh // 2),
                         fill=f"url(#{shine_id})"))
    dwg.add(shine_g)

    # "6.2" — the hero number
    num_y = cy - 10
    # Render "6.2" and "x" separately for different sizes
    num_fs = hc["number_font_size"]
    suf_fs = hc["suffix_font_size"]

    # Approximate widths for centering
    num_approx_w = num_fs * 0.6 * len(hc["number"])
    suf_approx_w = suf_fs * 0.55
    total_w = num_approx_w + suf_approx_w
    num_x = cx - int(total_w / 2) + 10
    suf_x = num_x + int(num_approx_w) - 5

    dwg.add(dwg.text(hc["number"], insert=(num_x, num_y),
                     font_size=num_fs,
                     font_weight=hc["number_font_weight"],
                     fill=palette["accent"]["badge_text"],
                     font_family=condensed,
                     text_anchor="start",
                     dominant_baseline="middle"))

    dwg.add(dwg.text(hc["suffix"], insert=(suf_x, num_y + 10),
                     font_size=suf_fs,
                     font_weight=hc["suffix_font_weight"],
                     fill=palette["accent"]["badge_text"],
                     font_family=condensed,
                     text_anchor="start",
                     dominant_baseline="middle",
                     opacity=0.85))

    # "more weight loss" sub-line
    sub_y = cy + 70
    dwg.add(dwg.text(hc["sub_text"], insert=(cx, sub_y),
                     font_size=hc["sub_font_size"],
                     font_weight=hc["sub_font_weight"],
                     fill=palette["accent"]["badge_text"],
                     font_family=font,
                     text_anchor="middle",
                     dominant_baseline="middle",
                     opacity=0.9))

    # "vs. placebo (-2.4%)" comparison line
    comp_y = sub_y + 38
    dwg.add(dwg.text(hc["compare_text"], insert=(cx, comp_y),
                     font_size=hc["compare_font_size"],
                     font_weight=hc["compare_font_weight"],
                     fill=palette["accent"]["badge_text"],
                     font_family=font,
                     text_anchor="middle",
                     dominant_baseline="middle",
                     opacity=0.65))


# ===================================================================
# DRAWING: MILESTONE BARS (Right Area)
# ===================================================================

def draw_milestone_bars(dwg, layout, palette, W, H):
    """Three stacked horizontal bars showing % of patients reaching thresholds.
    Each bar has semaglutide (teal) overlaid on the track (gray)."""
    ms = layout["milestones"]
    font = layout["font"]["family"]
    condensed = layout["font"]["condensed"]

    ms_x = int(W * ms["x_pct"])
    ms_w = int(W * ms["width_pct"])
    ms_y = int(H * ms["y_start_pct"])
    bar_h = ms["bar_height"]
    bar_gap = ms["bar_gap"]
    track_r = ms["track_radius"]

    colors = [
        palette["milestones"]["bar_15pct"],   # strongest first for >=5%
        palette["milestones"]["bar_10pct"],   # medium for >=10%
        palette["milestones"]["bar_5pct"],    # lightest for >=15% (counter-intuitive but
    ]
    # Actually: 86% is the biggest bar -> strongest color
    # Let's map by semaglutide_pct descending
    bar_colors = [
        palette["milestones"]["bar_15pct"],  # 86.4% -> darkest/strongest
        palette["milestones"]["bar_10pct"],  # 69.1% -> medium
        palette["milestones"]["bar_5pct"],   # 50.5% -> still strong but lighter
    ]

    # Section header
    header_y = ms_y - 55
    dwg.add(dwg.text("Patients achieving weight loss:", insert=(ms_x, header_y),
                     font_size=28,
                     font_weight="700",
                     fill=palette["text"]["primary"],
                     font_family=font,
                     text_anchor="start",
                     dominant_baseline="middle"))

    for i, item in enumerate(ms["items"]):
        y = ms_y + i * (bar_h + bar_gap + 34)  # extra space for labels
        sem_pct = item["semaglutide_pct"] / 100.0
        plc_pct = item["placebo_pct"] / 100.0

        # Track background
        dwg.add(dwg.rect((ms_x, y), (ms_w, bar_h),
                         fill=palette["milestones"]["bar_bg"],
                         rx=track_r, ry=track_r))

        # Placebo bar (subtle, behind semaglutide)
        plc_w = max(8, int(ms_w * plc_pct))
        dwg.add(dwg.rect((ms_x, y), (plc_w, bar_h),
                         fill=palette["contrast"]["light"],
                         rx=track_r, ry=track_r,
                         opacity=0.6))

        # Semaglutide bar (hero)
        sem_w = max(8, int(ms_w * sem_pct))
        bar_color = bar_colors[i]

        # Bar gradient (3D depth)
        bar_grad_id = f"ms_bar_grad_{i}"
        bar_grad = dwg.defs.add(dwg.linearGradient(
            id=bar_grad_id, x1="0%", y1="0%", x2="0%", y2="100%"))
        bar_grad.add_stop_color(0, lighten_hex(bar_color, 0.2))
        bar_grad.add_stop_color(0.5, bar_color)
        bar_grad.add_stop_color(1, darken_hex(bar_color, 0.15))

        dwg.add(dwg.rect((ms_x, y), (sem_w, bar_h),
                         fill=f"url(#{bar_grad_id})",
                         rx=track_r, ry=track_r))

        # Shine on bar
        shine_id = f"ms_shine_{i}"
        shine = dwg.defs.add(dwg.linearGradient(
            id=shine_id, x1="0%", y1="0%", x2="0%", y2="100%"))
        shine.add_stop_color(0, "#FFFFFF", opacity=0.25)
        shine.add_stop_color(0.4, "#FFFFFF", opacity=0.05)
        shine.add_stop_color(1, "#000000", opacity=0.0)
        # Clip to bar shape
        bar_clip_id = f"ms_clip_{i}"
        bar_clip = dwg.defs.add(dwg.clipPath(id=bar_clip_id))
        bar_clip.add(dwg.rect((ms_x, y), (sem_w, bar_h), rx=track_r, ry=track_r))
        bar_g = dwg.g(clip_path=f"url(#{bar_clip_id})")
        bar_g.add(dwg.rect((ms_x, y), (sem_w, bar_h // 2),
                           fill=f"url(#{shine_id})"))
        dwg.add(bar_g)

        # Semaglutide percentage inside bar (right-aligned)
        sem_label = f"{item['semaglutide_pct']:.0f}%"
        val_x = ms_x + sem_w - 14
        val_y = y + bar_h // 2 + ms["value_font_size"] // 4
        dwg.add(dwg.text(sem_label, insert=(val_x, val_y),
                         font_size=ms["value_font_size"],
                         font_weight=ms["value_font_weight"],
                         fill=palette["text"]["inverse"],
                         font_family=condensed,
                         text_anchor="end"))

        # Placebo percentage outside (after placebo bar end, above bar)
        plc_label = f"{item['placebo_pct']:.0f}%"
        plc_val_x = ms_x + plc_w + 12
        dwg.add(dwg.text(plc_label, insert=(plc_val_x, y - 5),
                         font_size=20,
                         font_weight="600",
                         fill=palette["contrast"]["dark"],
                         font_family=font,
                         text_anchor="start"))

        # Placebo marker text (only on first bar)
        if i == 0:
            dwg.add(dwg.text("placebo", insert=(plc_val_x + 42, y - 5),
                             font_size=18,
                             font_weight="400",
                             fill=palette["text"]["muted"],
                             font_family=font,
                             text_anchor="start"))

        # Label below bar
        label_y = y + bar_h + 20
        # Threshold in bold, description normal
        threshold_text = item["threshold"]
        desc_text = item["label"].replace(item["threshold"].replace(">", "\u2265").replace("=", ""), "").strip()

        dwg.add(dwg.text(item["label"].replace(">=", "\u2265"),
                         insert=(ms_x, label_y),
                         font_size=ms["label_font_size"],
                         font_weight=ms["label_font_weight"],
                         fill=palette["text"]["secondary"],
                         font_family=font,
                         text_anchor="start"))


# ===================================================================
# DRAWING: CONNECTING VISUAL ELEMENTS
# ===================================================================

def draw_connectors(dwg, layout, palette, W, H):
    """Subtle visual connectors between the three main areas:
    circles -> hero badge -> milestone bars."""
    # Light dotted lines connecting the sections
    hero = layout["hero_callout"]
    hcx = int(W * hero["cx_pct"])
    hcy = int(H * hero["cy_pct"])
    bw = hero["badge_width"]

    # Left connector: circles -> badge
    tc = layout["transformation"]
    circle_right_x = int(W * tc["before"]["cx_pct"]) + tc["before"]["radius"] + 20
    badge_left_x = hcx - bw // 2 - 10

    if badge_left_x > circle_right_x + 20:
        mid_y = hcy
        dwg.add(dwg.line((circle_right_x, mid_y), (badge_left_x, mid_y),
                         stroke=palette["structure"]["line"],
                         stroke_width=2,
                         stroke_dasharray="6,4",
                         opacity=0.3))

    # Right connector: badge -> milestones
    ms = layout["milestones"]
    badge_right_x = hcx + bw // 2 + 10
    ms_left_x = int(W * ms["x_pct"]) - 20

    if ms_left_x > badge_right_x + 20:
        mid_y = hcy
        dwg.add(dwg.line((badge_right_x, mid_y), (ms_left_x, mid_y),
                         stroke=palette["structure"]["line"],
                         stroke_width=2,
                         stroke_dasharray="6,4",
                         opacity=0.3))


# ===================================================================
# DRAWING: SOURCE LINE
# ===================================================================

def draw_source(dwg, layout, palette, W, H):
    """Source citation at bottom center."""
    src = layout["source"]
    font = layout["font"]["family"]
    sy = int(H * src["y_pct"])
    dwg.add(dwg.text(src["text"], insert=(W // 2, sy),
                     font_size=src["font_size"],
                     font_weight=src["font_weight"],
                     fill=palette["text"]["muted"],
                     font_family=font,
                     text_anchor="middle",
                     font_style="italic"))


# ===================================================================
# DRAWING: BOTTOM ACCENT LINE
# ===================================================================

def draw_bottom_accent(dwg, layout, palette, W, H):
    """Mirror of top accent — thin gradient bar at the very bottom."""
    accent_grad_id = "bottom_accent"
    accent_grad = dwg.defs.add(dwg.linearGradient(
        id=accent_grad_id, x1="100%", y1="0%", x2="0%", y2="0%"))
    accent_grad.add_stop_color(0, palette["hero"]["primary"], opacity=0.8)
    accent_grad.add_stop_color(0.5, palette["hero"]["glow"], opacity=0.6)
    accent_grad.add_stop_color(1, palette["hero"]["primary"], opacity=0.3)
    dwg.add(dwg.rect((0, H - 6), (W, 6), fill=f"url(#{accent_grad_id})"))


# ===================================================================
# MAIN
# ===================================================================

def main():
    print("Loading config...")
    config = load_config()
    layout = config["layout"]
    palette = config["palette"]

    W = layout["canvas"]["width"]
    H = layout["canvas"]["height"]
    dw = layout["canvas"]["delivery_width"]
    dh = layout["canvas"]["delivery_height"]

    svg_path = os.path.join(OUT_DIR, "ozempic_redesign.svg")
    full_png = os.path.join(OUT_DIR, "ozempic_redesign_full.png")
    delivery_png = os.path.join(OUT_DIR, "ozempic_redesign_delivery.png")

    print(f"Canvas: {W}x{H}, delivery: {dw}x{dh}")

    dwg = svgwrite.Drawing(svg_path, size=(f"{W}px", f"{H}px"),
                           viewBox=f"0 0 {W} {H}")
    dwg.attribs["xmlns"] = "http://www.w3.org/2000/svg"

    # 1. Background (warm-to-cool gradient + radial glow)
    print("  Drawing background...")
    draw_background(dwg, layout, palette, W, H)

    # 2. Title band (top-left)
    print("  Drawing title band...")
    draw_title_band(dwg, layout, palette, W, H)

    # 3. Transformation circles (left area)
    print("  Drawing transformation circles...")
    draw_transformation_circles(dwg, layout, palette, W, H)

    # 4. Hero callout badge (center — 6.2x)
    print("  Drawing hero callout...")
    draw_hero_callout(dwg, layout, palette, W, H)

    # 5. Milestone bars (right area)
    print("  Drawing milestone bars...")
    draw_milestone_bars(dwg, layout, palette, W, H)

    # 6. Connectors
    print("  Drawing connectors...")
    draw_connectors(dwg, layout, palette, W, H)

    # 7. Source
    print("  Drawing source...")
    draw_source(dwg, layout, palette, W, H)

    # 8. Bottom accent
    print("  Drawing bottom accent...")
    draw_bottom_accent(dwg, layout, palette, W, H)

    # Save SVG
    dwg.save()
    print(f"\nSVG saved: {svg_path}")

    # Render PNG
    print("Rendering PNG...")
    render_png(svg_path, full_png, delivery_png, W, H, dw, dh)

    print("\nOzempic STEP 1 GA V2 compilation complete.")


if __name__ == "__main__":
    main()
