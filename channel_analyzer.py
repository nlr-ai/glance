"""
Channel Analyzer — Enrich a GA's L3 graph with visual channel analysis.

Sends the GA image + its L3 graph + batches of 25 visual channels to Gemini.
For each channel, Gemini evaluates: is it used? how effectively? which nodes?
The enriched graph gets channel annotations on each node and link.

Usage:
    python channel_analyzer.py <ga_image_path> <graph_yaml_path> [--output enriched.yaml]
"""

import os
import sys
import yaml
import json
import time
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("channel_analyzer")

# Load env
_HERE = os.path.dirname(os.path.abspath(__file__))
_ENV = os.path.join(_HERE, ".env")
if os.path.exists(_ENV):
    with open(_ENV) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)


# ── Channel catalog (parsed from markdown) ──────────────────────────

def load_channel_catalog(path=None):
    """Parse the visual channel catalog markdown into a list of channel dicts."""
    if path is None:
        path = os.path.join(_HERE, "data", "visual_channel_catalog.md")

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    channels = []
    current = None
    section_stack = []

    for line in text.split("\n"):
        # Track section hierarchy
        if line.startswith("#### "):
            name = line.lstrip("#").strip()
            # Extract channel name (remove numbering like "1.1.1 ")
            clean = re.sub(r"^\d+(\.\d+)* ", "", name)
            current = {
                "id": clean.lower().replace(" ", "_").replace("/", "_"),
                "name": clean,
                "section": " > ".join(section_stack),
                "communicates": "",
                "speed": "",
                "glance_relevance": "",
            }
            channels.append(current)
        elif line.startswith("### "):
            section_stack = [line.lstrip("#").strip()]
        elif line.startswith("## "):
            section_stack = [line.lstrip("#").strip()]
        elif current:
            if line.startswith("- **Communicates:**"):
                current["communicates"] = line.split(":**", 1)[1].strip()
            elif line.startswith("- **Speed:**"):
                current["speed"] = line.split(":**", 1)[1].strip()
            elif line.startswith("- **GLANCE relevance:**"):
                current["glance_relevance"] = line.split(":**", 1)[1].strip()

    return channels


def batch_channels(channels, batch_size=25):
    """Split channels into batches."""
    for i in range(0, len(channels), batch_size):
        yield channels[i : i + batch_size]


# ── Gemini Analysis ─────────────────────────────────────────────────

CHANNEL_PROMPT_TEMPLATE = """You are analyzing a scientific Graphical Abstract (GA) against specific visual communication channels.

The GA's current L3 knowledge graph is:
```yaml
{graph_yaml}
```

Analyze the GA image against these {n_channels} visual channels:

{channel_list}

For EACH channel, respond in this YAML format:

```yaml
channels:
  - id: "{channel_id}"
    used: true/false
    effectiveness: 0.0-1.0  # how well this channel communicates its intended message
    nodes_affected:  # which graph nodes use this channel
      - node_id: "thing:1"
        role: "encodes hierarchy via bar length"
    issues: "description of any misuse or missed opportunity"
    recommendation: "specific fix if effectiveness < 0.7"
```

Rules:
- Be specific about which nodes use which channels
- effectiveness 0.0 = channel present but counterproductive, 0.5 = neutral, 1.0 = optimal use
- If a channel is NOT used, still note if it SHOULD be (missed opportunity)
- Focus on the 5-second comprehension window
- Reference Stevens' power law beta values where relevant
"""


def format_channel_batch(channels):
    """Format a batch of channels for the prompt."""
    lines = []
    for i, ch in enumerate(channels, 1):
        lines.append(f"{i}. **{ch['name']}**")
        if ch["communicates"]:
            lines.append(f"   Communicates: {ch['communicates'][:200]}")
        if ch["speed"]:
            lines.append(f"   Speed: {ch['speed'][:100]}")
        lines.append("")
    return "\n".join(lines)


