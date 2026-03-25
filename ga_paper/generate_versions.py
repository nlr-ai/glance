"""
Generate simulated V1-V5 snapshots of the GLANCE paper GA.

Each version adds progressive refinement, showing the evolution
from bare bones to near-final polish.

V1 — Bare bones: title + 3 flat bars + simple labels
V2 — Add scissors graph (thin lines, small dots)
V3 — Add lens + fracture + red tint + bar labels + Visual Spin
V4 — Better layout: axis, checkmark, shadows, accents, annotation
V5 — Polish: glow, subtitle, stats, bigger dots, stronger tint
"""

import copy
import os
import sys
import yaml
import svgwrite
import math

# Add scisense root to path for vec_lib import
_SCISENSE_ROOT = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", ".."))
if _SCISENSE_ROOT not in sys.path:
    sys.path.insert(0, _SCISENSE_ROOT)

from scripts.vec_lib import lighten_hex, lerp_color, darken_hex, render_png

# Import drawing functions from the compositor
from compose_paper_ga import (
    load_config, resolve_color, get_zone_rect,
    draw_scissors_graph, draw_magnifying_lens, draw_fracture,
    draw_angular_accents,
)

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "output")
VER_DIR = os.path.join(OUT_DIR, "versions")
os.makedirs(VER_DIR, exist_ok=True)


# ===================================================================
# SIMPLIFIED DRAWING FUNCTIONS (for early versions)
# ===================================================================

def draw_bg_white_only(dwg, W, H):
    """V1-V2: Plain white background, no gradient, no tint."""
    dwg.add(dwg.rect((0, 0), (W, H), fill="#FFFFFF"))


def draw_bg_with_gradient(dwg, W, H):
    """V3+: White background with subtle warm-to-cool gradient."""
    dwg.add(dwg.rect((0, 0), (W, H), fill="#FFFFFF"))
    canvas_grad = dwg.defs.add(dwg.linearGradient(
        id="canvas_gradient", x1="0%", y1="0%", x2="100%", y2="0%"))
    canvas_grad.add_stop_color(0, "#FFF5F0", opacity=0.5)
    canvas_grad.add_stop_color(1, "#F0F5FF", opacity=0.5)
    dwg.add(dwg.rect((0, 0), (W, H), fill="url(#canvas_gradient)"))


def draw_bg_red_tint(dwg, layout, tint_opacity, W, H):
    """Add red tint on left zone with configurable opacity."""
    lz = layout["zones"]["left"]
    lx = int(W * lz["x_pct"])
    lw = int(W * lz["width_pct"])
    dwg.add(dwg.rect((lx, 0), (lw, H),
                      fill="#FFECEC", opacity=tint_opacity))


def draw_title_simple(dwg, layout, W, H):
    """V1: Smaller, regular weight title."""
    font = layout["font"]["family"]
    cx = W // 2
    cy = int(H * layout["title"]["y_pct"])
    dwg.add(dwg.text("GLANCE", insert=(cx, cy),
                     font_size=48,
                     font_weight="400",
                     fill="#1D3557",
                     font_family=font,
                     text_anchor="middle",
                     dominant_baseline="middle"))


def draw_title_medium(dwg, layout, W, H):
    """V2-V4: Medium size, semi-bold title."""
    font = layout["font"]["family"]
    cx = W // 2
    cy = int(H * layout["title"]["y_pct"])
    dwg.add(dwg.text("GLANCE", insert=(cx, cy),
                     font_size=56,
                     font_weight="600",
                     fill="#1D3557",
                     font_family=font,
                     text_anchor="middle",
                     dominant_baseline="middle"))


def draw_title_full(dwg, layout, W, H):
    """V5: Full size, bold title (same as V6)."""
    font = layout["font"]["family"]
    cx = W // 2
    cy = int(H * layout["title"]["y_pct"])
    dwg.add(dwg.text("GLANCE", insert=(cx, cy),
                     font_size=68,
                     font_weight="800",
                     fill="#1D3557",
                     font_family=font,
                     text_anchor="middle",
                     dominant_baseline="middle"))


