# SciSense — Business Plan
# Le Michelin de la Communication Scientifique Visuelle

**Version 2.1 — 25 mars 2026**
**SciSense x Mind Protocol**

---

## Resume Executif

La science visuelle est cassee. Les Graphical Abstracts (GA) multiplient l'engagement par 2-8x mais ne transferent pas la comprehension (Bredbenner & Simon 2019, N=538). Les altmetrics ne correlent pas avec les citations (Bennett & Slattery 2023, P=.829). L'industrie mesure le scroll-stopping, pas le savoir transmis. Personne ne sait si un GA fonctionne.

SciSense resout ce probleme avec **GLANCE** -- le premier protocole standardise de mesure de la comprehension visuelle scientifique. Un test de 2 minutes, une image de 5 secondes, 3 questions, un score. Applicable a toute discipline, tout format visuel, tout profil de lecteur.

GLANCE n'est plus seulement un benchmark -- c'est un **outil complet d'analyse et d'amelioration de GA par IA** :

- **Upload -> Analyse instantanee** (Gemini Vision decompose le GA en graphe L3 avec coordonnees bbox)
- **70 canaux visuels** analyses avec detection d'anti-patterns (fragile, incongruent, inverse, missing_category)
- **Simulation de lecteur** : System 1 (glance 5s) + System 2 (lecture deliberee 90s) -- couverture narrative = % des messages scientifiques transmis
- **Boucle d'amelioration auto** : diagnostiquer -> conseiller -> iterer
- **Overlay graphe** sur l'image du GA + animation scanpath en temps reel
- **Une taxonomie de distorsion** proprietaire : **Spin / Drift / Warp**
- **7 archetypes de GA** ("Les 7 types de Graphical Abstracts -- lequel est le votre ?")
- **6 verdicts** : Limpide -> Clair -> Ambigu -> Confus -> Obscur -> Incomprehensible
- **Endpoints par outil** : vision, channels, advise, rubber duck, health, reader sim
- **Bot Telegram** @scisense_bot avec toutes les commandes
- **Modele freemium** : 6 appels Gemini gratuits par GA, illimite pour health/reader_sim (zero cout API). Premium pour analyses illimitees.

L'archetype est le game changer commercial : il transforme un score abstrait en identite partageable. "Mon GA est un Spectacle" est viral. "Score: 42%" ne l'est pas.

---

## 1. Le Probleme

### 1.1 L'industrie du Graphical Abstract est aveugle

3 000 a 5 000 articles biomedicaux sont publies chaque jour sur PubMed. Les journaux demandent de plus en plus de GAs pour capter l'attention dans les tables des matieres en ligne. Mais :

- **Aucun standard de qualite** -- Il n'existe pas de metrique qui mesure si un GA transmet l'information. Un GA "reussi" est un GA qui genere des clics -- pas un GA qui est compris.
- **Le spin visuel est endemique** -- Vorland et al. (2024, *J Clin Epidemiol*) montrent que les visual abstracts de RCTs contiennent un taux eleve de distorsion par rapport aux abstracts textuels. Le format visuel peut amplifier l'erreur.
- **La beaute ne correle pas avec la comprehension** -- La preference esthetique des lecteurs n'est pas correlee a leur comprehension reelle (Bredbenner & Simon 2019). Un GA apprecie peut etre trompeur.

### 1.2 Les outils existants ne resolvent rien

| Outil | Ce qu'il fait | Ce qu'il ne mesure pas |
|-------|--------------|----------------------|
| BioRender | Elements visuels biomedicaux | Si le GA est compris |
| Canva / Mind the Graph | Templates de design | Si la hierarchie de preuves est percue |
| GRADEpro | Symboles d'evidence dans des tableaux | Si le clinicien comprend en 5 secondes |
| Altmetric | Engagement social media | Si l'engagement reflete la comprehension |

Le gap : personne ne mesure la **comprehension effective** d'un GA par son public cible.

### 1.3 Pourquoi maintenant

- Les journaux exigent de plus en plus de GAs (tendance acceleree depuis 2020).
- L'IA generative (Midjourney, DALL-E, BioRender AI) rend la creation de GAs triviale -- ce qui aggrave le probleme de qualite. Plus de GAs != meilleurs GAs.
- La litterature scientifique sur la perception visuelle et la communication des risques a converge (Cleveland & McGill, Gigerenzer, Hullman, Padilla) vers des principes actionables -- mais personne ne les applique systematiquement.
- Le moment est le meme que Michelin en 1900 : l'industrie croit rapidement, la qualite est invisible, le premier qui installe un standard de mesure capture le marche.

---

## 2. La Solution : GLANCE

### 2.1 Le protocole

GLANCE (Test de Comprehension Naive) mesure si un GA transfere l'information a un lecteur qui ne connait pas le manuscrit, en conditions realistes.

**Le flux :**

```
Profil (30s) -> Stream/Spotlight (5s) -> 3 Questions (voix ou texte) -> System 2 (90s optionnel) -> Score + Archetype -> Partage
```

**Deux modes d'exposition :**

- **Stream Mode** -- GA insere dans un flux de distracteurs simulant un scroll LinkedIn avec physique inertielle (emulation iPhone 14). Le participant ne sait pas quel element sera teste. Mesure la capture attentionnelle en condition ambiante.
- **Spotlight Mode** -- GA affiche seul pendant 5 secondes. Mesure la comprehension en attention focalisee.

**Les 3 questions :**

