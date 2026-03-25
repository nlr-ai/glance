"""
Parametric GA Compositor — GLANCE Paper Graphical Abstract

Two-zone architecture:
  Left  (~45%): "Le Fosse" — scissors graph + magnifying lens (Visual Spin)
  Right (~55%): "La Mesure" — 3 horizontal bars (GLANCE vs GRADE vs Vanity)
  Fracture: vertical divider with chronometer (5.0s)

Reads config/layout.yaml + config/palette.yaml
Produces: output/glance_paper_ga.svg + _full.png + _delivery.png
"""

import yaml
import svgwrite
import os
import sys
import math

# Add scisense root to path for vec_lib import
_SCISENSE_ROOT = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", ".."))
if _SCISENSE_ROOT not in sys.path:
    sys.path.insert(0, _SCISENSE_ROOT)

from scripts.vec_lib import lighten_hex, lerp_color, darken_hex, render_png

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


def resolve_color(palette, key):
    """Resolve a dotted key like 'problem.dominant' from palette dict."""
    parts = key.split(".")
    val = palette
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p, "#888888")
        else:
            return "#888888"
    return val


# ===================================================================
# LAYOUT HELPERS
# ===================================================================

def get_zone_rect(layout, zone_key, W, H):
    """Return (x, y, w, h) for a named zone."""
    z = layout["zones"][zone_key]
    x = int(W * z["x_pct"])
    w = int(W * z["width_pct"])
    return x, 0, w, H


def graph_y(zone_y_start, zone_y_end, frac):
    """Convert a fractional y (0=top, 1=bottom) to absolute y within graph area."""
    return zone_y_start + (zone_y_end - zone_y_start) * frac


# ===================================================================
# DRAWING: BACKGROUND
# ===================================================================

def draw_background(dwg, layout, palette, W, H):
    """White background with warm-to-cool gradient + red tint on left zone."""
    # Full white background
    dwg.add(dwg.rect((0, 0), (W, H), fill=palette["background"]))

    # Subtle full-canvas gradient: warm left → cool right
    canvas_grad = dwg.defs.add(dwg.linearGradient(
        id="canvas_gradient", x1="0%", y1="0%", x2="100%", y2="0%"))
    canvas_grad.add_stop_color(0, "#FFF5F0", opacity=0.5)   # warm cream
    canvas_grad.add_stop_color(1, "#F0F5FF", opacity=0.5)   # cool ice-blue
    dwg.add(dwg.rect((0, 0), (W, H), fill="url(#canvas_gradient)"))

    # Left zone warm red tint (stronger)
    lz = layout["zones"]["left"]
    lx = int(W * lz["x_pct"])
    lw = int(W * lz["width_pct"])
    dwg.add(dwg.rect((lx, 0), (lw, H),
                      fill=palette["problem"]["bg_tint"], opacity=0.90))


# ===================================================================
# DRAWING: TITLE
# ===================================================================

def draw_title(dwg, layout, palette, W, H):
    """GLANCE title centered at top."""
    t = layout["title"]
    font = layout["font"]["family"]
    cx = W // 2
    cy = int(H * t["y_pct"])
    dwg.add(dwg.text(t["text"], insert=(cx, cy),
                     font_size=t["font_size"],
                     font_weight=t["font_weight"],
                     fill=palette["text"]["primary"],
                     font_family=font,
                     text_anchor="middle",
                     dominant_baseline="middle"))


# ===================================================================
# DRAWING: SCISSORS GRAPH (Left Zone)
# ===================================================================