def _resilient_yaml_parse(raw_text):
    """Parse YAML with progressive degradation strategies."""
    text = raw_text.strip()
    text = re.sub(r"^```ya?ml\s*\n", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*\n", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n```\s*$", "", text)

    # Strategy 1: direct parse
    try:
        parsed = yaml.safe_load(text)
        if isinstance(parsed, dict):
            return parsed
    except yaml.YAMLError:
        pass

    # Strategy 2: truncate from end until valid
    lines = text.split("\n")
    for trim in range(1, min(len(lines), 50)):
        try:
            result = yaml.safe_load("\n".join(lines[:-trim]))
            if isinstance(result, dict):
                logger.info(f"  YAML recovered by trimming {trim} lines")
                return result
        except yaml.YAMLError:
            continue

    # Strategy 3: extract individual channel blocks with regex
    # Each channel block starts with "  - id:" — extract them individually
    logger.info("  Attempting per-channel regex extraction...")
    channel_blocks = re.split(r"\n  - id:", text)
    channels = []
    for i, block in enumerate(channel_blocks):
        if i == 0 and "- id:" not in block:
            continue  # skip preamble
        block_text = "- id:" + block if i > 0 else block
        try:
            items = yaml.safe_load(block_text)
            if isinstance(items, list):
                channels.extend(items)
            elif isinstance(items, dict):
                channels.append(items)
        except yaml.YAMLError:
            # Strategy 4: extract fields with regex from this block
            ch = _regex_extract_channel(block)
            if ch:
                channels.append(ch)

    if channels:
        logger.info(f"  Recovered {len(channels)} channels via regex extraction")
        return {"channels": channels}

    # Strategy 5: return empty but log the raw for debugging
    logger.warning("  All parse strategies failed")
    return None


def _regex_extract_channel(block):
    """Last-resort: extract channel fields with regex patterns."""
    ch = {}
    # id
    m = re.search(r'id:\s*"?([^"\n]+)"?', block)
    if m:
        ch["id"] = m.group(1).strip()
    # used
    m = re.search(r'used:\s*(true|false)', block, re.IGNORECASE)
    if m:
        ch["used"] = m.group(1).lower() == "true"
    # effectiveness
    m = re.search(r'effectiveness:\s*([0-9.]+)', block)
    if m:
        ch["effectiveness"] = float(m.group(1))
    # issues
    m = re.search(r'issues:\s*"?([^"\n]{5,})"?', block)
    if m:
        ch["issues"] = m.group(1).strip()
    # recommendation
    m = re.search(r'recommendation:\s*"?([^"\n]{5,})"?', block)
    if m:
        ch["recommendation"] = m.group(1).strip()

    return ch if ch.get("id") else None


def analyze_batch(image_bytes, mime_type, graph_yaml, channels, model,
                  max_retries=2):
    """Send one batch of channels to Gemini for analysis. Self-healing on failure."""
    channel_list = format_channel_batch(channels)
    prompt = CHANNEL_PROMPT_TEMPLATE.format(
        graph_yaml=graph_yaml,
        n_channels=len(channels),
        channel_list=channel_list,
        channel_id=channels[0]["id"],
    )

    for attempt in range(max_retries + 1):
        try:
            response = model.generate_content(
                [prompt, {"mime_type": mime_type, "data": image_bytes}],
                generation_config={"temperature": 0.2, "max_output_tokens": 8192},
            )
            raw = response.text
        except Exception as e:
            logger.error(f"  Gemini API error (attempt {attempt+1}): {e}")
            if attempt < max_retries:
                time.sleep(5 * (attempt + 1))
                continue
            return {"channels": []}

        parsed = _resilient_yaml_parse(raw)
        if parsed is not None:
            return parsed

        # Self-heal: retry with smaller batch (split in half)
        if attempt < max_retries and len(channels) > 5:
            logger.info(f"  Retrying with smaller batch ({len(channels)}→{len(channels)//2})...")
            mid = len(channels) // 2
            r1 = analyze_batch(image_bytes, mime_type, graph_yaml,
                               channels[:mid], model, max_retries=0)
            time.sleep(3)
            r2 = analyze_batch(image_bytes, mime_type, graph_yaml,
                               channels[mid:], model, max_retries=0)
            merged = r1.get("channels", []) + r2.get("channels", [])
            return {"channels": merged}

        if attempt < max_retries:
            logger.info(f"  Retry {attempt+2}/{max_retries+1}...")
            time.sleep(4)

    logger.warning("  All retries exhausted, returning empty")
    return {"channels": []}