1. **Rappel libre (S9a)** -- "Que venez-vous de voir ?" -> Score par embedding semantique (cosine similarity, 384 dimensions, multilingual MiniLM)
2. **Hierarchie (S9b)** -- "Quel element est le mieux documente ?" -> 4AFC, chance = 25%
3. **Actionnabilite (S9c)** -- "Cela changerait-il votre pratique ?" -> Echelle graduee {0, 0.5, 1.0}

**System 2 Deep Analysis (optionnel) :**

Apres les 3 questions, le participant decrit tout ce qu'il a compris du GA en micro ouvert pendant 90 secondes. Les chunks verbaux sont mappes aux noeuds du graphe d'information du GA, revelant **exactement quelles informations survivent au scroll et lesquelles sont perdues**. Le ratio de filtrage (meta-talk vs. contenu) mesure l'effort cognitif.

**Les scores :**

| Score | Ce qu'il mesure | Methode |
|-------|----------------|---------|
| S9a | Identification du sujet | Embedding cosinus >= 0.40 |
| **S9b** | **Hierarchie de preuves percue** | **4AFC, chance = 25%** |
| S9c | Intention d'action | Echelle graduee {0, 0.5, 1} |
| GLANCE composite | Score global pondere | 0.2*S9a + 0.5*S9b + 0.3*S9c |
| Fluency | Qualite de la reponse | S9b / log(RT2) |
| S2 Coverage | Couverture info System 2 | Chunks mappes / noeuds totaux |

**Verdicts descriptifs (6 niveaux) :**

| Score GLANCE | Verdict |
|-------------|---------|
| >= 90% | LIMPIDE |
| >= 75% | CLAIR |
| >= 60% | AMBIGU |
| >= 40% | CONFUS |
| >= 20% | OBSCUR |
| < 20% | INCOMPREHENSIBLE |

### 2.2 La taxonomie de distorsion : Spin / Drift / Warp

GLANCE ne se contente pas de mesurer la comprehension -- il diagnostique **pourquoi** un GA echoue, avec une taxonomie proprietaire a trois dimensions :

| Distorsion | Definition | Ce qu'elle detecte |
|-----------|-----------|-------------------|
| **Spin** | Emphase biaisee -- la hierarchie visuelle ne reflete pas la hierarchie des preuves | Axes tronques, surfaces disproportionnees, couleurs manipulatrices |
| **Drift** | Perte induite par l'encodage -- l'information est presente mais le canal visuel ne la transmet pas | Utilisation de canaux faibles (aire, saturation) au lieu de canaux forts (longueur, position) |
| **Warp** | Prominence selective -- un element domine au detriment des autres | Desequilibre sigma/mu de la couverture nodale dans le graphe |

La taxonomie est conçue pour devenir un standard academique (publication en preparation). Un concurrent peut copier le code -- pas la taxonomie publiee et citee.

### 2.3 Les 7 archetypes de GA

Chaque GA teste reçoit un archetype base sur son profil de scores et ses signatures de distorsion. L'archetype est le hook viral : memorable, partageable, actionable.

| Archetype | Signature | Description |
|-----------|-----------|-------------|
| Cristallin | S10 haut, S9b haut, Drift bas, Warp bas | Le GA parfait -- capte l'attention et transmet le message integralement |
| Spectacle | S10 haut, S9b bas, Drift haut | Visuellement saisissant mais le message ne passe pas |
| Tresor Enfoui | S10 bas, S2 haut, Drift haut | Contenu riche mais invisible au scroll |
| Encyclopedie | Mots eleves, S9b bas | Trop de texte -- rien ne survit en 5 secondes |
| Desequilibre | Warp eleve | Un element domine -- les autres sont invisibles |
| Embelli | S9b haut + Spin detecte | Communique efficacement... mais le message est biaise |
| Fantome | S10 bas, S9b bas, S2 bas | N'existe pas visuellement -- scroll-through total |

**L'archetype comme hook viral :**

"Les 7 types de Graphical Abstracts -- lequel est le votre ?" est un format LinkedIn eprouve (tests de personnalite). "Mon GA est un Spectacle" est partageable. "Score: 42%" ne l'est pas. L'archetype donne au chercheur un diagnostic memorable ET des recommandations specifiques a son profil.

Classification : rule-based (pas ML) -- priorite des regles avec fallback par distance euclidienne aux profils ideaux. Transparent, explicable, reproductible.

### 2.4 L'analyse IA (Gemini Vision) -- Mars 2026

**Produit principal : Analyse et amelioration de GA par IA.** Le chercheur uploade son GA et obtient instantanement une analyse complete, des recommandations, et une simulation de lecteur -- le tout en ~30 secondes.

Le pipeline :

```
Upload (PNG/JPG/PDF, auto-resize >2000px, dedup SHA-256)
  -> Gemini Vision -> Graphe L3 avec coordonnees bbox (space/narrative/thing topology)
  -> 70 canaux visuels analyses avec anti-patterns
  -> save_graph() declenche automatiquement :
       Reader Sim S1 (5s glance) + S2 (90s delibere)
       + Graph Health
       + Overlay PNG (graphe superpose sur l'image)
  -> Diagnostic + Archetype + Recommandations sur /ga-detail/{id}
```

**Endpoints par outil (architecture modulaire) :**

