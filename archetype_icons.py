"""Archetype icons — inline SVGs + PNG generator for the 7 GA archetypes.

Each archetype has:
- A hand-crafted inline SVG (64x64 viewBox, 2px stroke, monochrome + accent)
- A programmatic PNG renderer (128x128, transparent background)

Style: geometric, minimal, scientific feel, consistent 2px stroke weight.
"""

import os
import math
from PIL import Image, ImageDraw

BASE = os.path.dirname(__file__)
ICONS_DIR = os.path.join(BASE, "static", "icons")

# ── Color palette ────────────────────────────────────────────────────────

ARCHETYPE_COLORS = {
    "cristallin": "#10b981",
    "spectacle": "#8b5cf6",
    "tresor_enfoui": "#f59e0b",
    "encyclopedie": "#3b82f6",
    "desequilibre": "#f97316",
    "embelli": "#ec4899",
    "fantome": "#64748b",
}


# ── SVG definitions ──────────────────────────────────────────────────────

ARCHETYPE_SVGS = {
    # 1. Cristallin — hexagonal diamond with radiating light lines
    "cristallin": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <!-- Diamond body -->
  <polygon points="32,8 48,22 48,42 32,56 16,42 16,22" />
  <!-- Inner facets -->
  <line x1="32" y1="8" x2="32" y2="56" />
  <line x1="16" y1="22" x2="48" y2="22" />
  <line x1="16" y1="42" x2="48" y2="42" />
  <!-- Radiating light -->
  <line x1="32" y1="2" x2="32" y2="5" />
  <line x1="52" y1="12" x2="54" y2="10" />
  <line x1="52" y1="52" x2="54" y2="54" />
  <line x1="12" y1="12" x2="10" y2="10" />
  <line x1="12" y1="52" x2="10" y2="54" />
  <line x1="56" y1="32" x2="59" y2="32" />
  <line x1="5" y1="32" x2="8" y2="32" />
</svg>''',

    # 2. Spectacle — eye shape with sparkles and hollow pupil
    "spectacle": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#8b5cf6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <!-- Eye outline -->
  <path d="M4,32 Q16,14 32,14 Q48,14 60,32 Q48,50 32,50 Q16,50 4,32 Z" />
  <!-- Iris circle -->
  <circle cx="32" cy="32" r="10" />
  <!-- Hollow pupil (dashed) -->
  <circle cx="32" cy="32" r="4" stroke-dasharray="2,2" />
  <!-- Sparkles -->
  <line x1="12" y1="8" x2="12" y2="14" />
  <line x1="9" y1="11" x2="15" y2="11" />
  <line x1="52" y1="8" x2="52" y2="14" />
  <line x1="49" y1="11" x2="55" y2="11" />
  <line x1="52" y1="50" x2="52" y2="56" />
  <line x1="49" y1="53" x2="55" y2="53" />
</svg>''',

    # 3. Tresor Enfoui — diamond partially buried in rock/ground
    "tresor_enfoui": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <!-- Diamond (top visible) -->
  <polygon points="32,8 44,22 44,34 32,42 20,34 20,22" />
  <!-- Inner facets of diamond -->
  <line x1="32" y1="8" x2="32" y2="42" />
  <line x1="20" y1="22" x2="44" y2="22" />
  <!-- Jagged ground line covering bottom -->
  <polyline points="4,36 12,32 18,38 24,34 30,40 36,33 42,38 48,34 54,37 60,33" />
  <!-- Rock/ground mass -->
  <polyline points="4,36 4,58 60,58 60,33" />
  <line x1="10" y1="44" x2="16" y2="44" />
  <line x1="36" y1="48" x2="44" y2="48" />
  <line x1="22" y1="52" x2="30" y2="52" />
</svg>''',

    # 4. Encyclopedie — text overflowing from a page
    "encyclopedie": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <!-- Page rectangle -->
  <rect x="12" y="8" width="40" height="48" rx="2" />
  <!-- Text lines inside (contained) -->
  <line x1="18" y1="16" x2="46" y2="16" />
  <line x1="18" y1="22" x2="46" y2="22" />
  <line x1="18" y1="28" x2="46" y2="28" />
  <line x1="18" y1="34" x2="46" y2="34" />
  <line x1="18" y1="40" x2="46" y2="40" />
  <line x1="18" y1="46" x2="46" y2="46" />
  <!-- Overflowing lines (spill past page edge) -->
  <line x1="18" y1="52" x2="50" y2="52" />
  <line x1="18" y1="58" x2="54" y2="58" opacity="0.6" />
  <line x1="18" y1="64" x2="48" y2="64" opacity="0.3" />
</svg>''',

    # 5. Desequilibre — tilted balance scale
    "desequilibre": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#f97316" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <!-- Base -->
  <line x1="22" y1="58" x2="42" y2="58" />
  <line x1="32" y1="58" x2="32" y2="18" />
  <!-- Fulcrum triangle -->
  <polygon points="28,58 36,58 32,52" />
  <!-- Tilted beam -->
  <line x1="10" y1="22" x2="54" y2="14" />
  <!-- Left pan (heavy, down) — 3 chain lines -->
  <line x1="10" y1="22" x2="10" y2="16" />
  <path d="M4,42 Q7,46 10,46 Q13,46 16,42" />
  <line x1="4" y1="42" x2="4" y2="22" />
  <line x1="16" y1="42" x2="16" y2="22" />
  <!-- Right pan (light, up) — 3 chain lines -->
  <line x1="54" y1="14" x2="54" y2="8" />
  <path d="M48,28 Q51,32 54,32 Q57,32 60,28" />
  <line x1="48" y1="28" x2="48" y2="14" />
  <line x1="60" y1="28" x2="60" y2="14" />
</svg>''',

    # 6. Embelli — bar chart with sparkle polish + warning triangle
    "embelli": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#ec4899" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <!-- Bar chart bars -->
  <rect x="10" y="34" width="8" height="22" rx="1" />
  <rect x="22" y="22" width="8" height="34" rx="1" />
  <rect x="34" y="28" width="8" height="28" rx="1" />
  <rect x="46" y="16" width="8" height="40" rx="1" />
  <!-- Sparkle effects -->
  <line x1="18" y1="14" x2="18" y2="20" />
  <line x1="15" y1="17" x2="21" y2="17" />
  <line x1="42" y1="8" x2="42" y2="14" />
  <line x1="39" y1="11" x2="45" y2="11" />
  <circle cx="56" cy="10" r="1.5" fill="#ec4899" />
  <!-- Warning triangle (corner) -->
  <polygon points="4,6 10,6 7,2" stroke-width="1.5" />
  <line x1="7" y1="3.5" x2="7" y2="4.5" stroke-width="1" />
  <circle cx="7" cy="5.5" r="0.3" fill="#ec4899" stroke-width="0" />
</svg>''',

    # 7. Fantome — dashed fading circle
    "fantome": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <!-- Main dashed circle -->
  <circle cx="32" cy="32" r="22" stroke-dasharray="4,4" opacity="0.7" />
  <!-- Inner faded circle -->
  <circle cx="32" cy="32" r="14" stroke-dasharray="3,5" opacity="0.4" />
  <!-- Innermost dot circle -->
  <circle cx="32" cy="32" r="6" stroke-dasharray="2,4" opacity="0.2" />
  <!-- Fade-out partial arcs (suggesting disappearance) -->
  <path d="M10,32 A22,22 0 0,1 32,10" stroke-dasharray="2,6" opacity="0.3" />
  <path d="M54,32 A22,22 0 0,1 32,54" stroke-dasharray="2,6" opacity="0.15" />
</svg>''',
}


# ── PNG generation ───────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert '#rrggbb' to (r, g, b)."""
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    """Convert hex to RGBA tuple."""
    r, g, b = _hex_to_rgb(hex_color)
    return (r, g, b, alpha)


def _draw_cristallin(draw: ImageDraw.ImageDraw, color: str, sz: int = 128):
    """Diamond/crystal with radiating lines."""
    c = _rgba(color)
    s = sz / 64  # scale factor

    # Diamond hexagon
    pts = [
        (32*s, 8*s), (48*s, 22*s), (48*s, 42*s),
        (32*s, 56*s), (16*s, 42*s), (16*s, 22*s),
    ]
    draw.polygon(pts, outline=c, width=max(2, int(2*s)))

    # Inner facets
    w = max(2, int(2*s))
    draw.line([(32*s, 8*s), (32*s, 56*s)], fill=c, width=w)
    draw.line([(16*s, 22*s), (48*s, 22*s)], fill=c, width=w)
    draw.line([(16*s, 42*s), (48*s, 42*s)], fill=c, width=w)

    # Radiating lines
    rays = [
        ((32*s, 2*s), (32*s, 5*s)),
        ((52*s, 12*s), (54*s, 10*s)),
        ((52*s, 52*s), (54*s, 54*s)),
        ((12*s, 12*s), (10*s, 10*s)),
        ((12*s, 52*s), (10*s, 54*s)),
        ((56*s, 32*s), (59*s, 32*s)),
        ((5*s, 32*s), (8*s, 32*s)),
    ]
    for p1, p2 in rays:
        draw.line([p1, p2], fill=c, width=w)


def _draw_spectacle(draw: ImageDraw.ImageDraw, color: str, sz: int = 128):
    """Eye with sparkles and hollow pupil."""
    c = _rgba(color)
    s = sz / 64
    w = max(2, int(2*s))

    # Eye shape (ellipse approximation)
    draw.ellipse(
        [(12*s, 18*s), (52*s, 46*s)],
        outline=c, width=w,
    )
    # Pointy ends
    draw.polygon(
        [(4*s, 32*s), (14*s, 24*s), (14*s, 40*s)],
        outline=c, width=max(1, int(1.5*s)),
    )
    draw.polygon(
        [(60*s, 32*s), (50*s, 24*s), (50*s, 40*s)],
        outline=c, width=max(1, int(1.5*s)),
    )

    # Iris
    draw.ellipse(
        [(22*s, 22*s), (42*s, 42*s)],
        outline=c, width=w,
    )

    # Hollow pupil (small dashed circle — approximate with dots)
    r_pupil = 4 * s
    cx, cy = 32*s, 32*s
    for angle_deg in range(0, 360, 30):
        a = math.radians(angle_deg)
        x = cx + r_pupil * math.cos(a)
        y = cy + r_pupil * math.sin(a)
        draw.ellipse(
            [(x - s*0.8, y - s*0.8), (x + s*0.8, y + s*0.8)],
            fill=c,
        )

    # Sparkles (+ shapes)
    for sx, sy in [(12*s, 11*s), (52*s, 11*s), (52*s, 53*s)]:
        draw.line([(sx, sy - 3*s), (sx, sy + 3*s)], fill=c, width=w)
        draw.line([(sx - 3*s, sy), (sx + 3*s, sy)], fill=c, width=w)


def _draw_tresor_enfoui(draw: ImageDraw.ImageDraw, color: str, sz: int = 128):
    """Diamond partially buried in rock."""
    c = _rgba(color)
    c_dim = _rgba(color, 140)
    s = sz / 64
    w = max(2, int(2*s))

    # Diamond top
    pts = [
        (32*s, 8*s), (44*s, 22*s), (44*s, 34*s),
        (32*s, 42*s), (20*s, 34*s), (20*s, 22*s),
    ]
    draw.polygon(pts, outline=c, width=w)

    # Inner facets
    draw.line([(32*s, 8*s), (32*s, 42*s)], fill=c, width=w)
    draw.line([(20*s, 22*s), (44*s, 22*s)], fill=c, width=w)

    # Ground line (jagged)
    ground_pts = [
        (4*s, 36*s), (12*s, 32*s), (18*s, 38*s), (24*s, 34*s),
        (30*s, 40*s), (36*s, 33*s), (42*s, 38*s), (48*s, 34*s),
        (54*s, 37*s), (60*s, 33*s),
    ]
    draw.line(ground_pts, fill=c, width=w)

    # Rock texture lines
    draw.line([(10*s, 44*s), (16*s, 44*s)], fill=c_dim, width=max(1, int(1.5*s)))
    draw.line([(36*s, 48*s), (44*s, 48*s)], fill=c_dim, width=max(1, int(1.5*s)))
    draw.line([(22*s, 52*s), (30*s, 52*s)], fill=c_dim, width=max(1, int(1.5*s)))


def _draw_encyclopedie(draw: ImageDraw.ImageDraw, color: str, sz: int = 128):
    """Text overflowing from a page."""
    c = _rgba(color)
    s = sz / 64
    w = max(2, int(2*s))

    # Page rectangle
    draw.rounded_rectangle(
        [(12*s, 8*s), (52*s, 56*s)],
        radius=int(2*s), outline=c, width=w,
    )

    # Text lines inside
    for y_val in [16, 22, 28, 34, 40, 46]:
        draw.line([(18*s, y_val*s), (46*s, y_val*s)], fill=c, width=w)

    # Overflowing lines
    draw.line([(18*s, 52*s), (50*s, 52*s)], fill=c, width=w)
    draw.line([(18*s, 58*s), (54*s, 58*s)], fill=_rgba(color, 150), width=w)
    draw.line([(18*s, 64*s), (48*s, 64*s)], fill=_rgba(color, 75), width=max(1, int(1.5*s)))


def _draw_desequilibre(draw: ImageDraw.ImageDraw, color: str, sz: int = 128):
    """Tilted balance scale."""
    c = _rgba(color)
    s = sz / 64
    w = max(2, int(2*s))

    # Base
    draw.line([(22*s, 58*s), (42*s, 58*s)], fill=c, width=w)
    draw.line([(32*s, 58*s), (32*s, 18*s)], fill=c, width=w)

    # Fulcrum triangle
    draw.polygon(
        [(28*s, 58*s), (36*s, 58*s), (32*s, 52*s)],
        outline=c, width=w,
    )

    # Tilted beam
    draw.line([(10*s, 22*s), (54*s, 14*s)], fill=c, width=w)

    # Left pan (heavy, down)
    draw.line([(4*s, 22*s), (4*s, 40*s)], fill=c, width=w)
    draw.line([(16*s, 22*s), (16*s, 40*s)], fill=c, width=w)
    draw.arc(
        [(4*s, 38*s), (16*s, 48*s)],
        start=0, end=180, fill=c, width=w,
    )

    # Right pan (light, up)
    draw.line([(48*s, 14*s), (48*s, 26*s)], fill=c, width=w)
    draw.line([(60*s, 14*s), (60*s, 26*s)], fill=c, width=w)
    draw.arc(
        [(48*s, 24*s), (60*s, 34*s)],
        start=0, end=180, fill=c, width=w,
    )


def _draw_embelli(draw: ImageDraw.ImageDraw, color: str, sz: int = 128):
    """Bar chart with sparkle polish + warning triangle."""
    c = _rgba(color)
    s = sz / 64
    w = max(2, int(2*s))

    # Bar chart bars
    bars = [
        (10, 34, 18, 56),
        (22, 22, 30, 56),
        (34, 28, 42, 56),
        (46, 16, 54, 56),
    ]
    for x1, y1, x2, y2 in bars:
        draw.rounded_rectangle(
            [(x1*s, y1*s), (x2*s, y2*s)],
            radius=int(1*s), outline=c, width=w,
        )

    # Sparkles
    for sx, sy in [(18, 17), (42, 11)]:
        draw.line([(sx*s, (sy-3)*s), (sx*s, (sy+3)*s)], fill=c, width=w)
        draw.line([((sx-3)*s, sy*s), ((sx+3)*s, sy*s)], fill=c, width=w)

    # Small dot sparkle
    draw.ellipse(
        [(54.5*s, 8.5*s), (57.5*s, 11.5*s)],
        fill=c,
    )

    # Warning triangle (top-left corner)
    draw.polygon(
        [(4*s, 8*s), (12*s, 8*s), (8*s, 2*s)],
        outline=c, width=max(1, int(1.5*s)),
    )
    # Exclamation mark inside triangle
    draw.line([(8*s, 4*s), (8*s, 5.5*s)], fill=c, width=max(1, int(s)))
    draw.ellipse(
        [(7.5*s, 6.5*s), (8.5*s, 7.5*s)],
        fill=c,
    )


def _draw_fantome(draw: ImageDraw.ImageDraw, color: str, sz: int = 128):
    """Dashed fading circles."""
    c_70 = _rgba(color, 180)
    c_40 = _rgba(color, 100)
    c_20 = _rgba(color, 50)
    s = sz / 64
    w = max(2, int(2*s))

    cx, cy = 32*s, 32*s

    # Outer dashed circle (draw as dotted segments)
    for r, alpha, seg_len, gap_len in [(22, 180, 4, 4), (14, 100, 3, 5), (6, 50, 2, 4)]:
        c_ring = _rgba(color, alpha)
        circumference = 2 * math.pi * r * s
        total_unit = (seg_len + gap_len) * s
        n_segments = max(1, int(circumference / total_unit))
        seg_angle = (seg_len * s / circumference) * 360

        for i in range(n_segments):
            start_angle = i * (360 / n_segments)
            draw.arc(
                [(cx - r*s, cy - r*s), (cx + r*s, cy + r*s)],
                start=start_angle,
                end=start_angle + seg_angle * 0.8,
                fill=c_ring, width=w,
            )


# Map archetype IDs to draw functions
_DRAW_FUNCS = {
    "cristallin": _draw_cristallin,
    "spectacle": _draw_spectacle,
    "tresor_enfoui": _draw_tresor_enfoui,
    "encyclopedie": _draw_encyclopedie,
    "desequilibre": _draw_desequilibre,
    "embelli": _draw_embelli,
    "fantome": _draw_fantome,
}


def generate_pngs(output_dir: str | None = None, size: int = 128) -> dict[str, str]:
    """Generate transparent PNG icons for all 7 archetypes.

    Returns dict mapping archetype_id -> absolute file path.
    """
    out = output_dir or ICONS_DIR
    os.makedirs(out, exist_ok=True)

    paths = {}
    for arch_id, draw_fn in _DRAW_FUNCS.items():
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        color = ARCHETYPE_COLORS[arch_id]
        draw_fn(draw, color, size)
        path = os.path.join(out, f"archetype_{arch_id}.png")
        img.save(path, "PNG")
        paths[arch_id] = path

    return paths


def get_svg(archetype_id: str) -> str | None:
    """Return inline SVG string for a given archetype ID, or None."""
    return ARCHETYPE_SVGS.get(archetype_id)


# ── CLI entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    paths = generate_pngs()
    print(f"Generated {len(paths)} PNG icons:")
    for arch_id, path in paths.items():
        print(f"  {arch_id}: {path}")