# ── Enrichment ──────────────────────────────────────────────────────

def enrich_graph(graph, all_channel_results):
    """Merge channel analysis results back into the graph nodes."""
    # Build node lookup
    nodes = {n["id"]: n for n in graph.get("nodes", [])}

    # Aggregate channel data per node
    node_channels = {}  # node_id -> list of channel annotations
    all_analyzed = []

    for batch_result in all_channel_results:
        for ch in batch_result.get("channels", []):
            ch_entry = {
                "channel": ch.get("id", "unknown"),
                "used": ch.get("used", False),
                "effectiveness": ch.get("effectiveness", 0),
                "issues": ch.get("issues", ""),
                "recommendation": ch.get("recommendation", ""),
            }
            all_analyzed.append(ch_entry)

            for na in ch.get("nodes_affected", []):
                nid = na.get("node_id", "")
                if nid not in node_channels:
                    node_channels[nid] = []
                node_channels[nid].append({
                    "channel": ch.get("id"),
                    "effectiveness": ch.get("effectiveness", 0),
                    "role": na.get("role", ""),
                })

    # Inject into graph nodes
    for node in graph.get("nodes", []):
        nid = node["id"]
        if nid in node_channels:
            node["visual_channels"] = node_channels[nid]
            # Compute channel score = avg effectiveness
            effs = [c["effectiveness"] for c in node_channels[nid]]
            node["channel_score"] = round(sum(effs) / len(effs), 3) if effs else 0

    # Add summary to graph metadata
    used = [c for c in all_analyzed if c.get("used")]
    unused_opportunities = [c for c in all_analyzed if not c.get("used") and c.get("recommendation")]
    low_eff = [c for c in used if c.get("effectiveness", 1) < 0.5]

    graph.setdefault("metadata", {})
    graph["metadata"]["channel_analysis"] = {
        "total_channels_analyzed": len(all_analyzed),
        "channels_used": len(used),
        "channels_unused": len(all_analyzed) - len(used),
        "low_effectiveness": len(low_eff),
        "missed_opportunities": len(unused_opportunities),
        "avg_effectiveness": round(
            sum(c["effectiveness"] for c in used) / len(used), 3
        ) if used else 0,
    }
    graph["metadata"]["channel_details"] = all_analyzed

    # Anti-pattern detection on important nodes (w >= 0.6)
    IMPORTANCE_THRESHOLD = 0.6
    anti_patterns = []

    for node in graph.get("nodes", []):
        w = node.get("weight", 0)
        if w < IMPORTANCE_THRESHOLD:
            continue

        channels = node.get("visual_channels", [])
        n_ch = len(channels)

        # 1. FRAGILE: important node with < 2 channels (no redundancy)
        if n_ch < 2:
            if n_ch == 0:
                issue = f"Text-only (w={w:.2f}) — no visual encoding"
            else:
                issue = f"Single-channel (w={w:.2f}) — only '{channels[0]['channel']}', no redundancy"
            anti_patterns.append({
                "type": "fragile",
                "node_id": node["id"],
                "name": node["name"],
                "weight": w,
                "severity": "HIGH" if w >= 0.8 else "MEDIUM",
                "issue": issue,
                "fix": "Add a second independent channel for congruent encoding",
            })

        # 2. INCONGRUENT: channels point to DIFFERENT MEANINGS
        # Not about importance level (that's Warp), but about semantic conflict.
        # E.g., color says "danger/pathology" but position says "positive result".
        # Detected via conflicting roles — channels whose "role" descriptions
        # imply opposing semantics on the same node.
        # We flag nodes where channels have high effectiveness spread AND
        # the roles contain opposing semantic cues.
        if n_ch >= 2:
            roles = [c.get("role", "") for c in channels]
            # Check for semantic opposition in roles
            positive_cues = ["positive", "success", "good", "solution", "healthy", "protected", "result"]
            negative_cues = ["negative", "danger", "problem", "damage", "patholog", "risk", "warning"]
            has_positive = any(any(cue in r.lower() for cue in positive_cues) for r in roles if r)
            has_negative = any(any(cue in r.lower() for cue in negative_cues) for r in roles if r)

            if has_positive and has_negative:
                pos_ch = [c["channel"] for c in channels
                          if any(cue in c.get("role", "").lower() for cue in positive_cues)]
                neg_ch = [c["channel"] for c in channels
                          if any(cue in c.get("role", "").lower() for cue in negative_cues)]
                anti_patterns.append({
                    "type": "incongruent",
                    "node_id": node["id"],
                    "name": node["name"],
                    "weight": w,
                    "severity": "HIGH",
                    "issue": f"Semantic conflict: {', '.join(neg_ch)} signal negative meaning while {', '.join(pos_ch)} signal positive on the same node",
                    "fix": "Align all channels to a single semantic direction — the node can't be both 'danger' and 'success'",
                })

            # 3. INVERSE: node importance vs channel signal mismatch
            # High-weight node (w >= 0.8) but avg channel effectiveness < 0.5
            # = the GA visually demotes something that should be prominent
            avg_eff = sum(effs) / len(effs)
            if w >= 0.8 and avg_eff < 0.5:
                anti_patterns.append({
                    "type": "inverse",
                    "node_id": node["id"],
                    "name": node["name"],
                    "weight": w,
                    "avg_effectiveness": round(avg_eff, 2),
                    "severity": "HIGH",
                    "issue": f"Visual demotion: node is important (w={w:.2f}) but channels average {avg_eff:.2f}",
                    "fix": "Increase visual prominence — larger size, stronger color, better position",
                })

    if anti_patterns:
        graph["metadata"]["anti_patterns"] = anti_patterns
        n_frag = sum(1 for a in anti_patterns if a["type"] == "fragile")
        n_inc = sum(1 for a in anti_patterns if a["type"] == "incongruent")
        n_inv = sum(1 for a in anti_patterns if a["type"] == "inverse")
        logger.warning(f"Anti-patterns: {n_frag} fragile, {n_inc} incongruent, {n_inv} inverse")

    return graph


