"""GLANCE Recommendation Engine — from scores to actionable design fixes.

Takes a scored GA graph and generates specific, prioritized recommendations
for improving visual comprehension. This is the explainability layer.
"""

import yaml
import os

BASE = os.path.dirname(__file__)

def load_pattern_registry():
    with open(os.path.join(BASE, "pattern_registry.yaml")) as f:
        return yaml.safe_load(f)

def load_ga_graph(path):
    with open(path) as f:
        return yaml.safe_load(f)

# Channel effectiveness database (Cleveland & McGill + Stevens)
CHANNEL_EFFECTIVENESS = {
    "position_common_scale": {"beta": 1.0, "rank": 1, "label": "Position sur échelle commune"},
    "length": {"beta": 1.0, "rank": 2, "label": "Longueur"},
    "angle": {"beta": 0.85, "rank": 3, "label": "Angle/pente"},
    "area": {"beta": 0.7, "rank": 4, "label": "Surface", "warning": "Stevens β≈0.7 — compresse les différences perçues"},
    "volume": {"beta": 0.6, "rank": 5, "label": "Volume", "warning": "Stevens β≈0.6 — forte compression"},
    "color_saturation": {"beta": 0.3, "rank": 6, "label": "Saturation couleur", "warning": "Non intuitif pour les magnitudes (MacEachren 2012)"},
    "color_hue": {"beta": None, "rank": 7, "label": "Teinte couleur", "warning": "Catégoriel uniquement, pas ordinal"},
    "luminance": {"beta": 0.9, "rank": 3, "label": "Luminance", "note": "Intuitif pour l'incertitude"},
}

# Upgrade paths: if you're using X, switch to Y
UPGRADE_PATHS = {
    "area": {
        "upgrade_to": "length",
        "reason": "Stevens β passe de 0.7 à 1.0 — les différences sont perçues à 100% au lieu de 70%",
        "example": "Remplacez les bulles/cercles par des barres horizontales",
        "expected_improvement": "+20-30% sur S9b"
    },
    "volume": {
        "upgrade_to": "length",
        "reason": "Stevens β passe de 0.6 à 1.0",
        "example": "Remplacez les sphères 3D par des barres 2D",
        "expected_improvement": "+30-40% sur S9b"
    },
    "color_saturation": {
        "upgrade_to": "luminance",
        "reason": "La luminance est intuitive pour l'incertitude (MacEachren 2012), la saturation ne l'est pas",
        "example": "Utilisez des niveaux de gris ou d'opacité au lieu de couleurs plus/moins vives",
        "expected_improvement": "+15-25% sur la perception de l'incertitude"
    },
    "color_hue": {
        "upgrade_to": "length + color_hue",
        "reason": "La teinte seule encode des catégories, pas des magnitudes. Ajoutez un canal de longueur redondant (P32)",
        "example": "Gardez les couleurs pour identifier les groupes, mais ajoutez des barres pour encoder les valeurs",
        "expected_improvement": "+10-20% sur S9b"
    },
    "no_channel": {
        "upgrade_to": "length",
        "reason": "L'information n'est encodée dans aucun canal visuel pré-attentif — elle est invisible en 5 secondes",
        "example": "Ajoutez un encodage visuel (barre, position, taille)",
        "expected_improvement": "De 0% à 60-80% de perception"
    }
}

# Accessibility checks
ACCESSIBILITY_CHECKS = {
    "color_pair_close": {
        "test": "Les paires de couleurs sont-elles distinguables pour les daltoniens ?",
        "fix": "Utilisez des couleurs séparées d'au moins 30° sur la roue chromatique, ou ajoutez des motifs/textures",
        "prevalence": "8% des hommes sont daltoniens (deutéranopie/protanopie)"
    },
    "text_density": {
        "test": "Le GA contient-il plus de 30 mots ?",
        "fix": "Réduisez à 30 mots max. Chaque mot supplémentaire active le Système 2 et augmente le temps de décodage",
        "reference": "V3 — Budget 30 mots"
    },
    "small_details": {
        "test": "Tous les éléments sont-ils lisibles à 50% de la taille originale ?",
        "fix": "Agrandissez les éléments critiques. Le GA sera vu en thumbnail 200px dans une TOC — si c'est illisible à 50%, c'est mort",
        "reference": "V7 — Lisibilité 50%"
    }
}


