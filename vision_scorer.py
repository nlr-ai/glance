"""GLANCE Vision Scorer — Gemini Pro Vision API -> L3 Graph + Analysis.

Sends a GA image to Gemini Vision, receives structured YAML analysis,
validates it, and saves the resulting L3 graph.

Model: Gemini Pro (default: gemini-2.5-pro-preview-06-05) via GEMINI_MODEL env var.
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
    # Strip markdown fences if present
    text = raw_text.strip()
    text = re.sub(r'^```ya?ml\s*\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^```\s*\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n```\s*$', '', text)

    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as e:
        logger.error(f"YAML parse error: {e}")
        # Try line-by-line cleanup: remove lines that break YAML
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            # Skip lines with unbalanced quotes that break parsing
            try:
                yaml.safe_load(line)
                cleaned.append(line)
            except yaml.YAMLError:
                cleaned.append(line)
        try:
            parsed = yaml.safe_load("\n".join(cleaned))
        except yaml.YAMLError:
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
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro-preview-06-05")
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
                "max_output_tokens": 4096,
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
