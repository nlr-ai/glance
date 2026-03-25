"""
GA Advisor — Targeted Gemini queries that return graph modifications.

Takes a GA image + its L3 graph + a user intent/question, and returns
a modified cluster with specific changes to implement.

Optional: pass `abstract` (paper abstract text) so Gemini's modifications
are scientifically grounded — ensuring suggested changes don't introduce
Spin or omit key findings.

Usage:
    python ga_advisor.py <image> <graph> "I want more emotional impact"
    python ga_advisor.py <image> <graph> "How to improve layout clarity?" --abstract "Paper abstract..."
    python ga_advisor.py <image> <graph> "Dark theme version"
    python ga_advisor.py <image> <graph> "Make the hierarchy obvious in 3 seconds"

The output is a MODIFIED graph YAML — not advice text, but actual
node/link changes that can be diff'd against the original.
"""

import os
import sys
import yaml
import json
import re
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("ga_advisor")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ENV = os.path.join(_HERE, ".env")
if os.path.exists(_ENV):
    with open(_ENV) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)


def _load_abstract(args_abstract=None, args_abstract_file=None, graph_path=None):
    """Load abstract from args, file, or sidecar JSON.

    Priority: direct text > file > sidecar JSON (semantic_references.L3[0]).
    Returns None if no abstract is available.
    """
    if args_abstract:
        return args_abstract
    if args_abstract_file and os.path.exists(args_abstract_file):
        with open(args_abstract_file, encoding="utf-8") as f:
            return f.read().strip()
    if graph_path:
        sidecar = os.path.splitext(graph_path)[0] + '.json'
        if os.path.exists(sidecar):
            with open(sidecar, encoding="utf-8") as f:
                data = json.load(f)
            l3 = data.get('semantic_references', {}).get('L3', [])
            if l3:
                return l3[0]
    return None


ADVISOR_PROMPT = """You are a visual communication expert analyzing a scientific Graphical Abstract (GA).

The GA's current L3 knowledge graph is:
```yaml
{graph_yaml}
```

The user's intent/question is:
> {intent}

Your job: return a MODIFIED version of the graph that implements the user's intent.

Rules:
1. Return the FULL graph YAML (nodes + links + metadata), not just the changes
2. For each node you modify, add a `_change` field explaining what changed and why
3. You can:
   - Modify existing nodes (weight, energy, stability, synthesis)
   - Add new nodes (for missing concepts)
   - Remove nodes (mark with `_removed: true` and `_change: "reason"`)
   - Add/remove/modify links
   - Add metadata fields
4. Every change must serve the user's intent — no gratuitous modifications
5. Include a `_advisor_summary` in metadata with:
   - `intent`: the user's original question
   - `changes_made`: count of modifications
   - `rationale`: 2-3 sentences explaining the strategy
   - `expected_impact`: which GLANCE metrics should improve (S9a, S9b, S10, etc.)

Return ONLY valid YAML. No markdown fences. No explanation text outside the YAML.

Example of a modified node:
```yaml
  - id: "thing:1"
    name: "Main Finding"
    weight: 0.95       # was 0.70 — increased per user intent
    stability: 1.0
    energy: 0.3        # was 0.8 — resolved by increasing visual weight
    synthesis: "..."
    _change: "Increased weight 0.70→0.95 and resolved energy 0.8→0.3 to make this the dominant visual element"
```
"""