def analyze_ga(ga_graph_path, channel_scoring_path=None):
    """Analyze a GA graph and generate recommendations.

    Returns a dict with:
    - overall_score (0-1)
    - node_scores (per node)
    - recommendations (prioritized list)
    - accessibility_warnings
    - strengths
    """
    graph = load_ga_graph(ga_graph_path)
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    links = graph.get("links", [])

    recommendations = []
    strengths = []
    warnings = []

    # Analyze each node
    for node in graph.get("nodes", []):
        nid = node["id"]
        w = node.get("weight", 0.5)
        s = node.get("stability", 0.5)
        e = node.get("energy", 0.5)

        # High weight + low stability = critical unstable node
        if w > 0.7 and s < 0.5:
            recommendations.append({
                "priority": "CRITICAL",
                "node": nid,
                "issue": f"Noeud important (w={w}) mais instable (s={s})",
                "fix": "Ce noeud a besoin de données empiriques pour se stabiliser. Lancez un test GLANCE.",
                "impact": "Sans validation, ce noeud est une promesse, pas une preuve."
            })

        # High energy = needs design work
        if e > 0.6:
            recommendations.append({
                "priority": "HIGH",
                "node": nid,
                "issue": f"Énergie haute (e={e}) — conception non résolue",
                "fix": f"Ce noeud nécessite une itération de design. Vérifiez le mapping canal visuel.",
                "impact": "Un noeud à haute énergie dans le GA final = un élément non finalisé."
            })

        # High weight + high stability = strength
        if w > 0.6 and s > 0.8:
            strengths.append({
                "node": nid,
                "reason": f"Solide (w={w}, s={s}) — bien établi dans la littérature ou le design."
            })

    # Analyze hierarchy encoding
    hierarchy_nodes = [n for n in graph.get("nodes", []) if n.get("hierarchy", 0) > 0]
    if hierarchy_nodes:
        # Check if hierarchy is encoded by length (good) or area (bad)
        # This would normally come from channel_scoring, but we can infer
        pass

    # Run accessibility checks
    for check_id, check in ACCESSIBILITY_CHECKS.items():
        warnings.append({
            "check": check_id,
            "test": check["test"],
            "fix": check["fix"],
            "reference": check.get("reference", check.get("prevalence", ""))
        })

    # Sort recommendations by priority
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    recommendations.sort(key=lambda r: priority_order.get(r["priority"], 99))

    return {
        "overall_score": sum(n.get("stability", 0.5) * n.get("weight", 0.5) for n in graph.get("nodes", [])) / max(len(graph.get("nodes", [])), 1),
        "node_count": len(graph.get("nodes", [])),
        "link_count": len(links),
        "recommendations": recommendations,
        "strengths": strengths,
        "accessibility_warnings": warnings,
        "upgrade_paths": UPGRADE_PATHS,
    }


def generate_report(analysis, output_path=None):
    """Generate a human-readable markdown report from the analysis."""
    lines = []
    lines.append("# GLANCE GA Analysis Report\n")
    lines.append(f"**Overall Score:** {analysis['overall_score']:.2f}")
    lines.append(f"**Nodes:** {analysis['node_count']} | **Links:** {analysis['link_count']}\n")

    lines.append("## Recommendations (prioritized)\n")
    for i, rec in enumerate(analysis["recommendations"], 1):
        lines.append(f"### {i}. [{rec['priority']}] {rec['node']}")
        lines.append(f"**Problème:** {rec['issue']}")
        lines.append(f"**Fix:** {rec['fix']}")
        lines.append(f"**Impact:** {rec['impact']}\n")

    lines.append("## Strengths\n")
    for s in analysis["strengths"]:
        lines.append(f"- **{s['node']}** — {s['reason']}")

    lines.append("\n## Accessibility Warnings\n")
    for w in analysis["accessibility_warnings"]:
        lines.append(f"- **{w['check']}:** {w['test']}")
        lines.append(f"  - Fix: {w['fix']}")
        lines.append(f"  - Ref: {w['reference']}\n")

    lines.append("## Channel Upgrade Paths\n")
    lines.append("| Current Channel | Upgrade To | Reason | Expected S9b Improvement |")
    lines.append("|----------------|-----------|--------|------------------------|")
    for ch, up in analysis["upgrade_paths"].items():
        lines.append(f"| {ch} | {up['upgrade_to']} | {up['reason'][:60]}... | {up['expected_improvement']} |")

    report = "\n".join(lines)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

    return report


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "data", "glance_ga_graph.yaml")
    # Derive output path from input filename
    input_name = os.path.splitext(os.path.basename(path))[0]
    output_name = input_name.replace("_ga_graph", "") + "_analysis_report.md"
    output_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "exports", output_name)
    analysis = analyze_ga(path)
    report = generate_report(analysis, output_path)
    print(report)