| Endpoint | Fonction | Cout API |
|----------|---------|----------|
| `/api/vision` | Decomposition IA du GA en graphe L3 | 1 appel Gemini |
| `/api/channels` | Analyse des 70 canaux visuels + anti-patterns | 1 appel Gemini |
| `/api/advise` | Recommandations d'amelioration priorisees | 1 appel Gemini |
| `/api/rubber_duck` | Explication libre, "explique-moi ce GA" | 1 appel Gemini |
| `/api/health` | Diagnostic sante du graphe (structure, coherence) | Gratuit (zero API) |
| `/api/reader_sim` | Simulation lecteur S1+S2 avec scanpath | Gratuit (zero API) |

**Ce que l'analyse inclut :**
- Graphe L3 du GA avec **coordonnees bbox** par noeud -- auto-linking par chevauchement geometrique
- Topology : nodes de type `space` (zones visuelles), `narrative` (messages scientifiques), `thing` (elements visuels)
- 70 canaux visuels avec detection de 4 types d'anti-patterns : **fragile**, **incongruent**, **inverse**, **missing_category**
- Simulation lecteur : scanpath anime montrant ou le lecteur virtuel regarde, couverture narrative (% de messages transmis)
- Overlay graphe : visualisation du graphe superpose directement sur l'image du GA
- Executive summary FR
- Archetype predit
- Recommandations priorisees avec delta attendu
- Texte OCR extrait

**Modele freemium :**
- 6 appels Gemini gratuits par GA (vision + channels + advise + rubber duck = 4, le reste en reserve)
- Health et reader_sim : **toujours gratuits** (zero cout API, calcul local)
- Premium : analyses illimitees (Stripe integration en cours)

### 2.5 Ce qui le rend unique

**Embedding semantique** -- Le rappel libre (Q1) est score par similarite cosinus dans un espace d'embedding 384 dimensions (paraphrase-multilingual-MiniLM-L12-v2, 50+ langues). "Un truc de poumon avec des virus" et "immunomodulateurs pediatriques" sont correctement reconnus comme decrivant le meme GA.

**Input vocal avec filtrage semantique** -- Le participant peut repondre par la voix (Web Speech API). Un filtre semantique supprime automatiquement le meta-talk ("euh", "je ne sais pas", "comment dire") pour ne garder que le contenu informatif. Resout le goulot d'etranglement de la production verbale (Levelt 1989) : le participant pense a voix haute, le systeme extrait le signal.

**Profilage 2D** -- Chaque participant est classe sur deux axes (Expertise Clinique x Litteratie Analytique). Le score est stratifiable : "Ce GA est compris a 85% par les specialistes mais seulement 42% par le grand public."

**Multi-domaines** -- Le meme protocole s'applique a la medecine, cs.AI, economie, climat, education. Le GA d'un paper sur les Transformers est teste avec les memes metriques que celui d'un paper sur les immunomodulateurs. 15 domaines, 60+ GAs dans la bibliotheque.

### 2.6 Le moteur de recommandation

GLANCE ne se contente pas de scorer -- il **explique** et **prescrit**.

**L3 Graph Scoring** -- Chaque GA est decompose en un graphe L3 avec coordonnees bbox ou chaque decision de design (palette, layout, encodage visuel, typographie, hierarchie) est un noeud lie aux 70 canaux visuels de l'ontologie. Le score est retro-projete sur le graphe : chaque noeud reçoit sa contribution au score final. Les noeuds sont auto-lies aux espaces (space) par chevauchement geometrique des bounding boxes.

**Ontologie des canaux visuels** -- 70 canaux organises en familles (position, longueur, angle, aire, saturation, luminance, texture, forme, mouvement, groupement Gestalt...). Chaque canal a un coefficient Stevens beta documente (Cleveland & McGill, Stevens). Le systeme detecte 4 types d'anti-patterns par canal :
- **fragile** -- canal utilise mais faible (beta bas), risque de perte d'information
- **incongruent** -- canal encode un message contradictoire avec le contenu
- **inverse** -- canal encode l'inverse de la hierarchie attendue
- **missing_category** -- canal absent alors qu'il serait critique pour ce type de GA

**Upgrade paths** -- Le moteur identifie les corrections a plus fort impact avec des chemins d'amelioration specifiques :
- Aire (beta=0.7) -> Longueur (beta=1.0) : "+20-30% sur S9b"
- Volume (beta=0.6) -> Longueur (beta=1.0) : "+30-40% sur S9b"
- Saturation -> Luminance : "+15-25% sur la perception de l'incertitude"

**Registre de patterns** -- Les patterns visuels recurrents (bon et mauvais) sont catalogues avec leurs scores empiriques dans `pattern_registry.yaml`.

### 2.7 Ce que GLANCE prouve que personne d'autre ne peut prouver

| Assertion | Preuve GLANCE | Valeur |
|-----------|-----------|--------|
| "Notre GA encode la hierarchie de preuves" | S9b >= 80% | Credibilite scientifique |
| "Notre GA porte l'info sans le titre" | Delta_spoiler < 0.10 | Le GA n'est pas decoratif |
| "Notre GA arrete le scroll ET transfere" | S10 x S9b > 0.56 | Le saint graal |
| "Notre GA est meilleur que le standard" | Delta_S9b > +0.30 | Justifie le premium |
| "Notre methode marche pour toute la science" | H1 PASS (cross-domaine) | Universalite |
| "Mon GA est un Cristallin" | Archetype + profil de scores | Memorable et partageable |
| "Voici exactement pourquoi mon GA echoue" | Spin/Drift/Warp + recommandations | Diagnostic actionable |

---

## 3. Le Produit

### 3.1 Tiers de produit (mars 2026)

