"""
Graph Overlay Renderer — SVG + PNG composites for GA attention visualization.

Renders the L3 graph on top of a GA image as a transparent overlay.
Every visual property encodes exactly one data dimension.

Visual mapping:
  - Node position: bbox center (from Gemini vision) or estimated
  - Node size: weight (12 + weight * 28 px)
  - Node fill: attention ratio (grey → blue → teal → amber → gold)
  - Node glow: energy (unresolved tension)
  - Node opacity: stability (0.4 → 1.0)
  - Node border: anti-pattern type (red dashed/solid for problems)
  - Links: weight >= 0.3 shown (gold for thing→narrative carriers, silver otherwise)
  - Spaces: teal border if visited, red dashed if dead
  - Narrative badges: small colored dots on carrier things

Two render targets:
  - SVG: inline HTML overlay for web (ga-detail page)
  - PNG: Pillow composite for export/sharing

Usage:
    from graph_renderer import render_overlay_svg, render_overlay_png
    svg = render_overlay_svg(graph, sim_result, 900, 600)
    png_path = render_overlay_png(graph, sim_result, "path/to/ga.png")
"""

import os
import math
import logging
from collections import defaultdict

logger = logging.getLogger("graph_renderer")


# ── Color interpolation ─────────────────────────────────────────────────

COLOR_ANCHORS = [
    (0.0, (71, 85, 105)),     # grey  #475569
    (0.2, (59, 130, 246)),    # blue  #3b82f6
    (0.5, (45, 212, 191)),    # teal  #2dd4bf
    (0.8, (245, 158, 11)),    # amber #f59e0b
    (1.0, (251, 191, 36)),    # gold  #fbbf24
]


def attention_to_color(ratio):
    """Interpolate between color anchors based on attention ratio 0-1.

    0.0 -> grey #475569
    0.2 -> blue #3b82f6
    0.5 -> teal #2dd4bf
    0.8 -> amber #f59e0b
    1.0 -> gold #fbbf24

    Returns (r, g, b) tuple.
    """
    ratio = max(0.0, min(1.0, ratio))
    for i in range(len(COLOR_ANCHORS) - 1):
        lo_t, lo_c = COLOR_ANCHORS[i]
        hi_t, hi_c = COLOR_ANCHORS[i + 1]
        if lo_t <= ratio <= hi_t:
            span = hi_t - lo_t
            if span == 0:
                return lo_c
            t = (ratio - lo_t) / span
            r = int(lo_c[0] + t * (hi_c[0] - lo_c[0]))
            g = int(lo_c[1] + t * (hi_c[1] - lo_c[1]))
            b = int(lo_c[2] + t * (hi_c[2] - lo_c[2]))
            return (r, g, b)
    return COLOR_ANCHORS[-1][1]