def draw_scissors_graph(dwg, layout, palette, W, H):
    """Two diverging lines: Engagement (up) and Comprehension (flat)."""
    lz = layout["zones"]["left"]
    zone_x = int(W * lz["x_pct"])
    zone_w = int(W * lz["width_pct"])
    sc = layout["scissors"]
    font = layout["font"]["family"]

    # Graph area absolute bounds
    graph_top = int(H * sc["y_start_pct"])
    graph_bot = int(H * sc["y_end_pct"])
    graph_left = zone_x + int(zone_w * sc["x_margin_pct"])
    graph_right = zone_x + zone_w - int(zone_w * sc["x_margin_pct"])
    graph_w = graph_right - graph_left
    graph_h = graph_bot - graph_top

    # Faint axis lines
    # X-axis (bottom)
    dwg.add(dwg.line((graph_left, graph_bot), (graph_right, graph_bot),
                     stroke=palette["text"]["light"], stroke_width=1.5,
                     opacity=0.4))
    # Y-axis (left)
    dwg.add(dwg.line((graph_left, graph_top), (graph_left, graph_bot),
                     stroke=palette["text"]["light"], stroke_width=1.5,
                     opacity=0.4))

    # Subtle horizontal grid lines for context
    if sc.get("grid_lines"):
        n_grid = sc.get("grid_line_count", 4)
        for gi in range(1, n_grid + 1):
            gy = graph_top + graph_h * gi / (n_grid + 1)
            dwg.add(dwg.line((graph_left, gy), (graph_right, gy),
                             stroke=palette["text"]["light"], stroke_width=0.8,
                             opacity=0.18, stroke_dasharray="6,4"))

    # Multiplier label at top of engagement line
    if sc.get("multiplier_label"):
        mult_x = graph_right - 10
        mult_y = graph_top + 24
        dwg.add(dwg.text(sc["multiplier_label"],
                         insert=(mult_x, mult_y),
                         font_size=26, fill=palette["problem"]["dominant"],
                         font_family=font, text_anchor="end",
                         font_weight="bold", opacity=0.85))

    # --- Engagement line (ascending, red-orange, thick) ---
    eng = sc["engagement"]
    eng_pts = []
    for fx, fy in eng["points"]:
        px = graph_left + graph_w * fx
        py = graph_top + graph_h * fy
        eng_pts.append((px, py))

    # Shaded area under engagement line (filled polygon, red 10% opacity) for grounding
    eng_fill_pts = list(eng_pts) + [(eng_pts[-1][0], graph_bot), (eng_pts[0][0], graph_bot)]
    dwg.add(dwg.polygon(eng_fill_pts, fill=palette["problem"]["dominant"], opacity=0.10))

    dwg.add(dwg.polyline(eng_pts, fill="none",
                         stroke=palette["problem"]["dominant"],
                         stroke_width=eng["stroke_width"],
                         stroke_linejoin="bevel",
                         stroke_linecap="round"))

    # Data point dots on engagement line (larger for saliency)
    for px, py in eng_pts:
        dwg.add(dwg.circle((px, py), 8,
                           fill=palette["problem"]["dominant"]))

    # Inline label for engagement
    last_eng = eng_pts[-1]
    lbl_off = eng["label_offset"]
    dwg.add(dwg.text(eng["label"],
                     insert=(last_eng[0] + lbl_off[0], last_eng[1] + lbl_off[1]),
                     font_size=22, fill=palette["problem"]["dominant"],
                     font_family=font, text_anchor="end",
                     font_weight="bold"))

    # --- Comprehension line (flat, gray, thin) ---
    comp = sc["comprehension"]
    comp_pts = []
    for fx, fy in comp["points"]:
        px = graph_left + graph_w * fx
        py = graph_top + graph_h * fy
        comp_pts.append((px, py))

    # Shaded area under comprehension line (filled polygon, gray 5% opacity) for grounding
    comp_fill_pts = list(comp_pts) + [(comp_pts[-1][0], graph_bot), (comp_pts[0][0], graph_bot)]
    dwg.add(dwg.polygon(comp_fill_pts, fill=palette["problem"]["accent"], opacity=0.05))

    dwg.add(dwg.polyline(comp_pts, fill="none",
                         stroke=palette["problem"]["accent"],
                         stroke_width=comp["stroke_width"],
                         stroke_linejoin="bevel",
                         stroke_linecap="round",
                         stroke_dasharray="10,5"))

    # Data point dots on comprehension line
    for px, py in comp_pts:
        dwg.add(dwg.circle((px, py), 4,
                           fill=palette["problem"]["accent"]))

    # Inline label for comprehension (white backdrop + dark text for contrast on pink bg)
    last_comp = comp_pts[-1]
    lbl_off = comp["label_offset"]
    comp_lbl_x = last_comp[0] + lbl_off[0]
    comp_lbl_y = last_comp[1] + lbl_off[1]
    # Semi-transparent white backdrop pill behind label
    comp_lbl_w = len(comp["label"]) * 11 + 16
    comp_lbl_h = 28
    dwg.add(dwg.rect(
        (comp_lbl_x - comp_lbl_w + 4, comp_lbl_y - comp_lbl_h + 6),
        (comp_lbl_w, comp_lbl_h),
        fill="#FFFFFF", opacity=0.70, rx=4, ry=4))
    dwg.add(dwg.text(comp["label"],
                     insert=(comp_lbl_x, comp_lbl_y),
                     font_size=20, fill=palette["text"]["primary"],
                     font_family=font, text_anchor="end",
                     font_weight="600"))

    # --- Annotation below graph (higher contrast) ---
    ann = sc["annotation"]
    ann_y = graph_bot + int(graph_h * ann["y_offset_pct"]) + 24
    ann_x = graph_left + graph_w // 2
    dwg.add(dwg.text(ann["text"],
                     insert=(ann_x, ann_y),
                     font_size=ann["font_size"],
                     fill=palette["text"]["secondary"],
                     font_family=font, text_anchor="middle",
                     font_weight="500"))