def _resilient_yaml_parse(raw_text):
    """Parse YAML with progressive degradation."""
    text = raw_text.strip()
    # Extract YAML from mixed text+YAML response
    yaml_match = re.search(r"```ya?ml\s*\n(.+?)```", text, re.DOTALL | re.IGNORECASE)
    if yaml_match:
        text = yaml_match.group(1).strip()
    else:
        text = re.sub(r"^```ya?ml\s*\n", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^```\s*\n", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\n```\s*$", "", text)

    # Strategy 1: direct
    try:
        parsed = yaml.safe_load(text)
        if isinstance(parsed, dict):
            return parsed
    except yaml.YAMLError:
        pass

    # Strategy 2: truncate from end
    lines = text.split("\n")
    for trim in range(1, min(len(lines), 50)):
        try:
            result = yaml.safe_load("\n".join(lines[:-trim]))
            if isinstance(result, dict):
                logger.info(f"  YAML recovered by trimming {trim} lines")
                return result
        except yaml.YAMLError:
            continue

    logger.warning("  YAML parse failed completely")
    return None


def advise(image_path, graph_path, intent, output_path=None, abstract=None,
           prior_graph=True):
    """Send GA + graph + intent to Gemini, get modified graph back.

    Args:
        image_path: Path to GA image file.
        graph_path: Path to L3 graph YAML file.
        intent: What the user wants to change.
        output_path: Optional output path for the advised graph.
        abstract: Optional paper abstract text. When provided, Gemini ensures
                  modifications are scientifically grounded.
        prior_graph: When True (default), includes the existing graph YAML in
                     the Gemini prompt as context so modifications build on the
                     current graph rather than starting from scratch.
    """
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-2.5-pro"))

    # Load image
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
    mime_type = mime_map.get(ext, "image/png")

    # Load graph
    with open(graph_path, "r", encoding="utf-8") as f:
        graph = yaml.safe_load(f)
    graph_yaml = yaml.dump(graph, default_flow_style=False, allow_unicode=True)

    # Build prompt — when prior_graph=True, include existing graph as context
    effective_graph_yaml = graph_yaml if prior_graph else "(no prior graph provided)"
    prompt = ADVISOR_PROMPT.format(graph_yaml=effective_graph_yaml, intent=intent)

    if abstract:
        prompt += (
            f"\n\nPAPER ABSTRACT: {abstract}\n\n"
            "Ensure all modifications are scientifically grounded. "
            "Do not introduce Spin (visual claims the data doesn't support). "
            "If the user's intent would misrepresent the findings, flag it and suggest "
            "a scientifically accurate alternative."
        )

    logger.info(f"Intent: {intent}")
    logger.info(f"Sending to Gemini ({len(graph.get('nodes',[]))} nodes)...")

    response = model.generate_content(
        [prompt, {"mime_type": mime_type, "data": image_bytes}],
        generation_config={"temperature": 0.3, "max_output_tokens": 8192},
    )

    parsed = _resilient_yaml_parse(response.text)
    if parsed is None:
        logger.error("Failed to parse Gemini response")
        return None

    # Compute diff summary
    old_nodes = {n["id"]: n for n in graph.get("nodes", [])}
    new_nodes = {n["id"]: n for n in parsed.get("nodes", [])}

    added = set(new_nodes) - set(old_nodes)
    removed = [n for n in parsed.get("nodes", []) if n.get("_removed")]
    modified = []
    for nid in set(old_nodes) & set(new_nodes):
        if new_nodes[nid].get("_change"):
            modified.append(new_nodes[nid])

    logger.info(f"Changes: {len(modified)} modified, {len(added)} added, {len(removed)} removed")

    # Print changes
    for n in modified:
        print(f"  ~ {n['name']}: {n.get('_change', '')}")
    for nid in added:
        n = new_nodes[nid]
        print(f"  + {n.get('name', nid)}: {n.get('_change', 'new node')}")
    for n in removed:
        print(f"  - {n.get('name', n['id'])}: {n.get('_change', 'removed')}")

    # Print advisor summary
    summary = parsed.get("metadata", {}).get("_advisor_summary", {})
    if summary:
        print(f"\nStrategy: {summary.get('rationale', '')}")
        print(f"Expected impact: {summary.get('expected_impact', '')}")

    # Save
    if output_path is None:
        base = os.path.splitext(graph_path)[0]
        output_path = f"{base}_advised.yaml"

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(parsed, f, default_flow_style=False, allow_unicode=True)

    logger.info(f"Advised graph saved: {output_path}")
    return parsed


def compare_graphs(original_path, advised_path):
    """Print a diff between original and advised graphs."""
    with open(original_path) as f:
        orig = yaml.safe_load(f)
    with open(advised_path) as f:
        adv = yaml.safe_load(f)

    orig_nodes = {n["id"]: n for n in orig.get("nodes", [])}
    adv_nodes = {n["id"]: n for n in adv.get("nodes", [])}

    print("=== GRAPH DIFF ===")
    print(f"{'Node':40s} | {'weight':>8s} | {'energy':>8s} | {'stab':>6s} | Change")
    print("-" * 100)

    all_ids = sorted(set(list(orig_nodes) + list(adv_nodes)))
    for nid in all_ids:
        o = orig_nodes.get(nid)
        a = adv_nodes.get(nid)
        if o and a and not a.get("_removed"):
            dw = a["weight"] - o["weight"]
            de = a["energy"] - o["energy"]
            name = a.get("name", nid)[:40]
            change = a.get("_change", "")[:40]
            if dw != 0 or de != 0 or change:
                print(f"{name:40s} | {o['weight']:.2f}→{a['weight']:.2f} | {o['energy']:.2f}→{a['energy']:.2f} | {a.get('stability',0):.2f} | {change}")
        elif o and not a:
            print(f"{o.get('name', nid)[:40]:40s} | REMOVED")
        elif a and not o:
            print(f"{a.get('name', nid)[:40]:40s} | {'':>8s} | {'':>8s} | {'':>6s} | NEW: {a.get('_change','')[:30]}")


MERGE_PROMPT = """You are a visual communication expert. You are given {n} versions of a Graphical Abstract (GA) for the same scientific paper.

The user wants: {intent}

{image_graph_sections}

Your job: Create a MERGED graph that takes the best elements from each version.
For each node in the merged graph, indicate which version it came from with a `_source` field (A, B, or C).
If a node is a fusion of elements from multiple versions, use "A+B" or "A+B+C".

Return ONLY valid YAML:

nodes:
  - id: "thing:{{short_id}}"
    name: "{{element name}}"
    node_type: "thing"
    synthesis: "{{what this element communicates}}"
    weight: 0.0-1.0
    stability: 0.0-1.0
    energy: 0.0-1.0
    _source: "A"
    _merge_rationale: "why this element was chosen from version A"
  ...

links:
  - source: "thing:{{source_id}}"
    target: "thing:{{target_id}}"
    link_type: "link"
    weight: 0.0-1.0
    _source: "B"
  ...

metadata:
  chart_type: "{{best chart type}}"
  hierarchy_clear: true/false
  merge_summary:
    intent: "{intent}"
    elements_from_a: <count>
    elements_from_b: <count>
{elements_from_c}    elements_fused: <count of A+B or A+B+C nodes>
    strategy: "2-3 sentences explaining the merge strategy"
    expected_improvement: "what the merged version should do better than any single version"
    tradeoffs: "what was sacrificed in the merge"

Instructions:
- Prefer the version that communicates faster (5-second rule)
- When both versions encode the same information, keep the one with higher stability
- Don't just union everything — a merged GA with too many elements loses clarity
- The merged graph should have 5-15 nodes (same as a single analysis)
- Every node MUST have _source and _merge_rationale
- Be specific about WHY each element was chosen

Return ONLY the YAML. No markdown fences. No explanation before or after.
"""


def advise_merge(image_paths: list, graph_paths: list, intent: str, output_path=None,
                 abstract=None, prior_graph=True) -> dict:
    """Merge the best elements from 2-3 GA versions into a single optimal graph.

    Args:
        image_paths: list of 2 or 3 image file paths
        graph_paths: list of 2 or 3 corresponding graph YAML paths
        intent: what the user wants from the merge
        output_path: Optional output path for the merged graph.
        abstract: Optional paper abstract text. When provided, Gemini ensures
                  merged elements are scientifically accurate.
        prior_graph: When True (default), includes existing graphs in the Gemini
                     prompt as context for iterative merging.

    Returns:
        dict: merged graph with _source annotations on each node
    """
    import google.generativeai as genai

    n = len(image_paths)
    if n < 2 or n > 3:
        raise ValueError(f"advise_merge requires 2 or 3 image/graph pairs, got {n}")
    if len(graph_paths) != n:
        raise ValueError(f"Number of images ({n}) must match number of graphs ({len(graph_paths)})")

    for p in image_paths + graph_paths:
        if not os.path.exists(p):
            raise FileNotFoundError(f"File not found: {p}")

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-2.5-pro"))

    # Build image/graph sections
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    content_parts = []
    section_texts = []

    for i in range(n):
        label = chr(65 + i)
        with open(graph_paths[i], "r", encoding="utf-8") as f:
            graph = yaml.safe_load(f)
        if prior_graph:
            graph_yaml = yaml.dump(graph, default_flow_style=False, allow_unicode=True)
            section_texts.append(
                f"--- Version {label} ({os.path.basename(image_paths[i])}) ---\n"
                f"Graph:\n```yaml\n{graph_yaml[:3000]}\n```\n"
            )
        else:
            section_texts.append(
                f"--- Version {label} ({os.path.basename(image_paths[i])}) ---\n"
                f"Graph: (no prior graph provided)\n"
            )

    elements_from_c = "    elements_from_c: <count>\n" if n == 3 else ""

    prompt = MERGE_PROMPT.format(
        n=n,
        intent=intent,
        image_graph_sections="\n".join(section_texts),
        elements_from_c=elements_from_c,
    )

    if abstract:
        prompt += (
            f"\n\nPAPER ABSTRACT: {abstract}\n\n"
            "Ensure the merged GA accurately represents the paper's findings. "
            "Prefer elements that faithfully communicate the science. "
            "Flag any merged element that would constitute Spin."
        )

    # Build content: prompt + all images
    parts = [prompt]
    for i in range(n):
        label = chr(65 + i)
        with open(image_paths[i], "rb") as f:
            img_bytes = f.read()
        ext = os.path.splitext(image_paths[i])[1].lower()
        mime = mime_map.get(ext, "image/png")
        parts.append(f"Version {label} image:")
        parts.append({"mime_type": mime, "data": img_bytes})

    logger.info(f"Merge intent: {intent}")
    logger.info(f"Merging {n} versions...")

    try:
        response = model.generate_content(
            parts,
            generation_config={"temperature": 0.3, "max_output_tokens": 8192},
        )
        raw = response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise RuntimeError(f"Gemini API error during merge: {e}")

    parsed = _resilient_yaml_parse(raw)
    if parsed is None:
        logger.error(
            "Failed to parse merged graph from Gemini. "
            f"Response was {len(raw)} chars, {len(raw.splitlines())} lines. "
            "This usually means the combined graph YAML exceeded Gemini's structured output capacity."
        )
        return None

    # Count sources
    source_counts = {}
    for node in parsed.get("nodes", []):
        src = node.get("_source", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1

    logger.info(f"Merged graph: {len(parsed.get('nodes', []))} nodes, sources: {source_counts}")

    # Print merge summary
    summary = parsed.get("metadata", {}).get("merge_summary", {})
    if summary:
        print(f"\nMerge strategy: {summary.get('strategy', '')}")
        print(f"Expected improvement: {summary.get('expected_improvement', '')}")
        print(f"Tradeoffs: {summary.get('tradeoffs', '')}")

    for node in parsed.get("nodes", []):
        src = node.get("_source", "?")
        name = node.get("name", node.get("id", "?"))
        rationale = node.get("_merge_rationale", "")
        print(f"  [{src}] {name}: {rationale[:60]}")

    # Save
    if output_path is None:
        base_names = "_plus_".join(
            os.path.splitext(os.path.basename(p))[0][:15] for p in image_paths
        )
        output_path = os.path.join(_HERE, "data", f"merged_{base_names}.yaml")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(parsed, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"Merged graph saved: {output_path}")

    return parsed


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GA Advisor — targeted Gemini queries")
    parser.add_argument("--compare", nargs="+", metavar="PATH",
                        help="Merge 2-3 GA versions: --compare img_a.png graph_a.yaml img_b.png graph_b.yaml [img_c.png graph_c.yaml] \"intent\"")
    parser.add_argument("--abstract", help="Paper abstract text for context")
    parser.add_argument("--abstract-file", help="Path to file containing abstract")
    parser.add_argument("image", nargs="?", help="Path to GA image (single mode)")
    parser.add_argument("graph", nargs="?", help="Path to L3 graph YAML (single mode)")
    parser.add_argument("intent", nargs="?", help="What you want (single mode)")
    parser.add_argument("--output", "-o", help="Output path")
    args = parser.parse_args()

    abstract = _load_abstract(args.abstract, args.abstract_file,
                              args.graph if hasattr(args, 'graph') else None)

    if args.compare:
        paths = args.compare
        # Last argument is the intent string, rest are image/graph pairs
        if len(paths) < 5:
            parser.error(
                "--compare requires pairs of (image, graph) + intent string at the end. "
                "Example: --compare img_a.png graph_a.yaml img_b.png graph_b.yaml \"Take the best of both\". "
                f"Got {len(paths)} arguments."
            )
        intent_str = paths[-1]
        pair_paths = paths[:-1]
        if len(pair_paths) not in (4, 6):
            parser.error(
                f"Expected 4 or 6 paths before the intent string (2 or 3 image/graph pairs), "
                f"got {len(pair_paths)}."
            )
        n = len(pair_paths) // 2
        image_paths = [pair_paths[i * 2] for i in range(n)]
        graph_paths = [pair_paths[i * 2 + 1] for i in range(n)]
        advise_merge(image_paths, graph_paths, intent_str, args.output, abstract=abstract)
    elif args.image and args.graph and args.intent:
        advise(args.image, args.graph, args.intent, args.output, abstract=abstract)
    else:
        parser.print_help()
