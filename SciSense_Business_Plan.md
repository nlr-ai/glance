# SciSense — Business Plan
# Le Michelin de la Communication Scientifique Visuelle

**Version 1.1 — 25 mars 2026**
**SciSense × Mind Protocol**

---

## Résumé Exécutif

La science visuelle est cassée. Les Graphical Abstracts (GA) multiplient l'engagement par 2-8× mais ne transfèrent pas la compréhension (Bredbenner & Simon 2019, N=538). Les altmetrics ne corrèlent pas avec les citations (Bennett & Slattery 2023, P=.829). L'industrie mesure le scroll-stopping, pas le savoir transmis. Personne ne sait si un GA fonctionne.

SciSense résout ce problème avec **GLANCE** — le premier protocole standardisé de mesure de la compréhension visuelle scientifique. Un test de 2 minutes, une image de 5 secondes, 3 questions, un score. Applicable à toute discipline, tout format visuel, tout profil de lecteur.

GLANCE n'est pas qu'un test — c'est un pipeline complet : **test + scoring L3 + explainabilité + recommandations**. Chaque GA est décomposé en un graphe de dimensions visuelles (75 canaux), scoré, et le système génère des recommandations priorisées avec l'amélioration S9b attendue par correction.

Le produit est le **benchmark**, pas le design. SciSense ne vend pas de belles images — SciSense mesure si une image transmet le savoir. Le design (VEC) est un service premium optionnel. Le benchmark est le cœur.

---

## 1. Le Problème

### 1.1 L'industrie du Graphical Abstract est aveugle

3 000 à 5 000 articles biomédicaux sont publiés chaque jour sur PubMed. Les journaux demandent de plus en plus de GAs pour capter l'attention dans les tables des matières en ligne. Mais :

- **Aucun standard de qualité** — Il n'existe pas de métrique qui mesure si un GA transmet l'information. Un GA "réussi" est un GA qui génère des clics — pas un GA qui est compris.
- **Le spin visuel est endémique** — Vorland et al. (2024, *J Clin Epidemiol*) montrent que les visual abstracts de RCTs contiennent un taux élevé de distorsion par rapport aux abstracts textuels. Le format visuel peut amplifier l'erreur.
- **La beauté ne corrèle pas avec la compréhension** — La préférence esthétique des lecteurs n'est pas corrélée à leur compréhension réelle (Bredbenner & Simon 2019). Un GA apprécié peut être trompeur.

### 1.2 Les outils existants ne résolvent rien

| Outil | Ce qu'il fait | Ce qu'il ne mesure pas |
|-------|--------------|----------------------|
| BioRender | Éléments visuels biomédicaux | Si le GA est compris |
| Canva / Mind the Graph | Templates de design | Si la hiérarchie de preuves est perçue |
| GRADEpro | Symboles d'évidence dans des tableaux | Si le clinicien comprend en 5 secondes |
| Altmetric | Engagement social media | Si l'engagement reflète la compréhension |

Le gap : personne ne mesure la **compréhension effective** d'un GA par son public cible.

### 1.3 Pourquoi maintenant

- Les journaux exigent de plus en plus de GAs (tendance accélérée depuis 2020).
- L'IA générative (Midjourney, DALL-E, BioRender AI) rend la création de GAs triviale — ce qui aggrave le problème de qualité. Plus de GAs ≠ meilleurs GAs.
- La littérature scientifique sur la perception visuelle et la communication des risques a convergé (Cleveland & McGill, Gigerenzer, Hullman, Padilla) vers des principes actionables — mais personne ne les applique systématiquement.
- Le moment est le même que Michelin en 1900 : l'industrie croît rapidement, la qualité est invisible, le premier qui installe un standard de mesure capture le marché.

---

## 2. La Solution : GLANCE

### 2.1 Le protocole

GLANCE (Test de Compréhension Naïve) mesure si un GA transfère l'information à un lecteur qui ne connaît pas le manuscrit, en conditions réalistes.

**Le flux :**

```
Profil (30s) → Brief (10s) → Image (5s chrono) → 3 Questions → Score → Suivant
```

**Les 3 questions :**