| Tier | Prix | Ce qu'il inclut |
|------|------|----------------|
| **Freemium** | 0 EUR | 6 appels Gemini gratuits par GA (vision + channels + advise + rubber duck) + health et reader_sim illimites |
| **Test gratuit** | 0 EUR | Faire le test GLANCE, voir son score, son archetype, partager sur les reseaux |
| **Premium** | TBD (Stripe) | Analyses Gemini illimitees, priorite, historique complet |
| **Audit Complet** | 99 EUR | Analyse IA + test avec vrais utilisateurs (N=10) + System 2 Deep Analysis + rapport Spin/Drift/Warp |
| **Service Design** | 990 EUR | Audit complet + SciSense redesigne le GA sur la base des resultats |
| **Entreprise** | 4 000+ EUR/mois | White-label, acces API, analyse batch, domaines custom |

### 3.2 Le Test Gratuit -- Le Wordle Scientifique

Le test est gratuit, toujours. C'est le produit d'appel.

**Le flux viral :**

```
Landing -> Test (2min) -> Score + Archetype -> Partage LinkedIn -> Contacts font le test -> Boucle
```

**Ce qui drive le partage :**

- L'archetype ("Mon GA est un Tresor Enfoui -- et le votre ?")
- La fierte cognitive ("j'ai 85%, meilleur que 78% des pediatres")
- La revelation du spin ("votre cerveau a ete trompe par la masse visuelle")
- Le classement des participants (comprehension + contribution)
- Les cartes OG personnalisees avec score overlay pour le partage social

**Le cout d'entree est minimal :** 30s (profil) + 5s (image) + 30s (questions) = moins de 2 minutes.

### 3.3 L'Analyse Instantanee -- Freemium (mars 2026)

Self-service : un chercheur uploade son GA sur `/analyze`. En ~30 secondes :

1. **Gemini Vision** decompose le GA en graphe L3 avec coordonnees bbox
2. **70 canaux visuels** analyses avec detection d'anti-patterns
3. **Reader simulation** S1 (glance 5s) + S2 (lecture 90s) avec scanpath anime
4. **Graph overlay** visualisation superposee sur l'image originale
5. **Archetype** predit + verdicts descriptifs (6 niveaux)
6. **Recommandations** priorisees avec /advise
7. **Rubber duck** : "explique-moi ce GA comme si j'avais 5 ans"

