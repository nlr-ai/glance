"""GLANCE Scanpath Video Generator — animated GIF of the reading simulation.

Generates a 5-second animated GIF showing the scanpath animation:
- GA image as background with dim overlay
- Nodes light up progressively as the virtual eye visits them
- Eye dot moves between nodes
- Trail grows as nodes are visited

Uses Pillow for frame-by-frame rendering (no external dependencies).

Usage:
    from video_generator import generate_scanpath_gif
    gif_bytes = generate_scanpath_gif(graph, sim_result, image_path)
"""

import io
import os
import math
import logging
from collections import defaultdict

logger = logging.getLogger("video_generator")

# ── Color anchors (same as graph_renderer.py) ──────────────────────────

COLOR_ANCHORS = [
    (0.0, (71, 85, 105)),     # grey
    (0.2, (59, 130, 246)),    # blue
    (0.5, (45, 212, 191)),    # teal
    (0.8, (245, 158, 11)),    # amber
    (1.0, (251, 191, 36)),    # gold
]


def _att_color(ratio):
    """Interpolate attention ratio (0-1) to RGB tuple."""
    ratio = max(0.0, min(1.0, ratio))
    for i in range(len(COLOR_ANCHORS) - 1):
        lo_t, lo_c = COLOR_ANCHORS[i]
        hi_t, hi_c = COLOR_ANCHORS[i + 1]
        if lo_t <= ratio <= hi_t:
            span = hi_t - lo_t
            if span == 0:
                return lo_c
            t = (ratio - lo_t) / span
            return (
                int(lo_c[0] + t * (hi_c[0] - lo_c[0])),
                int(lo_c[1] + t * (hi_c[1] - lo_c[1])),
                int(lo_c[2] + t * (hi_c[2] - lo_c[2])),
            )
    return COLOR_ANCHORS[-1][1]


