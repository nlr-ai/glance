"""
Graph Health — Route verification for space→thing→narrative transmission chains.

Checks that every narrative (desired effect) is reachable from spaces
(visual zones) through concrete things (visual elements).

Uses ENERGY PROPAGATION (mini tick engine) instead of naive min-weight:
  Energy flows from things toward narratives through links.
  Each link has friction (1 - link_weight). Energy decays at each hop.
  The energy that ARRIVES at a narrative = transmission strength.

Computes per-narrative:
  - route_exists: bool — is there at least one path?
  - received_energy: float — energy arrived via propagation (0-1)
  - diversity: int — number of independent paths (redundancy)
  - bottleneck_node: str — node that absorbs the most energy (highest friction)

Usage:
    from graph_health import check_transmission_health
    health = check_transmission_health(graph)
"""

import yaml
import os
from collections import defaultdict


def _build_adjacency(graph):
    """Build adjacency lists from graph links."""
    adj = defaultdict(list)       # node_id → [(target_id, weight)]
    adj_rev = defaultdict(list)   # node_id → [(source_id, weight)]
    for link in graph.get("links", []):
        src = link.get("source", "")
        tgt = link.get("target", "")
        w = link.get("weight", 0)
        adj[src].append((tgt, w))
        adj_rev[tgt].append((src, w))
    return adj, adj_rev


def _simulate_reader(graph, node_lookup, adj, n_ticks_per_space=3, total_budget=5):
    """Simulate a reader traversing the GA in Z-pattern.

    The reader (actor) enters each space in Z-order (top-left → top-right →
    bottom-left → bottom-right), modulated by space weight (heavier spaces
    attract more attention = more ticks).

    In each space, energy propagates from the actor through things to narratives.
    Returns: dict of narrative_id → received_energy after full traversal.
    """
    nodes = graph.get("nodes", [])

    # Collect spaces with approximate positions
    # Use node order as proxy for visual position (Gemini lists top-to-bottom, left-to-right)
    spaces = [n for n in nodes if n.get("node_type") == "space"]
    things = [n for n in nodes if n.get("node_type") == "thing"]
    narratives = [n for n in nodes if n.get("node_type") == "narrative"]

    if not spaces:
        # No spaces — treat all things as one flat space
        spaces = [{"id": "_implicit_space", "name": "full GA", "node_type": "space", "weight": 1.0}]
        # Link all things to implicit space
        for t in things:
            adj[t["id"]].append(("_implicit_space", 1.0))
            adj["_implicit_space"].append((t["id"], 1.0))

    # Z-pattern ordering: spaces are already in document order from Gemini
    # Modulate time per space by weight
    total_weight = sum(s.get("weight", 0.5) for s in spaces)
    if total_weight == 0:
        total_weight = len(spaces)

    # Energy accumulator per narrative
    narrative_energy = defaultdict(float)

    # Reader traverses each space
    for space in spaces:
        sid = space["id"]
        space_w = space.get("weight", 0.5)

        # Time budget for this space (proportional to weight)
        ticks = max(1, int(total_budget * space_w / total_weight))

        # Find things IN this space
        things_in_space = []
        for t in things:
            # Check if thing links to this space
            for neighbor, w in adj.get(t["id"], []):
                if neighbor == sid:
                    things_in_space.append(t)
                    break
            else:
                # Also check reverse
                for neighbor, w in adj.get(sid, []):
                    if neighbor == t["id"]:
                        things_in_space.append(t)
                        break

        if not things_in_space:
            continue

        # Reader's energy enters through things (weighted by thing prominence)
        thing_energy = {}
        for t in things_in_space:
            thing_energy[t["id"]] = t.get("weight", 0.5) * space_w

        # Propagate through ticks
        for tick in range(ticks):
            for tid, e in list(thing_energy.items()):
                if e < 0.01:
                    continue
                for neighbor, link_w in adj.get(tid, []):
                    if neighbor.startswith("narrative:"):
                        narrative_energy[neighbor] += e * link_w
                # Decay
                thing_energy[tid] *= 0.7

    # Normalize
    max_possible = total_budget * max(s.get("weight", 0.5) for s in spaces)
    for nid in narrative_energy:
        narrative_energy[nid] = min(narrative_energy[nid] / max(max_possible, 0.01), 1.0)

    return dict(narrative_energy)