def draw_bars_v1(dwg, layout, palette, W, H):
    """V1: 3 flat bars, no axis, no labels below, no shadows, no checkmark.
    Just a simple inline label next to each bar."""
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
    bar_h = 50  # smaller
    bar_gap = 55
    br = 4

    bar_colors = ["#2A9D8F", "#1D3557", "#A8DADC"]
    bar_widths = [1.0, 0.68, 0.03]
    bar_labels = ["GLANCE", "GRADE", "Vanity"]

    for i in range(3):
        bar_y = bars_top + i * (bar_h + bar_gap)
        bar_w = int(bars_max_w * bar_widths[i])

        # Flat rectangle, no shadow
        dwg.add(dwg.rect((bars_left, bar_y), (max(bar_w, 8), bar_h),
                         fill=bar_colors[i], rx=br, ry=br,
                         opacity=0.85))

        # Simple inline label to the right of the bar
        label_x = bars_left + max(bar_w, 8) + 12
        label_y = bar_y + bar_h // 2 + 6
        dwg.add(dwg.text(bar_labels[i],
                         insert=(label_x, label_y),
                         font_size=20,
                         fill="#1D3557",
                         font_family=font, text_anchor="start",
                         font_weight="400"))


def draw_bars_v2(dwg, layout, palette, W, H):
    """V2: Same as V1 bars (no axis, no labels below), but slightly refined."""
    # Identical to V1 for bars
    draw_bars_v1(dwg, layout, palette, W, H)


def draw_bars_v3(dwg, layout, palette, W, H):
    """V3: Bars with labels below them, but no axis, no shadows, no checkmark."""
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
    bar_h = 56
    bar_gap = 65
    br = 6

    for i, item in enumerate(bars["items"]):
        bar_y = bars_top + i * (bar_h + bar_gap)
        bar_w = int(bars_max_w * item["width_pct"])
        color = resolve_color(palette, f"bars.{item['key']}")

        # Flat rectangle
        dwg.add(dwg.rect((bars_left, bar_y), (max(bar_w, 8), bar_h),
                         fill=color, rx=br, ry=br, opacity=0.90))

        # Label below bar
        label_x = bars_left + 4
        label_y = bar_y + bar_h + 18
        dwg.add(dwg.text(item["label"],
                         insert=(label_x, label_y),
                         font_size=20,
                         fill="#1D3557",
                         font_family=font, text_anchor="start",
                         font_weight="500"))


def draw_bars_v4(dwg, layout, palette, W, H):
    """V4: Bigger bars, axis scale, shadows, checkmark, no gradient shine, no subtitle/stats."""
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
    bar_h = 66
    bar_gap = 68
    br = 8

    # Axis scale
    axis = bars["axis"]
    axis_y = bars_top + axis["y_offset"]
    dwg.add(dwg.line((bars_left, axis_y + axis["tick_height"]),
                     (bars_left + bars_max_w, axis_y + axis["tick_height"]),
                     stroke="#8D99AE", stroke_width=1.5))

    for tick_val in axis["ticks"]:
        tick_x = bars_left + int(bars_max_w * tick_val / 100)
        dwg.add(dwg.line((tick_x, axis_y),
                         (tick_x, axis_y + axis["tick_height"]),
                         stroke="#8D99AE", stroke_width=1.5))
        label_text = f"{tick_val}%" if tick_val == 100 else str(tick_val)
        dwg.add(dwg.text(label_text,
                         insert=(tick_x, axis_y - 6),
                         font_size=axis["font_size"],
                         fill="#8D99AE",
                         font_family=font, text_anchor="middle"))

    for i, item in enumerate(bars["items"]):
        bar_y = bars_top + i * (bar_h + bar_gap)
        bar_w = int(bars_max_w * item["width_pct"])
        color = resolve_color(palette, f"bars.{item['key']}")

        # Shadow
        dwg.add(dwg.rect((bars_left + 4, bar_y + 4), (max(bar_w, 8), bar_h),
                         fill="#000000", rx=br, ry=br, opacity=0.10))

        # Bar rectangle
        dwg.add(dwg.rect((bars_left, bar_y), (max(bar_w, 8), bar_h),
                         fill=color, rx=br, ry=br, opacity=0.95))

        # Standard inner highlight (top third lighter)
        highlight_h = bar_h // 3
        dwg.add(dwg.rect((bars_left + 2, bar_y + 2),
                         (max(bar_w - 4, 4), highlight_h),
                         fill="#FFFFFF", opacity=0.15, rx=br, ry=br))

        # Label below bar
        label_x = bars_left + 4
        label_y = bar_y + bar_h + bars["label_gap"] + 6
        dwg.add(dwg.text(item["label"],
                         insert=(label_x, label_y),
                         font_size=22,
                         fill="#1D3557",
                         font_family=font, text_anchor="start",
                         font_weight="600"))

        # Checkmark on GLANCE bar
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

    # "6 RCTs" annotation (in left zone, below scissors)
    # This is part of scissors annotation, handled by scissors draw