1. **Rappel libre** — "Que venez-vous de voir ?" → Mesure l'ancrage cognitif
2. **Hiérarchie** — "Quel élément est le mieux documenté ?" → Mesure si la hiérarchie de preuves est perçue
3. **Actionnabilité** — "Cela changerait-il votre pratique ?" → Mesure l'impact décisionnel

**Les scores :**

| Score | Ce qu'il mesure | Seuil |
|-------|----------------|-------|
| S9a | Le GA est-il reconnaissable ? | ≥60% |
| **S9b** | **La hiérarchie de preuves est-elle perçue ?** | **≥80%** |
| S9c | Le GA déclenche-t-il une intention d'action ? | ≥40% |
| S10 | Le GA capture-t-il l'attention dans un flux ? | >70% |
| Δ_S9b | Le GA est-il meilleur que le standard industrie ? | >+30% |

### 2.2 Ce qui le rend unique

**Embedding sémantique** — Le rappel libre (Q1) est scoré par similarité cosinus dans un espace d'embedding 768 dimensions, pas par mots-clés. "Un truc de poumon avec des virus" et "immunomodulateurs pédiatriques" sont correctement reconnus comme décrivant le même GA.

**Mode Stream** — Le GA est inséré dans un flux de distracteurs simulant un scroll de TOC. Le participant ne sait pas quel élément sera testé. Mesure la capture attentionnelle en condition ambiante — pas en condition d'examen.

**Profilage 2D** — Chaque participant est classé sur deux axes (Expertise Clinique × Littératie Analytique). Le score est stratifiable : "Ce GA est compris à 85% par les spécialistes mais seulement 42% par le grand public."

**Multi-domaines** — Le même protocole s'applique à la médecine, cs.AI, économie, climat, éducation. Le GA d'un paper sur les Transformers est testé avec les mêmes métriques que celui d'un paper sur les immunomodulateurs.

### 2.3 Le moteur de recommandation

GLANCE ne se contente pas de scorer — il **explique** et **prescrit**.

**L3 Graph Scoring** — Chaque GA est décomposé en un graphe L3 où chaque décision de design (palette, layout, encodage visuel, typographie, hiérarchie) est un nœud lié aux 75 canaux visuels de l'ontologie. Le score S9b est rétro-projeté sur le graphe : chaque nœud reçoit sa contribution au score final.

**Ontologie des canaux visuels** — 75 canaux organisés en familles (position, longueur, angle, aire, saturation, luminance, texture, forme, mouvement, groupement Gestalt...). Chaque canal a une bande passante perceptive documentée (Cleveland & McGill, Stevens). Le système sait quels canaux le GA utilise, lesquels il gaspille, lesquels il surcharge.

**Recommandations priorisées** — Le moteur identifie les corrections à plus fort impact : "Remplacer l'encodage par saturation (canal faible, bande passante 1.0 bit) par un encodage par longueur (canal fort, bande passante 3.25 bits) sur la variable principale améliorerait S9b de +0.12 à +0.18." Chaque recommandation a un ΔS9b attendu. Le chercheur sait exactement quoi corriger en premier.

**Registre de patterns** — Les patterns visuels récurrents (bon et mauvais) sont catalogués avec leurs scores empiriques. "Le pattern split-bar avec légende intégrée a un S9b moyen de 0.82 sur N=47. Le pattern camembert-3D a un S9b moyen de 0.31." Le registre grandit avec chaque GA testé.

### 2.4 Ce que GLANCE prouve que personne d'autre ne peut prouver

| Assertion | Preuve GLANCE | Valeur |
|-----------|-----------|--------|
| "Notre GA encode la hiérarchie de preuves" | S9b ≥ 80% | Crédibilité scientifique |
| "Notre GA porte l'info sans le titre" | Δ_spoiler < 0.10 | Le GA n'est pas décoratif |
| "Notre GA arrête le scroll ET transfère" | S10 × S9b > 0.56 | Le saint graal |
| "Notre GA est meilleur que le standard" | Δ_S9b > +0.30 | Justifie le premium |
| "Notre méthode marche pour toute la science" | H1 PASS (cross-domaine) | Universalité |

---

## 3. Le Produit

