"""
Reader Simulation — Physics-based visual attention model.

Simulates how a reader's eye moves through a GA in 5 seconds.
The reader is an ACTOR with finite attention that moves between
nodes, attracted by visual weight, constrained by spatial layout.

Physics:
  - Attention is finite (5s = 50 ticks at 100ms/tick)
  - The actor starts top-left (Western Z-pattern entry point)
  - At each tick, the actor is attracted to nearby high-weight nodes
  - Attraction force = node.weight / distance²
  - The actor moves to the most attractive unvisited node
  - At each visited node, attention flows to linked narratives
  - Friction on each link absorbs some attention
  - Revisits are possible but with diminishing returns (decay 0.5x)

Output:
  - Scanpath: ordered list of visited nodes with timestamps
  - Narrative coverage: how much attention each narrative received
  - Attention heatmap: time spent per node
  - Dead zones: spaces never visited

Usage:
    python reader_sim.py <graph.yaml> [--ticks 50] [--verbose]
"""

import yaml
import math
import os
import sys
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("reader_sim")


# ── Layout estimation ────────────────────────────────────────────────

def _estimate_positions(graph):
    """Estimate 2D positions for nodes based on graph structure.

    Since we don't have actual pixel coordinates, we infer positions from:
    1. Node order in the YAML (Gemini lists top→bottom, left→right)
    2. Space containment (things inside spaces cluster together)
    3. Node type (spaces = large regions, things = points within)

    Returns: dict of node_id → (x, y) normalized to [0, 1]
    """
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])

    # Build containment: which things are in which spaces
    space_children = defaultdict(list)
    for link in links:
        src = link.get("source", "")
        tgt = link.get("target", "")
        # thing → space = containment
        if src.startswith("thing:") and tgt.startswith("space:"):
            space_children[tgt].append(src)
        elif src.startswith("space:") and tgt.startswith("thing:"):
            space_children[src].append(tgt)
        # narrative → space
        if src.startswith("narrative:") and tgt.startswith("space:"):
            space_children[tgt].append(src)
        elif src.startswith("space:") and tgt.startswith("narrative:"):
            space_children[src].append(tgt)

    positions = {}
    spaces = [n for n in nodes if n.get("node_type") == "space"]
    non_spaces = [n for n in nodes if n.get("node_type") != "space"]

    # Layout spaces in a grid (Z-pattern)
    n_spaces = max(len(spaces), 1)
    cols = min(n_spaces, 3)  # max 3 columns
    rows = math.ceil(n_spaces / cols)

    for i, space in enumerate(spaces):
        col = i % cols
        row = i // cols
        # Center of each space cell
        cx = (col + 0.5) / cols
        cy = (row + 0.5) / rows
        positions[space["id"]] = (cx, cy)

        # Position children within the space cell
        children = space_children.get(space["id"], [])
        for j, child_id in enumerate(children):
            # Distribute children in a small cluster around space center
            angle = 2 * math.pi * j / max(len(children), 1)
            spread = 0.3 / cols  # cluster radius
            child_x = cx + spread * math.cos(angle)
            child_y = cy + spread * math.sin(angle)
            positions[child_id] = (
                max(0, min(1, child_x)),
                max(0, min(1, child_y)),
            )

    # Position orphan nodes (not in any space) along the bottom
    orphans = [n for n in non_spaces if n["id"] not in positions]
    for i, node in enumerate(orphans):
        positions[node["id"]] = (
            (i + 0.5) / max(len(orphans), 1),
            0.9,
        )

    return positions


# ── Core simulation ──────────────────────────────────────────────────

