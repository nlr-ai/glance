"""
GA Rubber Duck — Creative visual exploration of GA components.

Two modes:
1. RUBBER DUCK: For each visual channel, ask a synesthetic question about a component.
   "If [component] was a texture, which one? Why?"
   "If [component] was a color temperature, warm or cold? Why?"
   Forces lateral thinking about visual encoding.

2. SANDBOX: Decline a single concept across ALL visual channels at once.
   Input: "OM-85 clinical dominance"
   Output: a matrix of all possible visual encodings for that concept.
   Like a visual thesaurus — not "how should I?" but "here are ALL ways you COULD."

Optional: pass `abstract` (paper abstract text) so creative suggestions are
scientifically relevant — Gemini can ground its explorations in the actual findings.

Usage:
    # Rubber duck a specific component
    python ga_rubber_duck.py duck <image> <graph> "Tissue Damage Cascade"

    # Sandbox: explore all encodings for a concept
    python ga_rubber_duck.py sandbox <image> <graph> "OM-85 has the strongest clinical evidence"

    # Full rubber duck: all components × all channels
    python ga_rubber_duck.py full <image> <graph>
"""

import os
import sys
import yaml
import re
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("rubber_duck")

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


# ── Channel families for rubber duck questions ──────────────────────

CHANNEL_QUESTIONS = [
    {
        "family": "color",
        "channels": ["hue", "saturation", "luminance", "temperature"],
        "questions": [
            "Si {component} était une couleur, laquelle ? Pourquoi ?",
            "Si {component} était une température de couleur (chaud/froid), laquelle ? Que communiquerait-elle ?",
            "Quelle luminosité (clair/foncé) devrait avoir {component} pour refléter son importance ?",
            "Quelle saturation ? Vif = urgent, pastel = secondaire, gris = neutre. Où se situe {component} ?",
        ],
    },
    {
        "family": "form",
        "channels": ["shape", "size", "orientation", "curvature", "texture"],
        "questions": [
            "Si {component} était une forme géométrique, laquelle ? Cercle (doux/complet), carré (stable/rigide), triangle (direction/danger) ?",
            "Quelle taille relative devrait avoir {component} ? Le plus gros = le plus important. Quel % de l'espace total ?",
            "Si {component} avait une orientation (horizontal/vertical/diagonal), laquelle communiquerait le mieux son rôle ?",
            "Courbe ou angulaire ? Les courbes = organique/naturel, les angles = technique/tension. Qu'est {component} ?",
            "Si {component} était une texture (lisse/rugueux/granuleux/hachuré/pointillé), laquelle ? Pourquoi ?",
        ],
    },
    {
        "family": "position",
        "channels": ["spatial_position", "proximity", "enclosure", "layering"],
        "questions": [
            "Où devrait être {component} sur la page ? Haut-gauche = premier lu, centre = focal, bas-droite = conclusion. Où ?",
            "Près de quels autres éléments devrait être {component} ? La proximité crée l'association.",
            "Est-ce que {component} devrait être dans un cadre/boîte (enclosure) ou flottant librement ?",
            "Au premier plan ou en arrière-plan ? Devant = actif, derrière = contexte. Quel layer pour {component} ?",
        ],
    },
    {
        "family": "dynamics",
        "channels": ["direction", "flow", "rhythm", "contrast"],
        "questions": [
            "Si {component} était un mouvement, dans quelle direction irait-il ? ↑ croissance, ↓ déclin, → progression, ← régression ?",
            "Si {component} était un rythme (régulier/irrégulier/accéléré/ralenti), lequel refléterait son message ?",
            "Quel niveau de contraste entre {component} et son voisin ? Fort contraste = rupture, faible = continuité.",
        ],
    },
    {
        "family": "semantics",
        "channels": ["metaphor", "icon", "annotation", "redundancy"],
        "questions": [
            "Quelle métaphore visuelle incarnerait {component} ? (bouclier, flèche, pont, mur, flamme, vague, arbre, chaîne...)",
            "Si {component} devait être représenté par un seul icône 32×32px, lequel ?",
            "Est-ce que {component} a besoin de texte pour être compris, ou peut-il être purement visuel ?",
            "Combien de canaux redondants pour {component} ? 1 = fragile, 2 = robuste, 3 = impossible à rater.",
        ],
    },
]


