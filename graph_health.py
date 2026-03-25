"""
Graph Health — Route verification for message→effect transmission chains.

Checks that every narrative (desired effect) is reachable from at least
one space (message) through concrete things (visual elements).

Computes per-effect:
  - route_exists: bool — is there at least one path?
  - solidity: float — min weight on the strongest path (bottleneck)
  - diversity: int — number of independent paths (redundancy)
  - bottleneck_node: str — the weakest link in the strongest path

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


def _find_all_paths(adj, start, end, max_depth=6):
    """Find all paths from start to end (BFS, bounded depth)."""
    paths = []
    queue = [(start, [start], 1.0)]  # (current, path, min_weight)

    while queue:
        current, path, min_w = queue.pop(0)
        if len(path) > max_depth:
            continue
        if current == end:
            paths.append((path, min_w))
            continue
        for neighbor, weight in adj.get(current, []):
            if neighbor not in path:  # no cycles
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

        # Best path = highest min_weight (strongest bottleneck)
        best_path = max(paths, key=lambda p: p["min_weight"])
        solidity = best_path["min_weight"]

        # Bottleneck = node with lowest weight on best path
        bottleneck = None
        bottleneck_w = 1.0
        for node_id in best_path["path"]:
            node = node_lookup.get(node_id)
            if node and node.get("node_type") == "thing":
                w = node.get("weight", 0)
                if w < bottleneck_w:
                    bottleneck_w = w
                    bottleneck = node_id

        # Diversity = number of paths that use different bridge nodes
        unique_bridges = set()
        for p in paths:
            bridge_key = frozenset(p["bridge_nodes"])
            unique_bridges.add(bridge_key)
        diversity = len(unique_bridges)

        # Generate prompt if health is weak
        prompt = None
        if solidity < 0.5:
            bn_name = node_lookup.get(bottleneck, {}).get("name", bottleneck)
            prompt = (
                f"L'effet '{name}' est porté par un chemin dont le maillon faible est "
                f"'{bn_name}' (weight {bottleneck_w:.2f}). "
                f"Ce maillon risque de casser en scroll rapide. "
                f"Comment renforcer '{bn_name}' ou créer un chemin alternatif ?")
        elif diversity < 2:
            prompt = (
                f"L'effet '{name}' ne passe que par un seul chemin (diversité={diversity}). "
                f"Si un élément de ce chemin est raté (scroll, daltonisme, thumbnail), l'effet est perdu. "
                f"Quel chemin alternatif indépendant atteindrait le même effet ?")

        results.append({
            "narrative_id": nid,
            "narrative_name": name,
            "route_exists": True,
            "solidity": round(solidity, 3),
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
        avg_solidity = sum(r["solidity"] for r in results) / len(results)
        avg_diversity = sum(r["diversity"] for r in results) / len(results)
        overall = route_pct * 0.4 + avg_solidity * 0.3 + min(avg_diversity / 3, 1) * 0.3
    else:
        overall = 0

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
