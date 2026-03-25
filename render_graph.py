"""Render L3 YAML graphs as PNG images.

Usage:
    python render_graph.py data/glance_ga_graph.yaml
    python render_graph.py data/visual_channel_graph.yaml
    python render_graph.py data/glance_ga_graph.yaml --output exports/ga_graph.png
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import networkx as nx
import numpy as np
import yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BG_COLOR = "#0f172a"
TEXT_COLOR = "#e2e8f0"
MUTED_TEXT = "#94a3b8"
GRID_COLOR = "#1e293b"

NODE_TYPE_COLORS = {
    "actor":     "#d97706",  # amber
    "moment":    "#8b5cf6",  # purple
    "narrative": "#3b82f6",  # blue
    "space":     "#059669",  # green
    "thing":     "#ef4444",  # red
}

DEFAULT_NODE_COLOR = "#64748b"  # slate fallback

LINK_POSITIVE_COLOR = "#22c55e"   # green
LINK_NEGATIVE_COLOR = "#ef4444"   # red
LINK_NEUTRAL_COLOR  = "#475569"   # gray

FIG_W, FIG_H = 16, 9  # inches (1600x900 at 100 dpi)
DPI = 100
LAYOUT_SEED = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_float(node_or_link: dict, key: str, default: float = 0.5) -> float:
    """Extract a float dimension, returning *default* when missing/None."""
    val = node_or_link.get(key)
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def load_graph(path: Path) -> dict:
    """Load a YAML graph file and return the raw dict."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def is_containment_link(link: dict) -> bool:
    """Return True if this link is a space-containment link (hierarchy == -1)."""
    h = safe_float(link, "hierarchy", default=0.0)
    return h <= -0.9  # treat hierarchy <= -0.9 as containment


def link_valence_color(link: dict) -> str:
    """Derive link color from valence, affinity, and aversion."""
    valence = safe_float(link, "valence", default=None)
    affinity = safe_float(link, "affinity", default=0.0)
    aversion = safe_float(link, "aversion", default=0.0)

    if valence is not None and valence != 0.5:
        # valence was explicitly provided
        pass
    else:
        # derive from affinity/aversion
        valence = affinity - aversion

    if valence > 0.15:
        return LINK_POSITIVE_COLOR
    elif valence < -0.15:
        return LINK_NEGATIVE_COLOR
    return LINK_NEUTRAL_COLOR


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def compute_layout(G: nx.DiGraph, nodes_by_id: dict, containment: dict) -> dict:
    """Compute node positions respecting space containment.

    Strategy:
    - Identify space nodes and their contained children via containment links.
    - Run spring_layout on the full graph for an initial placement.
    - Then shift contained nodes so they cluster inside their space zone.
    - Space nodes named *left* go to x < 0, *right* to x > 0.
    """
    # Initial spring layout
    pos = nx.spring_layout(G, seed=LAYOUT_SEED, k=2.5, iterations=80)

    if not containment:
        return pos

    # Determine zone targets  (left → negative x, right → positive x)
    zone_targets = {}
    for space_id in containment:
        node = nodes_by_id.get(space_id, {})
        name_lower = node.get("name", "").lower()
        nid_lower = space_id.lower()
        if "left" in nid_lower or "left" in name_lower or "problème" in name_lower or "probleme" in name_lower:
            zone_targets[space_id] = np.array([-0.55, 0.0])
        elif "right" in nid_lower or "right" in name_lower or "solution" in name_lower:
            zone_targets[space_id] = np.array([0.55, 0.0])
        else:
            zone_targets[space_id] = np.array([0.0, 0.0])

    # Move contained nodes toward their space center
    for space_id, children in containment.items():
        target = zone_targets.get(space_id, np.array([0.0, 0.0]))
        if space_id in pos:
            pos[space_id] = target

        if not children:
            continue

        # Compute centroid of children in initial layout
        child_positions = np.array([pos[c] for c in children if c in pos])
        if len(child_positions) == 0:
            continue
        centroid = child_positions.mean(axis=0)
        shift = target - centroid

        for child_id in children:
            if child_id in pos:
                pos[child_id] = pos[child_id] + shift

    # Standalone nodes (not in any space, not a space) stay roughly centered
    all_contained = set()
    for children in containment.values():
        all_contained.update(children)
    all_contained.update(containment.keys())

    for nid in G.nodes:
        if nid not in all_contained:
            # nudge slightly toward origin if far away
            current = pos.get(nid, np.array([0.0, 0.0]))
            pos[nid] = current * 0.6

    return pos


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def draw_space_backgrounds(ax, pos: dict, containment: dict, nodes_by_id: dict):
    """Draw rounded-rectangle backgrounds for space nodes encompassing their children."""
    for space_id, children in containment.items():
        if not children:
            continue
        child_positions = [pos[c] for c in children if c in pos]
        if not child_positions:
            continue

        xs = [p[0] for p in child_positions]
        ys = [p[1] for p in child_positions]

        pad = 0.18
        x_min, x_max = min(xs) - pad, max(xs) + pad
        y_min, y_max = min(ys) - pad, max(ys) + pad

        node = nodes_by_id.get(space_id, {})
        ntype = node.get("node_type", "space")
        color = NODE_TYPE_COLORS.get(ntype, DEFAULT_NODE_COLOR)

        rect = FancyBboxPatch(
            (x_min, y_min),
            x_max - x_min,
            y_max - y_min,
            boxstyle="round,pad=0.05",
            facecolor=color,
            alpha=0.08,
            edgecolor=color,
            linewidth=1.5,
            linestyle="--",
            zorder=0,
        )
        ax.add_patch(rect)

        # Space label at top
        label = node.get("name", space_id.split(":")[-1])
        ax.text(
            (x_min + x_max) / 2,
            y_max + 0.04,
            label,
            fontsize=9,
            fontweight="bold",
            color=color,
            ha="center",
            va="bottom",
            alpha=0.7,
            zorder=1,
        )