# ===================================================================
# DRAWING: MAGNIFYING LENS (Visual Spin)
# ===================================================================

def draw_magnifying_lens(dwg, layout, palette, W, H):
    """Magnifying lens showing Visual Spin — data distortion metaphor."""
    lz = layout["zones"]["left"]
    zone_x = int(W * lz["x_pct"])
    zone_w = int(W * lz["width_pct"])
    lens = layout["lens"]
    font = layout["font"]["family"]

    cx = zone_x + int(zone_w * lens["cx_pct"])
    cy = int(H * lens["cy_pct"])
    radius = int(zone_w * lens["radius_pct"])

    # --- Data bars OUTSIDE the lens (normal scale, top-left of lens) ---
    bar_colors = [palette["problem"]["dominant"],
                  palette["problem"]["accent"],
                  palette["problem"]["secondary"],
                  darken_hex(palette["problem"]["secondary"], 0.2),
                  lighten_hex(palette["problem"]["dominant"], 0.3)]
    bar_heights_normal = [38, 26, 32, 20, 30]
    bar_w = int(radius * 0.18)
    outside_x = cx - radius - int(radius * 0.7)
    outside_y = cy - int(radius * 0.05)
    for i, (bh, bc) in enumerate(zip(bar_heights_normal, bar_colors)):
        bx = outside_x + i * (bar_w + 5)
        by = outside_y + (40 - bh)
        dwg.add(dwg.rect((bx, by), (bar_w, bh),
                         fill=bc, opacity=0.55, rx=2, ry=2))

    # --- Lens circle (clipping mask for inside content) ---
    clip_id = "lens_clip"
    clip = dwg.defs.add(dwg.clipPath(id=clip_id))
    clip.add(dwg.circle((cx, cy), radius))

    # Faint fill inside lens
    dwg.add(dwg.circle((cx, cy), radius,
                       fill=palette["problem"]["bg_tint"], opacity=0.3))

    # --- Distorted bars INSIDE the lens (stretched vertically) ---
    stretch = lens["inner_bar_stretch"]
    inner_bar_w = int(radius * 2 * lens["inner_bar_width_pct"] / lens["inner_bars"])
    inner_gap = int(inner_bar_w * lens["inner_bar_gap_pct"])
    total_inner_w = lens["inner_bars"] * inner_bar_w + (lens["inner_bars"] - 1) * inner_gap
    inner_start_x = cx - total_inner_w // 2

    g_inner = dwg.g(clip_path=f"url(#{clip_id})")
    for i, (bh, bc) in enumerate(zip(bar_heights_normal, bar_colors)):
        stretched_h = int(bh * stretch)
        bx = inner_start_x + i * (inner_bar_w + inner_gap)
        by = cy + int(radius * 0.35) - stretched_h
        g_inner.add(dwg.rect((bx, by), (inner_bar_w, stretched_h),
                             fill=bc, opacity=0.8, rx=3, ry=3))
    # Subtle stretch arrows (visual cue of distortion)
    arrow_x = cx
    arrow_top = cy - int(radius * 0.6)
    arrow_bot = cy + int(radius * 0.5)
    for ay, dy in [(arrow_top, -12), (arrow_bot, 12)]:
        g_inner.add(dwg.line((arrow_x - 8, ay), (arrow_x, ay + dy),
                             stroke="#FFFFFF", stroke_width=2, opacity=0.5))
        g_inner.add(dwg.line((arrow_x + 8, ay), (arrow_x, ay + dy),
                             stroke="#FFFFFF", stroke_width=2, opacity=0.5))
    dwg.add(g_inner)

    # --- Lens glow (subtle outer shadow) ---
    dwg.add(dwg.circle((cx, cy), radius + 6,
                       fill="none",
                       stroke=palette["problem"]["secondary"],
                       stroke_width=2,
                       opacity=0.25))
    dwg.add(dwg.circle((cx, cy), radius + 12,
                       fill="none",
                       stroke=palette["problem"]["secondary"],
                       stroke_width=1,
                       opacity=0.12))

    # --- Lens frame (orange circle, thick) ---
    dwg.add(dwg.circle((cx, cy), radius,
                       fill="none",
                       stroke=palette["problem"]["secondary"],
                       stroke_width=lens["stroke_width"] + 2))

    # --- Handle ---
    handle_len = int(zone_w * lens["handle_length_pct"])
    angle_rad = math.radians(lens["handle_angle_deg"])
    hx_start = cx + int(radius * math.cos(angle_rad))
    hy_start = cy + int(radius * math.sin(angle_rad))
    hx_end = cx + int((radius + handle_len) * math.cos(angle_rad))
    hy_end = cy + int((radius + handle_len) * math.sin(angle_rad))
    dwg.add(dwg.line((hx_start, hy_start), (hx_end, hy_end),
                     stroke=palette["problem"]["secondary"],
                     stroke_width=lens["stroke_width"] + 2,
                     stroke_linecap="round"))

    # --- "Visual Spin" label (prominent) ---
    label_y = cy + radius + 32
    dwg.add(dwg.text(lens["label"],
                     insert=(cx, label_y),
                     font_size=lens["label_font_size"] + 4,
                     fill=palette["problem"]["secondary"],
                     font_family=font, text_anchor="middle",
                     font_weight="bold",
                     font_style="italic"))