def _propagate_energy(adj, node_lookup, source_ids, target_id, n_ticks=5):
    """Propagate energy from source nodes toward target through the graph.

    Mini tick engine: energy flows through links with friction.
    Each link's friction = (1 - link_weight). Energy decays per hop.
    After n_ticks, measure how much energy arrived at target.

    Returns: (received_energy, path_trace)
    """
    # Initialize energy: source nodes emit their weight as energy
    energy = {}
    for sid in source_ids:
        node = node_lookup.get(sid, {})
        energy[sid] = node.get("weight", 0.5)

    trace = []  # [(tick, node_id, energy_delta)]

    for tick in range(n_ticks):
        new_energy = defaultdict(float)
        for node_id, e in energy.items():
            if e < 0.01:  # below threshold, stop propagating
                continue
            for neighbor, link_weight in adj.get(node_id, []):
                # Energy transferred = current_energy * link_weight
                # Friction = (1 - link_weight) absorbs the rest
                transferred = e * link_weight
                new_energy[neighbor] += transferred
                trace.append((tick, node_id, neighbor, round(transferred, 4)))

        # Decay: existing energy loses 20% per tick (ambient friction)
        for nid in energy:
            energy[nid] *= 0.8

        # Add propagated energy
        for nid, e in new_energy.items():
            energy[nid] = energy.get(nid, 0) + e

    received = energy.get(target_id, 0)
    # Normalize to 0-1 (cap at source total)
    source_total = sum(node_lookup.get(s, {}).get("weight", 0.5) for s in source_ids)
    normalized = min(received / max(source_total, 0.01), 1.0)

    return round(normalized, 4), trace


def _find_all_paths(adj, start, end, max_depth=6):
    """Find all paths from start to end (BFS, bounded depth)."""
    paths = []
    queue = [(start, [start], 1.0)]

    while queue:
        current, path, min_w = queue.pop(0)
        if len(path) > max_depth:
            continue
        if current == end:
            paths.append((path, min_w))
            continue
        for neighbor, weight in adj.get(current, []):
            if neighbor not in path:
                queue.append((neighbor, path + [neighbor], min(min_w, weight)))

    return paths


def _find_paths_through_type(adj, nodes_by_type, start_type, bridge_type, end_type):
    """Find all paths: start_type → bridge_type → end_type."""
    results = {}

    starts = nodes_by_type.get(start_type, [])
    bridges = nodes_by_type.get(bridge_type, [])
    ends = nodes_by_type.get(end_type, [])

    for end_node in ends:
        end_id = end_node["id"]
        all_paths = []

        for start_node in starts:
            start_id = start_node["id"]
            paths = _find_all_paths(adj, start_id, end_id)
            # Filter: must pass through at least one bridge node
            for path, min_w in paths:
                bridge_nodes_in_path = [n for n in path if any(
                    n == b["id"] for b in bridges)]
                if bridge_nodes_in_path:
                    all_paths.append({
                        "path": path,
                        "min_weight": min_w,
                        "bridge_nodes": bridge_nodes_in_path,
                        "from_space": start_id,
                    })

        results[end_id] = all_paths

    return results


