# GLANCE Paper — Graphical Abstract Specification

**Version:** 1.0
**Date:** 25 mars 2026
**Statut:** SPEC — pré-production
**Objectif:** Spécifier chaque pixel du GA du paper GLANCE pour qu'il passe son propre test GLANCE ≥ 80%

---

## 0. Le Contrat

Ce GA sera le premier graphical abstract testé par son propre protocole. S'il atteint S9b ≥ 80%, c'est la preuve d'existence du framework. S'il échoue, l'échec est rapporté dans la Discussion. Dans les deux cas, le self-test est data.

Le GA doit répondre correctement à ces 3 questions posées après 5 secondes d'exposition :

| Question | Réponse correcte | Ce que ça valide |
|---|---|---|
| Q1 "Que venez-vous de voir ?" | "L'engagement ne mesure pas la compréhension" / "les métriques de visibilité ne reflètent pas la compréhension" | Le problème est identifiable (S9a) |
| Q2 "Quelle métrique mesure le mieux la compréhension d'un GA ?" | **GLANCE Comprehension** (vs Altmetric / Taux de clic / Esthétique) | La hiérarchie est perçue (S9b) |
| Q3 "Utiliseriez-vous les likes pour évaluer votre prochaine publication ?" | Non | Le message change le comportement (S9c) |

Tout le design découle de Q2. Le GA doit faire en sorte que le Système 1 identifie GLANCE comme la métrique dominante en < 3 secondes, sans lire de texte.

---

## 1. Architecture Globale

### 1.1 Deux zones, pas trois

Le GA est divisé en deux moitiés par une fracture verticale. Pas trois zones. La V2/V5 avait une "Zone 2 : L'Expérience" qui décrivait la procédure (chronomètre, spotlight, stream). C'est du bruit — la procédure n'est pas le message. Le message c'est : problème (gauche) → preuve (droite).

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│    ZONE GAUCHE                    ZONE DROITE                  │
│    Le Fossé                       La Mesure                    │
│    (~45% de la largeur)           (~55% de la largeur)         │
│                                                                │
│    ROUGE / CHAUD / ANGULAIRE      BLEU / FROID / ARRONDI       │
│    = tension, problème            = résolution, confiance      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

La zone droite est légèrement plus large (55%) parce que c'est la zone de résolution — le regard doit finir là. Le flux de lecture occidental (gauche → droite) amène naturellement le lecteur du problème vers la solution.

