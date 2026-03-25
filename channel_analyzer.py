"""
Channel Analyzer — Enrich a GA's L3 graph with visual channel analysis.

Sends the GA image + its L3 graph + batches of 25 visual channels to Gemini.
For each channel, Gemini evaluates: is it used? how effectively? which nodes?
The enriched graph gets channel annotations on each node and link.

Optional: pass `abstract` (paper abstract text) so Gemini can judge whether
channels encode the RIGHT information (not just whether they're used effectively).

Usage:
    python channel_analyzer.py <ga_image_path> <graph_yaml_path> [--output enriched.yaml]
    python channel_analyzer.py <ga_image_path> <graph_yaml_path> --abstract "Paper abstract text..."
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
    # Extract YAML from mixed text+YAML response
    yaml_match = re.search(r"```ya?ml\s*\n(.+?)```", text, re.DOTALL | re.IGNORECASE)
    if yaml_match:
        text = yaml_match.group(1).strip()
    else:
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
                  max_retries=2, abstract=None, prior_graph=True):
    """Send one batch of channels to Gemini for analysis. Self-healing on failure.

    Args:
        abstract: Optional paper abstract. When provided, Gemini judges whether
                  channels encode the RIGHT information, not just effectiveness.
        prior_graph: When True (default), includes graph_yaml in the prompt as
                     context. When False, omits the graph from the prompt.
    """
    channel_list = format_channel_batch(channels)
    effective_graph_yaml = graph_yaml if prior_graph else "(no prior graph provided)"
    prompt = CHANNEL_PROMPT_TEMPLATE.format(
        graph_yaml=effective_graph_yaml,
        n_channels=len(channels),
        channel_list=channel_list,
        channel_id=channels[0]["id"],
    )

    if abstract:
        prompt += (
            f"\n\nPAPER ABSTRACT: {abstract}\n\n"
            "Use this abstract to judge whether each channel encodes the RIGHT information — "
            "not just whether it's used effectively. Flag channels that visually emphasize "
            "something the paper doesn't support (Spin) or that miss key findings."
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
                               channels[:mid], model, max_retries=0, abstract=abstract,
                               prior_graph=prior_graph)
            time.sleep(3)
            r2 = analyze_batch(image_bytes, mime_type, graph_yaml,
                               channels[mid:], model, max_retries=0, abstract=abstract,
                               prior_graph=prior_graph)
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

    # 4. MISSING_CATEGORY: GA-level anti-pattern
    # The GA doesn't use entire FAMILIES of visual channels.
    # Each family should have at least 1 channel used for a well-rounded GA.
    CHANNEL_FAMILIES = {
        "color": ["color_hue", "color_saturation", "color_luminance"],
        "form": ["orientation", "size", "shape", "curvature", "line_termination"],
        "grouping": ["closure", "spatial_position", "proximity", "similarity",
                      "continuity", "common_region", "connectedness"],
        "depth": ["figure-ground_segregation", "stereo_depth"],
    }

    used_channel_ids = {c.get("channel", "") for c in all_analyzed if c.get("used")}
    for family_name, family_channels in CHANNEL_FAMILIES.items():
        family_used = [ch for ch in family_channels if ch in used_channel_ids]
        if not family_used:
            anti_patterns.append({
                "type": "missing_category",
                "scope": "ga",
                "category": family_name,
                "severity": "MEDIUM" if family_name == "depth" else "HIGH",
                "issue": f"Entire '{family_name}' channel family unused — {len(family_channels)} channels available but none exploited",
                "fix": f"Add at least one {family_name} channel: {', '.join(family_channels[:3])}",
                "available": family_channels,
            })

    if anti_patterns:
        graph["metadata"]["anti_patterns"] = anti_patterns
        n_frag = sum(1 for a in anti_patterns if a["type"] == "fragile")
        n_inc = sum(1 for a in anti_patterns if a["type"] == "incongruent")
        n_inv = sum(1 for a in anti_patterns if a["type"] == "inverse")
        n_miss = sum(1 for a in anti_patterns if a["type"] == "missing_category")
        logger.warning(f"Anti-patterns: {n_frag} fragile, {n_inc} incongruent, {n_inv} inverse, {n_miss} missing_category")

    return graph


# ── Main ────────────────────────────────────────────────────────────

def analyze_ga_channels(image_path, graph_path, output_path=None, abstract=None,
                        prior_graph=True):
    """Full pipeline: load image + graph, batch-analyze channels, enrich graph.

    Args:
        image_path: Path to GA image file.
        graph_path: Path to L3 graph YAML file.
        output_path: Optional output path for enriched graph.
        abstract: Optional paper abstract text. When provided, Gemini judges
                  whether channels encode the RIGHT information.
        prior_graph: When True (default), the existing graph YAML is included
                     in the Gemini prompt as context. Set False to analyze
                     channels without prior graph context.
    """
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
            result = analyze_batch(image_bytes, mime_type, graph_yaml, batch, model, abstract=abstract,
                                      prior_graph=prior_graph)
            all_results.append(result)
            n_ch = len(result.get('channels', []))
            logger.info(f"  Got {n_ch} channel results")

            # ── Inter-batch self-healing ──
            # After each batch, do a partial enrichment to validate + heal
            if n_ch > 0:
                # Validate: clamp effectiveness to [0, 1]
                for ch in result.get("channels", []):
                    eff = ch.get("effectiveness", 0)
                    if not isinstance(eff, (int, float)):
                        ch["effectiveness"] = 0
                    else:
                        ch["effectiveness"] = max(0, min(1, eff))

                # Heal: fill missing fields with defaults
                for ch in result.get("channels", []):
                    ch.setdefault("used", False)
                    ch.setdefault("effectiveness", 0)
                    ch.setdefault("nodes_affected", [])
                    ch.setdefault("issues", "")
                    ch.setdefault("recommendation", "")

                # Feed partial results back into graph_yaml for next batch
                # so Gemini sees what channels were already detected
                partial = enrich_graph(
                    yaml.safe_load(yaml.dump(graph)),  # deep copy
                    all_results,
                )
                graph_yaml = yaml.dump(partial, default_flow_style=False, allow_unicode=True)
                logger.info(f"  Graph updated with {n_ch} channels for next batch context")

        except Exception as e:
            logger.error(f"  Batch {i+1} failed: {e}")
            all_results.append({"channels": []})

        # Rate limit
        if i < len(batches) - 1:
            time.sleep(4)

    # Final enrichment with all results
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


COMPARE_CHANNELS_PROMPT = """You are comparing the visual channel usage of {n} Graphical Abstracts (GAs).

