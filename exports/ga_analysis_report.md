# GLANCE GA Analysis Report

**Overall Score:** 0.59
**Nodes:** 19 | **Links:** 38

## Recommendations (prioritized)

### 1. [CRITICAL] thing:glance
**Problème:** Noeud important (w=1.0) mais instable (s=0.4)
**Fix:** Ce noeud a besoin de données empiriques pour se stabiliser. Lancez un test GLANCE.
**Impact:** Sans validation, ce noeud est une promesse, pas une preuve.

### 2. [HIGH] narrative:spin
**Problème:** Énergie haute (e=0.75) — conception non résolue
**Fix:** Ce noeud nécessite une itération de design. Vérifiez le mapping canal visuel.
**Impact:** Un noeud à haute énergie dans le GA final = un élément non finalisé.

### 3. [HIGH] thing:glance
**Problème:** Énergie haute (e=0.9) — conception non résolue
**Fix:** Ce noeud nécessite une itération de design. Vérifiez le mapping canal visuel.
**Impact:** Un noeud à haute énergie dans le GA final = un élément non finalisé.

### 4. [HIGH] thing:ga_thumbnail
**Problème:** Énergie haute (e=0.8) — conception non résolue
**Fix:** Ce noeud nécessite une itération de design. Vérifiez le mapping canal visuel.
**Impact:** Un noeud à haute énergie dans le GA final = un élément non finalisé.

## Strengths

- **space:ga:domain** — Solide (w=0.7, s=0.9) — bien établi dans la littérature ou le design.
- **space:ga:zone_left** — Solide (w=0.85, s=0.9) — bien établi dans la littérature ou le design.
- **thing:engagement** — Solide (w=0.8, s=0.95) — bien établi dans la littérature ou le design.
- **thing:comprehension** — Solide (w=0.75, s=0.9) — bien établi dans la littérature ou le design.
- **thing:comprehension_gap_data** — Solide (w=0.75, s=0.95) — bien établi dans la littérature ou le design.
- **narrative:gap** — Solide (w=0.95, s=0.9) — bien établi dans la littérature ou le design.
- **thing:5_seconds** — Solide (w=0.65, s=0.85) — bien établi dans la littérature ou le design.
- **thing:grade** — Solide (w=0.7, s=0.95) — bien établi dans la littérature ou le design.
- **moment:akl_2007** — Solide (w=0.74, s=0.95) — bien établi dans la littérature ou le design.
- **moment:6_rcts** — Solide (w=0.9, s=0.95) — bien établi dans la littérature ou le design.

## Accessibility Warnings

- **color_pair_close:** Les paires de couleurs sont-elles distinguables pour les daltoniens ?
  - Fix: Utilisez des couleurs séparées d'au moins 30° sur la roue chromatique, ou ajoutez des motifs/textures
  - Ref: 8% des hommes sont daltoniens (deutéranopie/protanopie)

- **text_density:** Le GA contient-il plus de 30 mots ?
  - Fix: Réduisez à 30 mots max. Chaque mot supplémentaire active le Système 2 et augmente le temps de décodage
  - Ref: V3 — Budget 30 mots

- **small_details:** Tous les éléments sont-ils lisibles à 50% de la taille originale ?
  - Fix: Agrandissez les éléments critiques. Le GA sera vu en thumbnail 200px dans une TOC — si c'est illisible à 50%, c'est mort
  - Ref: V7 — Lisibilité 50%

## Channel Upgrade Paths

| Current Channel | Upgrade To | Reason | Expected S9b Improvement |
|----------------|-----------|--------|------------------------|
| area | length | Stevens β passe de 0.7 à 1.0 — les différences sont perçues ... | +20-30% sur S9b |
| volume | length | Stevens β passe de 0.6 à 1.0... | +30-40% sur S9b |
| color_saturation | luminance | La luminance est intuitive pour l'incertitude (MacEachren 20... | +15-25% sur la perception de l'incertitude |
| color_hue | length + color_hue | La teinte seule encode des catégories, pas des magnitudes. A... | +10-20% sur S9b |
| no_channel | length | L'information n'est encodée dans aucun canal visuel pré-atte... | De 0% à 60-80% de perception |