**Justification :** Jambor & Bornhäuser (2024, règle #3) : "le GA doit être lisible comme une histoire avec un début et une fin clairs." Deux zones = deux actes (problème, solution). Trois zones diluent le message et ajoutent de la charge cognitive (Miller 1956 : 7±2 chunks).

### 1.2 Format et dimensions

| Paramètre | Valeur | Justification |
|---|---|---|
| Largeur | 1200px | Standard GA PLOS ONE / MDPI. Compatible TOC mobile. |
| Hauteur | 628px | Ratio 1.91:1 — optimisé pour LinkedIn preview card (le GA sera partagé). |
| Résolution | 300 DPI pour print, 72 DPI pour web | Double export. |
| Fond | Blanc (#FFFFFF) | Le fond ne porte aucune information. La couleur est dans les éléments. |
| Marges | 40px minimum sur chaque bord | Espace de respiration. Le GA ne touche jamais les bords. |

**Justification du ratio 1.91:1 :** C'est le ratio de la preview card LinkedIn (1200×628). Quand le GA est partagé sur LinkedIn (canal #1 de dissémination), il s'affiche sans crop. Un GA en 16:9 (1200×675) serait coupé en haut et en bas. Un GA carré (1200×1200) serait écrasé en preview. Le 1.91:1 est le compromis entre l'espace de design et la compatibilité de diffusion.

---

## 2. Palette Chromatique

### 2.1 Le principe : la couleur EST le message

Le lecteur ne doit pas lire "PROBLEM" pour savoir que c'est un problème. Il doit le **sentir**. La couleur fait 80% du travail émotionnel en pré-attentif (Système 1, < 250ms). Les formes font 15%. Le texte fait 5% — il confirme ce que le visuel a déjà communiqué.

### 2.2 Deux palettes opposées

| | Zone Gauche (Le Fossé) | Zone Droite (La Mesure) |
|---|---|---|
| **Couleur dominante** | Rouge-orange (#E63946) | Bleu profond (#1D3557) |
| **Couleur secondaire** | Orange vif (#F4A261) pour l'engagement | Teal (#2A9D8F) pour GLANCE |
| **Couleur d'accent** | Gris froid (#8D99AE) pour les citations | Bleu clair (#A8DADC) pour le fond des barres |
| **Température** | Chaude — alerte, danger, tension | Froide — calme, confiance, résolution |
| **Saturation** | Haute sur l'engagement (vif, criard), basse sur la compréhension (désaturée) | Haute sur GLANCE (affirmé), moyenne sur GRADE, basse sur Vanity |
| **Luminance** | L'engagement est clair (haute luminance = incertitude, P34). La compréhension est sombre (basse luminance = certitude). | GLANCE foncé = certitude haute. Vanity clair = certitude nulle. |

**Justification de chaque choix :**

- **Rouge-orange pour le problème :** Le rouge active l'amygdale et signale le danger sans médiation consciente (Elliot et al., 2007, *J Experimental Psychology*). Le lecteur ressent la tension avant de comprendre pourquoi.
- **Bleu profond pour la solution :** Le bleu est associé à la confiance, la compétence et la stabilité (Labrecque & Milne, 2012, *JAMS*). C'est la couleur dominante des institutions médicales (NHS, OMS, GRADE).
- **Luminance = certitude (P34) :** MacEachren et al. (2012) : la luminance est le canal intuitif pour l'incertitude. Plus foncé = plus certain. L'engagement (haute luminance, clair) = on ne sait pas si ça mesure la qualité. GLANCE (basse luminance, foncé) = on sait que ça mesure la compréhension.

### 2.3 Accessibilité daltoniens (V14)

La palette rouge/bleu est safe pour les 3 types de daltonisme (deutéranopie, protanopie, tritanopie) car le contraste repose sur la luminance (clair vs foncé) ET la teinte (chaud vs froid). Les daltoniens rouge-vert voient le rouge comme jaune-brun et le bleu comme bleu — le contraste de température est préservé. La distance CIEDE2000 entre les deux dominantes doit être > 40 sous chaque simulation.

Vérification obligatoire : passer le GA dans Coblis ou sim-daltonism avant validation.

---

## 3. Zone Gauche — Le Fossé

### 3.1 Ce qu'elle communique en 5 secondes

"L'engagement explose mais la compréhension ne suit pas. Quelque chose ne va pas."

### 3.2 Le graphique en ciseaux

Deux courbes qui divergent. Pas de barres (les barres sont réservées à la Zone Droite pour la hiérarchie P32).

```
         ╱ Engagement (×7.7, ×8.4)
        ╱   [rouge-orange, trait épais 4px, angulaire]
       ╱
──────╱
──────────── Comprehension / Citations
             [gris froid, trait 2px, plat]
             (IRR 0.97, no effect)
```

**L'engagement** est une ligne ascendante agressive. Rouge-orange (#E63946). Trait épais (4px). Angulaire (pas de courbe lissée — des segments droits avec des angles). La ligne monte en haut à droite de la zone. Elle est visuellement dominante — c'est voulu : le volume de l'engagement EST impressionnant.

**La compréhension** est une ligne plate. Gris froid (#8D99AE). Trait fin (2px). Elle ne monte pas. Elle reste au bas de la zone. Le contraste avec la ligne engagement est le message : l'une explose, l'autre stagne.

**Pas de légende séparée.** Les labels "Engagement" et "Comprehension" sont directement sur les lignes (annotation inline). Pas de boîte de légende qui force le regard ailleurs.

**Fréquences naturelles (P33) :** En bas de la zone gauche, petit texte : "6 RCTs · 538 participants" — pas "the literature shows" ou "evidence suggests". Les chiffres bruts.

**Justification :** Le graphique en ciseaux encode le fossé sans hiérarchie (pas de barres, pas de "qui est le meilleur"). Il montre une divergence — un trend, pas un classement. L'engagement est visuellement grand parce qu'il EST grand en volume. Mais la Zone Droite va montrer que le volume n'est pas la validité.

### 3.3 La loupe déformante (Spin Visuel)

Une loupe est positionnée sur les données dans la Zone Gauche. Sous la loupe, les données sont visuellement déformées (étirées, agrandies, distordues). Autour de la loupe, les données sont à leur taille réelle.

```
          Normal data
              │
              ▼
    ┌─────────────────┐
    │   ╭─────────╮   │
    │   │ DISTORTED│   │  ← La loupe grossit/étire
    │   │  DATA    │   │     les barres sous elle
    │   ╰─────────╯   │
    │   🔍             │
    └─────────────────┘
```

La loupe encode le mécanisme du spin : la perception déforme les données. C'est un métaphore visuelle qui ne requiert aucun label. Le lecteur voit "les données sont grossies par quelque chose" = distorsion perceptive.

**Taille :** La loupe occupe ~30% de la Zone Gauche. Elle est assez grande pour être vue en 5 secondes de scan mais ne domine pas les ciseaux.

**Couleur :** Le cadre de la loupe est orange (#F4A261). Le verre est un dégradé translucide qui déforme les éléments en dessous (CSS/SVG `filter: url(#magnify)` ou illustration manuelle).

**Label :** "Visual Spin" en petit sous la loupe. Pas de header "THE PROBLEM" — la couleur rouge et la loupe SONT le problème.

**Justification :** Marco a proposé la loupe plutôt qu'un cadran d'alerte. La loupe encode le *mécanisme* (distorsion), pas le *niveau d'alerte* (danger). Pour un paper méthodologique, le mécanisme est plus informatif. Et visuellement, une loupe posée sur des données qui les grossit est lisible sans légende — le concept de "zoom qui déforme" est universel.

---

## 4. La Fracture

### 4.1 Ce qu'elle est

La transition entre les deux zones n'est pas un sablier, pas un entonnoir, pas un gradient. C'est une **rupture nette**. Le rouge s'arrête. Le bleu commence. La ligne de fracture est verticale, légèrement irrégulière (pas parfaitement droite — comme une cassure).

```
    Rouge │ Bleu
    Chaud │ Froid
   Chaos  │ Ordre
  Angulaire│ Arrondi
```

### 4.2 Le chronomètre 5.0s

Le chronomètre peut exister à cheval sur la fracture — petit, centré sur la ligne de rupture. Il est le lien narratif entre le problème (les GAs ne sont pas mesurés) et la solution (GLANCE les mesure en 5 secondes). Mais il est **petit** (~60-80px de diamètre). Il ne domine pas. Il n'a pas de header "THE FILTER". Il est un détail qui récompense le lecteur attentif, pas l'élément principal.

**Couleur :** Bleu sombre (#1D3557) pour le cadre, orange (#F4A261) pour l'aiguille. Il fait le pont chromatique entre les deux zones.

**Justification :** Le chronomètre était l'élément le plus mémorable de la V2. Le supprimer complètement serait une perte. Le réduire à un détail de transition préserve sa mémorabilité sans qu'il vole l'espace aux messages critiques.

---

## 5. Zone Droite — La Mesure

### 5.1 Ce qu'elle communique en 5 secondes

"GLANCE mesure la compréhension. C'est la métrique la plus valide. Plus que GRADE. Infiniment plus que les vanity metrics."

### 5.2 Les 3 barres hiérarchiques (P32)

C'est le cœur du GA. La zone où Q2 est encodé. La longueur des barres encode la **validité** de chaque métrique pour mesurer la compréhension des GAs — pas le volume de données, pas la popularité.

```
0%                                                    100%
├──────────────────────────────────────────────────────┤

████████████████████████████████████████████████████   GLANCE
                                                       Comprehension ≥80%
                                                       [100% longueur]

████████████████████████████████████████              GRADE
                                                       Symbols (74%)
                                                       [74% longueur]

████                                                  Vanity Metrics
                                                       Engagement (~0%)
                                                       [~5% longueur]
```

### 5.3 Spécification de chaque barre

**Barre 1 — GLANCE Comprehension**

| Propriété | Valeur | Justification |
|---|---|---|
| Longueur | 100% de l'espace disponible | C'est la référence. Les autres sont relatives à elle. |
| Couleur | Teal saturé (#2A9D8F) | Distinct du bleu GRADE. Le teal signale "nouveau" / "innovation". |
| Luminance | Foncée, 100% opaque | P34 : foncé = certitude haute. |
| Bords | Arrondis (border-radius 6px) | Forme douce = confiance, solution. |
| Label | "GLANCE Comprehension (≥80%)" | Le nom du protocole + le seuil. |
| Position | En haut des 3 barres | La hiérarchie visuelle naturelle (haut = premier) renforce la longueur. |

**Barre 2 — GRADE Symbols**

| Propriété | Valeur | Justification |
|---|---|---|
| Longueur | **74%** de la barre GLANCE | Proportionnelle exacte. Akl et al. 2007 : 74% compréhension correcte. |
| Couleur | Bleu profond (#1D3557) | Le bleu "établi" / "institution". GRADE est le standard existant. |
| Luminance | Moyenne | Pas aussi sombre que GLANCE (c'est le deuxième). |
| Bords | Arrondis (border-radius 6px) | Même traitement que GLANCE — les deux sont des mesures valides. |
| Label | "GRADE Symbols (74%)" | Référence claire. Le pourcentage est la donnée d'Akl. |
| Position | Milieu | Hiérarchie visuelle : deuxième. |

**Barre 3 — Vanity Metrics**

| Propriété | Valeur | Justification |
|---|---|---|
| Longueur | **~5%** de la barre GLANCE | Quasi-nulle. Bennett & Slattery 2023 : IRR 0.97 = aucun effet sur les citations. |
| Couleur | Bleu très clair (#A8DADC) | Délavé, faible, insignifiant. |
| Luminance | Très claire, presque transparente | P34 : clair = certitude nulle. |
| Bords | Arrondis (border-radius 6px) | Même forme mais la couleur/taille disent tout. |
| Label | "Vanity Metrics (~0%)" | Le mot "Vanity" est un jugement — assumé et justifié par la data. |
| Position | En bas | Dernier de la hiérarchie. |

### 5.4 Détails critiques des barres

**Échelle commune (P32) :** Les 3 barres partagent la même ligne de départ (alignées à gauche) et la même échelle (0-100%). L'axe 0-100% est visible en haut de la zone. Cleveland & McGill (1984) : la position sur une échelle commune est le canal le plus précis (rang 1). La longueur est le rang 3. En combinant les deux (barres alignées sur une échelle), on maximise la précision perceptive.

**Pas de couleurs qui encodent aussi la hiérarchie.** Les 3 barres ont des couleurs différentes pour les distinguer, mais la couleur ne porte pas le message hiérarchique — la longueur le fait. Si le GA était imprimé en noir et blanc, la hiérarchie resterait lisible (la barre la plus longue est la meilleure). C'est le test de robustesse : le message survit à la perte du canal couleur.

**Pas de valeurs numériques SUR les barres.** Les pourcentages sont dans les labels, pas dans les barres. Écrire "80%" en gros dans la barre teal tenterait le cerveau de comparer le chiffre 80 au chiffre 74 — un calcul Système 2. La comparaison de longueur est Système 1 (pré-attentive, < 250ms). On veut Système 1.

### 5.5 La validation croisée

Le badge optionnel : un petit checkmark (✓) à droite de la barre GLANCE. Il dit "validé" sans texte. Le teal + la longueur maximale + le checkmark = triple redondance. Si le lecteur ne perçoit qu'un des trois, le message passe.

---

## 6. Typographie

### 6.1 Hiérarchie typographique

| Niveau | Usage | Police | Taille | Poids | Couleur |
|---|---|---|---|---|---|
| H1 | Titre du GA (si présent) | Sans-serif (Inter, Helvetica, Arial) | 24px | Bold | #1D3557 |
| H2 | Labels des barres | Sans-serif | 16px | Semibold | #1D3557 (droite), #E63946 (gauche) |
| Body | Fréquences naturelles, annotations | Sans-serif | 12px | Regular | #8D99AE |
| Accent | Pourcentages dans les labels | Sans-serif | 16px | Bold | Même couleur que la barre correspondante |

### 6.2 Règles typographiques

**Maximum 30 mots total sur le GA.** (V3, contrainte VEC). Chaque mot doit justifier sa présence. Si un mot peut être remplacé par un élément visuel, il est supprimé.

Comptage estimé :
- "Engagement" (1) + "Comprehension" (1) + "6 RCTs · 538 participants" (4) + "Visual Spin" (2) = 8 mots Zone Gauche
- "GLANCE Comprehension ≥80%" (3) + "GRADE Symbols 74%" (3) + "Vanity Metrics ~0%" (3) + "5.0s" (1) = 10 mots Zone Droite
- Total : ~18 mots. Sous le budget.

**Pas de header "THE PROBLEM" / "THE SOLUTION".** La couleur EST le message. Les headers sont du bruit textuel qui double l'information visuelle. "Show, don't tell."

**Pas de phrases.** Uniquement des mots-clés et des chiffres. Le GA n'est pas un paragraphe — c'est un signal.

---

## 7. Formes et Textures

### 7.1 Zone Gauche — Angulaire et bruitée

| Propriété | Traitement | Justification |
|---|---|---|
| Lignes | Segments droits, angles vifs, pas de courbes | L'angularité signale la tension (Bar & Neta, 2006, *Psychonomic Bulletin*) |
| Bords des éléments | Sharp corners (border-radius: 0) | Contraste avec les coins arrondis de la Zone Droite |
| Texture de fond | Léger grain ou hachures subtiles | Le bruit visuel signale le désordre. Pas excessif — juste perceptible. |
| Direction des éléments | Divergente (les courbes s'écartent) | La divergence est le message |

### 7.2 Zone Droite — Arrondie et propre

| Propriété | Traitement | Justification |
|---|---|---|
| Barres | Coins arrondis (border-radius: 6px) | La rondeur signale la sécurité et la confiance (Westerman et al., 2012) |
| Fond | Blanc pur, aucune texture | La propreté signale l'ordre et la clarté |
| Alignement | Strict — toutes les barres alignées à gauche | L'alignement signale la rigueur méthodologique |
| Direction des éléments | Horizontale, ordonnée | L'ordre est le message |

### 7.3 Le contraste forme-émotion

Le lecteur qui voit le GA sans lire un seul mot ressent :
- Gauche : "ça part dans tous les sens, c'est tendu, quelque chose ne va pas" (rouge, angles, divergence)
- Droite : "c'est calme, c'est ordonné, c'est résolu" (bleu, arrondis, alignement)

Ce contraste émotionnel est le message principal. Les chiffres et les labels le confirment mais ne le portent pas. Si le GA est vu en thumbnail à 200px (condition TOC), seule la couleur et la forme sont perceptibles — le texte est illisible. Le message doit survivre à la perte du texte.

---

## 8. La Question du Titre

### 8.1 Faut-il un titre sur le GA ?

Le titre du paper est : *"GLANCE: A Standardized Protocol for Measuring Visual Comprehension of Scientific Graphical Abstracts"*

Option A — Pas de titre. Le GA parle seul. En condition nude (test GLANCE), l'absence de titre force le GA à encoder le message visuellement. Si S9b passe sans titre, le design est validé.

Option B — Titre court. "GLANCE — Beyond Visual Spin" ou simplement "GLANCE". En haut, centré, 24px bold bleu profond. Discret.

**Recommandation : Option B avec "GLANCE" seul.** Le nom du protocole est le minimum nécessaire pour que le GA soit identifiable dans un feed. Et "GLANCE" est un mot anglais courant — même sans contexte, il dit "coup d'œil" = 5 secondes.

En condition Title-only du test GLANCE, le titre complet du paper est affiché au-dessus du GA. Le Δ_spoiler mesure si ce titre spoile Q2. Le mot "GLANCE" seul sur le GA ne devrait pas spoiler.

---

## 9. Ce Qui N'est PAS sur le GA

Aussi important que ce qui y est.

| Élément exclu | Pourquoi |
|---|---|
| Le flowchart du protocole (profil → brief → image → Q1/Q2/Q3) | C'est de la procédure, pas un message. Le lecteur n'a pas besoin de savoir *comment* ça marche en 5 secondes. |
| Les noms des auteurs | Sur le GA du paper, pas dans le GA. |
| Le logo SciSense / Mind Protocol | Ce n'est pas une pub, c'est un paper. |
| Le mot "GLANCE" | Remplacé par "GLANCE" — plus lisible, plus mémorable. |
| Les mots "THE PROBLEM" / "THE SOLUTION" | Show, don't tell. La couleur est le message. |
| Les p-values | Trop technique pour le Système 1. Les fréquences naturelles (6 RCTs, 538 participants) sont plus lisibles. |
| Les références bibliographiques | Pas dans un GA. Dans le paper. |
| Le mode spotlight/stream | Détail méthodologique. Pas le message. |
| Le scoring sémantique / embeddings | Détail technique. Pas le message. |

---

## 10. Self-Test GLANCE — Prédictions

### 10.1 Mode Spotlight Nude

| Métrique | Prédiction | Raisonnement |
|---|---|---|
| S9a | ≥ 0.70 | Le problème (engagement ≠ compréhension) est visuellement saillant. Le rappel devrait contenir "engagement", "compréhension", "mesure", "visuel". |
| S9b | **≥ 0.80** (target) | La barre GLANCE est la plus longue de la Zone Droite. Si le lecteur a regardé la Zone Droite ≥ 1 seconde, le Système 1 l'identifie comme la barre dominante. Le risque est que le lecteur ne quitte jamais la Zone Gauche (les ciseaux sont visuellement dramatiques). |
| S9c | ≥ 0.40 | "Utiliseriez-vous les likes pour évaluer ?" — la Zone Gauche montre que l'engagement ne corrèle pas avec la compréhension. Le lecteur devrait répondre "non". |
| RT₂ | < 2500ms | Le 4AFC est visuel — la barre la plus longue est identifiable pré-attentivement. Si RT₂ > 3000ms, le lecteur hésite (les barres ne sont pas assez discriminantes). |

### 10.2 Risques identifiés

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Le lecteur reste bloqué sur la Zone Gauche (ciseaux + loupe) et ne regarde jamais la Zone Droite | Moyenne | S9b échoue | Rendre les barres de la Zone Droite plus grandes / plus saturées. Le bleu profond doit être aussi visuellement attirant que le rouge. |
| Le lecteur confond "GLANCE" avec le nom d'une métrique d'engagement (ça sonne comme "glance = coup d'œil rapide = superficiel") | Faible | S9b confus | Le label "Comprehension ≥80%" dissipe l'ambiguïté. |
| Le daltonien ne distingue pas les 3 barres | Faible | S9b échoue pour 8% des hommes | Les barres ont des luminances différentes (foncé / moyen / clair). Le test V14 vérifie ça. |
| Le GA est trop "design" et pas assez "scientifique" — un reviewer le rejette | Faible | Paper rejeté (pas S9b) | Le GA contient des fréquences naturelles (6 RCTs, 538), un benchmark (GRADE 74%), et un seuil (≥80%). C'est data-driven, pas décoratif. |

---

## 11. Production

### 11.1 Outil recommandé

Figma ou Illustrator. Pas PowerPoint (trop peu de contrôle sur les couleurs et les formes). Pas de générateur IA (Midjourney, DALL-E) — le GA doit être pixel-precise pour respecter les proportions P32.

### 11.2 Exports

| Format | Usage | Paramètres |
|---|---|---|
| PNG 1200×628 @ 300 DPI | Soumission paper PLOS ONE | Fond blanc, RGB |
| PNG 1200×628 @ 72 DPI | LinkedIn / site web / GLANCE test | Optimisé poids (<500KB) |
| SVG | Archive / modification future | Vectoriel, couleurs exactes |
| PNG 200×105 | Test TOC-sim (thumbnail) | Downscale — V7 stress test |

### 11.3 Checklist pré-validation

- [ ] ≤ 30 mots total
- [ ] Pas de header "THE PROBLEM" / "THE SOLUTION"
- [ ] Barre GLANCE = 100% longueur, GRADE = 74%, Vanity = ~5%
- [ ] Palette rouge-gauche / bleu-droite respectée
- [ ] Simulé en noir et blanc — la hiérarchie des barres reste lisible
- [ ] Simulé en daltonisme (Coblis) — les 3 barres restent distinctes
- [ ] Simulé en thumbnail 200px — le contraste rouge/bleu reste visible
- [ ] Chargé sur GLANCE et testé en mode Spotlight — S9b mesuré

---

*Le GA qui se teste lui-même.*
*Si ça passe, c'est la preuve. Si ça échoue, c'est la donnée.*