def draw_bars_v5(dwg, layout, palette, W, H):
    """V5: Full bars with gradient shine, subtitle, stats — almost V6."""
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

    # Axis scale
    axis = bars["axis"]
    axis_y = bars_top + axis["y_offset"]
    dwg.add(dwg.line((bars_left, axis_y + axis["tick_height"]),
                     (bars_left + bars_max_w, axis_y + axis["tick_height"]),
                     stroke="#8D99AE", stroke_width=1.5))

    for tick_val in axis["ticks"]:
        tick_x = bars_left + int(bars_max_w * tick_val / 100)
        dwg.add(dwg.line((tick_x, axis_y),
                         (tick_x, axis_y + axis["tick_height"]),
                         stroke="#8D99AE", stroke_width=1.5))
        label_text = f"{tick_val}%" if tick_val == 100 else str(tick_val)
        dwg.add(dwg.text(label_text,
                         insert=(tick_x, axis_y - 6),
                         font_size=axis["font_size"],
                         fill="#8D99AE",
                         font_family=font, text_anchor="middle"))

    for i, item in enumerate(bars["items"]):
        bar_y = bars_top + i * (bar_h + bar_gap)
        bar_w = int(bars_max_w * item["width_pct"])
        color = resolve_color(palette, f"bars.{item['key']}")

        # Shadow
        dwg.add(dwg.rect((bars_left + 4, bar_y + 4), (max(bar_w, 8), bar_h),
                         fill="#000000", rx=br, ry=br, opacity=0.10))

        # Bar rectangle
        dwg.add(dwg.rect((bars_left, bar_y), (max(bar_w, 8), bar_h),
                         fill=color, rx=br, ry=br, opacity=0.95))

        # Gradient shine for GLANCE bar
        if item.get("gradient_shine"):
            shine_id = f"shine_{item['key']}"
            shine_grad = dwg.defs.add(dwg.linearGradient(
                id=shine_id, x1="0%", y1="0%", x2="0%", y2="100%"))
            shine_grad.add_stop_color(0, "#FFFFFF", opacity=0.35)
            shine_grad.add_stop_color(0.4, "#FFFFFF", opacity=0.08)
            shine_grad.add_stop_color(1, "#000000", opacity=0.05)
            dwg.add(dwg.rect((bars_left, bar_y), (max(bar_w, 8), bar_h),
                             fill=f"url(#{shine_id})", rx=br, ry=br))
            # Subtle glow
            dwg.add(dwg.rect((bars_left - 2, bar_y - 2),
                             (max(bar_w + 4, 12), bar_h + 4),
                             fill="none", rx=br + 2, ry=br + 2,
                             stroke=color, stroke_width=2, opacity=0.25))
        else:
            highlight_h = bar_h // 3
            dwg.add(dwg.rect((bars_left + 2, bar_y + 2),
                             (max(bar_w - 4, 4), highlight_h),
                             fill="#FFFFFF", opacity=0.15, rx=br, ry=br))

        # Label below bar
        label_x = bars_left + 4
        label_y = bar_y + bar_h + bars["label_gap"] + 6
        dwg.add(dwg.text(item["label"],
                         insert=(label_x, label_y),
                         font_size=bars["label_font_size"],
                         fill="#1D3557",
                         font_family=font, text_anchor="start",
                         font_weight="600"))

        # Underline
        label_text_width = len(item["label"]) * bars["label_font_size"] * 0.52
        underline_y = label_y + 5
        dwg.add(dwg.line((label_x, underline_y),
                         (label_x + label_text_width, underline_y),
                         stroke="#8D99AE", stroke_width=1.0, opacity=0.25))

        # Checkmark
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

    # Subtitle
    subtitle_y = bars_top + len(bars["items"]) * (bar_h + bar_gap) + 30
    dwg.add(dwg.text("What do readers actually understand?",
                     insert=(bars_left + bars_max_w // 2, subtitle_y),
                     font_size=22,
                     fill="#6B7280",
                     font_family=font, text_anchor="middle",
                     font_style="italic"))

    # Stats line
    stats_y = subtitle_y + 36
    dwg.add(dwg.text("47 GAs \u00b7 15 domains \u00b7 glance.scisense.fr",
                     insert=(bars_left + bars_max_w // 2, stats_y),
                     font_size=18,
                     fill="#8D99AE",
                     font_family=font, text_anchor="middle"))


def draw_scissors_simple(dwg, layout, palette, W, H):
    """V2: Simple scissors graph — thin lines, small dots, no grid, no multiplier."""
    lz = layout["zones"]["left"]
    zone_x = int(W * lz["x_pct"])
    zone_w = int(W * lz["width_pct"])
    sc = layout["scissors"]
    font = layout["font"]["family"]

    graph_top = int(H * sc["y_start_pct"])
    graph_bot = int(H * sc["y_end_pct"])
    graph_left = zone_x + int(zone_w * sc["x_margin_pct"])
    graph_right = zone_x + zone_w - int(zone_w * sc["x_margin_pct"])
    graph_w = graph_right - graph_left
    graph_h = graph_bot - graph_top

    # Faint axis lines
    dwg.add(dwg.line((graph_left, graph_bot), (graph_right, graph_bot),
                     stroke="#8D99AE", stroke_width=1, opacity=0.3))
    dwg.add(dwg.line((graph_left, graph_top), (graph_left, graph_bot),
                     stroke="#8D99AE", stroke_width=1, opacity=0.3))

    # Engagement line (thin, stroke 3)
    eng = sc["engagement"]
    eng_pts = []
    for fx, fy in eng["points"]:
        px = graph_left + graph_w * fx
        py = graph_top + graph_h * fy
        eng_pts.append((px, py))

    dwg.add(dwg.polyline(eng_pts, fill="none",
                         stroke="#E63946", stroke_width=3,
                         stroke_linejoin="bevel", stroke_linecap="round"))

    # Small dots
    for px, py in eng_pts:
        dwg.add(dwg.circle((px, py), 4, fill="#E63946"))

    # Inline label (small)
    last_eng = eng_pts[-1]
    dwg.add(dwg.text("Engagement",
                     insert=(last_eng[0] - 10, last_eng[1] - 16),
                     font_size=17, fill="#E63946",
                     font_family=font, text_anchor="end",
                     font_weight="500"))

    # Comprehension line (flat, thin)
    comp = sc["comprehension"]
    comp_pts = []
    for fx, fy in comp["points"]:
        px = graph_left + graph_w * fx
        py = graph_top + graph_h * fy
        comp_pts.append((px, py))

    dwg.add(dwg.polyline(comp_pts, fill="none",
                         stroke="#8D99AE", stroke_width=1.5,
                         stroke_linejoin="bevel", stroke_linecap="round",
                         stroke_dasharray="10,5"))

    for px, py in comp_pts:
        dwg.add(dwg.circle((px, py), 3, fill="#8D99AE"))

    last_comp = comp_pts[-1]
    dwg.add(dwg.text("Comprehension",
                     insert=(last_comp[0] - 10, last_comp[1] + 22),
                     font_size=15, fill="#1D3557",
                     font_family=font, text_anchor="end",
                     font_weight="400", opacity=0.6))


def draw_scissors_v3(dwg, layout, palette, W, H):
    """V3: Scissors graph slightly thicker than V2, still no grid or multiplier."""
    lz = layout["zones"]["left"]
    zone_x = int(W * lz["x_pct"])
    zone_w = int(W * lz["width_pct"])
    sc = layout["scissors"]
    font = layout["font"]["family"]

    graph_top = int(H * sc["y_start_pct"])
    graph_bot = int(H * sc["y_end_pct"])
    graph_left = zone_x + int(zone_w * sc["x_margin_pct"])
    graph_right = zone_x + zone_w - int(zone_w * sc["x_margin_pct"])
    graph_w = graph_right - graph_left
    graph_h = graph_bot - graph_top

    dwg.add(dwg.line((graph_left, graph_bot), (graph_right, graph_bot),
                     stroke="#8D99AE", stroke_width=1.5, opacity=0.4))
    dwg.add(dwg.line((graph_left, graph_top), (graph_left, graph_bot),
                     stroke="#8D99AE", stroke_width=1.5, opacity=0.4))

    # Engagement line (stroke 5)
    eng = sc["engagement"]
    eng_pts = []
    for fx, fy in eng["points"]:
        px = graph_left + graph_w * fx
        py = graph_top + graph_h * fy
        eng_pts.append((px, py))

    dwg.add(dwg.polyline(eng_pts, fill="none",
                         stroke="#E63946", stroke_width=5,
                         stroke_linejoin="bevel", stroke_linecap="round"))

    for px, py in eng_pts:
        dwg.add(dwg.circle((px, py), 5, fill="#E63946"))

    last_eng = eng_pts[-1]
    dwg.add(dwg.text("Engagement",
                     insert=(last_eng[0] - 10, last_eng[1] - 18),
                     font_size=19, fill="#E63946",
                     font_family=font, text_anchor="end",
                     font_weight="bold"))

    # Comprehension line
    comp = sc["comprehension"]
    comp_pts = []
    for fx, fy in comp["points"]:
        px = graph_left + graph_w * fx
        py = graph_top + graph_h * fy
        comp_pts.append((px, py))

    dwg.add(dwg.polyline(comp_pts, fill="none",
                         stroke="#8D99AE", stroke_width=2,
                         stroke_linejoin="bevel", stroke_linecap="round",
                         stroke_dasharray="10,5"))

    for px, py in comp_pts:
        dwg.add(dwg.circle((px, py), 3, fill="#8D99AE"))

    last_comp = comp_pts[-1]
    dwg.add(dwg.text("Comprehension",
                     insert=(last_comp[0] - 10, last_comp[1] + 24),
                     font_size=17, fill="#1D3557",
                     font_family=font, text_anchor="end",
                     font_weight="400", opacity=0.65))


def draw_scissors_v4(dwg, layout, palette, W, H):
    """V4: Thicker engagement line, grid lines, annotation. No multiplier yet."""
    lz = layout["zones"]["left"]
    zone_x = int(W * lz["x_pct"])
    zone_w = int(W * lz["width_pct"])
    sc = layout["scissors"]
    font = layout["font"]["family"]

    graph_top = int(H * sc["y_start_pct"])
    graph_bot = int(H * sc["y_end_pct"])
    graph_left = zone_x + int(zone_w * sc["x_margin_pct"])
    graph_right = zone_x + zone_w - int(zone_w * sc["x_margin_pct"])
    graph_w = graph_right - graph_left
    graph_h = graph_bot - graph_top

    dwg.add(dwg.line((graph_left, graph_bot), (graph_right, graph_bot),
                     stroke="#8D99AE", stroke_width=1.5, opacity=0.4))
    dwg.add(dwg.line((graph_left, graph_top), (graph_left, graph_bot),
                     stroke="#8D99AE", stroke_width=1.5, opacity=0.4))

    # Grid lines
    n_grid = 4
    for gi in range(1, n_grid + 1):
        gy = graph_top + graph_h * gi / (n_grid + 1)
        dwg.add(dwg.line((graph_left, gy), (graph_right, gy),
                         stroke="#8D99AE", stroke_width=0.8,
                         opacity=0.18, stroke_dasharray="6,4"))

    # Engagement line (stroke 7, close to final)
    eng = sc["engagement"]
    eng_pts = []
    for fx, fy in eng["points"]:
        px = graph_left + graph_w * fx
        py = graph_top + graph_h * fy
        eng_pts.append((px, py))

    dwg.add(dwg.polyline(eng_pts, fill="none",
                         stroke="#E63946", stroke_width=7,
                         stroke_linejoin="bevel", stroke_linecap="round"))

    for px, py in eng_pts:
        dwg.add(dwg.circle((px, py), 6, fill="#E63946"))

    last_eng = eng_pts[-1]
    dwg.add(dwg.text("Engagement",
                     insert=(last_eng[0] - 10, last_eng[1] - 20),
                     font_size=21, fill="#E63946",
                     font_family=font, text_anchor="end",
                     font_weight="bold"))

    # Comprehension line
    comp = sc["comprehension"]
    comp_pts = []
    for fx, fy in comp["points"]:
        px = graph_left + graph_w * fx
        py = graph_top + graph_h * fy
        comp_pts.append((px, py))

    dwg.add(dwg.polyline(comp_pts, fill="none",
                         stroke="#8D99AE", stroke_width=2.5,
                         stroke_linejoin="bevel", stroke_linecap="round",
                         stroke_dasharray="10,5"))

    for px, py in comp_pts:
        dwg.add(dwg.circle((px, py), 4, fill="#8D99AE"))

    last_comp = comp_pts[-1]
    dwg.add(dwg.text("Comprehension",
                     insert=(last_comp[0] - 10, last_comp[1] + 26),
                     font_size=19, fill="#1D3557",
                     font_family=font, text_anchor="end",
                     font_weight="500", opacity=0.65))

    # Annotation
    ann = sc["annotation"]
    ann_y = graph_bot + int(graph_h * ann["y_offset_pct"]) + 24
    ann_x = graph_left + graph_w // 2
    dwg.add(dwg.text(ann["text"],
                     insert=(ann_x, ann_y),
                     font_size=ann["font_size"],
                     fill="#6B7280",
                     font_family=font, text_anchor="middle",
                     font_weight="500"))


def draw_lens_small(dwg, layout, palette, W, H):
    """V3: Smaller magnifying lens, thinner stroke, no glow effects."""
    lz = layout["zones"]["left"]
    zone_x = int(W * lz["x_pct"])
    zone_w = int(W * lz["width_pct"])
    lens = layout["lens"]
    font = layout["font"]["family"]

    cx = zone_x + int(zone_w * lens["cx_pct"])
    cy = int(H * lens["cy_pct"])
    radius = int(zone_w * lens["radius_pct"] * 0.75)  # smaller

    # Faint fill inside lens
    dwg.add(dwg.circle((cx, cy), radius,
                       fill="#FFECEC", opacity=0.2))

    # Lens frame (thinner)
    dwg.add(dwg.circle((cx, cy), radius,
                       fill="none",
                       stroke="#F4A261",
                       stroke_width=4))

    # Handle
    handle_len = int(zone_w * lens["handle_length_pct"])
    angle_rad = math.radians(lens["handle_angle_deg"])
    hx_start = cx + int(radius * math.cos(angle_rad))
    hy_start = cy + int(radius * math.sin(angle_rad))
    hx_end = cx + int((radius + handle_len) * math.cos(angle_rad))
    hy_end = cy + int((radius + handle_len) * math.sin(angle_rad))
    dwg.add(dwg.line((hx_start, hy_start), (hx_end, hy_end),
                     stroke="#F4A261",
                     stroke_width=4,
                     stroke_linecap="round"))

    # "Visual Spin" label
    label_y = cy + radius + 28
    dwg.add(dwg.text(lens["label"],
                     insert=(cx, label_y),
                     font_size=18,
                     fill="#F4A261",
                     font_family=font, text_anchor="middle",
                     font_weight="bold",
                     font_style="italic"))


def draw_fracture_small(dwg, layout, palette, W, H):
    """V3: Fracture line + smaller chronometer, simpler."""
    frac = layout["fracture"]
    frac_zone = layout["zones"]["fracture"]
    frac_x = int(W * frac_zone["x_pct"])
    font = layout["font"]["family"]

    # Irregular fracture line
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
                     stroke="#1D3557",
                     stroke_width=2,
                     stroke_dasharray="10,6",
                     opacity=0.3))

    # Smaller chronometer
    chrono = frac["chrono"]
    chrono_cx = frac_x
    chrono_cy = int(H * chrono["cy_pct"])
    chrono_r = int(chrono["radius"] * 0.75)  # smaller

    # White backing
    dwg.add(dwg.circle((chrono_cx, chrono_cy), chrono_r + 3,
                       fill="#FFFFFF"))

    # Frame
    dwg.add(dwg.circle((chrono_cx, chrono_cy), chrono_r,
                       fill="#FFFFFF",
                       stroke="#1D3557",
                       stroke_width=3.5))

    # Major tick marks only (12 positions)
    for i in range(12):
        angle = math.radians(i * 30 - 90)
        inner_r = chrono_r * 0.78
        outer_r = chrono_r * 0.92
        sw = 2 if i % 3 == 0 else 1.2
        x1 = chrono_cx + inner_r * math.cos(angle)
        y1 = chrono_cy + inner_r * math.sin(angle)
        x2 = chrono_cx + outer_r * math.cos(angle)
        y2 = chrono_cy + outer_r * math.sin(angle)
        dwg.add(dwg.line((x1, y1), (x2, y2),
                         stroke="#1D3557", stroke_width=sw))

    # Center dot
    dwg.add(dwg.circle((chrono_cx, chrono_cy), 3, fill="#1D3557"))

    # Minute hand
    min_angle = math.radians(chrono["minute_angle_deg"] - 90)
    min_len = chrono_r * chrono["minute_length_pct"]
    min_x = chrono_cx + min_len * math.cos(min_angle)
    min_y = chrono_cy + min_len * math.sin(min_angle)
    dwg.add(dwg.line((chrono_cx, chrono_cy), (min_x, min_y),
                     stroke="#1D3557",
                     stroke_width=2.5, stroke_linecap="round"))

    # Second hand
    sec_angle = math.radians(chrono["second_angle_deg"] - 90)
    sec_len = chrono_r * chrono["second_length_pct"]
    sec_x = chrono_cx + sec_len * math.cos(sec_angle)
    sec_y = chrono_cy + sec_len * math.sin(sec_angle)
    dwg.add(dwg.line((chrono_cx, chrono_cy), (sec_x, sec_y),
                     stroke="#F4A261",
                     stroke_width=1.5, stroke_linecap="round"))

    # "5.0s" label
    label_y = chrono_cy + chrono_r + 22
    dwg.add(dwg.text(chrono["label"],
                     insert=(chrono_cx, label_y),
                     font_size=18,
                     fill="#6B7280",
                     font_family=font, text_anchor="middle",
                     font_weight="bold"))