Below are the channel analysis results for each GA.

{per_image_sections}

Generate a DELTA report comparing how these GAs use visual channels differently.

Return ONLY valid YAML:

delta:
  a_vs_b:
    channels_only_in_a:
      - channel: "channel_id"
        effectiveness: 0.0-1.0
        significance: "why this matters"
    channels_only_in_b:
      - channel: "channel_id"
        effectiveness: 0.0-1.0
        significance: "why this matters"
    a_more_effective:
      - channel: "channel_id"
        a_effectiveness: 0.0-1.0
        b_effectiveness: 0.0-1.0
        why: "explanation"
    b_more_effective:
      - channel: "channel_id"
        a_effectiveness: 0.0-1.0
        b_effectiveness: 0.0-1.0
        why: "explanation"
    anti_patterns_only_in_a:
      - pattern: "description"
        severity: "HIGH/MEDIUM/LOW"
    anti_patterns_only_in_b:
      - pattern: "description"
        severity: "HIGH/MEDIUM/LOW"
{extra_pairs}
  overall_winner: "A or B{or_c}"
  winner_rationale: "why this GA uses visual channels most effectively"
  key_insight: "the most important difference between these GAs' channel strategies"
"""


def compare_channels(image_paths: list, graph_paths: list, output_path=None, abstract=None,
                     prior_graph=True) -> dict:
    """Run channel analysis on each image independently, then generate a DELTA report.

    Args:
        image_paths: list of 2 or 3 image file paths
        graph_paths: list of 2 or 3 corresponding graph YAML paths
        output_path: Optional output path for the comparison report.
        abstract: Optional paper abstract text for scientific accuracy context.
        prior_graph: When True (default), includes existing graph YAML in
                     the Gemini prompt as context for iterative enrichment.

    Returns:
        dict with keys: per_image (list of enriched graphs), delta (comparison dict)
    """
    import google.generativeai as genai

    n = len(image_paths)
    if n < 2 or n > 3:
        raise ValueError(f"compare_channels requires 2 or 3 image/graph pairs, got {n}")
    if len(graph_paths) != n:
        raise ValueError(f"Number of images ({n}) must match number of graphs ({len(graph_paths)})")

    for i, (ip, gp) in enumerate(zip(image_paths, graph_paths)):
        if not os.path.exists(ip):
            raise FileNotFoundError(f"Image file not found: {ip}")
        if not os.path.exists(gp):
            raise FileNotFoundError(f"Graph file not found: {gp}")

    # Step 1: Run channel analysis on each image independently
    per_image = []
    for i, (img_path, grp_path) in enumerate(zip(image_paths, graph_paths)):
        label = chr(65 + i)
        logger.info(f"Analyzing channels for image {label}: {img_path}")
        enriched = analyze_ga_channels(img_path, grp_path, abstract=abstract,
                                          prior_graph=prior_graph)
        per_image.append(enriched)
        if i < n - 1:
            time.sleep(2)

    # Step 2: Build per-image summaries for the delta prompt
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-2.5-pro"))

    sections = []
    for i, enriched in enumerate(per_image):
        label = chr(65 + i)
        fname = os.path.basename(image_paths[i])
        ch_analysis = enriched.get("metadata", {}).get("channel_analysis", {})
        ch_details = enriched.get("metadata", {}).get("channel_details", [])
        anti_patterns = enriched.get("metadata", {}).get("anti_patterns", [])

        used_channels = [c for c in ch_details if c.get("used")]
        used_summary = yaml.dump(used_channels[:30], default_flow_style=False, allow_unicode=True)
        anti_summary = yaml.dump(anti_patterns, default_flow_style=False, allow_unicode=True) if anti_patterns else "none"

        sections.append(
            f"--- Image {label} ({fname}) ---\n"
            f"Channels used: {ch_analysis.get('channels_used', 0)}/{ch_analysis.get('total_channels_analyzed', 0)}\n"
            f"Avg effectiveness: {ch_analysis.get('avg_effectiveness', 0)}\n"
            f"Used channels:\n{used_summary}\n"
            f"Anti-patterns:\n{anti_summary}\n"
        )

    or_c = " or C" if n == 3 else ""
    extra_pairs = ""
    if n == 3:
        extra_pairs = (
            "  a_vs_c:\n"
            "    channels_only_in_a: [...]\n    channels_only_in_c: [...]\n"
            "    a_more_effective: [...]\n    c_more_effective: [...]\n"
            "    anti_patterns_only_in_a: [...]\n    anti_patterns_only_in_c: [...]\n"
            "  b_vs_c:\n"
            "    channels_only_in_b: [...]\n    channels_only_in_c: [...]\n"
            "    b_more_effective: [...]\n    c_more_effective: [...]\n"
            "    anti_patterns_only_in_b: [...]\n    anti_patterns_only_in_c: [...]\n"
        )

    prompt = COMPARE_CHANNELS_PROMPT.format(
        n=n,
        per_image_sections="\n".join(sections),
        extra_pairs=extra_pairs,
        or_c=or_c,
    )

    logger.info("Generating delta report...")
    try:
        response = model.generate_content(
            [prompt],
            generation_config={"temperature": 0.2, "max_output_tokens": 8192},
        )
        raw = response.text
    except Exception as e:
        logger.error(f"Gemini API error generating delta: {e}")
        return {"per_image": per_image, "delta": {"error": str(e)}}

    delta_parsed = _resilient_yaml_parse(raw)
    if delta_parsed is None:
        logger.error(
            "Failed to parse delta report from Gemini. "
            f"Response was {len(raw)} chars. "
            "This usually means the channel summaries were too large for structured output."
        )
        delta_parsed = {"error": "YAML parse failed — see logs for raw response details"}

    delta = delta_parsed.get("delta", delta_parsed)

    # Save comparison
    if output_path is None:
        base_names = "_vs_".join(
            os.path.splitext(os.path.basename(p))[0][:15] for p in image_paths
        )
        output_path = os.path.join(_HERE, "data", f"channel_compare_{base_names}.yaml")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    save_data = {"per_image_summaries": [], "delta": delta}
    for i, enriched in enumerate(per_image):
        label = chr(65 + i)
        save_data["per_image_summaries"].append({
            "label": label,
            "image": os.path.basename(image_paths[i]),
            "channel_analysis": enriched.get("metadata", {}).get("channel_analysis", {}),
        })

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(save_data, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"Channel comparison saved: {output_path}")

    return {"per_image": per_image, "delta": delta}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze GA visual channels")
    parser.add_argument("--compare", nargs="+", metavar="PATH",
                        help="Compare 2-3 GAs: --compare img_a.png graph_a.yaml img_b.png graph_b.yaml [img_c.png graph_c.yaml]")
    parser.add_argument("--abstract", help="Paper abstract text for context")
    parser.add_argument("--abstract-file", help="Path to file containing abstract")
    parser.add_argument("image", nargs="?", help="Path to GA image (single mode)")
    parser.add_argument("graph", nargs="?", help="Path to L3 graph YAML (single mode)")
    parser.add_argument("--output", "-o", help="Output path")
    args = parser.parse_args()

    abstract = _load_abstract(args.abstract, args.abstract_file,
                              args.graph if hasattr(args, 'graph') else None)

    if args.compare:
        paths = args.compare
        if len(paths) not in (4, 6):
            parser.error(
                "--compare requires pairs of (image, graph): "
                "4 paths for A/B comparison, 6 paths for A/B/C. "
                f"Got {len(paths)} paths."
            )
        n = len(paths) // 2
        image_paths = [paths[i * 2] for i in range(n)]
        graph_paths = [paths[i * 2 + 1] for i in range(n)]
        result = compare_channels(image_paths, graph_paths, args.output, abstract=abstract)
        delta = result.get("delta", {})
        print(f"\nOverall winner: {delta.get('overall_winner', 'N/A')}")
        print(f"Rationale: {delta.get('winner_rationale', 'N/A')}")
        print(f"Key insight: {delta.get('key_insight', 'N/A')}")
    elif args.image and args.graph:
        analyze_ga_channels(args.image, args.graph, args.output, abstract=abstract)
    else:
        parser.print_help()
