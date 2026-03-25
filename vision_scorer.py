"""GLANCE Vision Scorer — Gemini Pro Vision API -> L3 Graph + Analysis.

Sends a GA image to Gemini Vision, receives structured YAML analysis,
validates it, and saves the resulting L3 graph.

Model: Gemini Pro (default: gemini-2.5-pro) via GEMINI_MODEL env var.
Pro is preferred over Flash for this use case — more accurate structured output
and better vision analysis on complex charts.
"""

import os
import re
import yaml
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
BASE = os.path.dirname(__file__)

# Load API key from .env file (simple key=value parsing, no dotenv dependency)
_env_path = os.path.join(BASE, ".env")
if os.path.exists(_env_path):
    with open(_env_path, encoding="utf-8") as _ef:
        for _line in _ef:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())


VISION_PROMPT = """You are analyzing a scientific Graphical Abstract (GA) for the GLANCE benchmark.
GLANCE measures whether a GA communicates its key message in 5 seconds of scrolling.

Analyze this image thoroughly and return a YAML document with the following structure.

nodes:
  - id: "thing:{short_id}"
    name: "{element name}"
    node_type: "thing"
    synthesis: "{what this element communicates}"
    weight: 0.0-1.0
    stability: 0.0-1.0
    energy: 0.0-1.0

links:
  - source: "thing:{source_id}"
    target: "thing:{target_id}"
    link_type: "link"
    weight: 0.0-1.0

metadata:
  chart_type: bar|pie|scatter|line|heatmap|infographic|mixed|other
  word_count: <estimated number of visible words>
  visual_channels_used:
    - <list from: position, length, area, angle, color_hue, color_saturation, color_value, texture, shape, size, orientation, text_label, icon, border, spacing, grouping, alignment, contrast, whitespace>
  dominant_encoding: "<primary data encoding method>"
  hierarchy_clear: true|false
  accessibility_issues:
    - "<issue description>"
  executive_summary_fr: "<2-3 sentence summary in French of what this GA communicates>"
  main_finding: "<the key takeaway of this GA>"
  color_count: <number of distinct colors used>
  has_legend: true|false
  figure_text_ratio: <0.0-1.0 where 1.0 = all figure, 0.0 = all text>

Instructions:
- weight = visual prominence (1.0 = most prominent element)
- stability = how clearly/unambiguously encoded (1.0 = crystal clear)
- energy = attention-grabbing power / visual salience (1.0 = maximum)
- For links, weight = strength of visual connection between elements
- Create 5-15 nodes capturing ALL information elements visible
- Create links for visual relationships (arrows, proximity, shared color, etc.)
- Be specific in synthesis: describe WHAT information each element conveys
- executive_summary_fr must be in French
- hierarchy_clear: can you tell which result is most important in <5 seconds?

Return ONLY the YAML. No markdown fences. No explanation before or after.
"""