def draw_accents_faint(dwg, layout, palette, W, H):
    """V4: Angular accents, fainter than final."""
    lz = layout["zones"]["left"]
    zone_x = int(W * lz["x_pct"])
    zone_w = int(W * lz["width_pct"])
    accent_color = "#E63946"

    x1 = zone_x + 18
    y1 = int(H * 0.12)
    dwg.add(dwg.line((x1, y1), (x1 + 55, y1),
                     stroke=accent_color, stroke_width=2.5, opacity=0.25))
    dwg.add(dwg.line((x1, y1), (x1, y1 + 55),
                     stroke=accent_color, stroke_width=2.5, opacity=0.25))

    x2 = zone_x + zone_w - 18
    y2 = int(H * 0.92)
    dwg.add(dwg.line((x2, y2), (x2 - 55, y2),
                     stroke=accent_color, stroke_width=2.5, opacity=0.25))
    dwg.add(dwg.line((x2, y2), (x2, y2 - 55),
                     stroke=accent_color, stroke_width=2.5, opacity=0.25))


# ===================================================================
# VERSION DEFINITIONS
# ===================================================================

def compose_v1(layout, palette, W, H, svg_path):
    """V1 — Bare bones: white bg, small title, 3 flat bars, inline labels."""
    dwg = svgwrite.Drawing(svg_path, size=(f"{W}px", f"{H}px"),
                           viewBox=f"0 0 {W} {H}")
    dwg.attribs["xmlns"] = "http://www.w3.org/2000/svg"

    draw_bg_white_only(dwg, W, H)
    draw_title_simple(dwg, layout, W, H)
    draw_bars_v1(dwg, layout, palette, W, H)

    dwg.save()
    return svg_path


