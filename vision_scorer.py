"""GLANCE Vision Scorer — Gemini Pro Vision API -> L3 Graph + Analysis.

Sends a GA image to Gemini Vision, receives structured YAML analysis,
validates it, and saves the resulting L3 graph.

Model: Gemini Pro (default: gemini-2.5-pro) via GEMINI_MODEL env var.
Pro is preferred over Flash for this use case — more accurate structured output
and better vision analysis on complex charts.

Optional: pass `abstract` (paper abstract text) to any analysis function so
Gemini can compare what the GA communicates vs what the paper actually found,
detecting Spin (visual embellishment) and missed key findings.
"""

import os
import re
import yaml
import time
import json
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
    # Try sidecar JSON
    if graph_path:
        sidecar = os.path.splitext(graph_path)[0] + '.json'
        if os.path.exists(sidecar):
            with open(sidecar, encoding="utf-8") as f:
                data = json.load(f)
            l3 = data.get('semantic_references', {}).get('L3', [])
            if l3:
                return l3[0]
    return None


VISION_PROMPT = """You are analyzing a scientific Graphical Abstract (GA) for the GLANCE benchmark.
GLANCE measures whether a GA communicates its key message in 5 seconds of scrolling.

Analyze this image thoroughly and return a YAML document with the following structure.

nodes:
  # SPACE nodes = visual CONTAINERS / zones on the GA (2-5 per GA)
  - id: "space:{zone_id}"
    name: "{zone name — e.g. 'left panel', 'evidence bars area', 'header'}"
    node_type: "space"
    synthesis: "{what this zone contains and how it's visually bounded}"
    weight: 0.0-1.0  # visual prominence of this zone
    stability: 1.0
    energy: 0.0-1.0
    bbox: [x, y, w, h]  # normalized 0-1 bounding box (top-left origin)

  # NARRATIVE nodes = the MESSAGES the GA communicates (2-4 per GA)
  # Narratives LIVE INSIDE spaces. They are the meaning, not the container.
  - id: "narrative:{message_id}"
    name: "{the message in one sentence}"
    node_type: "narrative"
    synthesis: "{what this message means for the reader}"
    weight: 1.0  # primary message = 1.0, secondary = 0.6-0.8
    stability: 1.0
    energy: 0.0  # a clear message has zero energy (resolved)

  # THING nodes = the visual elements that CARRY the messages (5-12 per GA)
  - id: "thing:{short_id}"
    name: "{element name}"
    node_type: "thing"
    synthesis: "{what this element communicates visually}"
    weight: 0.0-1.0
    stability: 0.0-1.0
    energy: 0.0-1.0
    bbox: [x, y, w, h]  # normalized 0-1 bounding box (top-left origin)

links:
  # thing → narrative links = "this element CARRIES this message"
  - source: "thing:{source_id}"
    target: "narrative:{message_id}"
    link_type: "link"
    weight: 0.0-1.0  # how well the element transmits the message

  # thing → space links = "this element LIVES IN this zone"
  - source: "thing:{source_id}"
    target: "space:{zone_id}"
    link_type: "link"
    weight: 1.0  # containment

  # narrative → space links = "this message is communicated IN this zone"
  - source: "narrative:{message_id}"
    target: "space:{zone_id}"
    link_type: "link"
    weight: 1.0  # residency

  # thing → thing links = visual relationships (arrows, proximity, color)
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

Instructions — follow this order strictly:

STEP 1: Identify the ZONES (space nodes, 2-5)
- What are the visual containers/regions of this GA?
- E.g., "left panel", "bottom bar", "header", "evidence section"
- Space = a bounded visual area, not a message
- bbox: [x, y, w, h] normalized 0-1. x,y = top-left corner. Example: [0.0, 0.0, 0.5, 0.4] = left half, top 40%

STEP 2: Identify the MESSAGES (narrative nodes, 2-4)
- What are the key messages this GA communicates?
- Primary message = weight 1.0, secondary = 0.6-0.8
- Narratives LIVE IN spaces (link narrative→space)
- A narrative has energy=0.0 (the message is resolved — elements may not be)

STEP 3: Identify the VISUAL ELEMENTS (thing nodes, 5-12)
- What concrete visual elements exist? (bars, icons, text, shapes, arrows...)
- weight = visual prominence, stability = clarity, energy = unresolved tension
- Things LIVE IN spaces (link thing→space)
- Things CARRY narratives (link thing→narrative)
- bbox: [x, y, w, h] normalized 0-1. Estimate the bounding box of each element in the image.

STEP 4: Link everything
- thing → narrative = "this element carries this message" (weight = transmission quality)
- thing → space = "this element lives in this zone" (containment)
- narrative → space = "this message is communicated in this zone"
- thing → thing = visual relationships (arrows, proximity, color)
- A thing with no narrative link = visual noise
- A narrative with no thing link = invisible message

STEP 5: Metadata
- executive_summary_fr must be in French
- hierarchy_clear: can you tell which result is most important in <5 seconds?

Return ONLY the YAML. No markdown fences. No explanation before or after.
"""