def simulate_reading(graph, total_ticks=50, tick_ms=100, verbose=False):
    """Simulate a reader scanning a GA.

    Args:
        graph: L3 graph dict (nodes, links, metadata)
        total_ticks: number of simulation steps (50 = 5 seconds at 100ms/tick)
        tick_ms: milliseconds per tick
        verbose: log each tick

    Returns:
        dict with scanpath, narrative_attention, node_heatmap, dead_zones, stats
    """
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])

    node_lookup = {n["id"]: n for n in nodes}
    positions = _estimate_positions(graph)

    # Build adjacency
    adj = defaultdict(list)
    for link in links:
        src = link.get("source", "")
        tgt = link.get("target", "")
        w = link.get("weight", 0.5)
        adj[src].append((tgt, w))
        adj[tgt].append((src, w))

    # Separate node types
    things = [n for n in nodes if n.get("node_type") == "thing"]
    spaces = [n for n in nodes if n.get("node_type") == "space"]
    narratives = [n for n in nodes if n.get("node_type") == "narrative"]

    if not things:
        return {"error": "No thing nodes to visit"}

    # Actor state
    actor_pos = (0.05, 0.05)  # start top-left (Z-pattern entry)
    actor_attention = 1.0      # full attention at start
    visit_count = defaultdict(int)  # how many times each node was visited
    node_attention = defaultdict(float)  # total attention spent per node
    narrative_attention = defaultdict(float)  # attention received per narrative
    scanpath = []  # [(tick, node_id, x, y, attention)]

    # Saccade targets = only things (you look at elements, not messages)
    targets = {t["id"]: t for t in things}

    for tick in range(total_ticks):
        # ── Compute attraction to each unvisited/low-visit thing ──
        best_target = None
        best_attraction = -1

        for tid, thing in targets.items():
            pos = positions.get(tid, (0.5, 0.5))
            dx = pos[0] - actor_pos[0]
            dy = pos[1] - actor_pos[1]
            dist = math.sqrt(dx * dx + dy * dy) + 0.01  # avoid div by zero

            weight = thing.get("weight", 0.5)
            energy = thing.get("energy", 0.5)

            # Z-pattern bias: prefer nodes to the right and below current position
            # Western reading: left→right then top→bottom
            z_bias = 1.0
            if dx > 0:  # to the right = natural reading direction
                z_bias += 0.3
            if dy > 0 and abs(dx) < 0.2:  # below and roughly same column = line break
                z_bias += 0.2

            # Attraction = (weight + energy) * z_bias / distance²
            # High weight = important, high energy = attention-grabbing
            revisit_penalty = 0.5 ** visit_count[tid]
            attraction = (weight + energy * 0.5) * z_bias * revisit_penalty / (dist * dist)

            if attraction > best_attraction:
                best_attraction = attraction
                best_target = tid

        if best_target is None:
            break

        # ── Move actor to target ──
        target_pos = positions.get(best_target, (0.5, 0.5))
        dist = math.sqrt(
            (target_pos[0] - actor_pos[0]) ** 2 +
            (target_pos[1] - actor_pos[1]) ** 2
        ) + 0.01

        # Saccade cost: attention decays proportional to distance
        saccade_cost = dist * 0.15  # 15% attention per unit distance
        actor_attention = max(0, actor_attention - saccade_cost)

        actor_pos = target_pos
        visit_count[best_target] += 1

        # ── Fixation: spend attention at this node ──
        thing = targets[best_target]
        fixation_strength = actor_attention * thing.get("weight", 0.5)
        node_attention[best_target] += fixation_strength

        # ── Propagate attention to linked narratives ──
        for neighbor, link_w in adj.get(best_target, []):
            if neighbor.startswith("narrative:"):
                transmitted = fixation_strength * link_w
                narrative_attention[neighbor] += transmitted

        # ── Log ──
        scanpath.append({
            "tick": tick,
            "time_ms": tick * tick_ms,
            "node_id": best_target,
            "node_name": thing.get("name", ""),
            "x": round(target_pos[0], 3),
            "y": round(target_pos[1], 3),
            "attention": round(actor_attention, 4),
            "fixation": round(fixation_strength, 4),
        })

        if verbose:
            logger.info(
                f"  t={tick*tick_ms:4d}ms | {thing.get('name','')[:30]:30s} | "
                f"att={actor_attention:.3f} fix={fixation_strength:.3f}")

        # ── Natural attention decay (fatigue) ──
        actor_attention *= 0.97  # 3% decay per tick

        if actor_attention < 0.01:
            if verbose:
                logger.info(f"  Attention exhausted at tick {tick}")
            break

    # ── Results ──

    # Normalize narrative attention
    max_narr = max(narrative_attention.values()) if narrative_attention else 1
    normalized_narrative = {
        nid: round(v / max(max_narr, 0.01), 3)
        for nid, v in narrative_attention.items()
    }

    # Dead zones: spaces that were never visited (no thing inside them got attention)
    visited_spaces = set()
    for link in links:
        src, tgt = link.get("source", ""), link.get("target", "")
        if src in node_attention and tgt.startswith("space:"):
            visited_spaces.add(tgt)
        if tgt in node_attention and src.startswith("space:"):
            visited_spaces.add(src)

    dead_spaces = [
        {"id": s["id"], "name": s["name"]}
        for s in spaces if s["id"] not in visited_spaces
    ]

    # Orphan narratives: messages that received zero attention
    orphan_narratives = [
        {"id": n["id"], "name": n["name"]}
        for n in narratives if n["id"] not in narrative_attention
    ]

    # Heatmap: top nodes by attention
    heatmap = sorted(
        [{"id": nid, "name": node_lookup.get(nid, {}).get("name", ""),
          "attention": round(att, 4), "visits": visit_count[nid]}
         for nid, att in node_attention.items()],
        key=lambda x: -x["attention"]
    )

    # Overall transmission score
    if narratives:
        coverage = sum(1 for n in narratives if n["id"] in narrative_attention) / len(narratives)
        avg_attention = sum(normalized_narrative.values()) / len(narratives) if narratives else 0
    else:
        coverage = 0
        avg_attention = 0

    return {
        "scanpath": scanpath,
        "narrative_attention": normalized_narrative,
        "narrative_details": [
            {
                "id": n["id"],
                "name": n["name"],
                "received": normalized_narrative.get(n["id"], 0),
                "status": "reached" if n["id"] in narrative_attention else "missed",
            }
            for n in narratives
        ],
        "heatmap": heatmap,
        "dead_spaces": dead_spaces,
        "orphan_narratives": orphan_narratives,
        "stats": {
            "total_ticks": len(scanpath),
            "total_time_ms": len(scanpath) * tick_ms,
            "unique_nodes_visited": len(set(s["node_id"] for s in scanpath)),
            "total_nodes": len(things),
            "narrative_coverage": round(coverage, 3),
            "avg_narrative_attention": round(avg_attention, 3),
            "attention_remaining": round(actor_attention, 4),
            "dead_space_count": len(dead_spaces),
            "orphan_narrative_count": len(orphan_narratives),
        },
        "prompts": _generate_prompts(
            dead_spaces, orphan_narratives, heatmap, normalized_narrative, narratives
        ),
    }