def _parse_gemini_yaml(raw_text: str) -> dict:
    """Parse YAML from Gemini response, handling common LLM quirks."""
    text = raw_text.strip()
    # Extract YAML from mixed text+YAML response (Gemini often adds preamble)
    yaml_match = re.search(r'```ya?ml\s*\n(.+?)```', text, re.DOTALL | re.IGNORECASE)
    if yaml_match:
        text = yaml_match.group(1).strip()
    else:
        text = re.sub(r'^```ya?ml\s*\n', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^```\s*\n', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\n```\s*$', '', text)

    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as e:
        logger.error(f"YAML parse error: {e}")
        # Strategy: truncate at last complete top-level key block
        # Find the last successfully parseable prefix
        lines = text.split("\n")
        parsed = None
        # Try removing lines from the end until YAML parses
        for trim in range(1, min(len(lines), 40)):
            candidate = "\n".join(lines[:-trim])
            try:
                result = yaml.safe_load(candidate)
                if isinstance(result, dict):
                    parsed = result
                    logger.info(f"YAML recovered by trimming {trim} lines")
                    break
            except yaml.YAMLError:
                continue
        if parsed is None:
            raise ValueError(f"Cannot parse Gemini response as YAML: {e}")

    if not isinstance(parsed, dict):
        raise ValueError(f"Expected dict from YAML, got {type(parsed)}")

    return parsed


def _validate_graph(graph: dict) -> dict:
    """Validate and normalize the L3 graph structure."""
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])
    metadata = graph.get("metadata", {})

    # Validate nodes
    valid_nodes = []
    node_ids = set()
    for node in nodes:
        if not isinstance(node, dict):
            continue
        nid = node.get("id", "")
        if not nid:
            continue
        # Ensure required fields
        node.setdefault("name", nid)
        node.setdefault("node_type", "thing")
        node.setdefault("synthesis", "")
        # Clamp numeric fields to [0, 1]
        for field in ("weight", "stability", "energy"):
            val = node.get(field, 0.5)
            try:
                val = float(val)
            except (TypeError, ValueError):
                val = 0.5
            node[field] = max(0.0, min(1.0, val))
        valid_nodes.append(node)
        node_ids.add(nid)

    # Validate links
    valid_links = []
    for link in links:
        if not isinstance(link, dict):
            continue
        # Handle both source/target and node_a/node_b naming
        src = link.get("source", link.get("node_a", ""))
        tgt = link.get("target", link.get("node_b", ""))
        if not src or not tgt:
            continue
        link["source"] = src
        link["target"] = tgt
        link.setdefault("link_type", "link")
        # Clamp weight
        w = link.get("weight", 0.5)
        try:
            w = float(w)
        except (TypeError, ValueError):
            w = 0.5
        link["weight"] = max(0.0, min(1.0, w))
        valid_links.append(link)

    # Validate metadata
    if not isinstance(metadata, dict):
        metadata = {}
    metadata.setdefault("chart_type", "mixed")
    metadata.setdefault("word_count", 0)
    metadata.setdefault("visual_channels_used", [])
    metadata.setdefault("dominant_encoding", "unknown")
    metadata.setdefault("hierarchy_clear", False)
    metadata.setdefault("accessibility_issues", [])
    metadata.setdefault("executive_summary_fr", "")
    metadata.setdefault("main_finding", "")

    return {
        "nodes": valid_nodes,
        "links": valid_links,
        "metadata": metadata,
    }


COMPARE_PROMPT = """You are comparing {n} scientific Graphical Abstracts (GAs) for the GLANCE benchmark.
GLANCE measures whether a GA communicates its key message in 5 seconds of scrolling.

The images are labeled {labels}.

For EACH image, generate a full L3 graph (nodes + links + metadata) following the same schema as a single analysis.

Then provide a comparison section.

Return ONLY valid YAML with this structure:

graphs:
  A:
    nodes: [...]
    links: [...]
    metadata: {{...}}
  B:
    nodes: [...]
    links: [...]
    metadata: {{...}}
{graph_c_placeholder}
ranking:
  - label: "A"
    estimated_glance_score: 0.0-1.0
    rationale: "why this rank"
  - label: "B"
    estimated_glance_score: 0.0-1.0
    rationale: "why this rank"
{ranking_c_placeholder}
comparison:
  fastest_message: "A or B{or_c} — which communicates its message fastest and why"
  clearest_hierarchy: "A or B{or_c} — which has the clearest visual hierarchy and why"
  a_vs_b:
    a_better: "what A does better than B"
    b_better: "what B does better than A"
{extra_comparisons}

Instructions:
- For each graph, follow the same node schema: id, name, node_type (thing), synthesis, weight, stability, energy
- For links: source, target, link_type (link), weight
- For metadata: chart_type, word_count, visual_channels_used, dominant_encoding, hierarchy_clear, accessibility_issues, executive_summary_fr, main_finding, color_count, has_legend, figure_text_ratio
- weight = visual prominence, stability = clarity of encoding, energy = attention-grabbing power
- estimated_glance_score: 0.0 = fails completely at 5-second comprehension, 1.0 = perfect instant comprehension
- Be specific and concrete in comparisons — cite actual elements from each GA

Return ONLY the YAML. No markdown fences. No explanation before or after.
"""