def _rgb_hex(rgb):
    """Convert (r, g, b) tuple to hex string like #3b82f6."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _rgba_str(rgb, alpha=1.0):
    """Convert (r, g, b) + alpha to CSS rgba() string."""
    return f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{alpha:.2f})"


# ── Data assembly ────────────────────────────────────────────────────────

def assemble_render_data(graph, sim_result, image_width, image_height):
    """Assemble all data needed for rendering.

    Takes the L3 graph dict and reader sim result dict.
    Returns a render_data dict with:
    - nodes: list of {id, name, x, y, radius, color, color_rgb, glow, opacity, border, narrative_badges}
    - links: list of {x1, y1, x2, y2, width, color, is_gold}
    - spaces: list of {x, y, w, h, is_dead, border_color, name}
    - scanpath: list of {x, y, time_ms, node_name}
    - entry_point: {x, y} or None
    - stats: {verdict, pressure, coverage, visited, total}
    - skipped_nodes: list of {x, y, name}
    """
    if not graph or not sim_result:
        return None
    if sim_result.get("error"):
        return None

    nodes_list = graph.get("nodes", [])
    links_list = graph.get("links", [])

    node_lookup = {n["id"]: n for n in nodes_list}

    # Get positions (normalized 0-1) — prefer bbox, fallback to estimation
    try:
        from reader_sim import _estimate_positions
        positions = _estimate_positions(graph)
    except ImportError:
        positions = {}
        for node in nodes_list:
            bbox = node.get("bbox")
            if bbox and isinstance(bbox, list) and len(bbox) == 4:
                try:
                    x, y, w, h = [float(v) for v in bbox]
                    positions[node["id"]] = (min(1, max(0, x + w / 2)),
                                              min(1, max(0, y + h / 2)))
                except (ValueError, TypeError):
                    pass

    # Separate node types
    things = [n for n in nodes_list if n.get("node_type") == "thing"]
    spaces = [n for n in nodes_list if n.get("node_type") == "space"]
    narratives = [n for n in nodes_list if n.get("node_type") == "narrative"]

    # Build adjacency for link rendering and narrative badges
    # Support both key formats: source/target (L3 standard) and node_a/node_b (YAML exports)
    adj = defaultdict(list)
    for link in links_list:
        src = link.get("source") or link.get("node_a", "")
        tgt = link.get("target") or link.get("node_b", "")
        w = link.get("weight", 0.5)
        adj[src].append((tgt, w, link))
        adj[tgt].append((src, w, link))

    # Extract heatmap from sim result
    heatmap = sim_result.get("heatmap", [])
    node_attention_map = {h["id"]: h["attention"] for h in heatmap}
    max_attention = max(node_attention_map.values()) if node_attention_map else 1.0
    if max_attention == 0:
        max_attention = 1.0

    # Anti-patterns from graph metadata
    anti_patterns_by_node = defaultdict(list)
    for ap in graph.get("metadata", {}).get("channel_analysis", {}).get("anti_patterns", []):
        nid = ap.get("node_id")
        if nid:
            anti_patterns_by_node[nid].append(ap.get("type", ""))

    # Narrative attention from sim
    narrative_attention = sim_result.get("narrative_attention", {})
    narrative_details = sim_result.get("narrative_details", [])
    narr_detail_map = {nd["id"]: nd for nd in narrative_details}

    # Dead spaces from sim
    dead_space_ids = {ds["id"] for ds in sim_result.get("dead_spaces", [])}

    # Visited node ids (from scanpath)
    scanpath_raw = sim_result.get("scanpath", [])
    visited_ids = {s["node_id"] for s in scanpath_raw}

    # Skipped nodes from sim
    skipped_raw = sim_result.get("skipped_nodes", [])

    # Build thing→space mapping (find parent space for each thing via adjacency)
    thing_space_map = {}
    for space in spaces:
        sid = space["id"]
        for neighbor_id, _w, _l in adj.get(sid, []):
            if neighbor_id.startswith("thing:"):
                thing_space_map[neighbor_id] = sid

    # ── Assemble THING nodes ──
    render_nodes = []
    for thing in things:
        tid = thing["id"]
        pos = positions.get(tid, (0.5, 0.5))
        px_x = pos[0] * image_width
        px_y = pos[1] * image_height

        weight = thing.get("weight", 0.5)
        energy = thing.get("energy", 0.0)
        stability = thing.get("stability", 0.5)

        attention = node_attention_map.get(tid, 0)
        att_ratio = attention / max_attention if max_attention > 0 else 0

        color_rgb = attention_to_color(att_ratio)
        res_depth = thing.get("resolution_depth", 0)
        radius = (8 + weight * 18) / (1 + res_depth)  # visible spheres
        glow = 8 + energy * 20
        opacity = (0.4 + stability * 0.6) * (0.8 ** res_depth)  # more transparent for deeper

        # Border: check anti-patterns
        anti_types = anti_patterns_by_node.get(tid, [])
        if "fragile" in anti_types:
            border = {"color": "#ef4444", "width": 2.5, "dasharray": "4 2", "type": "fragile"}
        elif "incongruent" in anti_types:
            border = {"color": "#ef4444", "width": 2.5, "dasharray": "", "type": "incongruent"}
        elif "inverse" in anti_types:
            border = {"color": "#ef4444", "width": 3, "dasharray": "", "type": "inverse"}
        elif tid not in visited_ids and weight >= 0.3:
            # Orphan-like: not visited, moderate weight
            border = {"color": "#64748b", "width": 1, "dasharray": "2 2", "type": "orphan"}
        else:
            # Clean border — slightly darker version of fill
            darker = tuple(max(0, c - 30) for c in color_rgb)
            border = {"color": _rgb_hex(darker), "width": 2, "dasharray": "", "type": "clean"}

        # Narrative badges: check linked narratives
        badges = []
        for neighbor_id, link_w, _link in adj.get(tid, []):
            if neighbor_id.startswith("narrative:"):
                narr_att = narrative_attention.get(neighbor_id, 0)
                detail_info = narr_detail_map.get(neighbor_id, {})
                status = detail_info.get("status", "missed")
                received = detail_info.get("received", 0)

                if status == "reached" and received >= 0.3:
                    badges.append({"color": "#fbbf24", "status": "reached"})  # gold
                elif status == "reached":
                    badges.append({"color": "#f59e0b", "status": "weak"})  # amber
                else:
                    badges.append({"color": "#ef4444", "status": "missed"})  # red

        # Limit to 3 visible badges
        badges = badges[:3]

        render_nodes.append({
            "id": tid,
            "name": thing.get("name", ""),
            "x": px_x,
            "y": px_y,
            "radius": radius,
            "color": _rgb_hex(color_rgb),
            "color_rgb": color_rgb,
            "glow": glow,
            "opacity": min(1.0, opacity),
            "border": border,
            "narrative_badges": badges,
            "weight": weight,
            "attention": attention,
            "att_ratio": att_ratio,
            "space_id": thing_space_map.get(tid, ""),
        })

    # ── Assemble LINKS ──
    render_links = []
    seen_links = set()
    for link in links_list:
        src = link.get("source") or link.get("node_a", "")
        tgt = link.get("target") or link.get("node_b", "")
        w = link.get("weight", 0.5)

        # Only show thing-thing links with weight >= 0.3
        if not (src.startswith("thing:") and tgt.startswith("thing:")):
            continue
        if w < 0.3:
            continue

        link_key = tuple(sorted([src, tgt]))
        if link_key in seen_links:
            continue
        seen_links.add(link_key)

        pos_src = positions.get(src, (0.5, 0.5))
        pos_tgt = positions.get(tgt, (0.5, 0.5))

        # Check if either end connects to a narrative (gold indicator)
        src_narrs = [n for n, _w, _l in adj.get(src, []) if n.startswith("narrative:")]
        tgt_narrs = [n for n, _w, _l in adj.get(tgt, []) if n.startswith("narrative:")]
        is_gold = bool(src_narrs and tgt_narrs)

        line_width = 2 + w * 3
        color = "#fbbf24" if is_gold else "#64748b"

        render_links.append({
            "source": src,
            "target": tgt,
            "x1": pos_src[0] * image_width,
            "y1": pos_src[1] * image_height,
            "x2": pos_tgt[0] * image_width,
            "y2": pos_tgt[1] * image_height,
            "width": line_width,
            "color": color,
            "is_gold": is_gold,
        })

    # ── Assemble SPACES ──
    render_spaces = []
    for space in spaces:
        sid = space["id"]
        bbox = space.get("bbox")
        if bbox and isinstance(bbox, list) and len(bbox) == 4:
            try:
                bx, by, bw, bh = [float(v) for v in bbox]
                px_x = bx * image_width
                px_y = by * image_height
                px_w = bw * image_width
                px_h = bh * image_height
            except (ValueError, TypeError):
                continue
        else:
            # Estimate space box from positions of children
            children = []
            for neighbor_id, _w, _l in adj.get(sid, []):
                if neighbor_id.startswith("thing:") and neighbor_id in positions:
                    children.append(positions[neighbor_id])
            if not children:
                pos = positions.get(sid, (0.5, 0.5))
                px_x = pos[0] * image_width - 60
                px_y = pos[1] * image_height - 40
                px_w = 120
                px_h = 80
            else:
                min_x = min(c[0] for c in children)
                max_x = max(c[0] for c in children)
                min_y = min(c[1] for c in children)
                max_y = max(c[1] for c in children)
                pad = 0.04  # 4% padding
                px_x = max(0, (min_x - pad)) * image_width
                px_y = max(0, (min_y - pad)) * image_height
                px_w = (max_x - min_x + 2 * pad) * image_width
                px_h = (max_y - min_y + 2 * pad) * image_height

        is_dead = sid in dead_space_ids
        border_color = "#ef4444" if is_dead else "#2dd4bf"

        render_spaces.append({
            "id": sid,
            "x": px_x,
            "y": px_y,
            "w": max(20, px_w),
            "h": max(20, px_h),
            "is_dead": is_dead,
            "border_color": border_color,
            "name": space.get("name", ""),
        })

    # ── Assemble SCANPATH ──
    # Deduplicate scanpath to unique node visits (first fixation tick per node)
    seen_scan = set()
    render_scanpath = []
    for sp in scanpath_raw:
        nid = sp.get("node_id", "")
        if nid in seen_scan:
            continue
        seen_scan.add(nid)
        render_scanpath.append({
            "x": sp.get("x", 0.5) * image_width,
            "y": sp.get("y", 0.5) * image_height,
            "time_ms": sp.get("time_ms", 0),
            "node_name": sp.get("node_name", ""),
        })

    # Entry point
    entry_point = None
    if render_scanpath:
        entry_point = {"x": render_scanpath[0]["x"], "y": render_scanpath[0]["y"]}

    # Skipped node positions
    render_skipped = []
    for sk in skipped_raw:
        sk_name = sk.get("name", "")
        # Find the thing node by name to get position
        for thing in things:
            if thing.get("name", "") == sk_name:
                pos = positions.get(thing["id"], (0.5, 0.5))
                render_skipped.append({
                    "x": pos[0] * image_width,
                    "y": pos[1] * image_height,
                    "name": sk_name,
                })
                break

    # Stats
    sim_stats = sim_result.get("stats", {})
    render_stats = {
        "verdict": sim_stats.get("complexity_verdict", ""),
        "pressure": sim_stats.get("budget_pressure", 0),
        "coverage": sim_stats.get("narrative_coverage", 0),
        "visited": sim_stats.get("unique_nodes_visited", 0),
        "total": sim_stats.get("total_things", 0),
    }

    return {
        "nodes": render_nodes,
        "links": render_links,
        "spaces": render_spaces,
        "scanpath": render_scanpath,
        "entry_point": entry_point,
        "stats": render_stats,
        "skipped_nodes": render_skipped,
    }


# ── SVG Renderer (Web) ──────────────────────────────────────────────────

def render_overlay_svg(graph, sim_result, width, height):
    """Generate inline SVG string for web overlay.

    Returns an SVG string that can be placed on top of the GA image.
    Three toggleable layers: attention (default ON), scanpath (OFF), problems (OFF).
    Returns None if no data to render.
    """
    data = assemble_render_data(graph, sim_result, width, height)
    if not data:
        return None

    parts = []

    # SVG root — pointer-events: none so clicks pass through
    parts.append(
        f'<svg viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'class="graph-overlay" '
        f'style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;">'
    )

    # Defs: glow filters for animation
    parts.append('  <defs>')
    parts.append('    <filter id="glow-teal" x="-50%" y="-50%" width="200%" height="200%">')
    parts.append('      <feGaussianBlur stdDeviation="6" result="blur"/>')
    parts.append('      <feFlood flood-color="#2dd4bf" flood-opacity="0.6" result="color"/>')
    parts.append('      <feComposite in="color" in2="blur" operator="in" result="glow"/>')
    parts.append('      <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>')
    parts.append('    </filter>')
    parts.append('    <filter id="glow-amber" x="-50%" y="-50%" width="200%" height="200%">')
    parts.append('      <feGaussianBlur stdDeviation="6" result="blur"/>')
    parts.append('      <feFlood flood-color="#f59e0b" flood-opacity="0.6" result="color"/>')
    parts.append('      <feComposite in="color" in2="blur" operator="in" result="glow"/>')
    parts.append('      <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>')
    parts.append('    </filter>')
    parts.append('    <filter id="glow-blue" x="-50%" y="-50%" width="200%" height="200%">')
    parts.append('      <feGaussianBlur stdDeviation="6" result="blur"/>')
    parts.append('      <feFlood flood-color="#3b82f6" flood-opacity="0.6" result="color"/>')
    parts.append('      <feComposite in="color" in2="blur" operator="in" result="glow"/>')
    parts.append('      <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>')
    parts.append('    </filter>')
    # Dark halo behind nodes for contrast on any background
    parts.append('    <filter id="dark-halo" x="-100%" y="-100%" width="300%" height="300%">')
    parts.append('      <feGaussianBlur in="SourceAlpha" stdDeviation="6" result="shadow"/>')
    parts.append('      <feFlood flood-color="#000000" flood-opacity="0.8" result="dark"/>')
    parts.append('      <feComposite in="dark" in2="shadow" operator="in" result="halo"/>')
    parts.append('      <feMerge><feMergeNode in="halo"/><feMergeNode in="SourceGraphic"/></feMerge>')
    parts.append('    </filter>')
    # Marble texture: turbulence + specular highlight
    parts.append('    <filter id="marble" x="-20%" y="-20%" width="140%" height="140%">')
    parts.append('      <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="4" seed="42" result="noise"/>')
    parts.append('      <feColorMatrix type="saturate" values="0" in="noise" result="mono"/>')
    parts.append('      <feBlend in="SourceGraphic" in2="mono" mode="soft-light" result="textured"/>')
    parts.append('      <feComposite in="textured" in2="SourceGraphic" operator="in"/>')
    parts.append('    </filter>')
    # 3D shine: radial gradient overlay
    parts.append('    <radialGradient id="shine" cx="35%" cy="25%" r="65%">')
    parts.append('      <stop offset="0%" stop-color="white" stop-opacity="0.35"/>')
    parts.append('      <stop offset="50%" stop-color="white" stop-opacity="0.05"/>')
    parts.append('      <stop offset="100%" stop-color="black" stop-opacity="0.15"/>')
    parts.append('    </radialGradient>')
    # Zone texture: subtle noise fill
    parts.append('    <filter id="zone-texture" x="0" y="0" width="100%" height="100%">')
    parts.append('      <feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="3" seed="7" result="znoise"/>')
    parts.append('      <feColorMatrix type="saturate" values="0" in="znoise" result="zmono"/>')
    parts.append('      <feBlend in="SourceGraphic" in2="zmono" mode="overlay" result="ztextured"/>')
    parts.append('      <feComposite in="ztextured" in2="SourceGraphic" operator="in"/>')
    parts.append('    </filter>')
    # Subtle gradient background for standalone SVG viewing
    parts.append('    <radialGradient id="bg-grad" cx="50%" cy="40%" r="70%">')
    parts.append('      <stop offset="0%" stop-color="#1e293b" stop-opacity="0.03"/>')
    parts.append('      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.08"/>')
    parts.append('    </radialGradient>')
    parts.append('  </defs>')

    # Layer 1: Subtle gradient background (barely visible on image, nice standalone)
    parts.append(f'  <rect width="{width}" height="{height}" fill="url(#bg-grad)" rx="8"/>')

    # ── Layer group: Attention (default ON) ──
    parts.append('  <g class="layer-attention">')

    # Space outlines
    for space in data["spaces"]:
        dash = ' stroke-dasharray="6 3"' if space["is_dead"] else ' stroke-dasharray="8 4"'
        fill_alpha = 0.04 if space["is_dead"] else 0.025
        fill_rgb = (239, 68, 68) if space["is_dead"] else (45, 212, 191)
        sw = 1 if space["is_dead"] else 0.5
        glow_color = "#ef4444" if space["is_dead"] else "#2dd4bf"
        # Textured zone field with glow
        parts.append(
            f'    <rect x="{space["x"]:.1f}" y="{space["y"]:.1f}" '
            f'width="{space["w"]:.1f}" height="{space["h"]:.1f}" rx="6" '
            f'stroke="{space["border_color"]}" stroke-width="{sw}" '
            f'fill="{_rgba_str(fill_rgb, fill_alpha)}"{dash} '
            f'data-space-id="{_svg_escape(space.get("id", ""))}" '
            f'filter="url(#zone-texture)" '
            f'style="filter:drop-shadow(0 0 4px {glow_color});"/>'
        )

    # Links
    for link in data["links"]:
        opacity = 0.8 if link["is_gold"] else 0.4
        parts.append(
            f'    <line x1="{link["x1"]:.1f}" y1="{link["y1"]:.1f}" '
            f'x2="{link["x2"]:.1f}" y2="{link["y2"]:.1f}" '
            f'stroke="{link["color"]}" stroke-width="{link["width"]:.1f}" '
            f'opacity="{opacity}" '
            f'data-source="{_svg_escape(link.get("source", ""))}" '
            f'data-target="{_svg_escape(link.get("target", ""))}" '
            f'data-is-gold="{1 if link["is_gold"] else 0}"/>'
        )

    # Thing spheres
    for node in data["nodes"]:
        # Glow via CSS filter
        glow_px = node["glow"]
        border = node["border"]
        dash_attr = f' stroke-dasharray="{border["dasharray"]}"' if border["dasharray"] else ""

        # Marble sphere: base circle + texture filter + shine overlay
        r = node["radius"]
        cx = node["x"]
        cy = node["y"]
        parts.append(f'    <g data-node-id="{_svg_escape(node["id"])}" '
            f'data-weight="{node["weight"]:.3f}" '
            f'data-attention-ratio="{node["att_ratio"]:.3f}" '
            f'data-energy="{node.get("glow", 0):.1f}" '
            f'data-color="{node["color"]}" '
            f'data-space-id="{_svg_escape(node.get("space_id", ""))}" '
            f'data-narratives="{_svg_escape("|".join(b["name"] + ":" + b["status"] for b in node.get("narrative_badges", [])))}">')
        # Base sphere with marble texture
        parts.append(
            f'      <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
            f'fill="{node["color"]}" opacity="{node["opacity"]:.2f}" '
            f'stroke="{border["color"]}" stroke-width="{border["width"]}"{dash_attr} '
            f'filter="url(#dark-halo)" '
            f'style="filter:url(#dark-halo);"/>'
        )
        # 3D shine highlight
        parts.append(
            f'      <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
            f'fill="url(#shine)" opacity="0.9" pointer-events="none"/>'
        )
        # Tooltip
        parts.append(
            f'      <title>{_svg_escape(node["name"])} (w={node["weight"]:.2f}, att={node["att_ratio"]*100:.0f}%)</title>'
        )
        parts.append('    </g>')

        # Narrative badges — small dots at bottom-right
        for bi, badge in enumerate(node["narrative_badges"]):
            bx = node["x"] + node["radius"] - 2
            by = node["y"] + node["radius"] - 2 - bi * 6
            mark = ""
            if badge["status"] == "missed":
                # Add tiny ! for missed
                mark = (
                    f'    <text x="{bx:.1f}" y="{by + 2:.1f}" '
                    f'font-size="6" fill="white" text-anchor="middle" '
                    f'font-weight="bold">!</text>'
                )
            parts.append(
                f'    <circle cx="{bx:.1f}" cy="{by:.1f}" r="4" '
                f'fill="{badge["color"]}" opacity="0.9"/>'
            )
            if mark:
                parts.append(mark)

        # No node labels — clean overlay, hover for details

    parts.append('  </g>')

    # ── Static scanpath trail (always visible, animation plays on top) ──
    if data["scanpath"]:
        points_str = " ".join(
            f'{sp["x"]:.1f},{sp["y"]:.1f}' for sp in data["scanpath"]
        )
        parts.append(
            f'  <polyline points="{points_str}" '
            f'stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="4 3" '
            f'fill="none" opacity="0.35" class="static-trail"/>'
        )
        # Entry point dot
        if data["entry_point"]:
            ep = data["entry_point"]
            parts.append(
                f'  <circle cx="{ep["x"]:.1f}" cy="{ep["y"]:.1f}" r="5" '
                f'fill="none" stroke="#10b981" stroke-width="1.5" opacity="0.5"/>'
            )

    # ── Layer group: Problems (default OFF) ──
    parts.append('  <g class="layer-problems" style="display:none;">')

    # Dead space washes
    for space in data["spaces"]:
        if space["is_dead"]:
            parts.append(
                f'    <rect x="{space["x"]:.1f}" y="{space["y"]:.1f}" '
                f'width="{space["w"]:.1f}" height="{space["h"]:.1f}" '
                f'fill="rgba(239,68,68,0.08)" rx="8"/>'
            )

    # Skipped node markers
    for sk in data["skipped_nodes"]:
        parts.append(
            f'    <text x="{sk["x"]:.1f}" y="{sk["y"]:.1f}" '
            f'font-size="14" fill="#ef4444" text-anchor="middle" '
            f'dominant-baseline="central" font-weight="bold">'
            f'&#x2717;</text>'
        )

    # Anti-pattern nodes get highlighted
    for node in data["nodes"]:
        if node["border"]["type"] in ("fragile", "incongruent", "inverse"):
            parts.append(
                f'    <circle cx="{node["x"]:.1f}" cy="{node["y"]:.1f}" '
                f'r="{node["radius"] + 6:.1f}" '
                f'fill="none" stroke="#ef4444" stroke-width="1" '
                f'stroke-dasharray="3 2" opacity="0.6"/>'
            )

    parts.append('  </g>')

    # Empty group for animation particle effects (JS will inject here)
    parts.append('  <g class="layer-particles"></g>')

    # Eye dot for scanpath animation (hidden initially)
    parts.append('  <circle class="eye-dot" cx="0" cy="0" r="6" fill="white" opacity="0" style="display:none;"/>')

    # Scanpath trail polyline for animation (empty initially)
    parts.append('  <polyline class="anim-trail" points="" fill="none" stroke="#f59e0b" stroke-width="2" stroke-dasharray="6 4" opacity="0.6"/>')

    parts.append('</svg>')

    return "\n".join(parts)


# ── PNG Renderer (Export) ────────────────────────────────────────────────

def render_overlay_png(graph, sim_result, image_path, output_path=None):
    """Generate composite PNG: GA image + overlay.

    Uses Pillow to:
    1. Open original GA image
    2. Create RGBA overlay
    3. Draw dim layer, spaces, links, nodes, badges
    4. Alpha composite onto GA
    5. Save PNG

    Returns path to output PNG, or None on failure.
    """
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont
    except ImportError:
        logger.warning("Pillow not available, skipping PNG render")
        return None

    if not os.path.exists(image_path):
        logger.warning(f"GA image not found: {image_path}")
        return None

    # Open GA image
    ga_img = Image.open(image_path).convert("RGBA")
    img_w, img_h = ga_img.size

    data = assemble_render_data(graph, sim_result, img_w, img_h)
    if not data:
        return None

    # Create overlay
    overlay = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Dim layer
    dim = Image.new("RGBA", (img_w, img_h), (10, 14, 26, 89))  # ~0.35 alpha
    overlay = Image.alpha_composite(overlay, dim)
    draw = ImageDraw.Draw(overlay)

    # 2. Space outlines
    for space in data["spaces"]:
        sx, sy = int(space["x"]), int(space["y"])
        sw, sh = int(space["w"]), int(space["h"])
        r, g, b = _hex_to_rgb(space["border_color"])
        fill_alpha = 15 if space["is_dead"] else 10  # ~0.06 or ~0.04
        draw.rounded_rectangle(
            [sx, sy, sx + sw, sy + sh],
            radius=8,
            outline=(r, g, b, 200),
            width=2 if space["is_dead"] else 1,
        )
        # Fill with very low alpha
        fill_overlay = Image.new("RGBA", (sw, sh), (r, g, b, fill_alpha))
        overlay.paste(fill_overlay, (sx, sy), fill_overlay)

    # Recreate draw after paste operations
    draw = ImageDraw.Draw(overlay)

    # 3. Links
    for link in data["links"]:
        r, g, b = _hex_to_rgb(link["color"])
        alpha = 200 if link["is_gold"] else 100
        lw = max(1, int(link["width"]))
        draw.line(
            [(int(link["x1"]), int(link["y1"])),
             (int(link["x2"]), int(link["y2"]))],
            fill=(r, g, b, alpha),
            width=lw,
        )

    # 4. Node glow (pre-pass with larger radius, lower opacity)
    for node in data["nodes"]:
        cx, cy = int(node["x"]), int(node["y"])
        glow_r = int(node["radius"] + node["glow"])
        r, g, b = node["color_rgb"]
        glow_alpha = int(50 + node.get("glow", 4) * 3)
        glow_alpha = min(120, glow_alpha)
        draw.ellipse(
            [cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r],
            fill=(r, g, b, glow_alpha),
        )

    # 5. Node spheres
    for node in data["nodes"]:
        cx, cy = int(node["x"]), int(node["y"])
        nr = int(node["radius"])
        r, g, b = node["color_rgb"]
        alpha = int(node["opacity"] * 255)

        # Fill
        draw.ellipse(
            [cx - nr, cy - nr, cx + nr, cy + nr],
            fill=(r, g, b, alpha),
        )

        # Border
        br, bg, bb = _hex_to_rgb(node["border"]["color"])
        bw = max(1, int(node["border"]["width"]))
        draw.ellipse(
            [cx - nr, cy - nr, cx + nr, cy + nr],
            outline=(br, bg, bb, 220),
            width=bw,
        )

    # 6. Narrative badges
    for node in data["nodes"]:
        cx, cy = int(node["x"]), int(node["y"])
        nr = int(node["radius"])
        for bi, badge in enumerate(node["narrative_badges"]):
            bx = cx + nr - 2
            by = cy + nr - 2 - bi * 6
            br, bg, bb = _hex_to_rgb(badge["color"])
            draw.ellipse(
                [bx - 4, by - 4, bx + 4, by + 4],
                fill=(br, bg, bb, 230),
            )

    # Composite
    result = Image.alpha_composite(ga_img, overlay)

    # Determine output path
    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = base + "_overlay.png"

    result.save(output_path, "PNG")
    logger.info(f"Overlay PNG saved: {output_path}")
    return output_path


# ── Helpers ──────────────────────────────────────────────────────────────

def _svg_escape(text):
    """Escape text for safe SVG/XML inclusion."""
    if not text:
        return ""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def _truncate(text, max_len=25):
    """Truncate text with ellipsis."""
    if not text or len(text) <= max_len:
        return text or ""
    return text[:max_len - 1] + "\u2026"


def _hex_to_rgb(hex_str):
    """Convert hex color string to (r, g, b) tuple."""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) != 6:
        return (128, 128, 128)
    return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))


# ── CLI test ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import yaml
    import sys

    if len(sys.argv) < 2:
        print("Usage: python graph_renderer.py <graph.yaml> [--png <image.png>]")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        graph = yaml.safe_load(f)

    from reader_sim import simulate_reading
    sim = simulate_reading(graph, total_ticks=50, mode="system1")

    svg = render_overlay_svg(graph, sim, 900, 600)
    if svg:
        print(f"SVG generated: {len(svg)} chars")
        print(svg[:500])
    else:
        print("No SVG generated (empty data)")

    if "--png" in sys.argv:
        idx = sys.argv.index("--png")
        if idx + 1 < len(sys.argv):
            png_path = render_overlay_png(graph, sim, sys.argv[idx + 1])
            print(f"PNG saved: {png_path}")