def _generate_prompts(dead_spaces, orphan_narratives, heatmap, narrative_attention, narratives):
    """Generate FACT → PROBLEM → QUESTION prompts from simulation results."""
    prompts = []

    # Dead spaces
    for ds in dead_spaces:
        prompts.append(
            f"La zone '{ds['name']}' n'a reçu aucune visite du regard simulé. "
            f"Son contenu est invisible dans un scan de 5 secondes. "
            f"Qu'est-ce qui attirerait le regard vers cette zone ?")

    # Orphan narratives
    for on in orphan_narratives:
        prompts.append(
            f"Le message '{on['name']}' n'a reçu aucune attention. "
            f"Aucun élément visuel ne transmet ce message au lecteur. "
            f"Quel élément concret porterait ce message ?")

    # Narratives with low attention
    for n in narratives:
        att = narrative_attention.get(n["id"], 0)
        if 0 < att < 0.3:
            prompts.append(
                f"Le message '{n['name']}' ne reçoit que {att:.0%} de l'attention. "
                f"Les éléments qui le portent sont soit trop petits, soit mal positionnés. "
                f"Comment renforcer la transmission vers ce message ?")

    # Attention concentration (top node gets >50% of total)
    if heatmap and len(heatmap) > 1:
        total_att = sum(h["attention"] for h in heatmap)
        if total_att > 0:
            top_pct = heatmap[0]["attention"] / total_att
            if top_pct > 0.5:
                prompts.append(
                    f"'{heatmap[0]['name']}' absorbe {top_pct:.0%} de l'attention totale. "
                    f"Les autres éléments sont écrasés. "
                    f"Comment redistribuer le poids visuel sans perdre ce point focal ?")

    return prompts


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Reader Simulation — visual attention physics")
    parser.add_argument("graph", help="Path to L3 graph YAML")
    parser.add_argument("--ticks", type=int, default=50, help="Simulation ticks (default 50 = 5s)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Log each tick")
    parser.add_argument("--output", "-o", help="Save results YAML")
    args = parser.parse_args()

    with open(args.graph) as f:
        graph = yaml.safe_load(f)

    result = simulate_reading(graph, total_ticks=args.ticks, verbose=args.verbose)

    # Print summary
    stats = result["stats"]
    print(f"\n{'='*50}")
    print(f"READER SIMULATION — {stats['total_time_ms']}ms")
    print(f"{'='*50}")
    print(f"Nodes visited: {stats['unique_nodes_visited']}/{stats['total_nodes']}")
    print(f"Narrative coverage: {stats['narrative_coverage']:.0%}")
    print(f"Avg narrative attention: {stats['avg_narrative_attention']:.0%}")
    print(f"Attention remaining: {stats['attention_remaining']:.0%}")
    print(f"Dead spaces: {stats['dead_space_count']}")
    print(f"Orphan narratives: {stats['orphan_narrative_count']}")

    print(f"\nScanpath ({len(result['scanpath'])} fixations):")
    for s in result["scanpath"][:15]:
        print(f"  {s['time_ms']:4d}ms | {s['node_name'][:35]:35s} | att={s['attention']:.2f}")
    if len(result["scanpath"]) > 15:
        print(f"  ... +{len(result['scanpath'])-15} more")

    print(f"\nNarrative attention:")
    for n in result["narrative_details"]:
        status = "✓" if n["status"] == "reached" else "✗"
        print(f"  {status} {n['received']:.0%} | {n['name'][:50]}")

    print(f"\nHeatmap (top 5):")
    for h in result["heatmap"][:5]:
        print(f"  {h['attention']:.3f} ({h['visits']}x) | {h['name'][:40]}")

    if result["prompts"]:
        print(f"\nPrompts:")
        for p in result["prompts"]:
            print(f"  → {p[:100]}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            yaml.dump(result, f, default_flow_style=False, allow_unicode=True)
        print(f"\nSaved: {args.output}")