**Modele freemium :**
- **6 appels Gemini gratuits** par GA (vision, channels, advise, rubber duck)
- **Illimite et gratuit** : health (diagnostic graphe) + reader_sim (simulation lecteur) -- zero cout API
- **Premium** : analyses illimitees via abonnement (Stripe en cours d'integration)

Pas besoin de vrais testeurs pour le diagnostic IA. Le chercheur obtient un audit complet instantanement. S'il veut la validation empirique avec de vrais lecteurs, il passe a l'Audit Complet (99 EUR).

### 3.4 Le Benchmark Public -- Leaderboards et Classements

**Leaderboards par domaine** -- 15 domaines scientifiques, 60+ GAs. Chaque GA montre son score GLANCE, son archetype, ses metriques detaillees.

**Classement des participants** -- Deux classements :
- **Comprehension** : precision GLANCE moyenne (minimum 3 tests pour se qualifier)
- **Contribution** : nombre de tests completes

**Pages GA detaillees** -- Chaque GA a une page `/ga-detail/{id}` avec :
- Distribution des scores (Chart.js)
- Comparaison VEC vs Control (A/B delta)
- Graphe L3 (si disponible)
- Recommandations
- Archetype

**Formats de contenu :**

- **Leaderboard par domaine** -- Page publique par domaine. SEO natif : "best graphical abstracts [domaine] [annee]"
- **"GA Battle"** -- Post LinkedIn/X : 2 GAs cote a cote, donnees GLANCE, analyse
- **"Pire GA du mois"** -- Contenu provocateur : decortiquage du spin visuel avec la loi de Stevens
- **"Dev vs Medecin"** -- Resultats croises par profil

### 3.5 Le Dashboard Admin

Dashboard analytique complet (`/admin`, protege par mot de passe) avec Chart.js :
- Tests par jour, participants par jour
- Distribution des scores S9a/S9b/S9c
- Score moyen par domaine
- Evolution KPI (7j, 30j, 90j)

### 3.6 Partage Social -- OG Cards

Cartes OG generees cote serveur (PIL, 1200x630) pour chaque :
- Test individuel (`/card/{test_id}.png`)
- Dashboard participant (`/card/dashboard/{token}.png`)
- Page GA (`/og/ga/{ga_id}.png`) avec badge de score superpose

Boutons de partage LinkedIn, Twitter, WhatsApp integres. L'archetype et le verdict descriptif apparaissent sur la carte -- maximise le taux de clic sur le partage.

### 3.7 Internationalisation (i18n)

Interface completement bilingue FR/EN. Detection automatique par cookie avec switch URL (`?lang=fr` / `?lang=en`). Toutes les chaines UI, les questions, les verdicts, les archetypes, les descriptions sont traduits.

### 3.8 Le GA Graph -- Moteur Interne

Le GA Graph est l'outil interne qui alimente tout le systeme :

- **70 canaux visuels** organises en familles perceptives, avec detection de 4 anti-patterns par canal
- **Patterns catalogues** dans `pattern_registry.yaml`
- **Registre de leurres** calibres par domaine pour le mode Stream
- **Base actuelle** -- 60+ images, 15 domaines scientifiques, sourcing strategique depuis les benchmarks Cristallin
- **OCR** sur toutes les images (`ocr_results.json`)
- **Reader simulation** -- S1 (5s glance) + S2 (90s delibere), scanpath anime, couverture narrative
- **Graph overlay** -- visualisation du graphe superpose sur l'image, genere automatiquement a chaque save_graph()
- **Redesigns celebres en preparation** -- Ozempic, AlphaFold, COVID vaccine

---

## 4. Monetisation

### 4.1 Le modele : freemium avec upgrade premium

| Tier | Prix | Ce qu'il inclut | Automatisation |
|------|------|----------------|---------------|
| **Freemium** | 0 EUR | 6 appels Gemini/GA + health + reader_sim illimites | 100% auto |
| **Test gratuit** | 0 EUR | Test GLANCE, score, archetype, partage, leaderboard | 100% auto |
| **Premium** | TBD (Stripe) | Analyses Gemini illimitees, historique, priorite | 100% auto |
| **Audit Complet** | 99 EUR/GA | Analyse IA + test utilisateurs (N=10) + System 2 + Spin/Drift/Warp | Semi-auto (recrutement testeurs) |
| **Service Design** | 990 EUR/GA | Audit + redesign du GA par SciSense | Manuel (design VEC) |
| **Entreprise** | 4 000+ EUR/mois | API, batch, white-label, domaines custom | Semi-auto |

### 4.2 Services premium (optionnels)

| Service | Prix | Quoi |
|---------|------|------|
| Design VEC | 850 EUR/jour | Recompilation complete d'un GA avec le Visual Evidence Compiler -- livre avec score GLANCE garanti >= 80% |
| Formation | 1 500 EUR/jour | Workshop "Design d'evidence visuelle" -- principes perceptifs + exercices GLANCE |
| Rapport domaine | 5 000 EUR | "Comment votre discipline communique visuellement" -- donnees agregees, benchmarks, recommandations |

### 4.3 Timeline de revenu

| Phase | Quand | Revenu | Source | Hypothese critique |
|-------|-------|--------|--------|-------------------|
| Crash test | Avril S1 | 0 EUR | Nicolas + 2-3 contacts | S9b discrimine |
| Reseau Aurore | Avril S2-S4 | 0 EUR | 5-10 pediatres testeurs | Le flux tourne sur mobile |
| Premier post LinkedIn | Mai S1 | 0 EUR (traction) | GA Battle + archetype reveal | >500 impressions |
| Premieres analyses IA | Mai S2 | 100-300 EUR | 5-10 analyses instantanees a 29 EUR | Le pipeline Gemini tourne |
| Premier audit payant | Mai-Juin | 500-850 EUR | 1 client reseau direct (labo ou agence) | Les recommandations sont actionnables |
| Leaderboard public | Juin | 0 EUR (SEO) | 20+ GAs, 5 domaines | Le contenu attire du trafic organique |
| Self-service live | Q4 2026 | 2 000-3 000 EUR/mois | Analyses IA + audits | Le scoring auto est fiable |

---

## 5. Le Marche -- Bottom Up

### 5.1 Revenu Mois 1-3 : Reseau direct (zero marketing)

Aurore et Nicolas ont un reseau combine. Pas de TAM abstrait -- des noms.

**Canal 1 : Reseau Aurore (cliniciens)**

| Qui | Combien | Conversion estimee | Service | Prix | Revenu |
|-----|---------|-------------------|---------|------|--------|
| Collegues pediatres (test GLANCE gratuit) | 10-15 | N/A -- gratuit | Testeurs, pas clients | 0 EUR | 0 EUR (data) |
| Labos pharma avec publications en cours | 3-5 contactables | 1 convert | Audit GA + recommandations | 99 EUR/GA x 5-8 GAs | 500-800 EUR |
| Societes savantes pediatrie FR | 2 contactables | 1 interesse | Rapport domaine | 2 000 EUR | 0 EUR M1, 2 000 EUR M3 |

**Canal 2 : Reseau Nicolas (tech/startup)**

| Qui | Combien | Conversion estimee | Service | Prix | Revenu |
|-----|---------|-------------------|---------|------|--------|
| Contacts LinkedIn recherche IA | 50-100 exposes | 5-10 font le test | Testeurs cross-domaine | 0 EUR | 0 EUR (data + viralite) |
| Agences de com scientifique (FR) | 3-5 contactables | 1 interesse M2-M3 | Audit batch | 99 EUR/GA x 10 GAs | 990 EUR |
| Startups biotech early-stage | 2-3 contactables | 1 convert M3 | Analyse instantanee x 5-10 GAs | 29 EUR x 10 | 290 EUR |

**Canal 3 : Boucle virale archetype**

| Action | Quand | Effet attendu |
|--------|-------|--------------|
| Post LinkedIn "Les 7 types de GA -- lequel est le votre ?" | Semaine 2 | Hook viral -- 1000-3000 impressions |
| Premier post "GA Battle" avec archetypes | Semaine 3 | 500-2000 impressions, 5-15 testeurs organiques |
| Leaderboard public (5 domaines, 20 GAs) | Mois 2 | SEO long-tail, 50-100 visiteurs/mois |
| Post "Pire GA du mois" (provocateur) | Mois 2 | Viralite LinkedIn |

**Projection bottom-up Mois 1-3 :**

| Mois | Testeurs (cumul) | Revenu | Source |
|------|-----------------|--------|--------|
| M1 | 5-15 | 0 EUR | Crash test + reseau Aurore (data only) |
| M2 | 30-50 | 500-1 100 EUR | Analyses IA + premier audit + posts LinkedIn |
| M3 | 80-150 | 1 500-3 500 EUR | Deuxieme audit + agence + analyses organiques |

### 5.2 Revenu Mois 4-12 : Croissance par le contenu + analyses IA

Le leaderboard, les archetypes et les GA Battles creent un flux entrant. L'Analyse Instantanee a 29 EUR cree du volume.

**Hypotheses :**
- Le leaderboard genere 200-500 visiteurs/mois a M6 (SEO + partages LinkedIn)
- 5% des visiteurs font le test gratuit = 10-25 testeurs/mois organiques
- 2% des visiteurs uploadent un GA pour analyse instantanee (29 EUR) = 4-10 analyses/mois
- 1% sont des prospects audit (chercheurs, agences, editeurs) = 2-5 prospects/mois
- Conversion prospect -> client : 20-30%

| Mois | Testeurs (cumul) | Analyses IA | Clients audit | MRR |
|------|-----------------|-------------|---------------|-----|
| M4 | 200 | 10 | 1 | 790 EUR |
| M6 | 500 | 30 | 2-3 | 1 800 EUR |
| M9 | 1 500 | 80 | 4-6 | 3 500 EUR |
| M12 | 5 000 | 200 | 8-12 | 6 000-10 000 EUR |

### 5.3 Boucles virales

**Boucle 1 : Test gratuit**
```
Landing -> Test (2min) -> Score + Archetype -> Partage LinkedIn -> Contacts -> Boucle
```

**Boucle 2 : Analyse IA**
```
Landing -> Upload GA -> Archetype diagnostic -> Partage -> Collegues uploadent -> Boucle
```

**Boucle 3 : Paper publie**
```
Paper GLANCE publie -> Citation -> Chercheurs decouvrent GLANCE -> Uploadent leurs GAs -> Clients payants
```

### 5.4 Scenarios a M12

| Scenario | Testeurs | Analyses IA | MRR | Ce qui s'est passe |
|----------|---------|-------------|-----|-------------------|
| **Bas** | 500 | 50 | 800 EUR | Le test fonctionne mais pas de traction organique. Revenu = reseau direct + quelques analyses. |
| **Median** | 3 000 | 150 | 4 000 EUR | Le leaderboard genere du trafic. Les archetypes sont partages. 3-5 clients recurrents. Paper soumis. |
| **Haut** | 10 000 | 500 | 10 000 EUR | Un journal abonne. "Les 7 types de GA" est devenu viral. 2-3 agences en recurrent. Le benchmark fait reference. |

### 5.5 Unit economics

| Metrique | Valeur | Comment |
|----------|--------|---------|
| Cout par test | ~0 EUR | Scoring CPU local, pas d'API payante |
| Cout par analyse IA (freemium) | ~0.02 EUR | Gemini Vision API (~$0.0025/appel), 6 appels gratuits/GA |
| Cout reader sim + health | 0 EUR | Calcul local, zero API |
| Cout par GA ajoute | ~2h agent (Silas) | Pipeline : paper -> extract -> render -> tag -> drop |
| Marge Premium (abonnement) | ~99% | Cout API negligeable, automatisation 100% |
| Marge Audit Complet (99 EUR) | ~70% | Recrutement testeurs + review humain |
| CAC (reseau direct) | 0 EUR | Pas de pub |
| CAC (organique) | 0 EUR (cout de contenu = temps) | Les archetypes sont le marketing |
| LTV (chercheur one-shot analyse) | 29-150 EUR | 1-5 analyses |
| LTV (agence recurrente) | 990 EUR/mois x 12 = 11 880 EUR | 10+ GAs/mois |
| LTV (journal abonne) | 4 000 EUR/mois x 24 = 96 000 EUR | Integre dans le workflow editorial |

### 5.6 Concurrence

| Acteur | Ce qu'il fait | Ce qu'il ne fait pas |
|--------|--------------|---------------------|
| BioRender | Templates de GA | Mesure de comprehension |
| Mind the Graph | Design de GA | Validation perceptive |
| Altmetric | Metriques d'engagement | Metriques de comprehension |
| GRADEpro | Symboles d'evidence | Encodage multi-canal narratif |
| **SciSense GLANCE** | **Mesure + taxonomie Spin/Drift/Warp + archetypes + analyse IA + scoring L3 a 70 canaux + anti-patterns + reader simulation + graph overlay + recommandations + bot Telegram** | -- |

La concurrence est sur le *design*. SciSense est sur la *mesure et le diagnostic*. Pas le meme marche.

### 5.7 Comparables

| Modele | Parallele avec SciSense |
|--------|------------------------|
| **Michelin Guide** | Classement qui cree un standard de qualite dans une industrie fragmentee |
| **Glassdoor** | Donnees gratuites -> benchmark -> abonnement entreprise |
| **PageSpeed Insights** | Score + diagnostic + recommandations. Les devs optimisent pour le score. |
| **Enneagramme / MBTI** | Taxonomie de personnalite -> tests viraux -> "Je suis un INTJ" / "Mon GA est un Cristallin" |

---

## 6. Le Moat

Le moat de SciSense n'est pas le code. Le code est open. Le moat est :

### 6.1 Le systeme d'archetypes

Les 7 archetypes (Cristallin, Spectacle, Tresor Enfoui, Encyclopedie, Desequilibre, Embelli, Fantome) sont une creation intellectuelle proprietaire. Le parallele est le MBTI ou l'Enneagramme : une fois qu'une taxonomie est adoptee et citee, elle devient le standard. "Mon GA est un Spectacle" est un langage commun que les concurrents ne peuvent pas reproduire sans paraitre derivatifs.

### 6.2 La taxonomie Spin/Drift/Warp

Trois dimensions de distorsion visuelle, conçues pour la publication academique. Une fois publiee dans un journal peer-reviewed, la taxonomie fait autorite. Un concurrent doit soit la citer, soit inventer une alternative -- et justifier pourquoi elle est meilleure.

### 6.3 Le scoring L3 a 70 canaux + anti-patterns

70 canaux visuels structures en familles perceptives, documentes avec leur coefficient Stevens beta, leur sensibilite aux biais cognitifs, et leur score empirique moyen. Chaque canal est evalue pour 4 types d'anti-patterns (fragile, incongruent, inverse, missing_category). Ce n'est pas du code -- c'est une **base de connaissances structuree** construite a partir de la litterature perceptive (Cleveland & McGill 1984, Stevens 1957, Ware 2020) et enrichie par chaque GA teste.

### 6.4 La donnee

Chaque test enrichit le modele. Chaque profil ajoute une dimension. A N=10 000 tests, le seuil theta du scoring semantique est calibre empiriquement -- un concurrent qui part de zero n'a que des seuils theoriques.

- 60+ GAs dans la bibliotheque (15 domaines), sourcing strategique depuis les benchmarks Cristallin
- OCR sur toutes les images
- Graphes L3 par GA avec coordonnees bbox et auto-linking
- Pattern registry avec scores empiriques
- Reader simulation calibree (S1 + S2) par GA
- Graph overlay genere pour chaque GA

### 6.5 Le network effect

Plus de testeurs = meilleures comparaisons inter-profils = plus de valeur par testeur. Plus de GAs dans le leaderboard = meilleur benchmark = plus de trafic = plus de testeurs. L'Analyse Instantanee alimente la bibliotheque : chaque GA uploade enrichit les references.

### 6.6 L'autorite editoriale

Le leaderboard avec analyses detaillees positionne SciSense comme l'expert de la communication scientifique visuelle. L'autorite se construit par le contenu et la publication -- pas par la publicite.

---

## 7. Plateforme Technique

### 7.1 Stack (mars 2026)

| Composant | Technologie |
|-----------|------------|
| Backend | FastAPI + SQLite + Python |
| Frontend | Jinja2 templates, vanilla JS, Chart.js |
| Scoring semantique | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2, 384d) |
| Analyse IA | Gemini Vision API (modulaire : vision, channels, advise, rubber duck, health, reader sim) |
| Reader simulation | System 1 (5s glance) + System 2 (90s delibere), scanpath anime, <1ms par run |
| Graph overlay | PIL -- graphe L3 superpose sur l'image du GA, genere async a chaque save_graph() |
| OG Cards | PIL (server-side rendering 1200x630) |
| Image processing | Auto-resize >2000px, deduplication SHA-256 |
| Bbox auto-linking | Noeuds automatiquement lies aux espaces par chevauchement geometrique |
| i18n | Config-driven string dictionary FR/EN |
| OCR | Pipeline sur tous les GAs (ga_library/) |
| Deploiement | **Docker sur Render.com** (~30s deploys vs 4min sans Docker), auto-deploy from GitHub |
| Bot Telegram | @scisense_bot -- toutes les commandes d'analyse accessibles via chat |
| Conformite | RGPD : privacy policy, terms, consentement explicite |