def check_transmission_health(graph):
    """Check health of space→thing→narrative transmission chains.

    Returns dict with per-narrative health metrics + overall score.
    """
    nodes = graph.get("nodes", [])
    adj, adj_rev = _build_adjacency(graph)

    # Group nodes by type
    nodes_by_type = defaultdict(list)
    node_lookup = {}
    for node in nodes:
        nt = node.get("node_type", "thing")
        nodes_by_type[nt].append(node)
        node_lookup[node["id"]] = node

    spaces = nodes_by_type.get("space", [])
    things = nodes_by_type.get("thing", [])
    narratives = nodes_by_type.get("narrative", [])

    # No spaces or narratives = can't check transmission
    if not spaces:
        return {
            "status": "no_spaces",
            "message": "No space nodes (messages) in graph — cannot check transmission",
            "narratives": [],
            "overall_score": 0,
        }

    if not narratives:
        return {
            "status": "no_narratives",
            "message": "No narrative nodes (desired effects) in graph — add them to check transmission",
            "narratives": [],
            "overall_score": 0,
            "spaces": [{"id": s["id"], "name": s["name"]} for s in spaces],
        }

    # Find paths for each narrative: space → thing(s) → narrative
    narrative_paths = _find_paths_through_type(
        adj, nodes_by_type, "space", "thing", "narrative")

    # Also check reverse: narrative ← thing(s) ← space
    adj_bidir = defaultdict(list)
    for link in graph.get("links", []):
        src = link.get("source", "")
        tgt = link.get("target", "")
        w = link.get("weight", 0)
        adj_bidir[src].append((tgt, w))
        adj_bidir[tgt].append((src, w))  # bidirectional

    narrative_paths_bidir = _find_paths_through_type(
        adj_bidir, nodes_by_type, "space", "thing", "narrative")

    # Merge results (use bidir if directed found nothing)
    for nid in narrative_paths_bidir:
        if nid not in narrative_paths or not narrative_paths[nid]:
            narrative_paths[nid] = narrative_paths_bidir[nid]

    # Compute health per narrative
    results = []
    for narrative in narratives:
        nid = narrative["id"]
        name = narrative["name"]
        paths = narrative_paths.get(nid, [])

        if not paths:
            results.append({
                "narrative_id": nid,
                "narrative_name": name,
                "route_exists": False,
                "solidity": 0.0,
                "diversity": 0,
                "bottleneck_node": None,
                "issue": f"'{name}' has no path from any space through things — this effect is unreachable",
                "prompt": f"L'effet désiré '{name}' n'est porté par aucun élément visuel concret. "
                         f"Aucun chemin space→thing→narrative n'existe. "
                         f"Quel élément visuel pourrait porter cet effet ?",
            })
            continue

        # Energy from reader simulation (replaces naive min-weight)
        if not hasattr(check_transmission_health, '_reader_energy'):
            # Run reader sim once, cache results for all narratives
            check_transmission_health._reader_energy = _simulate_reader(
                graph, node_lookup, adj_bidir)
        reader_energy = check_transmission_health._reader_energy
        received_energy = reader_energy.get(nid, 0.0)

        # Bottleneck: thing on best path with lowest weight
        best_path = max(paths, key=lambda p: p["min_weight"])
        bottleneck = None
        bottleneck_w = 1.0
        for node_id in best_path["path"]:
            node = node_lookup.get(node_id)
            if node and node.get("node_type") == "thing":
                w = node.get("weight", 0)
                if w < bottleneck_w:
                    bottleneck_w = w
                    bottleneck = node_id

        # Diversity = number of paths using different bridge nodes
        unique_bridges = set()
        for p in paths:
            bridge_key = frozenset(p["bridge_nodes"])
            unique_bridges.add(bridge_key)
        diversity = len(unique_bridges)

        # Generate prompt if health is weak
        prompt = None
        if received_energy < 0.3:
            prompt = (
                f"L'effet '{name}' ne reçoit que {received_energy:.0%} de l'attention du lecteur. "
                f"Le visuel est parcouru en {len(paths)} chemin(s) mais trop peu d'attention arrive à ce message. "
                f"Quels éléments visuels renforceraient la transmission vers cet effet ?")
        elif diversity < 2:
            prompt = (
                f"L'effet '{name}' ne passe que par un seul chemin (diversité={diversity}). "
                f"Si un élément de ce chemin est raté (scroll, daltonisme, thumbnail), l'effet est perdu. "
                f"Quel chemin alternatif indépendant atteindrait le même effet ?")

        results.append({
            "narrative_id": nid,
            "narrative_name": name,
            "route_exists": True,
            "received_energy": received_energy,
            "diversity": diversity,
            "bottleneck_node": bottleneck,
            "bottleneck_weight": round(bottleneck_w, 3),
            "best_path": best_path["path"],
            "n_paths": len(paths),
            "issue": prompt if prompt else None,
            "prompt": prompt,
        })

    # Orphan detection
    # Things not linked to any space = visual noise
    thing_to_spaces = {}
    for thing in things:
        tid = thing["id"]
        linked_spaces = [t for t, w in adj.get(tid, []) if t.startswith("space:")]
        linked_spaces += [s for s, w in adj_rev.get(tid, []) if s.startswith("space:")]
        thing_to_spaces[tid] = list(set(linked_spaces))

    orphan_things = [
        {"id": t["id"], "name": t["name"], "weight": t.get("weight", 0)}
        for t in things
        if not thing_to_spaces.get(t["id"])
    ]

    # Spaces not linked to any thing = invisible messages
    space_to_things = {}
    for space in spaces:
        sid = space["id"]
        linked_things = [s for s, w in adj_rev.get(sid, []) if s.startswith("thing:")]
        linked_things += [t for t, w in adj.get(sid, []) if t.startswith("thing:")]
        space_to_things[sid] = list(set(linked_things))

    orphan_spaces = [
        {"id": s["id"], "name": s["name"], "weight": s.get("weight", 0)}
        for s in spaces
        if not space_to_things.get(s["id"])
    ]

    # Overall score
    if results:
        route_pct = sum(1 for r in results if r["route_exists"]) / len(results)
        avg_energy = sum(r.get("received_energy", 0) for r in results) / len(results)
        avg_diversity = sum(r["diversity"] for r in results) / len(results)
        overall = route_pct * 0.4 + avg_energy * 0.3 + min(avg_diversity / 3, 1) * 0.3
    else:
        overall = 0

    # Clear reader sim cache
    if hasattr(check_transmission_health, '_reader_energy'):
        del check_transmission_health._reader_energy

    return {
        "status": "checked",
        "overall_score": round(overall, 3),
        "narratives": results,
        "orphan_things": orphan_things,
        "orphan_spaces": orphan_spaces,
        "n_spaces": len(spaces),
        "n_things": len(things),
        "n_narratives": len(narratives),
        "prompts": [r["prompt"] for r in results if r.get("prompt")],
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Check GA graph transmission health")
    parser.add_argument("graph", help="Path to L3 graph YAML")
    args = parser.parse_args()

    with open(args.graph) as f:
        graph = yaml.safe_load(f)

    health = check_transmission_health(graph)

    print(f"\n=== TRANSMISSION HEALTH (score: {health['overall_score']:.2f}) ===")
    print(f"Spaces: {health['n_spaces']} | Things: {health['n_things']} | Narratives: {health['n_narratives']}")

    for r in health["narratives"]:
        status = "✓" if r["route_exists"] else "✗"
        sol = f"solidity={r['solidity']:.2f}" if r["route_exists"] else "NO ROUTE"
        div = f"diversity={r['diversity']}" if r["route_exists"] else ""
        print(f"  {status} {r['narrative_name']}: {sol} {div}")
        if r.get("prompt"):
            print(f"    → {r['prompt'][:100]}")

    if health["orphan_things"]:
        print(f"\n  Orphan things (visual noise):")
        for o in health["orphan_things"]:
            print(f"    - {o['name']} (w={o['weight']})")

    if health["orphan_spaces"]:
        print(f"\n  Orphan spaces (invisible messages):")
        for o in health["orphan_spaces"]:
            print(f"    - {o['name']} (w={o['weight']})")