# ── Main ────────────────────────────────────────────────────────────

def analyze_ga_channels(image_path, graph_path, output_path=None):
    """Full pipeline: load image + graph, batch-analyze channels, enrich graph."""
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-2.5-pro"))

    # Load image
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/png")

    # Load graph
    with open(graph_path, "r", encoding="utf-8") as f:
        graph = yaml.safe_load(f)

    graph_yaml = yaml.dump(graph, default_flow_style=False, allow_unicode=True)

    # Load channels
    channels = load_channel_catalog()
    logger.info(f"Loaded {len(channels)} visual channels from catalog")

    # Batch analyze
    batches = list(batch_channels(channels, 25))
    all_results = []

    for i, batch in enumerate(batches):
        logger.info(f"Analyzing batch {i+1}/{len(batches)} ({len(batch)} channels)...")
        try:
            result = analyze_batch(image_bytes, mime_type, graph_yaml, batch, model)
            all_results.append(result)
            logger.info(f"  Got {len(result.get('channels', []))} channel results")
        except Exception as e:
            logger.error(f"  Batch {i+1} failed: {e}")
            all_results.append({"channels": []})

        # Rate limit
        if i < len(batches) - 1:
            time.sleep(4)

    # Enrich
    enriched = enrich_graph(graph, all_results)

    # Save
    if output_path is None:
        base = os.path.splitext(graph_path)[0]
        output_path = f"{base}_enriched.yaml"

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(enriched, f, default_flow_style=False, allow_unicode=True)

    summary = enriched["metadata"]["channel_analysis"]
    logger.info(f"Done. {summary['channels_used']}/{summary['total_channels_analyzed']} channels used, "
                f"avg effectiveness {summary['avg_effectiveness']:.2f}")
    logger.info(f"Enriched graph saved: {output_path}")

    return enriched


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze GA visual channels")
    parser.add_argument("image", help="Path to GA image")
    parser.add_argument("graph", help="Path to L3 graph YAML")
    parser.add_argument("--output", "-o", help="Output enriched YAML path")
    args = parser.parse_args()

    analyze_ga_channels(args.image, args.graph, args.output)