def compare_ga_images(images: list, filenames: list) -> dict:
    """Compare 2 or 3 GA images side-by-side via a single Gemini call.

    Args:
        images: list of tuples (image_bytes, mime_type_or_ext) — 2 or 3 items
        filenames: list of filenames corresponding to each image

    Returns:
        dict with keys: graphs (dict of A/B/C -> graph), ranking (list),
        comparison (dict with a_vs_b etc.), raw_response
    """
    import google.generativeai as genai

    n = len(images)
    if n < 2 or n > 3:
        raise ValueError(f"compare_ga_images requires 2 or 3 images, got {n}")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set. Add it to .env file.")

    genai.configure(api_key=api_key)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
    model = genai.GenerativeModel(model_name)

    labels = ", ".join(chr(65 + i) for i in range(n))  # "A, B" or "A, B, C"
    or_c = " or C" if n == 3 else ""

    graph_c_placeholder = ""
    ranking_c_placeholder = ""
    extra_comparisons = ""
    if n == 3:
        graph_c_placeholder = '  C:\n    nodes: [...]\n    links: [...]\n    metadata: {...}'
        ranking_c_placeholder = '  - label: "C"\n    estimated_glance_score: 0.0-1.0\n    rationale: "why this rank"'
        extra_comparisons = (
            '  a_vs_c:\n    a_better: "what A does better than C"\n    c_better: "what C does better than A"\n'
            '  b_vs_c:\n    b_better: "what B does better than C"\n    c_better: "what C does better than B"'
        )

    prompt = COMPARE_PROMPT.format(
        n=n,
        labels=labels,
        or_c=or_c,
        graph_c_placeholder=graph_c_placeholder,
        ranking_c_placeholder=ranking_c_placeholder,
        extra_comparisons=extra_comparisons,
    )

    # Build content parts: prompt + all images interleaved with labels
    mime_map = {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "webp": "image/webp", "gif": "image/gif", "svg": "image/svg+xml",
    }
    content_parts = [prompt]
    for i, (img_bytes, img_hint) in enumerate(images):
        label = chr(65 + i)
        fname = filenames[i] if i < len(filenames) else f"image_{label}"
        # Determine MIME type
        if "/" in img_hint:
            mime_type = img_hint
        else:
            ext = img_hint.lower().replace(".", "")
            mime_type = mime_map.get(ext, "image/png")
        content_parts.append(f"Image {label} ({fname}):")
        content_parts.append({"mime_type": mime_type, "data": img_bytes})

    try:
        response = model.generate_content(
            content_parts,
            generation_config={"temperature": 0.2, "max_output_tokens": 16384},
        )
        raw_text = response.text
    except Exception as e:
        logger.error(f"Gemini API error during comparison: {e}")
        raise RuntimeError(f"Gemini Vision API error: {e}")

    parsed = _parse_gemini_yaml(raw_text)

    # Validate each graph in the comparison
    graphs = parsed.get("graphs", {})
    validated_graphs = {}
    for label_key, g in graphs.items():
        if isinstance(g, dict):
            validated_graphs[label_key] = _validate_graph(g)
        else:
            logger.warning(f"Graph for label '{label_key}' is not a dict, skipping validation")
            validated_graphs[label_key] = g

    # Save comparison result
    timestamp = int(time.time())
    compare_filename = f"compare_{timestamp}_{'_vs_'.join(f[:10] for f in filenames)}.yaml"
    compare_path = os.path.join(BASE, "data", compare_filename)
    os.makedirs(os.path.dirname(compare_path), exist_ok=True)

    save_data = {
        "graphs": validated_graphs,
        "ranking": parsed.get("ranking", []),
        "comparison": parsed.get("comparison", {}),
    }
    yaml_content = f"# GLANCE Comparison — {' vs '.join(filenames)}\n"
    yaml_content += f"# Compared: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    yaml_content += f"# Model: {model_name}\n\n"
    yaml_content += yaml.dump(save_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    with open(compare_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    return {
        "graphs": validated_graphs,
        "ranking": parsed.get("ranking", []),
        "comparison": parsed.get("comparison", {}),
        "raw_response": raw_text,
        "saved_path": compare_path,
    }


def analyze_ga_image(image_bytes: bytes, filename: str = "") -> dict:
    """Send GA image to Gemini Vision, get L3 graph + analysis.

    Args:
        image_bytes: Raw image bytes (PNG, JPG, etc.)
        filename: Original filename for reference

    Returns:
        dict with keys: graph (validated L3), metadata, raw_response, saved_path
    """
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set. Add it to .env file.")

    genai.configure(api_key=api_key)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
    model = genai.GenerativeModel(model_name)

    # Determine MIME type from filename
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "png").lower()
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "gif": "image/gif",
        "svg": "image/svg+xml",
    }
    mime_type = mime_map.get(ext, "image/png")

    # Send to Gemini Vision
    try:
        response = model.generate_content(
            [
                VISION_PROMPT,
                {"mime_type": mime_type, "data": image_bytes},
            ],
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 8192,
            },
        )
        raw_text = response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise RuntimeError(f"Gemini Vision API error: {e}")

    # Parse and validate
    parsed = _parse_gemini_yaml(raw_text)
    graph = _validate_graph(parsed)

    # Save the graph
    timestamp = int(time.time())
    safe_name = re.sub(r'[^\w\-.]', '_', filename.rsplit(".", 1)[0] if "." in filename else filename)
    graph_filename = f"user_{timestamp}_{safe_name}_ga_graph.yaml"
    graph_path = os.path.join(BASE, "data", graph_filename)
    os.makedirs(os.path.dirname(graph_path), exist_ok=True)

    # Build the YAML to save (include original filename and timestamp)
    save_data = {
        "# Generated by GLANCE Vision Scorer": None,
        "source_image": filename,
        "analyzed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "nodes": graph["nodes"],
        "links": graph["links"],
        "metadata": graph["metadata"],
    }
    # Write clean YAML (drop the comment hack)
    yaml_content = f"# GLANCE Vision Analysis — {filename}\n"
    yaml_content += f"# Analyzed: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    yaml_content += f"# Model: {model_name}\n\n"
    yaml_content += yaml.dump(
        {"nodes": graph["nodes"], "links": graph["links"], "metadata": graph["metadata"]},
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    with open(graph_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    # Also save raw response for debugging
    raw_path = os.path.join(BASE, "data", f"user_{timestamp}_{safe_name}_raw.txt")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(raw_text)

    return {
        "graph": graph,
        "metadata": graph["metadata"],
        "raw_response": raw_text,
        "saved_path": graph_path,
        "graph_filename": graph_filename,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GLANCE Vision Scorer")
    parser.add_argument("--compare", nargs="+", metavar="IMAGE",
                        help="Compare 2 or 3 GA images: --compare ga1.png ga2.png [ga3.png]")
    parser.add_argument("image", nargs="?", help="Single GA image to analyze")
    args = parser.parse_args()

    if args.compare:
        if len(args.compare) < 2 or len(args.compare) > 3:
            parser.error("--compare requires 2 or 3 image paths")
        images = []
        filenames = []
        for path in args.compare:
            if not os.path.exists(path):
                parser.error(f"File not found: {path}")
            with open(path, "rb") as f:
                data = f.read()
            ext = os.path.splitext(path)[1].lower().replace(".", "")
            images.append((data, ext))
            filenames.append(os.path.basename(path))
        result = compare_ga_images(images, filenames)
        print(f"\nRanking:")
        for r in result.get("ranking", []):
            print(f"  {r.get('label', '?')}: score={r.get('estimated_glance_score', '?')} — {r.get('rationale', '')}")
        comp = result.get("comparison", {})
        print(f"\nFastest message: {comp.get('fastest_message', 'N/A')}")
        print(f"Clearest hierarchy: {comp.get('clearest_hierarchy', 'N/A')}")
        for key in ["a_vs_b", "a_vs_c", "b_vs_c"]:
            if key in comp:
                print(f"\n{key.upper()}:")
                for k, v in comp[key].items():
                    print(f"  {k}: {v}")
        print(f"\nSaved: {result['saved_path']}")
    elif args.image:
        if not os.path.exists(args.image):
            parser.error(f"File not found: {args.image}")
        with open(args.image, "rb") as f:
            data = f.read()
        result = analyze_ga_image(data, os.path.basename(args.image))
        print(f"Graph saved: {result['saved_path']}")
    else:
        parser.print_help()