DUCK_PROMPT = """Tu es un expert en communication visuelle. On fait un exercice de "rubber duck" créatif sur un Graphical Abstract scientifique.

Le GA actuel est montré dans l'image. Son graph L3 est :
```yaml
{graph_yaml}
```

Je vais te poser des questions synesthésiques sur le composant "{component}" (node: {node_info}).

Pour CHAQUE question, réponds en YAML avec :
- La réponse créative (1-2 phrases)
- Le canal visuel impliqué
- Comment l'implémenter concrètement dans le GA
- L'impact attendu sur les métriques GLANCE

Questions :
{questions}

Réponds en YAML :
```yaml
responses:
  - question: "..."
    answer: "..."
    channel: "color_hue"
    implementation: "Change X to Y in the compositor"
    impact: "S9b +0.05 expected"
```
"""


SANDBOX_PROMPT = """Tu es un expert en communication visuelle. On explore TOUTES les façons possibles d'encoder un concept dans un Graphical Abstract.

Le GA actuel est montré dans l'image. Son graph L3 est :
```yaml
{graph_yaml}
```

Le concept à décliner : "{concept}"

Pour CHAQUE canal visuel ci-dessous, propose une façon concrète d'encoder ce concept.
C'est un bac à sable — pas de filtre, toutes les idées même folles.

Canaux à explorer :
1. Couleur (hue, saturation, luminance, température)
2. Forme (shape, taille, orientation, courbure)
3. Texture (lisse, rugueux, hachuré, pointillé, grain)
4. Position (où sur la page, proximity, enclosure, layer)
5. Mouvement/Direction (flèche, flow, rythme)
6. Métaphore (icône, symbole, analogie visuelle)
7. Typographie (poids, taille, style, casse)
8. Contraste (avec quoi, comment, intensité)
9. Redondance (combiner 2-3 canaux pour un message inarratable)
10. Anti-pattern (ce qu'il ne faut SURTOUT PAS faire pour ce concept)

Réponds en YAML :
```yaml
concept: "{concept}"
encodings:
  - channel: "color_hue"
    proposal: "..."
    why: "..."
    risk: "..."
  - channel: "shape"
    proposal: "..."
    why: "..."
    risk: "..."
  ...
best_combination: "Les 3 canaux qui ensemble rendent ce concept inarratable"
worst_trap: "L'erreur la plus fréquente pour encoder ce concept"
```
"""