### 3.1 Le Benchmark Public — Le Leaderboard

Le cœur visible de SciSense : un classement public des GAs par domaine, classés par compréhension réelle.

**"Les 10 meilleurs Graphical Abstracts en immunologie 2025 — classés par compréhension, pas par likes."**

Chaque entrée montre :
- Le GA (image)
- Son score S9b, S10, RT₂
- Son **graphe L3** — la décomposition en canaux visuels avec la contribution de chaque canal au score
- Une analyse de *pourquoi* il fonctionne (ou échoue) — citant les principes perceptifs (Cleveland & McGill, Stevens, Gigerenzer)
- Les **3 corrections à plus fort impact** avec le ΔS9b attendu par correction

**Formats de contenu :**

- **Leaderboard mensuel** — Page publique par domaine. SEO natif : "best graphical abstracts [domaine] [année]"
- **"GA Battle"** — Post LinkedIn/X : 2 GAs côte à côte, données GLANCE, analyse. "Le Transformer bat le PREDIMED — voici pourquoi."
- **"Pire GA du mois"** — Contenu provocateur : "Ce GA trompe 70% des lecteurs. Voici l'illusion qui vous piège." Décortiquage du spin visuel avec la loi de Stevens.
- **"Dev vs Médecin"** — Résultats croisés par profil. Qui lit mieux la science ? Débat garanti.

### 3.2 Le Test Gratuit — Le Wordle Scientifique

Le test est gratuit, toujours. C'est le produit d'appel.

**Le flux viral :**

Le participant fait le test → voit son score + comparaison inter-profils → reçoit une carte partageable (score + profil, pas les réponses) → partage sur LinkedIn/X → ses contacts cliquent → boucle.

**Ce qui drive le partage :**

- La fierté cognitive ("j'ai 85%, meilleur que 78% des pédiatres")
- La révélation du spin ("votre cerveau a été trompé par la masse visuelle — voici la preuve mathématique")
- Le cross-domaine ("un dev qui bat un médecin sur un GA médical")
- Le streak (série de tests sans erreur)

**Le coût d'entrée est minimal :** 30s (profil) + 5s (image) + 30s (questions) = moins de 2 minutes pour le premier datapoint.

### 3.3 L'Audit GA à la Demande (99€)

Self-service : un chercheur ou un journal uploade son GA. Le système génère en 48h :

1. **Score GLANCE** — S9a, S9b, S9c, S10, Δ_S9b vs. industrie
2. **Graphe L3 du GA** — Décomposition complète : chaque décision de design mappée aux 75 canaux visuels, avec la contribution de chaque canal au score
3. **Analyse de couverture des canaux** — Quels canaux le GA utilise, lesquels sont sous-exploités, lesquels sont en conflit perceptif
4. **5 recommandations priorisées** — Chaque recommandation a un ΔS9b attendu : "Remplacer saturation → longueur sur la variable principale : +0.15 S9b estimé"

Exemple de diagnostic : "Votre GA encode la hiérarchie par la saturation — un canal que le cerveau ne lit pas intuitivement (bande passante 1.0 bit). Passez à la longueur (3.25 bits). Votre palette teal/vert fusionne pour 8% des hommes. Correction estimée : +0.18 S9b."

Le chercheur corrige lui-même avec la feuille de route, ou paie pour un service premium (VEC).

### 3.4 Le GA Graph — Outil Interne

Le GA Graph est l'outil interne qui alimente l'audit et le leaderboard. Il mappe chaque décision de design d'un GA sur les dimensions L3 :

- **75 canaux visuels** organisés en familles (position, longueur, angle, aire, couleur, texture, forme, groupement Gestalt...)
- **Patterns catalogués** — chaque pattern visuel récurrent est enregistré avec son score empirique moyen
- **Registre de leurres** — 32 leurres calibrés par domaine pour le mode Stream
- **Base actuelle** — 47 images, 15 domaines scientifiques

Le GA Graph n'est pas exposé directement — il est la base de données structurée derrière chaque recommandation, chaque score, chaque entrée du leaderboard.

---

## 4. Monétisation

### 4.1 Le modèle : le benchmark est gratuit, les services sont payants