# ===================================================================
# DRAWING: FRACTURE LINE + CHRONOMETER
# ===================================================================

def draw_fracture(dwg, layout, palette, W, H):
    """Sharp vertical fracture line with chronometer straddling it."""
    frac = layout["fracture"]
    frac_zone = layout["zones"]["fracture"]
    frac_x = int(W * frac_zone["x_pct"])
    font = layout["font"]["family"]

    # --- Irregular fracture line ---
    import random
    rng = random.Random(42)
    n_segments = 20
    jitter = frac["jitter_amplitude"]
    pts = []
    for i in range(n_segments + 1):
        y = H * i / n_segments
        x = frac_x + rng.uniform(-jitter, jitter)
        pts.append((x, y))

    path_d = f"M {pts[0][0]},{pts[0][1]} "
    for px, py in pts[1:]:
        path_d += f"L {px},{py} "

    dwg.add(dwg.path(d=path_d, fill="none",
                     stroke=palette["fracture"]["line"],
                     stroke_width=frac["stroke_width"],
                     stroke_dasharray=frac["dash"],
                     opacity=0.4))

    # --- Chronometer ---
    chrono = frac["chrono"]
    chrono_cx = frac_x
    chrono_cy = int(H * chrono["cy_pct"])
    chrono_r = chrono["radius"]

    # White backing circle (to obscure fracture line behind chrono)
    dwg.add(dwg.circle((chrono_cx, chrono_cy), chrono_r + 4,
                       fill=palette["background"]))

    # Frame circle
    dwg.add(dwg.circle((chrono_cx, chrono_cy), chrono_r,
                       fill=palette["background"],
                       stroke=palette["fracture"]["chrono_frame"],
                       stroke_width=chrono["frame_width"]))

    # Minor tick marks (60 positions) for precision
    for i in range(60):
        angle = math.radians(i * 6 - 90)
        if i % 5 == 0:
            # Major tick (12 positions)
            inner_r = chrono_r * 0.75
            outer_r = chrono_r * 0.92
            sw = 2.8 if i % 15 == 0 else 1.8
        else:
            # Minor tick
            inner_r = chrono_r * 0.85
            outer_r = chrono_r * 0.92
            sw = 0.8
        x1 = chrono_cx + inner_r * math.cos(angle)
        y1 = chrono_cy + inner_r * math.sin(angle)
        x2 = chrono_cx + outer_r * math.cos(angle)
        y2 = chrono_cy + outer_r * math.sin(angle)
        dwg.add(dwg.line((x1, y1), (x2, y2),
                         stroke=palette["fracture"]["chrono_frame"],
                         stroke_width=sw))

    # Center dot
    dwg.add(dwg.circle((chrono_cx, chrono_cy), 4,
                       fill=palette["fracture"]["chrono_frame"]))

    # Minute hand (blue, pointing up)
    min_angle = math.radians(chrono["minute_angle_deg"] - 90)
    min_len = chrono_r * chrono["minute_length_pct"]
    min_x = chrono_cx + min_len * math.cos(min_angle)
    min_y = chrono_cy + min_len * math.sin(min_angle)
    dwg.add(dwg.line((chrono_cx, chrono_cy), (min_x, min_y),
                     stroke=palette["fracture"]["chrono_frame"],
                     stroke_width=3, stroke_linecap="round"))

    # Second hand (orange, pointing right)
    sec_angle = math.radians(chrono["second_angle_deg"] - 90)
    sec_len = chrono_r * chrono["second_length_pct"]
    sec_x = chrono_cx + sec_len * math.cos(sec_angle)
    sec_y = chrono_cy + sec_len * math.sin(sec_angle)
    dwg.add(dwg.line((chrono_cx, chrono_cy), (sec_x, sec_y),
                     stroke=palette["fracture"]["chrono_needle"],
                     stroke_width=2, stroke_linecap="round"))

    # "5.0s" label below
    label_y = chrono_cy + chrono_r + chrono["label_y_offset"]
    dwg.add(dwg.text(chrono["label"],
                     insert=(chrono_cx, label_y),
                     font_size=chrono["label_font_size"],
                     fill=palette["text"]["secondary"],
                     font_family=font, text_anchor="middle",
                     font_weight="bold"))