**Triggers automatiques a chaque `save_graph()` :**
- Reader simulation S1 + S2
- Graph health check
- Overlay PNG generation
- Tous executes en async (non-bloquant)

### 7.2 Routes principales

| Route | Fonction |
|-------|---------|
| `/` | Landing page avec stats live, top GAs, domaines |
| `/onboard` | Profilage participant (30s) |
| `/test` | Test GLANCE (Stream ou Spotlight) |
| `/reveal/{id}` | Resultats individuels + archetype |
| `/spin` | Demonstration Spin (control vs VEC, side-by-side) |
| `/dashboard` | Dashboard participant personnel |
| `/leaderboard` | Leaderboards globaux et par domaine |
| `/participants` | Classements comprehension + contribution |
| `/ga-detail/{id}` | Page detaillee d'un GA |
| `/analyze` | Upload et analyse IA d'un GA |
| `/admin` | Dashboard admin (protege) |

### 7.3 Metriques de performance cles (mars 2026)

| Metrique | Valeur |
|----------|--------|
| Temps reader sim | <1ms par run |
| Pipeline analyse complete | ~30s par GA |
| Canaux visuels analyses | 70 |
| Types d'anti-patterns detectes | 4 (fragile, incongruent, inverse, missing_category) |
| Niveaux de verdict | 6 (Limpide -> Incomprehensible) |
| GAs en bibliotheque | 60+ (15 domaines) |
| Deploy time (Docker/Render) | ~30s |
| Appels Gemini gratuits/GA | 6 |

