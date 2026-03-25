"""GLANCE Recommendation Engine — from scores to actionable design fixes.

Takes a scored GA graph and generates specific, prioritized recommendations
for improving visual comprehension. This is the explainability layer.
"""

import yaml
import os

from archetype import classify_from_vision_metadata

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


def get_plain_text(recommendation):
    """Generate a plain-language French explanation for a recommendation.

    Maps technical jargon to conversational, actionable text that
    non-expert researchers can understand immediately.
    """
    issue = (recommendation.get("issue") or "").lower()
    fix = (recommendation.get("fix") or "").lower()
    node = (recommendation.get("node") or "").lower()

    # Encoding channel: area -> length
    if "area" in issue and ("beta" in issue or "encoding" in node or "stevens" in issue):
        return ("Les donnees sont representees par des surfaces (camemberts ou bulles), "
                "ce qui rend les comparaisons difficiles. Utilisez des barres — "
                "vos lecteurs comprendront ~20% mieux les differences entre les valeurs.")

    # Volume encoding
    if "volume" in issue or ("3d" in issue and "sphere" in fix):
        return ("Les spheres 3D deforment la perception des donnees. "
                "Remplacez-les par des barres 2D — le gain de comprehension est de +30-40%.")

    # Color saturation
    if "saturation" in issue or "saturation" in node:
        return ("La saturation des couleurs n'est pas intuitive pour representer des quantites. "
                "Utilisez plutot des niveaux de gris ou d'opacite pour encoder les magnitudes.")

    # Color accessibility / daltonism
    if "daltonien" in issue or "color_pair" in node or "distinguable" in issue or "couleur" in fix:
        return ("Certaines couleurs de votre image sont indiscernables pour les daltoniens "
                "(~8% des hommes). Ajoutez des textures ou des motifs pour differencier les elements.")

    # Text density / word count
    if "texte" in issue or "text_density" in node or "30 mots" in fix or "word" in issue:
        return ("Votre image contient trop de texte. En 5 secondes de scroll, "
                "seuls les 5-10 mots les plus gros sont lus. Reduisez a 30 mots maximum.")

    # Small details / readability
    if "lisib" in issue or "small_detail" in node or "50%" in fix or "thumbnail" in fix:
        return ("Certains elements sont trop petits pour etre lus. "
                "Votre image sera vue en miniature dans un flux — "
                "agrandissez les elements critiques.")

    # Hierarchy clarity
    if "hierarch" in issue or "hierarchy" in node:
        return ("On ne voit pas immediatement quel resultat est le plus fort. "
                "Utilisez la taille, la position ou la couleur pour montrer "
                "la hierarchie des preuves.")

    # Product count / cognitive load
    if "product_count" in node or "cognitive load" in issue or "exceed" in issue:
        return ("Votre image montre trop de niveaux d'information. "
                "Le lecteur ne peut retenir que 3-4 groupes en 5 secondes. "
                "Regroupez les elements secondaires.")

    # Semantic depth
    if "semantic" in issue or "semantic_depth" in node:
        return ("Les descriptions de votre image manquent de precision. "
                "Enrichissez les metadonnees pour ameliorer la mesure automatique "
                "de comprehension.")

    # High energy / unresolved design
    if "energie" in issue or "energy" in issue or "conception" in fix:
        return ("Cet element du design n'est pas finalise. "
                "Verifiez que les donnees sont encodees dans un canal visuel clair "
                "(barres, position, taille).")

    # Unstable important node
    if "instable" in issue or "unstable" in issue:
        return ("Cet element est important mais n'a pas ete valide par des tests. "
                "Lancez un test GLANCE pour verifier que les lecteurs le comprennent.")

    # Hue-only encoding
    if "teinte" in issue or "hue" in issue or "color_hue" in node:
        return ("La couleur seule ne peut pas representer des quantites — "
                "elle sert uniquement a categoriser. Ajoutez des barres pour encoder "
                "les valeurs numeriques.")

    # Figure/text ratio
    if "ratio" in issue and ("text" in issue or "figure" in issue):
        return ("Le texte prend plus de place que les donnees visuelles. "
                "Inversez le ratio : les graphiques doivent dominer.")

    # Contrast / figure-ground
    if "contraste" in issue or "contrast" in issue or "fond" in issue:
        return ("Les elements importants ne ressortent pas assez du fond. "
                "Augmentez le contraste entre les donnees et l'arriere-plan.")

    # Directional flow
    if "direction" in issue or "flow" in issue or "ordre" in issue:
        return ("L'oeil ne sait pas dans quel ordre lire votre image. "
                "Ajoutez des fleches ou une numerotation pour guider la lecture.")

    # Generic fallback
    return None