| Tier | Prix | Ce qu'il inclut |
|------|------|----------------|
| **Gratuit** | 0€ | Faire le test, voir son score, voir le leaderboard public |
| **Chercheur** | 99€/GA | Upload + score GLANCE + graphe L3 du GA + analyse de couverture des canaux + 5 recommandations priorisées avec ΔS9b attendu par correction |
| **Journal** | 990€/mois | Audit batch (jusqu'à 50 GAs/mois) + rapports de recommandation par GA + accès leaderboard avec explainabilité complète + badge "GLANCE Tested" |
| **Entreprise** | 2 900€/mois | Tout Journal + API programmatique + export L3 graph (JSON/YAML) + registre de patterns custom + données stratifiées par profil + support |

### 4.2 Services premium (optionnels, ne dépendent pas du benchmark)

| Service | Prix | Quoi |
|---------|------|------|
| Design VEC | 850€/jour | Recompilation complète d'un GA avec le Visual Evidence Compiler — livré avec score GLANCE garanti ≥80% |
| Formation | 1 500€/jour | Workshop "Design d'évidence visuelle" — principes perceptifs + exercices GLANCE |
| Rapport domaine | 5 000€ | "Comment votre discipline communique visuellement" — données agrégées, benchmarks, recommandations |

### 4.3 Timeline de revenu

| Phase | Quand | Revenu | Source | Hypothèse critique |
|-------|-------|--------|--------|-------------------|
| Crash test | Avril S1 | 0€ | Nicolas + 2-3 contacts | S9b discrimine |
| Réseau Aurore | Avril S2-S4 | 0€ | 5-10 pédiatres testeurs | Le flux tourne sur mobile |
| Premier post LinkedIn | Mai S1 | 0€ (traction) | GA Battle + résultats GLANCE | >500 impressions |
| Premier audit payant | Mai-Juin | 500-850€ | 1 client réseau direct (labo ou agence) | Les recommandations priorisées sont actionnables |
| Leaderboard public | Juin | 0€ (SEO) | 20+ GAs, 5 domaines | Le contenu attire du trafic organique |
| Deuxième client | Juillet | 290-500€ | Inbound ou réseau | Le flywheel commence |
| Premier journal contacté | Q3 2026 | En discussion | MDPI ou équivalent | Le benchmark a >200 tests |
| Self-service live | Q4 2026 | 2 000-3 000€/mois | Chercheurs + agences | Le scoring auto est fiable (θ calibré) |

---

## 5. Le Marché — Bottom Up

### 5.1 Revenu Mois 1-3 : Réseau direct (zéro marketing)

Aurore et Nicolas ont un réseau combiné. Pas de TAM abstrait — des noms.

**Canal 1 : Réseau Aurore (cliniciens)**

| Qui | Combien | Conversion estimée | Service | Prix | Revenu |
|-----|---------|-------------------|---------|------|--------|
| Collègues pédiatres (test GLANCE gratuit) | 10-15 | N/A — gratuit | Testeurs, pas clients | 0€ | 0€ (data) |
| Labos pharma avec publications en cours (réseau congrès) | 3-5 contactables | 1 convert (premier client) | Audit GA + graphe L3 + recommandations | 99€/GA × 5-8 GAs | 500-800€ |
| Sociétés savantes pédiatrie FR | 2 contactables | 1 intéressé | Rapport "comment votre discipline communique" | 2 000€ | 0€ M1, 2 000€ M3 |

**Canal 2 : Réseau Nicolas (tech/startup)**

| Qui | Combien | Conversion estimée | Service | Prix | Revenu |
|-----|---------|-------------------|---------|------|--------|
| Contacts LinkedIn dans la recherche IA | 50-100 exposés à un post | 5-10 font le test gratuit | Testeurs cross-domaine | 0€ | 0€ (data + viralité) |
| Agences de com scientifique (FR) | 3-5 contactables | 1 intéressé M2-M3 | Audit batch de leurs GAs clients | 99€/GA × 10 GAs | 990€ |
| Startups biotech early-stage (réseau incubateur) | 2-3 contactables | 1 convert M3 | Audit GA + recommandations | 99€/GA × 3-5 GAs | 300-500€ |

**Canal 3 : Leaderboard organique**

| Action | Quand | Effet attendu |
|--------|-------|--------------|
| Premier post LinkedIn "GA Battle" avec données GLANCE | Semaine 3 | 500-2000 impressions, 5-15 testeurs organiques |
| Leaderboard public (5 domaines, 20 GAs) | Mois 2 | SEO long-tail, 50-100 visiteurs/mois |
| Post "Pire GA du mois" (provocateur) | Mois 2 | Viralité LinkedIn — le contenu à controverse performe |

**Projection bottom-up Mois 1-3 :**

| Mois | Testeurs (cumul) | Revenu | Source |
|------|-----------------|--------|--------|
| M1 | 5-15 | 0€ | Crash test + réseau Aurore (data only) |
| M2 | 30-50 | 500-850€ | Premier audit payant + posts LinkedIn |
| M3 | 80-150 | 1 500-3 500€ | Deuxième audit + agence + début organique |

### 5.2 Revenu Mois 4-12 : Croissance par le contenu

Le leaderboard et les GA Battles créent un flux entrant. Le revenu shift de "réseau direct" à "inbound".

**Hypothèses :**
- Le leaderboard génère 200-500 visiteurs/mois à M6 (SEO + partages LinkedIn)
- 5% des visiteurs font le test gratuit = 10-25 testeurs/mois organiques
- 1% des visiteurs sont des prospects (chercheurs avec un GA à auditer, agences, petits éditeurs) = 2-5 prospects/mois
- Conversion prospect → client : 20-30% (le diagnostic est factuel, pas un pitch)

| Mois | Testeurs (cumul) | Prospects inbound | Clients | MRR |
|------|-----------------|-------------------|---------|-----|
| M4 | 200 | 2-3 | 1 | 500€ |
| M6 | 500 | 5-8 | 2-3 | 1 500€ |
| M9 | 1 500 | 10-15 | 4-6 | 3 000€ |
| M12 | 5 000 | 20-30 | 8-12 | 5 000-8 000€ |

**Ce qui accélère :**
- Premier journal abonné (990€/mois) → crédibilité massive → les autres suivent
- Paper publié (méthodologie GLANCE) → citations → autorité académique → clients institutionnels
- 5 000 tests dans la base → le benchmark a de la valeur statistique → data licensing possible

**Ce qui bloque :**
- S9b ne discrimine pas → le produit est inutile (détecté au crash test M1)
- Zéro traction LinkedIn → le contenu ne résonne pas (pivoter vers l'outreach direct)
- Le scoring sémantique est trop bruité → les diagnostics sont non fiables (calibrer θ avec plus de données)

### 5.3 Scénarios à M12

| Scénario | Testeurs | MRR | Ce qui s'est passé |
|----------|---------|-----|-------------------|
| **Bas** | 500 | 500€ | Le test fonctionne mais pas de traction organique. Revenu = réseau direct uniquement. Viable comme side-project. |
| **Médian** | 3 000 | 3 000€ | Le leaderboard génère du trafic. 3-5 clients récurrents. Le paper est soumis. Début de flywheel. |
| **Haut** | 10 000 | 8 000€ | Un journal abonné. Le post "Pire GA du mois" est devenu viral. 2-3 agences en récurrent. Le benchmark fait référence. |

### 5.4 Unit economics

| Métrique | Valeur | Comment |
|----------|--------|---------|
| Coût par test | ~0€ | Hébergement mutualisé, scoring CPU local, pas d'API payante |
| Coût par GA ajouté à la bibliothèque | ~2h agent (Silas) | SELECT paper → EXTRACT data → RENDER → TAG → DROP |
| Coût marginal par client audit | ~30 min humain (review des recommandations auto) | Le graphe L3 + recommandations sont auto-générés, l'humain valide |
| CAC (réseau direct) | 0€ | Pas de pub, pas de cold email massif |
| CAC (organique) | 0€ (coût de contenu = temps) | Les GA Battles sont le marketing |
| LTV (chercheur one-shot) | 99-500€ | Single audit (1-5 GAs), pas de récurrence sauf nouveau paper |
| LTV (agence récurrente) | 990€/mois × 12 = 11 880€ | 10 GAs/mois pour leurs clients |
| LTV (journal abonné) | 990€/mois × 24 = 23 760€ | Churn bas si le benchmark est intégré dans leur workflow |

**Le ratio LTV/CAC est théoriquement infini en phase 1** (CAC = 0, LTV > 0). En pratique, le coût est le temps de Nicolas et Aurore pour le réseau direct, et le temps de Silas pour le contenu. Le vrai CAC est le coût d'opportunité.

### 5.5 Concurrence

| Acteur | Ce qu'il fait | Ce qu'il ne fait pas |
|--------|--------------|---------------------|
| BioRender | Templates de GA | Mesure de compréhension |
| Mind the Graph | Design de GA | Validation perceptive |
| Altmetric | Métriques d'engagement | Métriques de compréhension |
| GRADEpro | Symboles d'évidence | Encodage multi-canal dans un format narratif |
| **SciSense GLANCE** | **Mesure + scoring L3 + explainabilité + recommandations priorisées** | — |

La concurrence est sur le *design*. SciSense est sur la *mesure*. Pas le même marché.

### 5.6 Comparables

| Modèle | Parallèle avec SciSense |
|--------|------------------------|
| **Michelin Guide** | Classement qui crée un standard de qualité dans une industrie fragmentée. Le guide est gratuit, l'étoile est précieuse. |
| **Glassdoor** | Données gratuites (salaires) → benchmark → abonnement entreprise. Plus de données = plus de valeur pour tous. |
| **Journal Impact Factor** | Métrique standard qui gouverne les décisions d'un marché entier. Critiqué mais incontournable. |
| **Lighthouse (Google)** | Score de performance web. Gratuit, automatisé, avec diagnostic. Les développeurs optimisent pour le score. |

---

## 6. Le Moat

Le moat de SciSense n'est pas le code. Le code est open. Le moat est :

### 6.1 La donnée

Chaque test enrichit le modèle. Chaque profil ajoute une dimension. Chaque GA testé renforce le benchmark. À N=10 000 tests, le seuil θ du scoring sémantique est calibré empiriquement sur des données réelles — un concurrent qui part de zéro n'a que des seuils théoriques.

### 6.2 La méthodologie publiée

GLANCE_Mathematics.md est conçu pour devenir un paper. Premier framework quantitatif de compréhension des GAs, avec des choix mathématiques justifiés par la littérature (McNemar, Stevens, Cleveland & McGill, Signal Detection Theory, RSVP). Une fois publié et cité, SciSense est l'auteur de la méthodologie de référence. Un concurrent doit soit citer SciSense, soit inventer une alternative — et justifier pourquoi elle est meilleure.

### 6.3 L'ontologie des canaux visuels

75 canaux visuels structurés en familles perceptives, documentés avec leur bande passante (bits), leur sensibilité aux biais cognitifs, et leur score empirique moyen. Ce n'est pas du code — c'est une **base de connaissances structurée** construite à partir de la littérature perceptive (Cleveland & McGill 1984, Stevens 1957, Ware 2020) et enrichie par chaque GA testé.

Un concurrent peut copier le code du scoring. Il ne peut pas copier :
- Les 75 canaux avec leurs propriétés perceptives calibrées
- Le registre de patterns visuels avec scores empiriques (47 images, 15 domaines, 32 leurres)
- Le graphe L3 qui relie chaque décision de design à son impact sur S9b

L'ontologie est le moat intellectuel : elle encode des décennies de recherche perceptive en structure actionable.

### 6.4 Le network effect

Plus de testeurs = meilleures comparaisons inter-profils = plus de valeur pour chaque testeur. Plus de GAs dans le leaderboard = meilleur benchmark = plus de trafic = plus de testeurs. Le flywheel s'auto-renforce.

### 6.5 L'autorité éditoriale

Le leaderboard avec analyses détaillées positionne SciSense comme l'expert de la communication scientifique visuelle. Les journalistes citent le leaderboard. Les éditeurs de journaux consultent le classement. Les sociétés savantes commandent des rapports. L'autorité se construit par le contenu, pas par la publicité — et elle ne se copie pas.

---

## 7. L'Équipe

| Rôle | Qui | Ce qu'il apporte |
|------|-----|-----------------|
| Direction scientifique | Aurore (MD, pédiatre) | Crédibilité clinique, réseau hospitalier, validation GLANCE, premier domaine (pédiatrie) |
| Direction technique | Nicolas (NLR) | Architecture Mind Protocol, infrastructure, IA, stratégie produit |
| Implémentation | Silas (AI citizen) | Code backend/frontend, pipeline GA, scoring sémantique, analytics |
| Audit & orchestration | Marco (AI citizen, NotebookLM) | Analyse littérature, quality assurance, doc chain, traçabilité scientifique |

---

## 8. Ce qu'on Demande

### Phase 1 — Validation (Avril 2026) — 0€

- Crash test Nicolas (localhost) — le flux E2E tourne
- Test GLANCE avec 5-10 personnes du réseau direct — premiers datapoints réels
- 1 post LinkedIn avec résultats GLANCE — test de traction organique
- Validation : S9b discrimine (pas tous les GAs à ~50%)

### Phase 2 — Premier revenu (Mai-Juillet 2026) — 200€ (hébergement)

- Déploiement scisense.fr (VPS 20€/mois)
- Leaderboard public (5 domaines, 50 GAs)
- Premier audit payant dans le réseau d'Aurore (objectif : 1 client, 500€)
- 5 posts LinkedIn (GA Battles + Pire GA du mois)
- Objectif : 80 testeurs, 1 500€ revenu cumulé

### Phase 3 — Flywheel (Q3-Q4 2026) — 500€

- API self-service pour upload + scoring auto
- Badge "GLANCE Tested" (prototype)
- Contenu éditorial bi-mensuel
- Approche d'un journal (MDPI ou équivalent) pour abonnement
- Paper soumis (méthodologie GLANCE)
- Objectif : 500 testeurs, 3 000€ MRR, 1 journal en discussion

---

## 9. Métriques de Succès

| Métrique | M1 | M3 | M6 | M12 |
|----------|-----|-----|-----|------|
| Tests GLANCE complétés | 10 | 80 | 500 | 3 000 |
| GAs dans la bibliothèque | 47 | 60 | 100 | 200 |
| Clients payants (cumul) | 0 | 2 | 5 | 10 |
| MRR | 0€ | 1 500€ | 3 000€ | 5 000€ |
| Posts LinkedIn publiés | 1 | 5 | 15 | 40 |
| Visiteurs /mois scisense.fr | 0 | 50 | 300 | 1 000 |
| Paper soumis | Non | Non | Draft | Soumis |

Chaque chiffre est dérivé du bottom-up §5.1-5.3. Pas de "si on prend 1% du marché".

---

## 10. Risques

| Risque | Probabilité | Impact | Mitigation |
|--------|------------|--------|-----------|
| S9b ne discrimine pas (tous les GAs à ~50%) | Faible | Fatal | Le crash test le révèle immédiatement. Si les scores sont plats, le protocole est revu. |
| Pas assez de testeurs (N insuffisant) | Moyenne | Haut | Multi-domaines = plusieurs communautés. Viralité Wordle. Posts LinkedIn. Le coût d'entrée est 2 minutes. |
| Un journal crée son propre benchmark | Faible | Moyen | L'avantage first-mover + la data + la méthodologie publiée créent le standard. Un benchmark rival sans data cross-domaine n'a pas la même valeur. |
| Cadre RGPD (données de profil + performances cognitives) | Certaine | Moyen | Consentement explicite à l'onboarding. Données de profil ≠ données de santé. Droit à l'effacement. Avis éthique si publication. À résoudre avant le déploiement public. |
| Le VEC n'est pas meilleur que l'industrie | Moyenne | Faible pour GLANCE | GLANCE est le produit, pas le VEC. Si le VEC échoue, GLANCE reste un benchmark valide. Le leaderboard classe les meilleurs GAs quel que soit leur créateur. |

---

*SciSense ne demande pas si c'est beau.*
*SciSense mesure si l'information a survécu au transfert.*

---

*Document rédigé le 25 mars 2026*
*SciSense × Mind Protocol*