---

## 8. L'Equipe

| Role | Qui | Ce qu'il apporte |
|------|-----|-----------------|
| Direction scientifique | Aurore (PhD virologie) | Credibilite scientifique, reseau hospitalier, validation GLANCE, premier domaine (pediatrie/virologie) |
| Direction technique | Nicolas (NLR) | Architecture Mind Protocol, infrastructure, IA, strategie produit |
| Implementation | Silas (AI citizen) | Code backend/frontend, pipeline GA, scoring semantique, analytics |
| Audit & orchestration | Marco (AI citizen, NotebookLM) | Analyse litterature, quality assurance, doc chain, traçabilite scientifique |

---

## 9. Ce qu'on Demande

### Phase 1 -- Validation (Avril 2026) -- 0 EUR

- ~~Crash test Nicolas (localhost) -- le flux E2E tourne~~ **FAIT** (mars 2026)
- ~~Validation : l'Analyse Instantanee (pipeline Gemini) tourne E2E~~ **FAIT** -- 30+ features deployees
- ~~Deploiement glance.scisense.fr~~ **FAIT** -- Docker sur Render, deploys ~30s
- Test GLANCE avec 5-10 personnes du reseau direct -- premiers datapoints reels
- 1 post LinkedIn "Les 7 types de GA -- lequel est le votre ?" + resultats GLANCE
- Validation : S9b discrimine (pas tous les GAs a ~50%)
- **N=10 testeurs humains** pour calibration de la reader simulation