def render(yaml_path: Path, output_path: Path):
    """Main render pipeline."""
    data = load_graph(yaml_path)
    nodes_list = data.get("nodes", [])
    links_list = data.get("links", [])

    # Build lookup
    nodes_by_id = {n["id"]: n for n in nodes_list}

    # Build networkx graph
    G = nx.DiGraph()
    for n in nodes_list:
        G.add_node(n["id"])

    # Separate containment links from semantic links
    containment: dict[str, list[str]] = {}  # space_id → [child_ids]
    semantic_links: list[dict] = []

    for link in links_list:
        src = link.get("node_a")
        dst = link.get("node_b")
        if src is None or dst is None:
            continue
        if is_containment_link(link):
            containment.setdefault(src, []).append(dst)
        else:
            semantic_links.append(link)
            G.add_edge(src, dst, **link)

    # Also add containment edges (lighter) so layout sees them
    for space_id, children in containment.items():
        for child_id in children:
            G.add_edge(space_id, child_id, _containment=True)

    # Layout
    pos = compute_layout(G, nodes_by_id, containment)

    # --- Figure ---
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_aspect("equal")
    ax.axis("off")

    # Space backgrounds
    draw_space_backgrounds(ax, pos, containment, nodes_by_id)

    # --- Draw semantic links ---
    for link in semantic_links:
        src = link.get("node_a")
        dst = link.get("node_b")
        if src not in pos or dst not in pos:
            continue

        w = safe_float(link, "weight", 0.5)
        h = safe_float(link, "hierarchy", 0.0)
        color = link_valence_color(link)
        style = "--" if h < -0.5 else "-"
        linewidth = 0.5 + w * 3.0

        x_coords = [pos[src][0], pos[dst][0]]
        y_coords = [pos[src][1], pos[dst][1]]
        ax.plot(
            x_coords, y_coords,
            linestyle=style,
            linewidth=linewidth,
            color=color,
            alpha=0.5 + w * 0.3,
            zorder=2,
            solid_capstyle="round",
        )

    # --- Draw containment links (very subtle) ---
    for space_id, children in containment.items():
        for child_id in children:
            if space_id not in pos or child_id not in pos:
                continue
            x_coords = [pos[space_id][0], pos[child_id][0]]
            y_coords = [pos[space_id][1], pos[child_id][1]]
            ax.plot(
                x_coords, y_coords,
                linestyle=":",
                linewidth=0.6,
                color=GRID_COLOR,
                alpha=0.3,
                zorder=1,
            )

    # --- Draw nodes ---
    space_ids = set(containment.keys())

    for nid, node in nodes_by_id.items():
        if nid in space_ids:
            continue  # space nodes drawn as backgrounds, skip scatter

        if nid not in pos:
            continue

        x, y = pos[nid]
        ntype = node.get("node_type", "thing")
        color = NODE_TYPE_COLORS.get(ntype, DEFAULT_NODE_COLOR)

        weight    = safe_float(node, "weight", 0.5)
        stability = safe_float(node, "stability", 0.5)
        energy    = safe_float(node, "energy", 0.3)

        # Node size from weight
        size = 200 + weight * 800

        # Glow / halo from energy (draw first, behind the node)
        if energy > 0.2:
            glow_size = size * (1.5 + energy)
            ax.scatter(
                [x], [y],
                s=glow_size,
                c=color,
                alpha=energy * 0.25,
                edgecolors="none",
                zorder=3,
            )

        # Node border thickness from stability
        border_width = 0.5 + stability * 2.5

        # Main node
        ax.scatter(
            [x], [y],
            s=size,
            c=color,
            alpha=0.85,
            edgecolors="white",
            linewidths=border_width,
            zorder=5,
        )

        # Label: name
        name = node.get("name", nid.split(":")[-1])
        ax.text(
            x, y + 0.06,
            name,
            fontsize=8,
            fontweight="bold",
            color=TEXT_COLOR,
            ha="center",
            va="bottom",
            zorder=6,
        )

        # Sub-label: w/s/e dimensions
        dims = f"w={weight:.2f}  s={stability:.2f}  e={energy:.2f}"
        ax.text(
            x, y - 0.05,
            dims,
            fontsize=5.5,
            color=MUTED_TEXT,
            ha="center",
            va="top",
            zorder=6,
        )

    # --- Legend ---
    legend_handles = []
    for ntype, color in NODE_TYPE_COLORS.items():
        legend_handles.append(
            mpatches.Patch(facecolor=color, edgecolor="white", linewidth=0.5, label=ntype)
        )
    # Link valence legend entries
    legend_handles.append(plt.Line2D([0], [0], color=LINK_POSITIVE_COLOR, lw=2, label="link: positive"))
    legend_handles.append(plt.Line2D([0], [0], color=LINK_NEGATIVE_COLOR, lw=2, label="link: negative"))
    legend_handles.append(plt.Line2D([0], [0], color=LINK_NEUTRAL_COLOR, lw=2, label="link: neutral"))
    # Dimension hints
    legend_handles.append(plt.Line2D([0], [0], color="none", label="size = weight"))
    legend_handles.append(plt.Line2D([0], [0], color="none", label="border = stability"))
    legend_handles.append(plt.Line2D([0], [0], color="none", label="glow = energy"))

    leg = ax.legend(
        handles=legend_handles,
        loc="lower right",
        fontsize=7,
        frameon=True,
        facecolor=BG_COLOR,
        edgecolor=MUTED_TEXT,
        labelcolor=TEXT_COLOR,
        ncol=2,
    )
    leg.set_zorder(10)

    # --- Title ---
    title = yaml_path.stem.replace("_", " ").title()
    ax.set_title(
        title,
        fontsize=14,
        fontweight="bold",
        color=TEXT_COLOR,
        pad=15,
    )

    # --- Save ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        str(output_path),
        dpi=DPI,
        facecolor=BG_COLOR,
        edgecolor="none",
        bbox_inches="tight",
        pad_inches=0.3,
    )
    plt.close(fig)
    print(f"Rendered: {output_path}  ({output_path.stat().st_size / 1024:.0f} KB)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Render L3 YAML graphs as PNG images.")
    parser.add_argument("yaml_file", type=Path, help="Path to the YAML graph file")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output PNG path (default: exports/<stem>.png)")
    args = parser.parse_args()

    yaml_path = args.yaml_file
    if not yaml_path.is_absolute():
        yaml_path = Path.cwd() / yaml_path
    if not yaml_path.exists():
        print(f"Error: {yaml_path} not found", file=sys.stderr)
        sys.exit(1)

    if args.output:
        output_path = args.output
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
    else:
        output_path = Path.cwd() / "exports" / f"{yaml_path.stem}.png"

    render(yaml_path, output_path)


if __name__ == "__main__":
    main()