def get_score_interpretation(metric_name, value):
    """Return a plain-language French interpretation of a score.

    Args:
        metric_name: one of 's9a', 's9b', 's9c', 'fluency', 'glance', 's2_coverage'
        value: float between 0 and 1
    """
    pct = value * 100

    if metric_name == "s9a":
        if pct >= 60:
            return "Les lecteurs identifient le sujet de votre image"
        else:
            return "Les lecteurs ne comprennent pas de quoi parle votre image"

    elif metric_name == "s9b":
        if pct >= 80:
            return "La hierarchie des preuves est claire"
        elif pct >= 25:
            return "Les lecteurs ne voient pas quel resultat est le plus important"
        else:
            return "Comprehension au niveau du hasard — le design ne transmet aucune hierarchie"

    elif metric_name == "s9c":
        if pct >= 40:
            return "Votre image declenche une intention d'action"
        else:
            return "Les lecteurs ne voient pas en quoi ca les concerne"

    elif metric_name == "fluency":
        if pct >= 70:
            return "Decodage rapide et precis — le design est fluide"
        elif pct >= 40:
            return "Comprehension correcte mais lente — le design demande un effort"
        else:
            return "Le design bloque la comprehension rapide"

    elif metric_name == "glance":
        if pct >= 70:
            return "Votre GA communique efficacement en conditions reelles"
        else:
            return "Votre GA perd trop d'information dans un contexte de scroll"

    elif metric_name == "s2_coverage":
        if pct >= 60:
            return "La majorite des informations cles est retenue apres lecture attentive"
        elif pct >= 30:
            return "Moins de la moitie des informations cles est retenue"
        else:
            return "Tres peu d'informations passent — le design est trop dense ou confus"

    return None


def enrich_recommendations_with_plain_text(recommendations):
    """Add plain_text field to each recommendation in a list.

    Modifies recommendations in-place and returns the list.
    """
    for rec in recommendations:
        plain = get_plain_text(rec)
        if plain:
            rec["plain_text"] = plain
    return recommendations


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

    # Enrich with plain-text translations
    enrich_recommendations_with_plain_text(recommendations)

    # Archetype classification from graph metadata
    metadata = graph.get("metadata", {})
    archetype = None
    if metadata:
        try:
            archetype = classify_from_vision_metadata(metadata)
        except Exception:
            pass

    result = {
        "overall_score": sum(n.get("stability", 0.5) * n.get("weight", 0.5) for n in graph.get("nodes", [])) / max(len(graph.get("nodes", [])), 1),
        "node_count": len(graph.get("nodes", [])),
        "link_count": len(links),
        "recommendations": recommendations,
        "strengths": strengths,
        "accessibility_warnings": warnings,
        "upgrade_paths": UPGRADE_PATHS,
    }
    if archetype:
        result["archetype"] = archetype
    return result


def generate_report(analysis, output_path=None):
    """Generate a human-readable markdown report from the analysis."""
    lines = []
    lines.append("# GLANCE GA Analysis Report\n")
    lines.append(f"**Overall Score:** {analysis['overall_score']:.2f}")
    lines.append(f"**Nodes:** {analysis['node_count']} | **Links:** {analysis['link_count']}\n")

    # Archetype section
    arch = analysis.get("archetype")
    if arch:
        info = arch.get("archetype_info", {})
        lines.append(f"## Diagnostic: {info.get('emoji', '')} {info.get('name_fr', '')} ({info.get('name_en', '')})\n")
        lines.append(f"**{info.get('description_fr', '')}**\n")
        lines.append(f"*Signature:* `{info.get('signature', '')}`")
        lines.append(f"*Confiance:* {round(arch.get('confidence', 0) * 100)}% ({arch.get('method', '')})\n")
        lines.append(f"> {info.get('recommendation_fr', '')}\n")

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