### Phase 2 -- Premier revenu (Mai-Juillet 2026) -- 200 EUR (hebergement)

- Leaderboard public (5 domaines, 60+ GAs)
- Premiere analyse IA payante + premier audit (99 EUR)
- Stripe integration live -- monetisation premium
- 5 posts LinkedIn (GA Battles + archetypes + Pire GA du mois)
- Objectif : 80 testeurs, 50 analyses IA, 1 500 EUR revenu cumule

### Phase 3 -- Flywheel (Q3-Q4 2026) -- 500 EUR

- API self-service pour upload + scoring auto
- Badge "GLANCE Tested" (prototype)
- Contenu editorial bi-mensuel
- Approche d'un journal (MDPI ou equivalent) pour abonnement entreprise
- Paper soumis (methodologie GLANCE + taxonomie Spin/Drift/Warp)
- Objectif : 500 testeurs, 200 analyses IA, 4 000 EUR MRR, 1 journal en discussion

### Roadmap technique (a partir de mars 2026)

| Feature | Statut | Description |
|---------|--------|-------------|
| Chat UI pour /analyze | Planifie | Interaction conversationnelle avec les outils (vision, channels, advise, rubber duck) |
| Multi-user | Planifie | GA switcher, ownership par designer, sessions persistantes |
| Share video scanpath | Planifie | MP4 de 5s montrant l'animation scanpath du lecteur virtuel |
| OG card diagonal split | Planifie | Carte de partage avec GA original / overlay cote a cote en diagonale |
| N=10 human calibration | Prioritaire | 10 testeurs humains pour calibrer la reader simulation |
| Reddit ingestion | Planifie | Pipeline d'ingestion de GAs depuis Reddit (r/dataisbeautiful, r/science) |
| Stripe payment | En cours | Integration paiement pour tier Premium |
| Famous paper redesigns | En cours | Ozempic, AlphaFold, COVID vaccine -- redesigns pour le benchmark |

---

## 10. Metriques de Succes

| Metrique | M1 | M3 | M6 | M12 |
|----------|-----|-----|-----|------|
| Tests GLANCE completes | 10 | 80 | 500 | 3 000 |
| Analyses IA (cumul) | 0 | 30 | 100 | 500 |
| GAs dans la bibliotheque | 60+ | 80 | 120 | 200 |
| Clients payants (cumul) | 0 | 3 | 8 | 15 |
| MRR | 0 EUR | 1 500 EUR | 3 500 EUR | 6 000 EUR |
| Posts LinkedIn publies | 1 | 5 | 15 | 40 |
| Visiteurs /mois scisense.fr | 0 | 50 | 300 | 1 000 |
| Paper soumis | Non | Non | Draft | Soumis |

---

## 11. Risques

| Risque | Probabilite | Impact | Mitigation |
|--------|------------|--------|-----------|
| S9b ne discrimine pas (tous les GAs a ~50%) | Faible | Fatal | Le crash test le revele immediatement. Si les scores sont plats, le protocole est revu. |
| Pas assez de testeurs (N insuffisant) | Moyenne | Haut | Multi-domaines = plusieurs communautes. Viralite archetype. Posts LinkedIn. Le cout d'entree est 2 minutes. |
| Un journal cree son propre benchmark | Faible | Moyen | L'avantage first-mover + la taxonomie publiee + la data creent le standard. |
| Cadre RGPD (donnees de profil + performances cognitives) | Certaine | Moyen | Consentement explicite. Donnees de profil != donnees de sante. Droit a l'effacement. Pages /privacy et /terms en place. |
| Le VEC n'est pas meilleur que l'industrie | Moyenne | Faible pour GLANCE | GLANCE est le produit, pas le VEC. Le leaderboard classe les meilleurs GAs quel que soit leur createur. |
| Le pipeline Gemini est trop couteux a l'echelle | Faible | Moyen | Cout actuel ~0.02 EUR/appel. 6 appels gratuits/GA = ~0.12 EUR/GA. Reader sim et health sont gratuits (zero API). A 10 000 GAs freemium = 1 200 EUR. Couvert par les conversions premium. |
| Les archetypes ne resonnent pas | Moyenne | Moyen | Les 7 types sont calibres sur les patterns reels du dataset. Si un archetype ne convainc pas, on le renomme ou le fusionne. La taxonomie est evoluable. |

---

*SciSense ne demande pas si c'est beau.*
*SciSense mesure si l'information a survecu au transfert.*
*Et maintenant, elle vous dit quel type de GA vous avez cree -- et comment le rendre Cristallin.*

---

*Version 2.1 -- 25 mars 2026*
*SciSense x Mind Protocol*