def _resilient_yaml_parse(raw_text):
    """Parse YAML with degradation. Logs WHY it failed."""
    text = raw_text.strip()
    # Extract YAML block from mixed text+YAML response
    yaml_match = re.search(r"```ya?ml\s*\n(.+?)```", text, re.DOTALL | re.IGNORECASE)
    if yaml_match:
        text = yaml_match.group(1).strip()
    else:
        # Fallback: strip fences if at start/end
        text = re.sub(r"^```ya?ml\s*\n", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^```\s*\n", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\n```\s*$", "", text)

    # Strategy 1: direct
    try:
        parsed = yaml.safe_load(text)
        if isinstance(parsed, dict):
            return parsed
        logger.warning(f"  YAML parsed but got {type(parsed).__name__}, not dict")
    except yaml.YAMLError as e:
        logger.warning(f"  Direct YAML parse failed: {str(e)[:120]}")

    # Strategy 2: truncate
    lines = text.split("\n")
    logger.info(f"  Response was {len(lines)} lines, {len(text)} chars. Trying truncation...")
    for trim in range(1, min(len(lines), 50)):
        try:
            result = yaml.safe_load("\n".join(lines[:-trim]))
            if isinstance(result, dict):
                logger.info(f"  Recovered by trimming {trim} lines")
                return result
        except yaml.YAMLError:
            continue

    # Log first/last lines for debugging
    logger.error(f"  All parse strategies failed. First 3 lines: {lines[:3]}")
    logger.error(f"  Last 3 lines: {lines[-3:]}")
    logger.error(f"  Total length: {len(text)} chars, {len(lines)} lines")

    # Save raw for debugging
    debug_path = os.path.join(_HERE, "data", f"_debug_rubber_duck_{int(time.time())}.txt")
    with open(debug_path, "w", encoding="utf-8") as f:
        f.write(raw_text)
    logger.error(f"  Raw response saved to {debug_path}")

    return None


def _load_gemini():
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    return genai.GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-2.5-pro"))


def _load_image(path):
    with open(path, "rb") as f:
        data = f.read()
    ext = os.path.splitext(path)[1].lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(ext, "image/png")
    return data, mime


def rubber_duck(image_path, graph_path, component_name, output_path=None, abstract=None,
                prior_graph=True):
    """Ask synesthetic questions about one component across all channel families.

    Args:
        image_path: Path to GA image file.
        graph_path: Path to L3 graph YAML file.
        component_name: Name of the component to explore.
        output_path: Optional output path.
        abstract: Optional paper abstract text for scientific grounding.
        prior_graph: When True (default), includes the existing graph YAML in
                     the Gemini prompt as context for iterative exploration.
    """
    model = _load_gemini()
    image_bytes, mime = _load_image(image_path)

    with open(graph_path) as f:
        graph = yaml.safe_load(f)
    graph_yaml = yaml.dump(graph, default_flow_style=False, allow_unicode=True)

    # Find the node
    node = None
    for n in graph.get("nodes", []):
        if component_name.lower() in n.get("name", "").lower():
            node = n
            break
    node_info = f"{node['id']} (w={node['weight']}, e={node['energy']})" if node else "not found in graph"

    # Collect all questions for this component
    all_questions = []
    for family in CHANNEL_QUESTIONS:
        for q in family["questions"]:
            all_questions.append(q.format(component=component_name))

    questions_text = "\n".join(f"{i+1}. {q}" for i, q in enumerate(all_questions))

    effective_graph_yaml = graph_yaml[:3000] if prior_graph else "(no prior graph provided)"
    prompt = DUCK_PROMPT.format(
        graph_yaml=effective_graph_yaml,
        component=component_name,
        node_info=node_info,
        questions=questions_text,
    )

    if abstract:
        prompt += (
            f"\n\nPAPER ABSTRACT: {abstract}\n\n"
            "Ground your creative suggestions in the paper's actual findings. "
            "Ensure proposed visual encodings accurately represent the science."
        )

    logger.info(f"Rubber duck: '{component_name}' × {len(all_questions)} questions")

    response = model.generate_content(
        [prompt, {"mime_type": mime, "data": image_bytes}],
        generation_config={"temperature": 0.5, "max_output_tokens": 8192},
    )

    parsed = _resilient_yaml_parse(response.text)
    if not parsed:
        logger.error("Failed to parse response")
        return None

    # Print results
    for r in parsed.get("responses", []):
        print(f"\n  Q: {r.get('question', '')[:80]}")
        print(f"  A: {r.get('answer', '')}")
        print(f"  → {r.get('channel', '')} | {r.get('implementation', '')[:60]}")

    # Save
    if output_path is None:
        base = os.path.splitext(graph_path)[0]
        output_path = f"{base}_duck_{component_name.replace(' ', '_')[:20]}.yaml"
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(parsed, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"Saved: {output_path}")
    return parsed


def sandbox(image_path, graph_path, concept, output_path=None, abstract=None,
            prior_graph=True):
    """Decline a concept across ALL possible visual encodings.

    Args:
        image_path: Path to GA image file.
        graph_path: Path to L3 graph YAML file.
        concept: The concept to explore encodings for.
        output_path: Optional output path.
        abstract: Optional paper abstract text for scientific grounding.
        prior_graph: When True (default), includes the existing graph YAML in
                     the Gemini prompt as context for iterative exploration.
    """
    model = _load_gemini()
    image_bytes, mime = _load_image(image_path)

    with open(graph_path) as f:
        graph = yaml.safe_load(f)
    graph_yaml = yaml.dump(graph, default_flow_style=False, allow_unicode=True)

    effective_graph_yaml = graph_yaml[:3000] if prior_graph else "(no prior graph provided)"
    prompt = SANDBOX_PROMPT.format(
        graph_yaml=effective_graph_yaml,
        concept=concept,
    )

    if abstract:
        prompt += (
            f"\n\nPAPER ABSTRACT: {abstract}\n\n"
            "Ground your creative proposals in the paper's actual findings. "
            "Ensure proposed encodings accurately represent the science — "
            "flag any proposal that would constitute Spin."
        )

    logger.info(f"Sandbox: '{concept}' × 10 channel families")

    response = model.generate_content(
        [prompt, {"mime_type": mime, "data": image_bytes}],
        generation_config={"temperature": 0.6, "max_output_tokens": 8192},
    )

    parsed = _resilient_yaml_parse(response.text)
    if not parsed:
        logger.error("Failed to parse response")
        return None

    # Print results
    print(f"\n=== SANDBOX: {concept} ===\n")
    for enc in parsed.get("encodings", []):
        ch = enc.get("channel", "?")
        prop = enc.get("proposal", "")
        risk = enc.get("risk", "")
        print(f"  [{ch}] {prop}")
        if risk:
            print(f"       ⚠ {risk}")

    best = parsed.get("best_combination", "")
    worst = parsed.get("worst_trap", "")
    if best:
        print(f"\n  ★ Best combo: {best}")
    if worst:
        print(f"  ✗ Worst trap: {worst}")

    # Save
    if output_path is None:
        base = os.path.splitext(graph_path)[0]
        slug = concept.replace(" ", "_")[:30]
        output_path = f"{base}_sandbox_{slug}.yaml"
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(parsed, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"Saved: {output_path}")
    return parsed


def full_duck(image_path, graph_path, output_path=None, abstract=None,
              prior_graph=True):
    """Rubber duck ALL nodes × all channel families. Expensive but comprehensive.

    Args:
        image_path: Path to GA image file.
        graph_path: Path to L3 graph YAML file.
        output_path: Optional output path.
        abstract: Optional paper abstract text for scientific grounding.
        prior_graph: When True (default), includes graph context in each call.
    """
    model = _load_gemini()
    image_bytes, mime = _load_image(image_path)

    with open(graph_path) as f:
        graph = yaml.safe_load(f)

    results = {}
    nodes = [n for n in graph.get("nodes", []) if n.get("weight", 0) >= 0.5]
    logger.info(f"Full duck: {len(nodes)} important nodes")

    for i, node in enumerate(nodes):
        name = node["name"]
        logger.info(f"  [{i+1}/{len(nodes)}] {name}...")
        result = rubber_duck(image_path, graph_path, name, abstract=abstract,
                             prior_graph=prior_graph)
        if result:
            results[name] = result
        if i < len(nodes) - 1:
            time.sleep(4)

    if output_path is None:
        base = os.path.splitext(graph_path)[0]
        output_path = f"{base}_full_duck.yaml"
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(results, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"Full duck saved: {output_path}")
    return results


SANDBOX_COMPARE_PROMPT = """Tu es un expert en communication visuelle. Tu compares comment {n} Graphical Abstracts (GAs) encodent le concept "{concept}".

Les images sont labellisees {labels}.

{graph_sections}

Pour CHAQUE canal visuel ci-dessous, compare comment chaque GA encode le concept "{concept}".
Pour chaque canal, determine quel GA le fait le mieux et pourquoi.

Canaux a comparer :
1. Couleur (hue, saturation, luminance, temperature)
2. Forme (shape, taille, orientation, courbure)
3. Texture
4. Position (ou sur la page, proximity, enclosure, layer)
5. Mouvement/Direction (fleche, flow, rythme)
6. Metaphore (icone, symbole, analogie visuelle)
7. Typographie (poids, taille, style)
8. Contraste
9. Redondance (combinaison de canaux)

Reponds en YAML :

concept: "{concept}"
per_channel:
  - channel: "color"
    per_ga:
      - label: "A"
        encoding: "how A encodes this concept via color"
        effectiveness: 0.0-1.0
      - label: "B"
        encoding: "how B encodes this concept via color"
        effectiveness: 0.0-1.0
{per_ga_c}    winner: "A or B{or_c}"
    why: "why this GA wins on this channel"
  - channel: "form"
    per_ga: [...]
    winner: "..."
    why: "..."
  ...

overall:
  winner: "A or B{or_c}"
  rationale: "which GA should the others learn from and why"
  key_lesson: "the single most important thing the weaker GA(s) should steal"
  concept_clarity_ranking:
    - label: "A"
      score: 0.0-1.0
      summary: "how clearly A communicates this concept"
    - label: "B"
      score: 0.0-1.0
      summary: "how clearly B communicates this concept"
{clarity_c}
Return ONLY the YAML. No markdown fences. No explanation.
"""


def sandbox_compare(image_paths: list, graph_paths: list, concept: str, output_path=None,
                    abstract=None, prior_graph=True) -> dict:
    """Compare how 2-3 GAs encode a specific concept across all visual channels.

    Args:
        image_paths: list of 2 or 3 image file paths
        graph_paths: list of 2 or 3 corresponding graph YAML paths
        concept: the concept to compare encoding of
        output_path: Optional output path for the comparison.
        abstract: Optional paper abstract text for scientific grounding.
        prior_graph: When True (default), includes existing graph YAML in
                     the Gemini prompt as context for iterative comparison.

    Returns:
        dict with per_channel comparison, winner per channel, and overall recommendation
    """
    import google.generativeai as genai

    n = len(image_paths)
    if n < 2 or n > 3:
        raise ValueError(f"sandbox_compare requires 2 or 3 image/graph pairs, got {n}")
    if len(graph_paths) != n:
        raise ValueError(f"Number of images ({n}) must match number of graphs ({len(graph_paths)})")

    for p in image_paths + graph_paths:
        if not os.path.exists(p):
            raise FileNotFoundError(f"File not found: {p}")

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-2.5-pro"))

    labels = ", ".join(chr(65 + i) for i in range(n))
    or_c = " or C" if n == 3 else ""

    # Build graph sections
    graph_sections = []
    for i in range(n):
        label = chr(65 + i)
        with open(graph_paths[i], "r", encoding="utf-8") as f:
            graph = yaml.safe_load(f)
        if prior_graph:
            graph_yaml = yaml.dump(graph, default_flow_style=False, allow_unicode=True)
            graph_sections.append(
                f"--- GA {label} ({os.path.basename(image_paths[i])}) ---\n"
                f"```yaml\n{graph_yaml[:3000]}\n```\n"
            )
        else:
            graph_sections.append(
                f"--- GA {label} ({os.path.basename(image_paths[i])}) ---\n"
                f"(no prior graph provided)\n"
            )

    per_ga_c = ""
    clarity_c = ""
    if n == 3:
        per_ga_c = '      - label: "C"\n        encoding: "how C encodes this concept"\n        effectiveness: 0.0-1.0\n'
        clarity_c = '    - label: "C"\n      score: 0.0-1.0\n      summary: "how clearly C communicates this concept"\n'

    prompt = SANDBOX_COMPARE_PROMPT.format(
        n=n,
        labels=labels,
        concept=concept,
        graph_sections="\n".join(graph_sections),
        or_c=or_c,
        per_ga_c=per_ga_c,
        clarity_c=clarity_c,
    )

    if abstract:
        prompt += (
            f"\n\nPAPER ABSTRACT: {abstract}\n\n"
            "Judge each GA's encoding of this concept against the paper's actual findings. "
            "Factor scientific accuracy into effectiveness scores and winner selection."
        )

    # Build content: prompt + all images
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    parts = [prompt]
    for i in range(n):
        label = chr(65 + i)
        with open(image_paths[i], "rb") as f:
            img_bytes = f.read()
        ext = os.path.splitext(image_paths[i])[1].lower()
        mime = mime_map.get(ext, "image/png")
        parts.append(f"GA {label}:")
        parts.append({"mime_type": mime, "data": img_bytes})

    logger.info(f"Sandbox compare: '{concept}' across {n} GAs")

    try:
        response = model.generate_content(
            parts,
            generation_config={"temperature": 0.4, "max_output_tokens": 8192},
        )
        raw = response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise RuntimeError(f"Gemini API error during sandbox compare: {e}")

    parsed = _resilient_yaml_parse(raw)
    if not parsed:
        logger.error(
            f"Failed to parse sandbox compare response. "
            f"Response was {len(raw)} chars, {len(raw.splitlines())} lines. "
            f"Concept: '{concept}'. "
            "Check the debug file saved by _resilient_yaml_parse for raw output."
        )
        return None

    # Print results
    print(f"\n=== COMPARE: '{concept}' ===\n")
    for ch_result in parsed.get("per_channel", []):
        channel = ch_result.get("channel", "?")
        winner = ch_result.get("winner", "?")
        why = ch_result.get("why", "")
        print(f"  [{channel}] Winner: {winner} — {why[:80]}")
        for ga in ch_result.get("per_ga", []):
            lbl = ga.get("label", "?")
            eff = ga.get("effectiveness", "?")
            enc = ga.get("encoding", "")[:60]
            print(f"    {lbl}: {eff} — {enc}")

    overall = parsed.get("overall", {})
    print(f"\n  Overall winner: {overall.get('winner', 'N/A')}")
    print(f"  Rationale: {overall.get('rationale', 'N/A')}")
    print(f"  Key lesson: {overall.get('key_lesson', 'N/A')}")

    # Save
    if output_path is None:
        slug = concept.replace(" ", "_")[:30]
        base_names = "_vs_".join(
            os.path.splitext(os.path.basename(p))[0][:15] for p in image_paths
        )
        output_path = os.path.join(_HERE, "data", f"compare_{base_names}_{slug}.yaml")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(parsed, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"Comparison saved: {output_path}")

    return parsed


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GA Rubber Duck — creative visual exploration")
    parser.add_argument("mode", choices=["duck", "sandbox", "full", "compare"],
                        help="duck=one component, sandbox=one concept all channels, full=all components, compare=compare GAs on a concept")
    parser.add_argument("--compare", nargs="+", metavar="PATH",
                        help="Compare mode paths: --compare img_a.png graph_a.yaml img_b.png graph_b.yaml \"concept\"")
    parser.add_argument("--abstract", help="Paper abstract text for context")
    parser.add_argument("--abstract-file", help="Path to file containing abstract")
    parser.add_argument("image", nargs="?", help="GA image path")
    parser.add_argument("graph", nargs="?", help="L3 graph YAML path")
    parser.add_argument("target", nargs="?", default=None,
                        help="Component name (duck) or concept (sandbox)")
    parser.add_argument("--output", "-o", help="Output path")
    args = parser.parse_args()

    abstract = _load_abstract(args.abstract, args.abstract_file,
                              args.graph if hasattr(args, 'graph') else None)

    if args.mode == "compare" or args.compare:
        if not args.compare:
            parser.error("compare mode requires --compare with image/graph pairs + concept")
        paths = args.compare
        if len(paths) < 5:
            parser.error(
                "--compare requires pairs of (image, graph) + concept string at the end. "
                "Example: --compare img_a.png graph_a.yaml img_b.png graph_b.yaml \"concept\". "
                f"Got {len(paths)} arguments."
            )
        concept_str = paths[-1]
        pair_paths = paths[:-1]
        if len(pair_paths) not in (4, 6):
            parser.error(
                f"Expected 4 or 6 paths before the concept string (2 or 3 image/graph pairs), "
                f"got {len(pair_paths)}."
            )
        n_pairs = len(pair_paths) // 2
        img_paths = [pair_paths[i * 2] for i in range(n_pairs)]
        grp_paths = [pair_paths[i * 2 + 1] for i in range(n_pairs)]
        sandbox_compare(img_paths, grp_paths, concept_str, args.output, abstract=abstract)
    elif args.mode == "duck":
        if not args.target:
            parser.error("duck mode requires a component name")
        rubber_duck(args.image, args.graph, args.target, args.output, abstract=abstract)
    elif args.mode == "sandbox":
        if not args.target:
            parser.error("sandbox mode requires a concept")
        sandbox(args.image, args.graph, args.target, args.output, abstract=abstract)
    elif args.mode == "full":
        full_duck(args.image, args.graph, args.output, abstract=abstract)