def compose_v2(layout, palette, W, H, svg_path):
    """V2 — Add scissors graph: thin lines, small dots, no grid."""
    dwg = svgwrite.Drawing(svg_path, size=(f"{W}px", f"{H}px"),
                           viewBox=f"0 0 {W} {H}")
    dwg.attribs["xmlns"] = "http://www.w3.org/2000/svg"

    draw_bg_white_only(dwg, W, H)
    draw_title_medium(dwg, layout, W, H)
    draw_scissors_simple(dwg, layout, palette, W, H)
    draw_bars_v2(dwg, layout, palette, W, H)

    dwg.save()
    return svg_path


def compose_v3(layout, palette, W, H, svg_path):
    """V3 — Add lens + fracture + faint red tint + bar labels + Visual Spin."""
    dwg = svgwrite.Drawing(svg_path, size=(f"{W}px", f"{H}px"),
                           viewBox=f"0 0 {W} {H}")
    dwg.attribs["xmlns"] = "http://www.w3.org/2000/svg"

    draw_bg_with_gradient(dwg, W, H)
    draw_bg_red_tint(dwg, layout, 0.40, W, H)  # faint tint
    draw_title_medium(dwg, layout, W, H)
    draw_scissors_v3(dwg, layout, palette, W, H)
    draw_lens_small(dwg, layout, palette, W, H)
    draw_fracture_small(dwg, layout, palette, W, H)
    draw_bars_v3(dwg, layout, palette, W, H)

    dwg.save()
    return svg_path