# ===================================================================
# DRAWING: THREE BARS (Right Zone)
# ===================================================================

def draw_bars(dwg, layout, palette, W, H):
    """Three horizontal bars: GLANCE (100%), GRADE (74%), Vanity (~5%)."""
    rz = layout["zones"]["right"]
    zone_x = int(W * rz["x_pct"])
    zone_w = int(W * rz["width_pct"])
    bars = layout["bars"]
    font = layout["font"]["family"]

    margin = int(zone_w * bars["x_margin_pct"])
    right_margin = int(zone_w * bars.get("right_margin_pct", bars["x_margin_pct"]))
    bars_left = zone_x + margin
    bars_max_w = zone_w - margin - right_margin
    bars_top = int(H * bars["y_start_pct"])
    bar_h = bars["bar_height"]
    bar_gap = bars["bar_gap"]
    br = bars["border_radius"]

    # --- Scale axis at top ---
    axis = bars["axis"]
    axis_y = bars_top + axis["y_offset"]

    # Axis line
    dwg.add(dwg.line((bars_left, axis_y + axis["tick_height"]),
                     (bars_left + bars_max_w, axis_y + axis["tick_height"]),
                     stroke=palette["text"]["light"], stroke_width=1.5))

    # Tick marks and labels
    for tick_val in axis["ticks"]:
        tick_x = bars_left + int(bars_max_w * tick_val / 100)
        dwg.add(dwg.line((tick_x, axis_y),
                         (tick_x, axis_y + axis["tick_height"]),
                         stroke=palette["text"]["light"], stroke_width=1.5))
        label_text = f"{tick_val}{axis['label']}" if tick_val == 100 else str(tick_val)
        dwg.add(dwg.text(label_text,
                         insert=(tick_x, axis_y - 6),
                         font_size=axis["font_size"],
                         fill=palette["text"]["light"],
                         font_family=font, text_anchor="middle"))

    # --- Bars ---
    for i, item in enumerate(bars["items"]):
        bar_y = bars_top + i * (bar_h + bar_gap)
        bar_w = int(bars_max_w * item["width_pct"])
        color = resolve_color(palette, f"bars.{item['key']}")

        # Bar shadow (depth)
        dwg.add(dwg.rect((bars_left + 4, bar_y + 4), (max(bar_w, 8), bar_h),
                         fill="#000000", rx=br, ry=br,
                         opacity=0.10))
        # Bar rectangle
        dwg.add(dwg.rect((bars_left, bar_y), (max(bar_w, 8), bar_h),
                         fill=color, rx=br, ry=br,
                         opacity=0.95))

        # Gradient shine effect for GLANCE bar
        if item.get("gradient_shine"):
            shine_id = f"shine_{item['key']}"
            shine_grad = dwg.defs.add(dwg.linearGradient(
                id=shine_id, x1="0%", y1="0%", x2="0%", y2="100%"))
            shine_grad.add_stop_color(0, "#FFFFFF", opacity=0.35)
            shine_grad.add_stop_color(0.4, "#FFFFFF", opacity=0.08)
            shine_grad.add_stop_color(1, "#000000", opacity=0.05)
            dwg.add(dwg.rect((bars_left, bar_y), (max(bar_w, 8), bar_h),
                             fill=f"url(#{shine_id})", rx=br, ry=br))
            # Subtle glow around GLANCE bar
            dwg.add(dwg.rect((bars_left - 2, bar_y - 2),
                             (max(bar_w + 4, 12), bar_h + 4),
                             fill="none", rx=br + 2, ry=br + 2,
                             stroke=color, stroke_width=2, opacity=0.25))
        else:
            # Standard inner highlight (top third lighter)
            highlight_h = bar_h // 3
            dwg.add(dwg.rect((bars_left + 2, bar_y + 2),
                             (max(bar_w - 4, 4), highlight_h),
                             fill="#FFFFFF", opacity=0.15,
                             rx=br, ry=br))

        # Label below bar (left-aligned with bar start)
        label_x = bars_left + 4
        label_y = bar_y + bar_h + bars["label_gap"] + 6
        dwg.add(dwg.text(item["label"],
                         insert=(label_x, label_y),
                         font_size=bars["label_font_size"],
                         fill=palette["text"]["primary"],
                         font_family=font, text_anchor="start",
                         font_weight="600"))

        # Subtle underline beneath each bar label for visual grounding
        label_text_width = len(item["label"]) * bars["label_font_size"] * 0.52
        underline_y = label_y + 5
        dwg.add(dwg.line((label_x, underline_y),
                         (label_x + label_text_width, underline_y),
                         stroke=palette["text"]["light"], stroke_width=1.0,
                         opacity=0.25))

        # Checkmark inside the bar (right end) for full-width bars
        if item.get("show_check"):
            check_x = bars_left + bar_w - 36
            check_y = bar_y + bar_h // 2
            check_path = (f"M {check_x - 10},{check_y} "
                          f"L {check_x - 3},{check_y + 9} "
                          f"L {check_x + 12},{check_y - 10}")
            dwg.add(dwg.path(d=check_path, fill="none",
                             stroke="#FFFFFF",
                             stroke_width=4.0, stroke_linecap="round",
                             stroke_linejoin="round"))

    # --- Section subtitle under bars ---
    subtitle_y = bars_top + len(bars["items"]) * (bar_h + bar_gap) + 30
    dwg.add(dwg.text("What do readers actually understand?",
                     insert=(bars_left + bars_max_w // 2, subtitle_y),
                     font_size=22,
                     fill=palette["text"]["secondary"],
                     font_family=font, text_anchor="middle",
                     font_style="italic"))

    # Stats line
    stats_y = subtitle_y + 36
    dwg.add(dwg.text("49 GAs · glance.scisense.fr",
                     insert=(bars_left + bars_max_w // 2, stats_y),
                     font_size=18,
                     fill=palette["text"]["light"],
                     font_family=font, text_anchor="middle"))


# ===================================================================
# DRAWING: ANGULAR DECORATIVE ACCENTS (Left Zone)
# ===================================================================

def draw_angular_accents(dwg, layout, palette, W, H):
    """Sharp angular decorative lines in the left zone — no curves."""
    lz = layout["zones"]["left"]
    zone_x = int(W * lz["x_pct"])
    zone_w = int(W * lz["width_pct"])

    accent_color = palette["problem"]["dominant"]

    # Top-left angular bracket (stronger for saliency)
    x1 = zone_x + 18
    y1 = int(H * 0.12)
    dwg.add(dwg.line((x1, y1), (x1 + 55, y1),
                     stroke=accent_color, stroke_width=3.5, opacity=0.40))
    dwg.add(dwg.line((x1, y1), (x1, y1 + 55),
                     stroke=accent_color, stroke_width=3.5, opacity=0.40))

    # Bottom-right angular bracket (mirrored, stronger)
    x2 = zone_x + zone_w - 18
    y2 = int(H * 0.92)
    dwg.add(dwg.line((x2, y2), (x2 - 55, y2),
                     stroke=accent_color, stroke_width=3.5, opacity=0.40))
    dwg.add(dwg.line((x2, y2), (x2, y2 - 55),
                     stroke=accent_color, stroke_width=3.5, opacity=0.40))


# ===================================================================
# MAIN
# ===================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", "-v", type=int, default=None,
                        help="Version number — auto-saves snapshot to output/versions/")
    args = parser.parse_args()

    print("Loading config...")
    config = load_config()
    layout = config["layout"]
    palette = config["palette"]

    W = layout["canvas"]["width"]
    H = layout["canvas"]["height"]
    dw = layout["canvas"]["delivery_width"]
    dh = layout["canvas"]["delivery_height"]

    svg_path = os.path.join(OUT_DIR, "glance_paper_ga.svg")
    full_png = os.path.join(OUT_DIR, "glance_paper_ga_full.png")
    delivery_png = os.path.join(OUT_DIR, "glance_paper_ga_delivery.png")

    print(f"Canvas: {W}x{H}, delivery: {dw}x{dh}")

    dwg = svgwrite.Drawing(svg_path, size=(f"{W}px", f"{H}px"),
                           viewBox=f"0 0 {W} {H}")
    dwg.attribs["xmlns"] = "http://www.w3.org/2000/svg"

    # 1. Background
    print("  Drawing background...")
    draw_background(dwg, layout, palette, W, H)

    # 2. Angular accents (left zone decorative)
    print("  Drawing angular accents...")
    draw_angular_accents(dwg, layout, palette, W, H)

    # 3. Scissors graph (left zone)
    print("  Drawing scissors graph...")
    draw_scissors_graph(dwg, layout, palette, W, H)

    # 4. Magnifying lens / Visual Spin (left zone)
    print("  Drawing magnifying lens...")
    draw_magnifying_lens(dwg, layout, palette, W, H)

    # 5. Fracture line + chronometer (center)
    print("  Drawing fracture + chronometer...")
    draw_fracture(dwg, layout, palette, W, H)

    # 6. Three bars (right zone)
    print("  Drawing bars...")
    draw_bars(dwg, layout, palette, W, H)

    # 7. Title
    print("  Drawing title...")
    draw_title(dwg, layout, palette, W, H)

    # Save SVG
    dwg.save()
    print(f"\nSVG saved: {svg_path}")

    # Render PNG
    print("Rendering PNG...")
    render_png(svg_path, full_png, delivery_png, W, H, dw, dh)

    # Auto-save versioned snapshot
    if args.version:
        ver_dir = os.path.join(OUT_DIR, "versions")
        os.makedirs(ver_dir, exist_ok=True)
        import shutil
        for src, tag in [(full_png, "full"), (delivery_png, "delivery"), (svg_path, "svg")]:
            ext = os.path.splitext(src)[1]
            dst = os.path.join(ver_dir, f"v{args.version}_{tag}{ext}")
            shutil.copy2(src, dst)
        print(f"  Snapshot saved: v{args.version} -> {ver_dir}/")

    print("\nGLANCE GA compilation complete.")


if __name__ == "__main__":
    main()