def generate_scanpath_gif(graph, sim_result, image_path,
                          fps=10, duration_s=5, max_size=(480, 320)):
    """Generate an animated GIF of the scanpath simulation.

    Args:
        graph: L3 graph dict with nodes and links
        sim_result: reader sim result dict with scanpath, heatmap, etc.
        image_path: path to the GA image file
        fps: frames per second (default 10 for reasonable GIF size)
        duration_s: total animation duration in seconds
        max_size: (width, height) max dimensions for the GIF

    Returns:
        bytes of the animated GIF, or None on failure.
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        logger.warning("Pillow not available")
        return None

    if not graph or not sim_result or sim_result.get("error"):
        return None

    if not os.path.exists(image_path):
        logger.warning(f"Image not found: {image_path}")
        return None

    # Load and resize GA image
    try:
        ga_img = Image.open(image_path).convert("RGBA")
    except Exception as e:
        logger.warning(f"Failed to open image: {e}")
        return None

    # Resize to max_size maintaining aspect ratio
    ga_img.thumbnail(max_size, Image.LANCZOS)
    img_w, img_h = ga_img.size

    # Get render data
    try:
        from graph_renderer import assemble_render_data
        data = assemble_render_data(graph, sim_result, img_w, img_h)
    except Exception as e:
        logger.warning(f"assemble_render_data failed: {e}")
        return None

    if not data:
        return None

    # Build scanpath timeline from sim_result
    scanpath = sim_result.get("scanpath", [])
    if not scanpath:
        return None

    TICK_MS = 100
    total_sim_ms = scanpath[-1].get("time_ms", 0) + TICK_MS

    # Build timeline: group consecutive ticks on same node
    timeline = []
    cur = None
    for s in scanpath:
        nid = s.get("node_id", "")
        if not cur or cur["node_id"] != nid:
            if cur:
                timeline.append(cur)
            cur = {
                "node_id": nid,
                "start_ms": s.get("time_ms", 0),
                "end_ms": s.get("time_ms", 0) + TICK_MS,
                "x": s.get("x", 0.5),
                "y": s.get("y", 0.5),
            }
        else:
            cur["end_ms"] = s.get("time_ms", 0) + TICK_MS
    if cur:
        timeline.append(cur)

    # Build node lookup from render data
    node_lookup = {}
    for node in data["nodes"]:
        node_lookup[node["id"]] = node

    # Prepare base frame: GA image with dim overlay
    dim = Image.new("RGBA", (img_w, img_h), (10, 14, 26, 100))
    base_frame = Image.alpha_composite(ga_img, dim)

    # Generate frames
    total_frames = fps * duration_s
    frames = []

    for frame_idx in range(total_frames):
        # Map frame time to sim time
        frame_time_s = frame_idx / fps
        elapsed_ms = (frame_time_s / duration_s) * total_sim_ms

        # Determine visited nodes and current step
        visited = {}
        cumulative_att = defaultdict(float)
        current_step = None
        trail_points = []

        for step in timeline:
            if step["start_ms"] <= elapsed_ms:
                visited[step["node_id"]] = True
                # Accumulate attention proportionally
                overlap_start = step["start_ms"]
                overlap_end = min(elapsed_ms, step["end_ms"])
                cumulative_att[step["node_id"]] += max(0, overlap_end - overlap_start)
                trail_points.append((step["x"] * img_w, step["y"] * img_h))
            if step["start_ms"] <= elapsed_ms < step["end_ms"]:
                current_step = step

        max_att = max(cumulative_att.values()) if cumulative_att else 1.0
        if max_att == 0:
            max_att = 1.0

        # Draw frame
        frame = base_frame.copy()
        draw = ImageDraw.Draw(frame)

        # Draw links (dim)
        for link in data["links"]:
            r, g, b = 100, 116, 139
            alpha = 60
            if link["is_gold"]:
                # Check if both endpoints visited
                src_vis = link.get("source", "") in visited
                tgt_vis = link.get("target", "") in visited
                if src_vis and tgt_vis:
                    r, g, b = 251, 191, 36
                    alpha = 150
            draw.line(
                [(int(link["x1"]), int(link["y1"])),
                 (int(link["x2"]), int(link["y2"]))],
                fill=(r, g, b, alpha), width=1,
            )

        # Draw nodes
        for node in data["nodes"]:
            nid = node["id"]
            cx, cy = int(node["x"]), int(node["y"])
            nr = max(2, int(node["radius"]))

            if nid in visited:
                att_ratio = cumulative_att[nid] / max_att
                color = _att_color(att_ratio)
                alpha = 220
                is_active = current_step and current_step["node_id"] == nid

                # Active node: slightly larger + glow
                if is_active:
                    glow_r = nr + 4
                    draw.ellipse(
                        [cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r],
                        fill=(color[0], color[1], color[2], 80),
                    )
                    nr_draw = nr + 1
                else:
                    nr_draw = nr

                draw.ellipse(
                    [cx - nr_draw, cy - nr_draw, cx + nr_draw, cy + nr_draw],
                    fill=(color[0], color[1], color[2], alpha),
                    outline=(255, 255, 255, 100), width=1,
                )
            else:
                # Unvisited: dim grey
                draw.ellipse(
                    [cx - nr, cy - nr, cx + nr, cy + nr],
                    fill=(71, 85, 105, 80),
                )

        # Draw trail
        if len(trail_points) > 1:
            for i in range(len(trail_points) - 1):
                x1, y1 = trail_points[i]
                x2, y2 = trail_points[i + 1]
                draw.line(
                    [(int(x1), int(y1)), (int(x2), int(y2))],
                    fill=(245, 158, 11, 120), width=1,
                )

        # Draw eye dot
        if current_step:
            ex = int(current_step["x"] * img_w)
            ey = int(current_step["y"] * img_h)
            draw.ellipse(
                [ex - 4, ey - 4, ex + 4, ey + 4],
                fill=(255, 255, 255, 220),
                outline=(200, 200, 200, 180), width=1,
            )

        # Convert to P mode for GIF (palette)
        frame_rgb = frame.convert("RGB")
        frames.append(frame_rgb)

    if not frames:
        return None

    # Save animated GIF
    buf = io.BytesIO()
    frames[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / fps),  # ms per frame
        loop=0,  # infinite loop
        optimize=True,
    )
    buf.seek(0)
    return buf.getvalue()