def compose_v4(layout, palette, W, H, svg_path):
    """V4 — Better layout: axis, checkmark, shadows, accents, annotation."""
    dwg = svgwrite.Drawing(svg_path, size=(f"{W}px", f"{H}px"),
                           viewBox=f"0 0 {W} {H}")
    dwg.attribs["xmlns"] = "http://www.w3.org/2000/svg"

    draw_bg_with_gradient(dwg, W, H)
    draw_bg_red_tint(dwg, layout, 0.60, W, H)
    draw_title_medium(dwg, layout, W, H)
    draw_accents_faint(dwg, layout, palette, W, H)
    draw_scissors_v4(dwg, layout, palette, W, H)
    # Use the full lens from compose_paper_ga (V4 has lens at full size)
    draw_magnifying_lens(dwg, layout, palette, W, H)
    draw_fracture(dwg, layout, palette, W, H)
    draw_bars_v4(dwg, layout, palette, W, H)

    dwg.save()
    return svg_path


def compose_v5(layout, palette, W, H, svg_path):
    """V5 — Polish: stronger tint, glow, subtitle, stats, bigger dots."""
    dwg = svgwrite.Drawing(svg_path, size=(f"{W}px", f"{H}px"),
                           viewBox=f"0 0 {W} {H}")
    dwg.attribs["xmlns"] = "http://www.w3.org/2000/svg"

    draw_bg_with_gradient(dwg, W, H)
    draw_bg_red_tint(dwg, layout, 0.80, W, H)  # stronger
    draw_title_full(dwg, layout, W, H)
    draw_angular_accents(dwg, layout, palette, W, H)  # full accents

    # Full scissors from compositor (with grid, multiplier)
    draw_scissors_graph(dwg, layout, palette, W, H)

    # Full lens with glow
    draw_magnifying_lens(dwg, layout, palette, W, H)

    # Full fracture
    draw_fracture(dwg, layout, palette, W, H)

    # Polished bars
    draw_bars_v5(dwg, layout, palette, W, H)

    dwg.save()
    return svg_path


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

    composers = [
        (1, compose_v1),
        (2, compose_v2),
        (3, compose_v3),
        (4, compose_v4),
        (5, compose_v5),
    ]

    for ver, compose_fn in composers:
        print(f"\n--- Generating V{ver} ---")
        svg_path = os.path.join(VER_DIR, f"v{ver}_temp.svg")
        full_png = os.path.join(VER_DIR, f"v{ver}_full.png")
        delivery_png = os.path.join(VER_DIR, f"v{ver}_delivery.png")

        compose_fn(layout, palette, W, H, svg_path)
        print(f"  SVG saved: {svg_path}")

        print(f"  Rendering PNG...")
        render_png(svg_path, full_png, delivery_png, W, H, dw, dh)

        # Clean up temp SVG
        if os.path.exists(svg_path):
            os.remove(svg_path)

    print("\n=== All 5 versions generated ===")
    for v in range(1, 6):
        dp = os.path.join(VER_DIR, f"v{v}_delivery.png")
        exists = "OK" if os.path.exists(dp) else "MISSING"
        print(f"  V{v}: {exists} -> {dp}")


if __name__ == "__main__":
    main()