ENRICHMENT_PROMPT = """You are reviewing an existing L3 graph for a scientific Graphical Abstract (GA) in the GLANCE benchmark.
GLANCE measures whether a GA communicates its key message in 5 seconds of scrolling.

The current graph has {node_count} nodes and {link_count} links. It was built from a previous analysis pass.

## Current Graph
```yaml
{prior_yaml}
```

## Your Task: ENRICH, do not recreate

Compare the current graph against the image. Look for:

1. **MISSING nodes** — visual elements, spaces, or narratives present in the image but absent from the graph
2. **INCORRECT properties** — wrong bbox, wrong weight, wrong name, wrong synthesis on existing nodes
3. **MISSING links** — relationships between existing nodes that aren't captured
4. **INCOMPLETE narratives** — messages that are partially described or missing nuance

Rules:
- DO NOT recreate nodes that already exist and are correct. Only output ADDITIONS and CORRECTIONS.
- For corrections to existing nodes, use the SAME id and include only the changed fields.
- For new nodes, use the same id schema: "space:{{zone_id}}", "narrative:{{message_id}}", "thing:{{short_id}}"
- For new links, use the same schema: source, target, link_type, weight
- If the graph is already complete and accurate, return an empty nodes/links list with a metadata note.

Return ONLY valid YAML with this structure:

nodes:
  # Only NEW nodes or CORRECTIONS to existing nodes (same id, updated fields)
  - id: "thing:new_element"
    name: "..."
    node_type: "thing"
    synthesis: "..."
    weight: 0.0-1.0
    stability: 0.0-1.0
    energy: 0.0-1.0
    bbox: [x, y, w, h]

links:
  # Only NEW links not in the current graph
  - source: "thing:source_id"
    target: "narrative:message_id"
    link_type: "link"
    weight: 0.0-1.0

metadata:
  chart_type: bar|pie|scatter|line|heatmap|infographic|mixed|other
  word_count: <estimated number of visible words>
  visual_channels_used:
    - <list of channels>
  dominant_encoding: "<primary data encoding method>"
  hierarchy_clear: true|false
  accessibility_issues:
    - "<issue description>"
  executive_summary_fr: "<2-3 sentence summary in French>"
  main_finding: "<the key takeaway>"
  color_count: <number of distinct colors>
  has_legend: true|false
  figure_text_ratio: <0.0-1.0>
  enrichment_notes: "<what was added/corrected vs the prior graph>"

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

    # ── Auto-link by bbox overlap ──
    # If things/narratives have bbox and overlap with a space bbox,
    # create containment links automatically (thing→space, narrative→space)
    existing_links = {(l["source"], l["target"]) for l in valid_links}
    existing_links |= {(l["target"], l["source"]) for l in valid_links}

    spaces_with_bbox = [
        n for n in valid_nodes
        if n.get("node_type") == "space" and n.get("bbox") and len(n.get("bbox", [])) == 4
    ]

    for node in valid_nodes:
        if node.get("node_type") == "space":
            continue
        bbox = node.get("bbox")
        if not bbox or not isinstance(bbox, list) or len(bbox) != 4:
            continue
        try:
            nx, ny, nw, nh = [float(v) for v in bbox]
        except (ValueError, TypeError):
            continue
        # Center of this node
        ncx, ncy = nx + nw / 2, ny + nh / 2

        for space in spaces_with_bbox:
            try:
                sx, sy, sw, sh = [float(v) for v in space["bbox"]]
            except (ValueError, TypeError):
                continue
            # Check if node center is inside space bbox (containment)
            if sx <= ncx <= sx + sw and sy <= ncy <= sy + sh:
                pair = (node["id"], space["id"])
                if pair not in existing_links:
                    valid_links.append({
                        "source": node["id"],
                        "target": space["id"],
                        "link_type": "link",
                        "weight": 1.0,
                        "_auto": "bbox_containment",
                    })
                    existing_links.add(pair)
                    existing_links.add((space["id"], node["id"]))

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


def compare_ga_images(images: list, filenames: list, abstract: str = None,
                      prior_graph=True) -> dict:
    """Compare 2 or 3 GA images side-by-side via a single Gemini call.

    Args:
        images: list of tuples (image_bytes, mime_type_or_ext) — 2 or 3 items
        filenames: list of filenames corresponding to each image
        abstract: Optional paper abstract text. When provided, Gemini judges
                  which GA most faithfully represents the paper's findings.
        prior_graph: When True and prior graphs exist (passed as dict mapping
                     labels to graph dicts), includes them as context so Gemini
                     builds on previous analysis. Accepts True/False or a dict
                     like {"A": graph_a, "B": graph_b}.

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

    if isinstance(prior_graph, dict):
        prior_yaml = yaml.dump(prior_graph, default_flow_style=False, allow_unicode=True)
        prompt += (
            "\n\n## Current Graphs (starting point)\n"
            "Use these as your base. Modify/extend them rather than starting from scratch.\n"
            "```yaml\n"
            f"{prior_yaml}"
            "```\n"
        )

    if abstract:
        prompt += (
            f"\n\nPAPER ABSTRACT: {abstract}\n\n"
            "Compare what each GA communicates vs what the paper actually found. "
            "Flag any Spin (GA says something the data doesn't support) or missed key findings. "
            "Factor scientific accuracy into the ranking."
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


def analyze_ga_image(image_bytes: bytes, filename: str = "", abstract: str = None,
                     prior_graph=True) -> dict:
    """Send GA image to Gemini Vision, get L3 graph + analysis.

    Args:
        image_bytes: Raw image bytes (PNG, JPG, etc.)
        filename: Original filename for reference
        abstract: Optional paper abstract text. When provided, Gemini compares
                  what the GA communicates vs what the paper actually found,
                  detecting Spin and missed key findings.
        prior_graph: When a dict is passed, includes it as context so Gemini
                     extends/modifies rather than starting from scratch.
                     True (default) is accepted but has no effect when no dict
                     is provided. False disables prior graph injection.

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

    # Build prompt: enrichment mode when prior graph has nodes, fresh otherwise
    has_prior_nodes = (isinstance(prior_graph, dict)
                       and len(prior_graph.get("nodes", [])) > 0)
    if has_prior_nodes:
        prior_yaml = yaml.dump(prior_graph, default_flow_style=False,
                               allow_unicode=True)
        node_count = len(prior_graph.get("nodes", []))
        link_count = len(prior_graph.get("links", []))
        prompt = ENRICHMENT_PROMPT.format(
            node_count=node_count,
            link_count=link_count,
            prior_yaml=prior_yaml,
        )
    else:
        prompt = VISION_PROMPT
    if abstract:
        prompt += (
            f"\n\nPAPER ABSTRACT: {abstract}\n\n"
            "Compare what the GA communicates vs what the paper actually found. "
            "Flag any Spin (GA says something the data doesn't support) or missed key findings."
        )

    # Send to Gemini Vision
    try:
        response = model.generate_content(
            [
                prompt,
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
    parser.add_argument("--abstract", help="Paper abstract text for context")
    parser.add_argument("--abstract-file", help="Path to file containing abstract")
    parser.add_argument("image", nargs="?", help="Single GA image to analyze")
    args = parser.parse_args()

    abstract = _load_abstract(args.abstract, args.abstract_file)

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
        result = compare_ga_images(images, filenames, abstract=abstract)
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
        result = analyze_ga_image(data, os.path.basename(args.image), abstract=abstract)
        print(f"Graph saved: {result['saved_path']}")
    else:
        parser.print_help()
