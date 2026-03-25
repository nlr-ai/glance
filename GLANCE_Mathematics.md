# S2b — Modèle Mathématique
# De la réponse brute à la preuve quantitative

**SciSense × Mind Protocol — Mars 2026**

---

## 1. Variables Mesurées

Chaque test produit un vecteur de mesures brutes :

```
T = {
    participant_id,         -- identifiant unique (lié au profil)
    ga_id,                  -- quel GA a été montré

    -- Condition d'exposition (le contexte)
    exposure_mode,          -- 'spotlight' | 'stream'
    exposure_condition,     -- 'nude' | 'title_only' | 'toc_sim' | 'social_sim'
    stimulus_frame,         -- quel chrome autour de l'image (none | mdpi_grid | twitter_card | linkedin_card)
    stimulus_text,          -- texte accompagnant (null | titre seul | titre+auteurs | tweet complet)
    stimulus_image_width,   -- largeur effective en px (200 pour TOC, 500 pour social, 550 pour nude)

    -- Intégrité
    tab_switched,           -- bool : le participant a-t-il changé d'onglet pendant l'exposition ?
    exposure_actual_ms,     -- durée réelle d'exposition (≤5000 si tab switch)

    -- Q1 : Rappel libre
    q1_text,                -- rappel libre (string)
    q1_first_keystroke_ms,  -- temps entre apparition Q1 et première frappe (ms)
    q1_last_keystroke_ms,   -- temps entre apparition Q1 et dernière frappe (ms)
    q1_rt,                  -- temps entre apparition Q1 et soumission (ms)

    -- Q2 : Hiérarchie
    q2_choice,              -- choix hiérarchie (enum)
    q2_rt,                  -- temps entre apparition Q2 et clic (ms)

    -- Q3 : Actionnabilité
    q3_choice               -- (yes | no | need_more)
}
```

### Définition formelle du stimulus

Le GA n'existe jamais seul dans la nature. Le stimulus est un **triplet** :

```
Stimulus = (frame, text, image)
```

| Composant | Définition | Exemples |
|-----------|-----------|----------|
| `frame` | Le chrome visuel autour de l'image — la "coquille" de la plateforme | Aucun / grille TOC MDPI / card Twitter / card LinkedIn |
| `text` | Le texte accompagnant qui peut ancrer, spoiler, ou biaiser l'interprétation | Aucun / titre article / titre+auteurs / tweet 280 chars |
| `image` | Le GA à la résolution de la plateforme simulée | 200px (TOC thumbnail) / 500px (social) / 550px (nude) |

### Les conditions d'exposition

| Condition | Mode | Frame | Texte | Image width | Ce qu'on isole |
|-----------|------|-------|-------|-------------|----------------|
| **Nude** | Spotlight | Aucun | Aucun | 550px | Performance pure du design — le GA seul, sans aide ni spoiler |
| **Title-only** | Spotlight | Minimal | Titre de l'article | 550px | Effet du titre : spoile-t-il S9b ? |
| **Feed LinkedIn** | Stream | Card LinkedIn (avatar, boutons 👍💬↗🔖) | Titre + auteur + timestamp | 500px dans le feed | Condition écologique réseau social professionnel |
| **Feed LinkedIn nude** | Stream | Card LinkedIn (avatar, boutons) | **Pas de titre** — auteur + timestamp seulement | 500px | Isole la contribution du GA vs le titre en condition stream (H6, Δ_spoiler écologique) |
| **Feed Twitter** | Stream | Card Twitter (handle, boutons ♡🔁💬) | Tweet + titre | 500px | Condition écologique dissémination rapide |
| **TOC Journal** | Stream | Grille MDPI/Elsevier | Titre + auteurs | 200px thumbnail | Condition écologique la plus fréquente — le scan de TOC |

**Règle structurante : en mode stream, le titre est TOUJOURS présent.** Un feed sans titre ne simule rien. En mode spotlight, le titre est une variable contrôlée (nude = absent, title-only = présent).

**Pourquoi ces conditions :**

La condition **Nude** (spotlight only) est le baseline scientifique. C'est le seul moyen d'isoler l'effet du *design du GA* de tout contexte. Si S9b(Nude) < 0.80, le design est cassé — pas besoin de tester les autres conditions.

La condition **Title-only** (spotlight) est le test de spoiler. Si S9b(Title-only) >> S9b(Nude), le titre porte l'information — le GA est décoratif. Δ_spoiler = S9b(Title-only) - S9b(Nude) doit être faible (<0.10) pour un VEC réussi. C'est le piège documenté par Bredbenner & Simon (2019) : les GA captent l'attention mais le *texte* transfère la compréhension.

Les conditions **Feed** (stream) sont les conditions écologiques réelles. Le GA est vu avec son titre, dans un chrome de plateforme, au milieu d'autres posts, en scroll automatique. Le titre est toujours là parce que le titre est *toujours* là en réalité. La question n'est pas "le GA fonctionne-t-il sans titre ?" (Nude répond) mais "le couple titre+GA fonctionne-t-il dans le bruit d'un feed ?" (Stream répond).

La condition **TOC Journal** (stream) est le stress test ultime : le GA est un thumbnail de 200px dans une grille. C'est là que P6 (mobile-first) et V7 (lisibilité 50%) sont réellement mis à l'épreuve.

**Justification (paper)** : La distinction nude/contextualisé suit la méthodologie de Hollands & Spence (1998, *Applied Cognitive Psychology*) qui montrent que la performance de lecture des graphiques varie significativement selon la présence ou l'absence de contexte textuel. La simulation de plateforme (TOC, social media) suit le paradigme de validité écologique recommandé par Munzner (2014, *Visualization Analysis and Design*) : un résultat en laboratoire (nude) n'est généralisable que s'il tient en condition naturelle (contextualisé). La séparation en 4 conditions permet d'isoler chaque source de variance : design seul (nude), effet du titre (title-only), effet de l'échelle (TOC-sim), effet du texte social (social-sim).

### Priorité d'implémentation

| Phase | Mode + Condition | Ce qu'on apprend | Complexité |
|-------|-----------------|------------------|------------|
| MVP | Spotlight nude | Le design encode-t-il la hiérarchie seul ? | Trivial — ce qu'on a déjà |
| V2 | Spotlight nude + title-only | Le titre spoile-t-il ? | +1 ligne de texte au-dessus du GA |
| V3 | + Stream feed LinkedIn | Le GA survit-il au bruit d'un feed réel ? | Auto-scroll + chrome + distracteurs |
| V4 | + Stream TOC Journal | Le GA survit-il en thumbnail 200px ? | Grille + downscale |

### Ce que les nouvelles variables capturent

**`tab_switched`** — Mesure d'intégrité. Si le participant change d'onglet pendant les 5 secondes d'exposition, le test est **invalidé**. Il ne rentre pas dans les calculs de S9a/S9b/S9c. Détection côté client via `document.visibilitychange`. Pas de punition UX (pas de message d'erreur agressif) — le test est simplement marqué `invalid` en base et le GA suivant est proposé.

**`q1_first_keystroke_ms`** — Proxy de la **latence d'accès mémoire**. Le temps entre l'apparition de Q1 et le premier caractère tapé mesure la vitesse à laquelle le souvenir émerge. Un rappel immédiat (<1500ms) indique un ancrage fort (PH1 T=1s a fonctionné). Un délai long (>5000ms) indique une reconstruction effortée.

**`q1_last_keystroke_ms`** — Combiné avec `q1_first_keystroke_ms`, donne la **durée de production** : `q1_production_ms = q1_last_keystroke_ms - q1_first_keystroke_ms`. Une production longue avec un premier keystroke rapide = le participant a beaucoup à dire (riche encodage). Une production longue avec un premier keystroke lent = il cherche ses mots (encodage faible).

Le profil du participant ajoute 5 covariables :

```
P = {
    clinical_domain,        -- {pediatrician, gp, researcher_bio, tech_data, none}
    data_literacy,          -- {published_author, tech_data, general_public}
    experience_years,       -- {lt5, 5to15, gt15}
    grade_familiar,         -- {0, 1}
    color_vision            -- {normal, colorblind, unknown}
}
```

---

## 2. Les 3 Scores Primaires

### S9a — Reconnaissance Sémantique (Q1)

**Définition** : Le participant a-t-il identifié le sujet du GA ?

**Méthode** : Similarité cosinus entre l'embedding du texte de rappel libre et l'embedding d'une description de référence du GA.

```
S9a(q1_text, ref_text) = {
    1   si cos_sim(embed(q1_text), embed(ref_text)) ≥ θ
    0   sinon
}
```

où :
- `embed()` est un modèle d'embedding de phrases (sentence-transformers, e.g. `all-MiniLM-L6-v2` ou le endpoint Anthropic)
- `ref_text` est la description sémantique attendue, définie dans `ga_metadata`
- `θ` est le seuil de similarité (calibré empiriquement, point de départ : **θ = 0.35**)

Exemple immunomodulateur :
```
ref_text = "Immunomodulators preventing recurrent respiratory tract infections in children, 
            with evidence hierarchy comparing OM-85, PMBL, MV130, and CRL1505"
```

Le scoring par embedding résout le problème fondamental du recall libre : les participants ne répondent pas dans le vocabulaire du concepteur. "Un poumon attaqué par des virus avec des barres de couleurs" et "Graphical abstract sur les immunomodulateurs pédiatriques" désignent le même objet mais partagent zéro mot-clé. La similarité cosinus dans l'espace d'embedding capture cette équivalence sémantique.

**Score continu** : En plus du binaire S9a ∈ {0, 1}, on conserve la valeur continue :

```
S9a_raw(q1_text, ref_text) = cos_sim(embed(q1_text), embed(ref_text))    ∈ [-1, 1]
```

La distribution de `S9a_raw` sur N participants est plus informative que le binaire — elle révèle si les participants sont proches du seuil (signal faible mais présent) ou loin (GA non identifiable).

**Calibration de θ** : Le seuil θ = 0.35 est un point de départ. En phase 2 (N=20-50), on trace la courbe ROC de S9a_raw vs. jugement humain (un annotateur code manuellement "compris / pas compris" sur les 50 rappels) et on choisit θ qui maximise le F1-score. Ce θ calibré devient le standard SciSense pour toutes les missions futures.

**Métrique agrégée** :
```
Taux_S9a(GA) = Σ S9a(i) / N
```
où N = nombre de participants valides ayant testé ce GA.

**Justification du choix (paper)** : Le rappel libre (free recall) est la mesure standard de la rétention en psychologie cognitive depuis Tulving (1962). Nous préférons le rappel libre au rappel indicé (cued recall) car il mesure ce que le participant a spontanément encodé, sans indice qui pourrait reconstruire une mémoire absente. L'utilisation d'embeddings plutôt que de mots-clés pour le scoring automatisé suit la méthodologie de Cer et al. (2018, *SemEval*) qui montre que la similarité cosinus de sentence embeddings corrèle à r=0.78-0.86 avec le jugement humain de similarité sémantique, contre r=0.40-0.55 pour les méthodes lexicales (BLEU, keyword overlap). Le seuil θ est calibré empiriquement par courbe ROC sur un sous-ensemble annoté humainement, suivant la pratique standard en NLP appliqué (Manning et al., 2008).

### Le biais de la modalité de production (Q1) — Voice vs Texte

**Le problème** : Le rappel libre tapé au clavier ne mesure pas la compréhension. Il mesure l'intersection de la compréhension avec la motivation à taper. Un participant qui a parfaitement compris le GA mais écrit "un truc de poumon" par flemme produit un S9a_raw faible — le scoring punit la laziness, pas l'ignorance.

Ce biais a un nom : le **production bottleneck** (Levelt, 1989). La production écrite requiert trois étapes coûteuses que la production orale court-circuite :

1. **Formulation lexicale** — trouver le mot juste ("immunomodulateurs" vs "trucs pour le système immunitaire"). À l'oral, le locuteur utilise des approximations et des périphrases sans friction. À l'écrit, il s'autocensure ("je ne suis pas sûr de l'orthographe, je vais mettre un mot plus simple").
2. **Encodage moteur** — taper sur un clavier est 3-5× plus lent que parler (frappe ~40 mots/minute vs parole ~150 mots/minute, Wobbrock et al., 2006). Le participant optimise inconsciemment le ratio information/effort et coupe du contenu.
3. **Auto-édition** — le texte tapé est visible, relu, corrigé. Le locuteur oral produit un stream of consciousness non filtré, plus proche de la trace mnésique brute.

**La conséquence mesurable** : En condition texte, le rappel Q1 est typiquement 5-15 mots. En condition voice, les études sur le rappel libre verbal montrent des productions de 30-80 mots (Anderson & Conway, 1993, *Memory*). Le scoring sémantique reçoit un input 3-5× plus riche, ce qui augmente mécaniquement la qualité du matching : un vecteur d'embedding calculé sur 50 mots est plus discriminant qu'un vecteur sur 5 mots (la loi des grands nombres s'applique aux dimensions d'embedding).

**Le protocole** : Q1 propose un choix de modalité :

```
"Que venez-vous de voir ?"
    [🎤 Parler]    [⌨️ Taper]
```

Si voice :
1. Enregistrement audio (`MediaRecorder API` → blob webm)
2. Transcription temps réel (SpeechRecognition API browser-native, ou Whisper server-side en V2)
3. Affichage du transcript — le participant voit le texte et peut corriger les erreurs STT
4. Bouton "Valider" — le transcript corrigé devient `q1_text`
5. L'audio est stocké pour traçabilité (`data/audio/{test_id}_q1.webm`)

**Whisper avec vocabulaire guidé (V2)** : L'API Whisper accepte un `initial_prompt` qui biaise la reconnaissance vers un vocabulaire technique. Chaque GA metadata fournit un champ `whisper_prompt` contenant les termes techniques du paper ("immunomodulateurs OM-85 PMBL MV130 CRL1505 épithélium IgA RTI"). La reconnaissance des termes spécialisés passe de ~60% à ~95% avec ce seeding (Radford et al., 2022, *Robust Speech Recognition via Large-Scale Weak Supervision*).

**Variables stockées** :

```
q1_input_mode,          -- 'text' | 'voice'
q1_raw_transcript,      -- STT output AVANT édition utilisateur (null si text)
q1_edit_distance,       -- Levenshtein(raw_transcript, q1_text) — mesure l'erreur STT
q1_audio_path,          -- chemin vers le fichier audio (null si text)
q1_text,                -- texte FINAL (tapé ou transcript validé) — scoré par embedding
```

`q1_text` reste le champ unique d'entrée du scoring sémantique. Que le participant ait tapé ou parlé, `embed(q1_text)` est calculé sur le texte final validé. Le scoring ne change pas. Seul l'input change — il est plus riche en voice.

**Le problème du méta-talk (observé en crash test) :**

Le voice capture le stream of consciousness — y compris le méta-talk ("est-ce que ça marche", "trop bien ça", "j'ai envie de faire mon truc", "qu'est-ce que je voulais"). Sur un transcript réel de ~80 mots, ~15 sont du rappel et ~65 sont du bruit. L'embedding calculé sur les 80 mots est tiré vers le bruit — le cos_sim avec la référence est artificiellement bas. Le scoring punit la verbosité, pas l'ignorance.

En mode texte ce problème n'existe pas : l'auto-édition filtre le méta-talk gratuitement (personne ne tape "bon voilà c'est trop bien ça").

**Solution — Filtrage sémantique par phrases :**

Preprocessing du transcript voice AVANT le scoring :

```
1. Segmentation : découper q1_raw_transcript en phrases
   (par ponctuation STT ou pauses > 500ms dans l'audio)

2. Scoring par phrase : embed(phrase_i) vs embed(ref_text)
   → cos_sim_i pour chaque phrase

3. Filtrage : garder uniquement les phrases avec cos_sim_i > θ_filter
   θ_filter = 0.15 (seuil bas — filtre le bruit évident,
   garde les approximations pertinentes)

4. Recomposition : q1_text_filtered = join(phrases retenues)

5. Scoring final : S9a_raw = cos_sim(embed(q1_text_filtered), embed(ref_text))
```

**Exemple sur le crash test :**

```
Phrase                                              cos_sim    Retenue?
"alors est-ce que ça marche alors oui"              0.03       ✗ méta-talk
"j'ai vu abstract une comparaison matricielle       0.41       ✓ RAPPEL
 de mélanome de je sais pas quoi avec des 
 corrélations"
"oh non bon voilà toi c'est ça c'est trop bien ça"  0.02       ✗ méta-talk
"et ensuite il y a un abstract enfin il y a un       0.18       ✓ rappel vague
 paper qui expliquait"
"qui explique à tous les choix derrière"             0.08       ✗ trop vague
"je t'explique ainsi dire un business plan"          0.05       ✗ hors-sujet
"j'ai envie de faire mon truc là"                    0.01       ✗ méta-talk
"qu'est-ce que je voulais"                           0.01       ✗ méta-talk

→ q1_text_filtered = "j'ai vu abstract une comparaison matricielle 
                       de mélanome avec des corrélations. 
                       et ensuite il y a un paper qui expliquait"
→ S9a_raw passe de ~0.12 (sur 80 mots bruités) à ~0.38 (sur 20 mots filtrés)
```

Le filtrage n'invente rien — il retire le bruit. Le rappel réel est préservé. Le brut est toujours stocké (`q1_raw_transcript`) pour traçabilité et ré-analyse.

**Variables additionnelles :**

```
q1_text_filtered,       -- texte après filtrage sémantique (voice only, null si text)
q1_phrases_total,       -- nombre de phrases dans le transcript brut
q1_phrases_retained,    -- nombre de phrases retenues après filtrage
q1_filter_ratio,        -- phrases_retained / phrases_total (proxy du ratio signal/bruit)
```

`q1_filter_ratio` est une métrique intéressante en soi : un ratio de 0.20 (20% de signal) vs 0.80 (80% de signal) indique des styles cognitifs différents. Les "penseurs à voix haute" ont un ratio bas. Les "rapporteurs focalisés" ont un ratio élevé. En phase 4, on peut tester si le ratio corrèle avec S9b — les gens qui filtrent mal leur propre parole décodent-ils aussi mal les GAs ?

**Justification (paper)** : Le filtrage par seuil de similarité sémantique sur les segments du transcript suit la méthodologie de passage retrieval en NLP (Robertson & Zaragoza, 2009, *Foundations and Trends in IR*). Le seuil θ_filter = 0.15 est calibré pour maximiser le recall (ne pas perdre de rappel pertinent) au prix d'un peu de bruit résiduel — un choix conservateur justifié par le fait que l'embedding final tolère mieux le bruit résiduel que le signal manquant. Le stockage du transcript brut permet la ré-analyse avec des modèles de filtrage améliorés.

**Adaptation de la chronométrie keystroke** :

En mode voice, les métriques keystroke (`q1_first_keystroke_ms`, `q1_last_keystroke_ms`) sont remplacées par leurs équivalents vocaux :

| Métrique texte | Équivalent voice | Comment |
|---|---|---|
| `q1_first_keystroke_ms` | `q1_first_utterance_ms` | Temps entre apparition Q1 et début de la première détection vocale (SpeechRecognition `onresult` timestamp) |
| `q1_last_keystroke_ms` | `q1_last_utterance_ms` | Timestamp de la fin du dernier segment vocal détecté |
| `q1_rt` (soumission) | `q1_rt` (clic "Valider") | Identique — mesure le délai de validation post-production |

La latence d'accès (`q1_first_utterance_ms`) est l'**exact analogue** du Voice Onset Time (VOT) en psycholinguistique — le temps entre le stimulus et le début de la production verbale. C'est un proxy encore plus pur de la vitesse de récupération mnésique que le first keystroke, car il ne contient pas la latence motrice du clavier (Levelt, 1989, ch. 12).

**Hypothèse testable (H5)** :

```
H5 : S9a_raw(voice) > S9a_raw(text)
```

Si la voice produit des scores sémantiques systématiquement plus élevés, ça confirme que le bottleneck en condition texte est la production, pas la compréhension. Les deux populations (voice et text) sont marquées par `q1_input_mode` et ne doivent pas être agrégées sans contrôle : la modalité est une covariable dans la régression de phase 4.

```
logit(S9b) = ... + β₇·q1_input_mode
```

Si β₇ est non significatif, la modalité de Q1 n'affecte pas Q2 — les deux modes sont interchangeables pour le scoring. Si β₇ est significatif, la richesse du rappel vocal prédit un meilleur S9b — ce qui suggère que la qualité de l'encodage en mémoire (capturée par Q1) et la lecture de la hiérarchie (Q2) sont couplées.

**Justification du choix (paper)** : La supériorité du rappel oral sur le rappel écrit en termes de volume et de fidélité est documentée depuis Rubin (1977, *Memory & Cognition*) et confirmée par Kvavilashvili & Fisher (2007). Le bottleneck de production écrite a été formalisé par Grabowski (2008, *Written Language & Literacy*) qui montre que la transcription manuelle réduit le contenu du rappel de 30-40% par rapport à la dictée. L'approche bimodale (choix texte/voice) suit le principe d'accessibilité universelle et évite le biais d'exclusion des participants moins à l'aise avec le clavier (personnes âgées, cliniciens sur mobile, locuteurs non-natifs). Le stockage de l'audio brut garantit la traçabilité et permet une ré-analyse future avec des modèles STT améliorés. L'utilisation d'un `initial_prompt` Whisper pour le vocabulaire technique suit la recommandation de Radford et al. (2022) pour les domaines spécialisés.

### S9b — Hiérarchie Perceptive (Q2)

**Définition** : Le participant a-t-il identifié l'élément le mieux documenté ?

```
S9b(q2_choice, correct) = {
    1   si q2_choice == correct
    0   sinon (y compris "Je ne sais pas")
}
```

C'est **la métrique reine**. C'est elle qui valide P32 (longueur), P34 (luminance), V5 (hiérarchie). Si S9b est élevé, le VEC encode correctement. Si S9b est bas, le design est cassé.

**Métrique agrégée** :
```
Taux_S9b(GA) = Σ S9b(i) / N
```

**Seuils de décision** :
- Taux_S9b ≥ 0.80 → **PASS** — le VEC encode correctement
- 0.60 ≤ Taux_S9b < 0.80 → **WARN** — signal présent mais pas dominant
- Taux_S9b < 0.60 → **FAIL** — le design n'encode pas la hiérarchie

**Référence** : GRADE symboles = 74% compréhension (Akl 2007). Le VEC doit battre ce benchmark (≥80%) pour justifier sa supériorité.

**Justification du choix (paper)** : La question à choix forcé (forced-choice) est le standard en psychophysique pour mesurer la discrimination perceptive (Green & Swets, 1966, *Signal Detection Theory*). Le format 4AFC (4-Alternative Forced Choice) + option "Je ne sais pas" évite le biais de devinette : avec 4 options, le taux de chance est 25%. Un taux S9b de 80% représente donc un d' (d-prime) d'environ 2.3, indiquant une forte discrimination. Le seuil de 80% est choisi pour dépasser à la fois le taux de chance (25%) avec p<0.001 (test binomial, N≥10) et le benchmark GRADE (74%, Akl et al., 2007). L'option "Je ne sais pas" est comptée comme incorrect plutôt qu'exclue, suivant la recommandation de Krosnick et al. (2002) qui montrent que l'exclusion des "ne sais pas" surestime la compréhension réelle.

### S9c — Actionnabilité (Q3)

**Définition** : Le participant envisage-t-il un changement de pratique ?

```
S9c(q3_choice) = {
    1.0   si "yes"
    0.5   si "need_more_data"
    0.0   si "no"
}
```

L'échelle 0-0.5-1 capture la nuance : "besoin de plus de données" est une réponse scientifiquement honnête, pas un échec.

**Métrique agrégée** :
```
Score_S9c(GA) = Σ S9c(i) / N     ∈ [0, 1]
```

**Justification du choix (paper)** : L'actionnabilité est la métrique terminale d'un outil de knowledge translation (Grimshaw et al., 2012, *Implementation Science*). Nous utilisons une échelle ordinale à 3 points plutôt qu'un Likert à 5 ou 7 points car : (a) la question est posée après une exposition de 5 secondes — la granularité fine serait du bruit, (b) en condition d'incertitude, les échelles à 3 points produisent des données plus fiables que les échelles fines (Jacoby & Matell, 1971, *Journal of Marketing Research*). La valeur intermédiaire de 0.5 pour "besoin de plus de données" reflète le fait qu'en evidence-based medicine, demander plus de preuves est un comportement rationnel (Djulbegovic & Guyatt, 2017, *The Lancet*), pas un signe d'incompréhension.

### Diagnostic Adaptatif Post-Test (Q4-Q5)

Après Q1/Q2/Q3, le protocole pose 2-3 questions ciblées sur les **dimensions que l'algorithme a identifiées comme critiques** pour ce GA spécifique. Ce ne sont pas des questions fixes — elles changent par GA.

**Le principe : les dimensions critiques sont détectées, pas déclarées.** Le concepteur du GA ne déclare pas ses propres faiblesses — il les sous-déclarerait. Et pour les GAs uploadés par des tiers (audit à 99€), il n'y a pas de concepteur dans la boucle. Les `critical_dimensions` sont dérivées automatiquement de deux sources :

**Source 1 — Détection visuelle (analyse de l'image).** Un pipeline d'analyse d'image extrait les propriétés visuelles du GA et identifie les patterns à risque :

| Propriété détectée | Dimension critique déclenchée | Question générée |
|---|---|---|
| Encodage par aire (bubbles, blocs de taille variable) | P21 — Stevens β≈0.7 | "Les différences de taille vous ont-elles semblé proportionnelles ?" |
| Palette avec ΔE < 20 entre deux couleurs (CIEDE2000) | V14 — risque daltonisme | "Avez-vous eu du mal à distinguer certaines couleurs ?" |
| Densité textuelle > 40 mots | V3 — surcharge | "Les textes sur l'image étaient-ils lisibles ?" |
| Absence de barres/longueur comme canal primaire | P32 — canal sous-optimal | "La hiérarchie entre les éléments vous a-t-elle semblé claire ?" |
| Luminance uniforme (pas de gradient clair→foncé) | P34 — incertitude non encodée | "Pouviez-vous identifier quelles informations étaient les plus fiables ?" |
| Image > 50% remplie (peu d'espace blanc) | Densité visuelle | "L'image vous a-t-elle semblé chargée ou aérée ?" |

**Source 2 — Données accumulées (après N≥20 tests sur ce GA).** Les dimensions qui corrèlent avec S9b=0 émergent des données. Si 70% des participants qui échouent sur S9b répondent "tailles trompeuses" à Q4, P21 est confirmé comme la cause — indépendamment de toute analyse a priori. C'est la boucle de calibration : les premières questions sont choisies par la détection visuelle (Source 1), puis les données affinent le choix au fur et à mesure.

**Implémentation MVP (Source 1 simplifiée) :** En phase 1, pas de vision par ordinateur. Le registre de patterns VEC (`pattern_registry.yaml`) contient une table de risques par type d'encodage. Quand un GA est ajouté à la bibliothèque (manuellement ou via upload), le tagger catégorise les canaux visuels utilisés ("area", "length", "saturation", "luminance"). Le système lookup les dimensions critiques associées dans le registre. C'est semi-automatique mais pas subjectif — le tagger catégorise des faits visuels ("ce GA utilise des bulles de tailles différentes"), pas des opinions ("ce GA est bien").

```yaml
# pattern_registry.yaml — Table de risques par canal visuel
encoding_channels:
  area:
    risk: high
    pattern: P21
    justification: "Stevens β≈0.7 — area compresses perceived differences"
    question_en: "Did the size differences between elements seem proportional?"
    question_fr: "Les différences de taille entre les éléments vous ont-elles semblé proportionnelles ?"
  
  saturation:
    risk: high
    pattern: P34
    justification: "MacEachren 2012 — saturation is NOT intuitive for uncertainty"
    question_en: "Could you identify which information was most reliable?"
    question_fr: "Pouviez-vous identifier quelles informations étaient les plus fiables ?"
  
  length:
    risk: low
    pattern: P32
    justification: "Cleveland & McGill rank 3 — β≈1.0, near-linear"
    question_en: null  # No question needed — low risk
    
  color_pair_close:
    risk: medium
    pattern: V14
    justification: "ΔE < 20 CIEDE2000 — risk of confusion for ~8% of male population"
    question_en: "Did you have difficulty distinguishing any colors?"
    question_fr: "Avez-vous eu du mal à distinguer certaines couleurs ?"
    
  text_density_high:
    risk: medium
    pattern: V3
    justification: ">30 words — exceeds 5-second scan capacity"
    question_en: "Was the text on the image readable?"
    question_fr: "Les textes sur l'image étaient-ils lisibles ?"
```

Le `ga_metadata.json` ne contient pas `critical_dimensions` déclarées par le designer. Il contient `encoding_channels` (liste factuelle des canaux utilisés : `["area", "color_pair_close"]`). Le système resolve les dimensions critiques à runtime depuis le `pattern_registry.yaml`.

```json
// ga_library/sidecars/immunomodulators_vec.json
{
  "encoding_channels": ["length", "luminance", "area", "color_pair_close"],
  // critical_dimensions resolved at runtime from pattern_registry.yaml:
  // → area → P21 question
  // → color_pair_close → V14 question
  // (length and luminance are low-risk → no question)
}
```

**Le flux UX :**

```
[Après Q3 — Actionnabilité]

[Transition douce]
    "Deux dernières questions rapides sur l'image elle-même :"

[Q4 — Dimension critique #1 (la plus risquée)]
    "Les différences de taille entre les éléments vous ont-elles 
     semblé proportionnelles ?"
    [Oui, clairement]  [Pas sûr]  [Non, trompeur]

[Q5 — Dimension critique #2 (si applicable)]
    "Avez-vous eu du mal à distinguer certaines couleurs ?"
    [Non]  [Oui]

[→ Reveal]
```

Maximum 2-3 questions diagnostiques. Au-delà, la fatigue biaise les réponses. Les questions sont en langage non-technique — le participant ne sait pas qu'il évalue P21 ou V14. Il répond à son ressenti, qui est la donnée perceptive réelle.

**Ce que ça produit :**

| Donnée | Ce qu'on en fait |
|---|---|
| Q4/Q5 réponses × profil | Un daltonien qui dit "oui, difficile" sur la question couleur confirme V14 |
| Q4/Q5 réponses × S9b | Si S9b=1 mais Q4="trompeur" → le participant a compensé un design faible par un effort cognitif. Même signal que le filter_ratio. |
| Q4/Q5 agrégées par GA | "70% des participants trouvent les tailles trompeuses" → le concepteur sait que P21 est le problème, pas P32 |
| Q4/Q5 agrégées par dimension | "P21 est perçu comme trompeur dans 60% des GAs qui l'utilisent" → donnée pour le leaderboard et le VEC |

**Variables stockées :**

```
q4_dimension_id TEXT,            -- ex: "size_hierarchy" (from sidecar)
q4_pattern TEXT,                 -- ex: "P21"
q4_response TEXT,                -- ex: "Oui, clairement" | "Pas sûr" | "Non, trompeur"
q4_rt INTEGER,                   -- ms

q5_dimension_id TEXT,            -- ex: "color_distinguishability"
q5_pattern TEXT,                 -- ex: "V14"
q5_response TEXT,                -- ex: "Non" | "Oui"
q5_rt INTEGER,                   -- ms
```

**Justification (paper)** : Les questions diagnostiques adaptatives suivent le principe du Cognitive Task Analysis (CTA, Crandall, Klein & Hoffman, 2006) : au lieu de demander un jugement global ("est-ce bon ?"), on cible les dimensions spécifiques que l'analyse a priori identifie comme critiques. La sélection des dimensions depuis les metadata du GA est analogue au testing adaptatif en psychométrie (Computerized Adaptive Testing, Wainer et al., 2000) : chaque stimulus reçoit les questions les plus informatives pour lui, pas un questionnaire fixe. Limiter à 2-3 questions diagnostiques suit la recommandation de Krosnick (1999, *Annual Review of Psychology*) sur la fatigue de réponse : au-delà de 3 items post-stimulus, la qualité des réponses se dégrade significativement.

---

## 3. Les Métriques Temporelles

### RT₂ — Temps de Décision Hiérarchique

Le temps de réponse à Q2 (`q2_rt`) est un proxy de la **fluence perceptive**. Si le design encode bien, la réponse est rapide. Si le participant hésite, le signal est ambigu.

**Modèle** : RT₂ suit une distribution log-normale (comme tous les temps de réaction cognitifs).

```
log(RT₂) ~ Normal(μ, σ²)
```

On utilise la **médiane** (pas la moyenne) comme statistique de tendance centrale, robuste aux outliers.

```
Médiane_RT₂(GA) = median({q2_rt(i) : i ∈ participants_valides})
```

**Interprétation** :
- Médiane_RT₂ < 3000ms → Décision fluide, le canal perceptif primaire (longueur) a suffi
- 3000ms < Médiane_RT₂ < 8000ms → Hésitation, canaux secondaires mobilisés
- Médiane_RT₂ > 8000ms → Le design ne guide pas la décision

**Justification du choix (paper)** : Les temps de réaction en tâche de décision perceptive suivent une distribution log-normale, pas normale — propriété documentée depuis Luce (1986, *Response Times*) et confirmée par Ratcliff (1993). La médiane est donc l'estimateur approprié de tendance centrale, la moyenne étant biaisée par la queue droite. Le seuil de 3000ms est dérivé de la littérature sur le traitement visuel à deux systèmes (Kahneman, 2011) : le Système 1 (automatique, pré-attentif) traite les features visuelles en <250ms (Treisman & Gelade, 1980) mais la décision complète intégrant mémoire de travail prend 1-3s. Au-delà de 3s, le Système 2 (délibératif, effortful) est engagé — ce qui signifie que le design n'a pas réussi à rendre la hiérarchie "évidente" au sens perceptif.

### Couplage S9b × RT₂

La métrique la plus informative est le **Speed-Accuracy Tradeoff** :

```
                    S9b_correct (répondu juste)
                   /                           \
          RT₂ < 3s                              RT₂ > 3s
        "Fast & Right"                    "Slow & Right"
        (design parfait)                  (signal présent, effort requis)

                    S9b_incorrect (répondu faux)
                   /                           \
          RT₂ < 3s                              RT₂ > 3s
       "Fast & Wrong"                     "Slow & Wrong"
       (design trompe activement)         (design ne guide pas)
```

**"Fast & Wrong"** est le pire cas : le design envoie activement le mauvais signal. C'est exactement le **spin visuel** que Vorland et al. (2024) documentent.

**"Fast & Right"** est l'objectif : le cerveau décode la hiérarchie sans effort conscient, via le traitement pré-attentif (Treisman, <250ms pour les features ; la décision complète prend 1-3s).

### Invalidation : Tab Switch

```
valid(T) = {
    0   si tab_switched == true
    1   sinon
}
```

Un test invalidé est **enregistré mais exclu** de tous les calculs de S9a/S9b/S9c et des métriques temporelles. On ne le supprime pas — le taux d'invalidation lui-même est informatif :

```
Taux_invalidation(GA) = Σ (1 - valid(i)) / N_total
```

Un taux d'invalidation élevé (>20%) signale un problème UX (le brief n'a pas préparé le participant) ou un GA trop peu engageant (le participant s'ennuie et switch).

L'implémentation côté client est simple : `document.addEventListener('visibilitychange', ...)`. Dès que `document.hidden == true` pendant la phase d'exposition, `tab_switched = true`. Pas de message d'erreur agressif — juste un flag silencieux.

**Tous les N dans ce document sont des N_valides** : `N = Σ valid(i)`.

**Justification du choix (paper)** : L'exclusion des essais avec interruption d'attention est standard en psychophysique (Pashler, 1998, *The Psychology of Attention*). Un changement d'onglet pendant l'exposition réduit la durée de stimulation effective à une valeur inconnue, invalidant la comparabilité avec les essais complets (5000ms). Nous choisissons l'exclusion silencieuse plutôt que l'exclusion punitive (message d'erreur) pour deux raisons : (a) éviter l'effet de demande (demand characteristics — Orne, 1962) où le participant modifie son comportement parce qu'il se sent surveillé, (b) le taux d'invalidation lui-même est une métrique diagnostique de la qualité UX et de l'engagement. Les essais invalides sont *conservés en base* avec le flag `tab_switched=1` pour analyse secondaire — ils pourraient révéler des patterns (par ex. les profils "grand public" switchent plus que les cliniciens).

### Chronométrie Keystroke — La Dynamique du Rappel (Q1)

Le rappel libre (Q1) est la seule question ouverte. Les timestamps keystroke donnent 3 métriques dérivées qui racontent comment le souvenir émerge :

```
Latence d'accès     = q1_first_keystroke_ms
Durée de production = q1_last_keystroke_ms - q1_first_keystroke_ms
Délai de validation = q1_rt - q1_last_keystroke_ms
```

**Latence d'accès** (`q1_first_keystroke_ms`) :

Le temps avant la première frappe est un proxy de la vitesse de récupération mnésique. Le GA a disparu — le participant fouille sa mémoire de travail.

| Latence | Interprétation |
|---------|---------------|
| < 1500ms | Ancrage immédiat. Le choc cognitif PH1 (T=1s) a imprimé une trace forte. |
| 1500-4000ms | Récupération standard. L'information est là mais demande un effort. |
| > 4000ms | Reconstruction. Le participant ne se souvient pas clairement et compose. |

**Durée de production** (`q1_last_keystroke_ms - q1_first_keystroke_ms`) :

La longueur de la frappe, combinée à la latence, crée une matrice 2×2 :

```
                    Production courte          Production longue
                    (< 3000ms)                 (> 3000ms)
                 ┌────────────────────┬────────────────────┐
  Latence        │                    │                    │
  courte         │  Flash : sait      │  Riche : sait      │
  (< 1500ms)     │  exactement quoi   │  et a beaucoup     │
                 │  dire, le dit vite │  à dire             │
                 ├────────────────────┼────────────────────┤
  Latence        │                    │                    │
  longue         │  Minimal : cherche │  Laborieux : ne se │
  (> 1500ms)     │  puis résume en    │  souvient pas      │
                 │  un mot            │  clairement        │
                 └────────────────────┴────────────────────┘
```

"Flash" et "Riche" sont les bons signaux — le GA a imprimé. "Laborieux" corrèle avec S9a faible.

**Délai de validation** (`q1_rt - q1_last_keystroke_ms`) :

Le temps entre la dernière frappe et la soumission. Si > 3000ms, le participant relit et hésite. Si < 500ms, il soumet sans relire. Informatif pour la confiance subjective mais pas intégré au scoring.

**Justification du choix (paper)** : La décomposition du temps de réponse en latence d'initiation + durée de production + délai de validation est un paradigme standard en psycholinguistique (Levelt, 1989, *Speaking: From Intention to Articulation*). La latence d'initiation (time to first keystroke) est l'analogue écrit du voice onset time (VOT) utilisé en production verbale — elle mesure le temps de planification pré-articulatoire, qui est un proxy direct de l'accessibilité de la représentation en mémoire de travail (Baddeley, 2003). La durée de production reflète la quantité d'information encodée (Cowan, 2001, *The magical number 4*). La décomposition keystroke a été validée pour le scoring automatisé de rappel par Kalyuga & Sweller (2005) dans le contexte de la charge cognitive, et par Grabowski (2008) pour la mesure de la fluence rédactionnelle. Nous utilisons `performance.now()` (résolution sub-milliseconde, W3C High Resolution Time Level 2) plutôt que `Date.now()` (résolution ~15ms) pour garantir la précision temporelle.

---

## 4. Stratification par Profil

### La Matrice 2D

Les 2 axes du profil créent 4 quadrants :

```
                        Littératie Analytique
                    Basse               Haute
                 ┌───────────────┬───────────────┐
    Expertise    │               │               │
    Clinique     │  Q1: Public   │  Q2: Tech     │
    Basse        │  naïf         │  (Nicolas)    │
                 │               │               │
                 ├───────────────┼───────────────┤
                 │               │               │
    Expertise    │  Q3: Clinicien│  Q4: Clinicien│
    Clinique     │  non-data     │  + chercheur  │
    Haute        │               │               │
                 │               │               │
                 └───────────────┴───────────────┘
```

**Hypothèses testables** :

| Hypothèse | Prédiction | Ce que ça prouve si vrai |
|-----------|-----------|------------------------|
| H1 : Le VEC est universel | Taux_S9b(Q1) ≈ Taux_S9b(Q2) ≈ Taux_S9b(Q3) ≈ Taux_S9b(Q4) | Le design porte le savoir indépendamment de l'expertise |
| H2 : La littératie data aide | Taux_S9b(Q2) > Taux_S9b(Q1) | Les profils analytiques décodent mieux les barres (attendu) |
| H3 : L'expertise clinique court-circuite | Taux_S9b(Q4) > Taux_S9b(Q2) | La connaissance du domaine ajoute un canal (reconnaissance vs décodage) |
| H4 : Le daltonisme casse le signal | Taux_S9b(colorblind) < Taux_S9b(normal) | V14 n'est pas résolu |
| H5 : La voice capture mieux | S9a_raw(voice) > S9a_raw(text) | Le bottleneck est la production écrite, pas la compréhension |
| H6 : Le titre spoile en stream | S9b(stream+titre) > S9b(stream nude) | Le titre porte l'info, pas le GA — le fossé Bredbenner persiste |

**Test statistique** : Chi² d'indépendance (S9b binaire × quadrant catégoriel). Requiert N≥5 par cellule = N≥20 minimum. Fisher exact si N<5 par cellule.

**Justification du choix (paper)** : La matrice 2D (Expertise Clinique × Littératie Analytique) est motivée par la dissociation documentée entre domain knowledge et graph literacy dans la compréhension des représentations visuelles. Garcia-Retamero & Cokely (2017, N=27 885, 60 pays) ont montré que la numératie (notre axe Littératie) prédit la compréhension des aides visuelles indépendamment de l'expertise médicale. Okan et al. (2012, *Health Expectations*) confirment que la graph literacy — pas l'éducation générale — est le prédicteur dominant de l'interprétation correcte des graphiques de risque. H1 (universalité) est l'hypothèse la plus forte : si le VEC fonctionne, les quadrants ne devraient PAS différer significativement sur S9b, car le design compense les différences d'expertise. Un résultat non-significatif au chi² (p>0.05) est ici le résultat *souhaité* — ce qui justifie un calcul de puissance pour le risque β (erreur de type II) plutôt que le seul risque α. Avec N=20 par cellule (N=80 total) et α=0.05, la puissance de détecter un effet modéré (w=0.3) au chi² est de 85%.

---

## 5. Le Delta de Correction Cognitive (A/B Testing — V2)

Quand l'A/B séquentiel sera implémenté, chaque participant verra d'abord un GA contrôle (industrie) puis un GA VEC. Le delta mesure l'élimination du spin.

### Définition

```
Δ_S9b(participant_i) = S9b(VEC) - S9b(contrôle)     ∈ {-1, 0, +1}
```

Au niveau agrégé :

```
Δ̄_S9b = Taux_S9b(VEC) - Taux_S9b(contrôle)
```

### Interprétation

| Δ̄_S9b | Signification |
|--------|--------------|
| > +0.30 | Le VEC élimine massivement le spin. Publiable. |
| +0.10 à +0.30 | Amélioration modérée. Le design aide mais ne domine pas. |
| -0.10 à +0.10 | Pas de différence. Le VEC n'est pas meilleur que l'industrie. |
| < -0.10 | Le VEC est PIRE. Alarme design. |

### Test statistique

Les données sont appariées (même participant, deux conditions). Test de McNemar sur la table 2×2 :

```
                    VEC correct     VEC incorrect
Contrôle correct        a                b
Contrôle incorrect      c                d
```

```
χ² = (b - c)² / (b + c)
```

Si χ² > 3.84 (seuil p=0.05, 1 ddl) → différence significative.

**Puissance** : Pour détecter un Δ̄_S9b = 0.30 avec 80% de puissance et α=0.05, McNemar requiert N ≈ 30 paires. Avec un effet de 0.40 (attendu si le contrôle utilise l'aire comme encodage primaire et le VEC utilise la longueur), N ≈ 20 paires suffisent.

**Justification du choix (paper)** : Le test de McNemar (1947) est le test exact pour comparer deux proportions appariées sur données binaires. Le design intra-sujet (within-subject) est choisi plutôt qu'inter-sujet (between-subject) car il contrôle automatiquement toutes les variables individuelles (expertise, numératie, motivation) — chaque participant est son propre contrôle. Cela réduit la variance d'erreur et donc le N requis d'un facteur ~2-4 par rapport à un design entre-groupes (Fleiss et al., 2003, *Statistical Methods for Rates and Proportions*). L'ordre séquentiel (contrôle d'abord, VEC ensuite) introduit un biais d'apprentissage potentiel — le participant pourrait mieux performer sur l'image VEC simplement parce qu'il a compris le format. Ce biais joue *contre* notre hypothèse si le contrôle est aussi un GA, et *pour* notre hypothèse si le contrôle est un format très différent. En phase 4 (N=500+), un contrebalancement (randomisation de l'ordre) éliminera ce biais. Pour la phase 3 (N=30), le biais est documenté et accepté comme limitation. Le calcul de puissance suit Lachin (1992, *Controlled Clinical Trials*) pour le test de McNemar.

### Au-delà du binaire : le Score de Fluence

Le McNemar traite un succès à 1.5 secondes et un succès à 8 secondes comme identiques. Cliniquement, ce n'est pas le cas : un pédiatre qui identifie le bon immunomodulateur en 1.5s en mode stream va agir dessus. Un pédiatre qui met 8s a lutté — et dans un feed réel, il n'aurait pas eu 8 secondes. Le binaire S9b ∈ {0, 1} jette l'information temporelle.

**Score de Fluence :**

```
Fluence(i) = S9b(i) / log₂(RT₂(i))
```

où RT₂ est en millisecondes. Le log₂ compresse les RT très longs (un participant à 10s n'est pas 5× pire qu'un participant à 2s — il est juste lent) tout en préservant la discrimination dans la zone pertinente (1-5s).

| RT₂ (ms) | log₂(RT₂) | Fluence (si S9b=1) | Interprétation |
|---|---|---|---|
| 1000 | 10.0 | 0.10 | Instantané — Système 1 pur |
| 2000 | 11.0 | 0.091 | Rapide — bon encodage |
| 3000 | 11.6 | 0.086 | Normal — seuil Système 1/2 |
| 5000 | 12.3 | 0.081 | Lent — reconstruction |
| 8000 | 13.0 | 0.077 | Laborieux — le design n'a pas ancré |
| (si S9b=0) | — | 0.00 | Échec — quelle que soit la vitesse |

La Fluence est une métrique continue qui combine exactitude et vitesse. Un GA avec Fluence moyenne élevée encode à la fois correctement ET rapidement — c'est un meilleur indicateur d'impact réel qu'un S9b binaire.

**Pour l'A/B testing :** Au lieu du McNemar binaire, on peut utiliser un **modèle linéaire généralisé mixte (GLMM)** avec la Fluence comme variable dépendante continue :

```
Fluence(i,j) = β₀ + β₁·ga_version + β₂·clinical + β₃·literacy 
             + β₄·q1_filter_ratio + (1|participant_i) + ε
```

où `(1|participant_i)` est l'intercept aléatoire par participant (structure mixte). Le β₁ (effet de la version VEC vs contrôle) capture simultanément l'amélioration d'exactitude ET de vitesse. Le GLMM est plus puissant que le McNemar car il utilise une variable continue au lieu d'un binaire, et il contrôle les covariables directement dans le modèle.

**Quand utiliser quoi :**

| N | Test | Variable | Justification |
|---|---|---|---|
| N=10-30 | McNemar | S9b binaire | Robuste en petit échantillon, pas de distribution à vérifier |
| N=30-80 | GLMM | Fluence continue | Plus puissant, contrôle les covariables, exploite l'info temporelle |
| N>80 | GLMM + régression exploratoire | Fluence + 10 β | Modèle complet avec profiling, voice, dwell time, DPR |

Le McNemar reste le test de base pour le paper (simple, robuste, compréhensible par tous les reviewers). Le GLMM avec Fluence est l'analyse de sensibilité qui montre que le résultat tient avec une métrique plus riche.

**Justification (paper)** : La combinaison exactitude × vitesse en une métrique unique est standard en psychologie cognitive. Le Inverse Efficiency Score (IES = RT / accuracy) de Townsend & Ashby (1978) est l'ancêtre de cette approche. Notre formulation avec log₂(RT₂) est préférée à l'IES classique car elle est bornée (pas de division par zéro quand S9b=0), compresse les valeurs extrêmes, et est monotone dans les deux composantes. Le GLMM pour données appariées avec intercept aléatoire suit les recommandations de Baayen, Davidson & Bates (2008, *Journal of Memory and Language*) pour l'analyse de données psycholinguistiques avec effets croisés sujet × item.

---

## 6. Temporalité de la Preuve

### Phase 1 : Test Manuel (N=3-5, cette semaine)

Pas de statistique inférentielle possible. Données descriptives :
- Taux_S9b brut (ex: 4/5 = 80%)
- Rappels libres Q1 (analyse qualitative)
- RT₂ si mesurable (chronomètre téléphone)

**Critère de décision** : ≥4/5 correct sur S9b → go soumission MDPI

### Phase 2 : MVP Localhost (N=20-50)

Premiers tests d'hypothèse :
- Chi² S9b × profil (si N≥20)
- Médiane RT₂ avec intervalle interquartile
- Taux S9a, S9b, S9c par GA
- **Taux d'invalidation (tab switch)** — si >20%, diagnostic UX
- **Distribution latence d'accès Q1** — histogramme par profil
- **Corrélation latence Q1 × S9a** — la latence prédit-elle la reconnaissance ?

### Phase 3 : A/B Testing (N=30+)

McNemar sur paires contrôle/VEC + GLMM Fluence :
- Δ̄_S9b avec intervalle de confiance
- Fluence moyenne VEC vs contrôle (GLMM, β₁)
- Stratification par quadrant si N≥80 (20 par cellule)

**Invariant A/B : contexte de flux identique.** Quand un participant fait le test séquentiel (contrôle puis VEC), les deux GAs doivent être insérés dans un flux **rigoureusement identique** : même seed (= même séquence de flicks), mêmes distracteurs dans le même ordre, même position dans le feed. Seule l'image du GA change. Si le contrôle est entre une thumbnail vidéo et un post texte en position 5, le VEC est au même endroit avec les mêmes voisins. Sinon, on confond l'effet du design avec l'effet du contexte (un GA entre deux vidéos flashy a un S10 différent qu'un GA entre deux posts texte sobres). Le seed est partagé entre les deux sessions A/B d'un même participant et enregistré dans `test_results` (`stream_flick_seed`).

### Phase 4 : Données de masse (N=500+)

Régression logistique :
```
logit(S9b) = β₀ + β₁·clinical_domain + β₂·data_literacy + β₃·grade_familiar 
           + β₄·color_vision + β₅·ga_version + β₆·log(q1_first_keystroke_ms)
           + β₇·q1_input_mode + β₈·stream_target_dwell_ms + β₉·screen_dpr
           + β₁₀·q1_filter_ratio
```

β₅ est le coefficient du VEC : son effet net sur la compréhension, contrôlé pour toutes les covariables du profil.

β₆ teste si la latence d'accès mémoire (Q1) prédit indépendamment le succès sur Q2. Si β₆ est significatif et négatif (accès rapide → meilleure hiérarchie), cela confirme que l'ancrage PH1 et le décodage P32 sont couplés.

β₇ teste si la modalité de production (voice vs texte) affecte S9b. Si non significatif → les deux modes sont interchangeables.

β₈ teste si le dwell time du post cible (stream only) prédit S9b. Si significatif et positif → quantifie le temps minimum de transfert.

β₉ teste si la résolution d'écran affecte S9b. Un VEC robuste devrait avoir un β₉ non significatif.

β₁₀ teste si le ratio de filtrage cognitif (voice only, `q1_filter_ratio = phrases_pertinentes / phrases_totales`) prédit S9b. C'est la covariable la plus subtile : un participant avec S9b=1 et filter_ratio=0.20 a *lutté* — 80% de son rappel était du méta-talk, le GA a forcé le Système 2 pour reconstruire le souvenir. Un participant avec S9b=1 et filter_ratio=0.80 a rappelé fluidement — le Système 1 a encodé directement. Le même résultat binaire, une qualité d'encodage radicalement différente. Si β₁₀ est significatif et positif, la fluence du rappel prédit le décodage hiérarchique. Le GA idéal produit à la fois un S9b élevé ET un filter_ratio élevé : correct ET sans effort.

**Justification du choix (paper)** : La régression logistique est le modèle standard pour les variables dépendantes binaires en recherche clinique (Hosmer & Lemeshow, 2013, *Applied Logistic Regression*). La log-transformation de la latence Q1 (`log(q1_first_keystroke_ms)`) est nécessaire car les temps de réaction sont log-normalement distribués (Luce, 1986) — inclure la valeur brute violerait l'hypothèse de linéarité du logit. L'inclusion simultanée des covariables de profil et de la version du GA dans un modèle unique permet de tester l'effet du VEC *contrôlé pour* les différences individuelles — c'est l'équivalent statistique de la question "le design fait-il la différence, à profil constant ?". Si β₅ est significatif après contrôle, l'effet est attribuable au design, pas à la composition de l'échantillon. L'ajout de β₆ teste une hypothèse mécaniste (le couplage ancrage-décodage) qui, si confirmée, fournit une explication causale de l'efficacité du VEC, pas seulement une corrélation.

---

## 7. Le Score Composite (pour le dashboard)

Pour le `GET /api/stats` et l'affichage post-test, un score unique par test :

```
Score_S2b = (0.2 × S9a) + (0.5 × S9b) + (0.3 × S9c)     ∈ [0, 1]
```

Pondération :
- S9b pèse 50% car c'est la métrique reine (le VEC encode-t-il la hiérarchie ?)
- S9c pèse 30% car l'actionnabilité est le but final
- S9a pèse 20% car le rappel libre a la variance la plus élevée (dépend du vocabulaire, de la fluence rédactionnelle)

**Affichage** :
- Score_S2b ≥ 0.70 → "Décodage réussi"
- Score_S2b < 0.70 → "Le design n'a pas survécu au transfert"

**Justification du choix (paper)** : Le score composite est une commodité opérationnelle, pas une variable primaire d'analyse. Dans le paper, les 3 scores (S9a, S9b, S9c) seront rapportés séparément comme recommandé par les guidelines CONSORT pour les outcomes multiples (Moher et al., 2010). Le composite sert au dashboard temps réel et à la gamification (V2). Les poids (0.2/0.5/0.3) reflètent la hiérarchie de validité : S9b est un 4AFC avec taux de chance connu (25%) et scoring objectif ; S9c est un ordinal à 3 niveaux avec scoring semi-arbitraire (0/0.5/1) ; S9a dépend du modèle d'embedding et du seuil θ. Dans un paper formel, ces poids seraient dérivés empiriquement par analyse factorielle ou par Analytic Hierarchy Process (Saaty, 1980). Pour le MVP, ils sont fixés a priori et documentés comme tels.

---

## 8. Justification du Protocole d'Exposition — Du Spotlight au Stream

### Le biais du Spotlight

Le protocole initial (brief → countdown → image isolée 5s) place le participant en condition d'**attention focalisée** (spotlight attention). Le brief active le Système 2 (Kahneman, 2011). Le countdown pré-alloue la mémoire de travail. Le participant *sait* qu'il va devoir se souvenir de quelque chose et *sait* exactement quand ça va arriver.

C'est l'inverse du contexte écologique. Le pédiatre qui scrolle sa TOC MDPI à 23h est en **attention ambiante** : son regard balaie des thumbnails, des titres, des GAs — il ne sait pas lequel va l'interpeller. L'attention n'est pas *dirigée* vers le GA, elle est *capturée* par lui (ou pas). La différence est fondamentale en psychophysique : la capture attentionnelle (exogenous attention) est bottom-up et dépend des propriétés du stimulus, tandis que l'attention dirigée (endogenous attention) est top-down et dépend de l'instruction (Posner, 1980; Theeuwes, 2010).

Un protocole spotlight surestime systématiquement les taux S9a/S9b car il élimine la compétition attentionnelle. Le VEC ne sera jamais vu en condition spotlight dans la vraie vie.

### Le protocole Stream (v2) — Simulation de Feed Réel

Le GA cible est inséré dans un **feed auto-scrollant qui ressemble à une vraie plateforme** — pas un diaporama d'images nues.

#### Le stimulus en mode stream est un post complet

Chaque élément du flux est un **post** avec la structure d'un vrai réseau social ou d'une vraie TOC :

```
┌──────────────────────────────────────────────────┐
│  👤 Dr. Sarah Chen · Lancet Infectious Diseases  │
│     il y a 3h                                     │
│                                                    │
│  "Immunomodulators for Recurrent Respiratory      │
│   Tract Infections in Children: A Comparative     │
│   Review"                                          │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │                                              │ │
│  │              [  GRAPHICAL ABSTRACT  ]         │ │
│  │                                              │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  ♡ 47    💬 12    ↗ Share    🔖 Save              │
│                                                    │
└──────────────────────────────────────────────────┘
```

Les boutons like/comment/share/save sont **visuels mais non-fonctionnels**. Ils servent uniquement à mettre le cerveau en mode "je scrolle un feed", pas en mode "je passe un test". Le titre est **toujours présent** — c'est une composante indissociable du stimulus écologique.

#### Pourquoi le titre est obligatoire en mode stream

Sans titre, le mode stream ne simule rien. Dans la réalité :

1. Le titre est lu **avant** le GA — souvent le seul élément lu. L'eye-tracking sur les feeds Twitter montre que le regard va titre → image → engagement buttons (Bakhshi et al., 2014, *CHI*).
2. Le titre **ancre** l'interprétation. "A Comparative Review" dit au cerveau "il y a une comparaison" avant que l'image ne charge. C'est un primer cognitif.
3. Le titre peut **spoiler** — et c'est exactement ce qu'on veut mesurer. Si le titre dit "OM-85 shows strongest evidence", S9b(stream) mesurera le couple titre+GA, pas le GA seul. C'est la condition écologique réelle. Le mode spotlight en condition nude mesure le GA seul.

Les deux modes sont complémentaires, pas substitutifs :

| Ce qu'on mesure | Mode | Condition |
|-----------------|------|-----------|
| Le GA encode-t-il la hiérarchie seul ? | Spotlight | Nude |
| Le couple titre+GA fonctionne-t-il en contexte réel ? | Stream | Feed complet |
| Le titre spoile-t-il ? | Comparaison | S9b(stream) vs S9b(spotlight nude) |

#### Le scroll est automatique mais par à-coups (inertial flick)

Personne ne scrolle à vitesse constante — un scroll linéaire à 60px/s est un signal immédiat de "ceci est une animation". Le vrai scroll mobile est un pattern physique : **flick rapide → décélération exponentielle → micro-pause → flick**. Le scroll par à-coups résout le dilemme : il *ressemble* à un vrai scroll (validité écologique) tout en *contrôlant* le dwell time (validité expérimentale).

**Pourquoi auto-scroll plutôt que scroll libre :**

Le scroll libre introduit un confound fatal : le dwell time devient une *décision* du participant, pas une *propriété* du GA. Un participant lent aura 8s et S9b=90%. Un pressé aura 2s et S9b=40%. On ne sait pas si le S9b est bas parce que le *design* est mauvais ou parce que le *participant* scrolle trop vite. Le dwell time et le S9b sont confondus.

Avec scroll libre : N=60-120 requis + modèle mixte (dwell time comme covariable). Avec scroll par à-coups contrôlé : N=30 suffit pour le McNemar.

**Le modèle physique — décélération inertielle, calibrée dynamiquement :**

Principe Mind Protocol : zéro constante arbitraire. Chaque paramètre du scroll est **dérivé** d'une mesure réelle à runtime, pas hardcodé.

```
Friction coefficient:  γ = 0.96  (phénomène physique : ~25× distance de décélération)
Flick velocity:        v₀ = avgItemHeight / 25  (dérivé de la hauteur réelle des items rendus)
Pause duration:        p = ITEM_DURATION_MS - 700ms ± 30%  (cible le temps d'exposition config)
Target dwell:          ITEM_DURATION_MS = config.yaml → stream.item_duration_ms (default: 4000)
```

**Pourquoi aucun paramètre n'est hardcodé :**

- `v₀` dépend de `avgItemHeight` — si les posts sont plus grands (titre long, GA large), le flick est plus rapide pour compenser. Sur un écran 4K avec des posts de 600px, v₀ est différent que sur un mobile avec des posts de 350px. Le résultat : **chaque item est visible ~`item_duration_ms` quelle que soit la résolution ou la taille de l'écran.**
- `p` (pause) cible le dwell time configuré, pas un chiffre random. Si on veut 4 secondes de dwell time, la pause = 4000 - 700ms (temps de décélération) ± 30% de jitter (pour éviter la régularité artificielle).
- `γ = 0.96` est le seul vrai paramètre physique — c'est la friction d'un scroll tactile standard. Il n'est pas arbitraire, il modélise l'inertie réelle du doigt sur verre.

Le résultat : le feed accélère, décélère, s'arrête brièvement, repart. Le pattern est reconnaissable comme un vrai scroll mobile, et le dwell time est garanti ± 15% du target configuré.

```javascript
// Calibration dynamique à runtime
const items = document.querySelectorAll('.feed-post');
const avgItemHeight = Array.from(items).reduce((sum, el) => sum + el.offsetHeight, 0) / items.length;
const flickVelocity = avgItemHeight / 25;  // dérivé, pas hardcodé
const friction = 0.96;  // phénomène physique
const targetDwell = config.stream.item_duration_ms;  // depuis config.yaml
const pauseBase = targetDwell - 700;  // 700ms = temps de décélération moyen à γ=0.96
```

**Contrôle expérimental :** La séquence est déterministe pour un (seed, résolution) donné. Le dwell time varie *entre posts* (certains passent vite, d'autres lentement) mais pas *entre participants ayant la même résolution*. Le post cible est positionné dans un flick lent.

| | Scroll constant | Scroll inertiel calibré | Scroll libre |
|---|---|---|---|
| Perception | "Animation" → mode test | "Feed" → mode scan | "Feed" → mode scan |
| Dwell time | Fixe (~6.7s) | Calibré au target ± 15%, adapté à la résolution | Variable par tout |
| Constantes hardcodées | Oui (60px/s) | **Non** — tout dérivé de la résolution + config | N/A |
| Contrôle expérimental | Maximal mais artificiel | Fort et réaliste | Aucun (confound) |
| N requis (puissance 80%) | 30 | 30 | 60-120 |

**Variable dérivée :** Sur N sessions avec des seeds différents, le dwell time du post cible varie. `logit(S9b) = ... + β₈·stream_target_dwell_ms` quantifie le temps minimum dont le GA a besoin pour transférer la hiérarchie.

**V4 — Scroll libre instrumenté :** Quand N>200, un troisième mode mesure le vrai comportement d'arrêt (vitesse instantanée via `scroll` events). La corrélation "ralentissement devant un post" × "sélection dans le recall" valide S10 comme proxy du scroll-stopping réel.

**Justification (paper)** : La calibration dynamique des paramètres de scroll à partir de la hauteur rendue des items suit le principe de responsive experimental design : les paramètres du protocole s'adaptent à l'environnement d'affichage du participant plutôt que d'imposer des constantes qui ne sont valides que pour une résolution. La friction γ=0.96 correspond au coefficient de décélération des frameworks natifs iOS/Android (Baglioni et al., 2011, *CHI*). L'absence de constantes arbitraires dans le calcul du flick suit la philosophie "constant-free" : chaque nombre est soit un phénomène physique (γ), soit dérivé d'une mesure (avgItemHeight), soit configurable (item_duration_ms).

### Simulation mobile sur desktop (phone frame)

Sur desktop, le feed est affiché dans un **cadre de téléphone CSS** centré à l'écran. Sur mobile natif, le cadre est masqué — le viewport EST le téléphone.

**Device émulé : iPhone 14 — 390×844 CSS, DPR 3, aspect ratio 19.5:9**

Le choix est data-driven. StatCounter février 2026 montre que les largeurs CSS mobiles se concentrent dans la bande 360-414px (80%+ du marché). Les 3 résolutions dominantes :

| Résolution CSS | Part mondiale | Device | Note |
|---|---|---|---|
| 414×896 | 11.8% | iPhone 11/XR | Device de 2019, en déclin |
| 360×800 | 9.9% | Samsung mid-range | Surreprésenté marchés émergents |
| **390×844** | **6.9%** | **iPhone 13/14** | **Tendance montante, dominant chez les professionnels EU** |
| 393×873 | 4.6% | iPhone 15/16 | Nouveau standard, encore en montée |

**Pourquoi 390×844 :**

Notre audience (chercheurs/cliniciens en Europe) est biaisée iPhone — les professionnels de santé en France ont un taux d'iPhone supérieur à la moyenne. La résolution 390×844 est le milieu de la bande de fragmentation (ni la plus large à 414, ni la plus étroite à 360). C'est le cas *typique*, pas le cas optimiste. Si le design fonctionne à 390px de large, il fonctionne pour ~85% des devices mobiles.

```
Desktop:  ┌─── écran desktop ────────────────────────────────┐
          │                                                     │
          │         ┌──── 390×844 CSS ────────┐                │
          │         │  ╭────────────────────╮  │                │
          │         │  │                    │  │                │
          │         │  │ [feed auto-scroll] │  │                │
          │         │  │                    │  │                │
          │         │  ╰────────────────────╯  │                │
          │         └──────────────────────────┘                │
          │              corner-radius: 47px                    │
          └─────────────────────────────────────────────────────┘

Mobile:   Le feed occupe 100% du viewport. Pas de frame.
```

**Détection auto :** `window.innerWidth > 768 ? showPhoneFrame() : hidePhoneFrame()`.

Le corner radius (47px) et la notch simulée (barre de statut noire en haut) sont des indices contextuels qui disent au cerveau "tu es sur un téléphone" → activation du mode scan. Ce n'est pas décoratif — c'est un primer cognitif qui contribue à la validité écologique.

**Stress test multi-résolution (V3) :** Quand N est suffisant, les tests peuvent être rejoués en 360×800 (Samsung, pire cas) et 414×896 (iPhone 11, meilleur cas). La comparaison S9b(360px) vs S9b(390px) vs S9b(414px) mesure la robustesse du design au downscale.

### Résolution d'écran — variable stockée

La résolution du participant est une covariable critique. Un GA rendu à 200px sur un écran Retina (DPR=3, 600 pixels physiques) est objectivement plus lisible qu'à 200px sur un écran 1080p (DPR=1, 200 pixels physiques). Si on ne stocke pas la résolution, on confond la qualité du design avec la qualité de l'écran.

**Variables stockées à chaque test :**

```
screen_width INTEGER,           -- window.innerWidth (px CSS)
screen_height INTEGER,          -- window.innerHeight (px CSS)
screen_dpr REAL,                -- window.devicePixelRatio (1.0, 2.0, 3.0...)
screen_user_agent TEXT,         -- navigator.userAgent (device + browser)
screen_is_mobile INTEGER,       -- 1 si phone frame masqué (mobile natif), 0 si phone frame affiché (desktop)
```

`screen_dpr` est la variable la plus importante. En phase 4, elle entre dans la régression :

```
logit(S9b) = ... + β₉·screen_dpr
```

Si β₉ est significatif et positif, les écrans haute résolution améliorent S9b — ce qui signifie que le GA dépend de détails fins (micro-ancres P22, labels petits) qui disparaissent en basse résolution. Un VEC robuste devrait avoir un β₉ non significatif : le design fonctionne quelle que soit la résolution.

### Pixel de validation (exposure verification)

Un pixel de vérification confirme que le GA a bien été affiché pendant la durée attendue. C'est une mesure d'intégrité du protocole, pas du participant.

**Implémentation :** `IntersectionObserver` sur le post cible mesure :
- `stream_target_enter_ts` — timestamp d'entrée dans le viewport
- `stream_target_exit_ts` — timestamp de sortie du viewport
- `stream_target_dwell_ms = exit_ts - enter_ts` — dwell time réel mesuré

**Invariant :** Si `|stream_target_dwell_ms - config.stream.item_duration_ms| > 500ms`, le test est flaggé `exposure_valid = 0`. Le scroll n'a pas respecté sa calibration — bug technique, pas comportement du participant. Le test est exclu des analyses (même logique que `tab_switched`).

```sql
ALTER TABLE test_results ADD COLUMN stream_target_enter_ts REAL;    -- ms (performance.now)
ALTER TABLE test_results ADD COLUMN stream_target_exit_ts REAL;     -- ms
ALTER TABLE test_results ADD COLUMN exposure_valid INTEGER DEFAULT 1; -- 0 si dwell time hors tolérance
```

**Le flux UX :**

```
[Brief simplifié]
    "Vous allez voir un fil d'actualité scientifique défiler.
     Laissez-le passer — ne cliquez sur rien.
     Après le défilement, nous vous poserons des questions
     sur un des articles."
    ☑ J'ai compris

[Feed auto-scroll — 40-60 secondes]
    Post 1: [Titre réel + GA distracteur + boutons]    ← arrive, passe, sort
    Post 2: [Titre réel + figure d'article + boutons]  ← arrive, passe, sort
    Post 3: [Titre réel + GA distracteur + boutons]    ← arrive, passe, sort
    Post 4: [TITRE CIBLE + GA CIBLE + boutons]         ← arrive, passe, sort
    Post 5: [Titre réel + GA distracteur + boutons]    ← arrive, passe, sort
    Post 6: [Titre réel + texte abstract seul + boutons] ← arrive, passe, sort

[Le feed s'arrête — fondu noir]

[Écran de sélection]
    "Sur quel article portent les questions ?"
    → 3 thumbnails miniatures (titre + mini-GA) parmi les posts vus
    → Le participant clique sur celui dont il se souvient le mieux

[Branche conditionnelle post-sélection]

    SI le participant a sélectionné le post cible (S10 = 1) :
        → Q1, Q2, Q3 comme en mode spotlight
        → Score S9a/S9b/S9c normalement

    SI le participant a sélectionné un autre post (S10 = 0) :
        → "Autopsie du Rejet" (voir ci-dessous)
        → Puis Q1/Q2/Q3 sur le post QU'IL A CHOISI (données exploratoires)

    SI le participant clique "Aucune image ne m'a marqué" :
        → "Autopsie du Rejet" sur le GA cible
        → Pas de Q1/Q2/Q3 (pas de données de compréhension — le GA n'a pas été vu)
```

### Autopsie du Rejet (stream mode, S10 = 0)

Quand le participant n'a pas retenu le GA cible, le test ne s'arrête pas. Il capture *pourquoi*.

**Le flux :**

```
[Le GA cible est affiché en spotlight forcé — plein écran, 5s]
    "Vous avez ignoré cette image lors du défilement. Pourquoi ?"

    □ Trop chargé / Je ne sais pas où regarder
    □ Aspect amateur ou décoratif
    □ Trop de texte sur l'image
    □ Ennuyeux / Déjà vu / Rien de nouveau
    □ Je ne l'ai simplement pas remarqué
    □ Autre : [champ libre]
```

**Chaque option est mappée sur un pattern VEC violé :**

| Motif de rejet | Pattern violé | Action corrective |
|---|---|---|
| "Trop chargé / illisible" | P29 (Densité Locale) ou P26 (Espace négatif) | Réduire les éléments, augmenter le whitespace |
| "Aspect amateur / clip-art" | P20 (Abstraction Professionnelle) | Passer au line art vectoriel, typographie froide |
| "Trop de texte" | V3 (Budget 30 mots) | Couper le texte, laisser le visuel porter |
| "Ennuyeux / déjà vu" | PH1 (Choc Cognitif) absent | Ajouter une métaphore visuelle (P3), un ancrage émotionnel |
| "Pas remarqué" | Saillance pure = 0 | Le GA manque de contraste, de couleur signal, ou de taille dans le feed |

**Variables stockées :**

```sql
ALTER TABLE test_results ADD COLUMN rejection_autopsy INTEGER DEFAULT 0;  -- 1 si l'autopsie a été déclenchée
ALTER TABLE test_results ADD COLUMN rejection_reason TEXT;                 -- motif sélectionné
ALTER TABLE test_results ADD COLUMN rejection_free_text TEXT;              -- champ libre si "Autre"
```

**Valeur analytique :** L'autopsie transforme un S10=0 (donnée binaire pauvre) en un diagnostic actionable. "Votre GA est ignoré par 88% des lecteurs" est frustrant. "Votre GA est ignoré par 88% des lecteurs, et 65% l'ont catégorisé comme 'trop dense' en moins de 2 secondes" est un diagnostic pour lequel un journal paie 990€/mois.

**Valeur pour le paper :** La distribution des motifs de rejet par profil (quadrant 2D) est une donnée originale. Si les cliniciens rejettent pour "trop de texte" et les data scientists pour "aspect amateur", c'est une preuve que le design doit cibler un profil — et que le profilage S2b est nécessaire.

**Justification (paper)** : Le recueil du motif de rejet post-hoc suit la méthodologie du "think-aloud protocol" adapté en format fermé (Ericsson & Simon, 1993, *Protocol Analysis*). Les catégories de rejet sont dérivées de la taxonomie des échecs de communication visuelle de Jambor & Bornhäuser (2024, *PLOS Comput Biol*, 10 rules for GAs). Le mapping catégorie → pattern violé permet un diagnostic automatisé sans intervention humaine.

#### Variantes de feed simulé

**Plateformes cibles — liste définitive :**

Le GA n'est jamais vu dans le vide. Il est vu sur une plateforme spécifique, au milieu d'un content mix spécifique. Les 3 plateformes à simuler sont choisies par usage réel des chercheurs (Collins et al., 2016 ; données 2025-2026) :

| Priorité | Plateforme | Pourquoi | Phase |
|----------|-----------|----------|-------|
| **1** | **LinkedIn** | Canal #1 de dissémination scientifique professionnelle. >50% des chercheurs l'utilisent. C'est là que le scroll-stopping compte. | V3 |
| **2** | **TOC Journal** (MDPI, Elsevier, PubMed) | C'est là que les GAs sont vus *en premier* — dans la table des matières du journal. Grille de thumbnails à 200px. | V3 |
| **3** | **X/Twitter** | En déclin (11% actifs en 2025) mais encore 2M posts recherche/semaine. Layout compact, sombre. | V4 |

Bluesky et ResearchGate sont exclus pour le MVP : Bluesky n'a pas encore de content mix stabilisé, et ResearchGate n'a pas de feed scrollable (c'est une page de profil/article statique).

**Le content mix — le GA n'est pas seul dans le feed :**

Un feed LinkedIn réel en 2025-2026 n'est pas 100% posts texte+image. Les données AuthoredUp (621 833 posts) et Socialinsider (1.3M posts) montrent la distribution suivante :

| Type de contenu | % du feed LinkedIn 2025 | Ce que voit le participant |
|---|---|---|
| Image + texte | ~30% | Photo, infographie, GA, schéma |
| Vidéo native | ~20% | Thumbnail vidéo avec bouton play, autoplay muet |
| Carrousel / document PDF | ~15% | Slide 1/N avec flèche "suivant" |
| Texte seul | ~16% | Bloc de texte, pas d'image |
| Lien externe | ~15% | Carte de preview avec mini-thumbnail |
| Poll | ~4% | Question + barres de votes |

**Implication pour le feed simulé :** Si le flux S2b est composé de 8 posts, le mix réaliste est :

```
Post 1: [Texte seul — commentaire d'opinion d'un chercheur]
Post 2: [Vidéo — thumbnail avec bouton ▶, autoplay muet NON activé]
Post 3: [Image + texte — GA DISTRACTEUR d'un autre paper]
Post 4: [Carrousel — slide 1/6 d'un thread pédagogique]
Post 5: [Image + texte — GA CIBLE]
Post 6: [Lien externe — preview card d'un article de journal]
Post 7: [Vidéo — thumbnail talking-head avec sous-titres]
Post 8: [Image + texte — photo de conférence avec légende]
```

Le GA cible est en compétition avec des vidéos, des carrousels et du texte pur. C'est la *vraie* condition attentionnelle. Un feed de 8 GA alignés ne simule rien — dans la réalité, le GA est un signal visuel parmi des signaux hétérogènes.

**Simulation des types non-GA :**

Les distracteurs non-GA n'ont pas besoin d'être interactifs. Ils doivent *ressembler* au vrai contenu :

| Type | Simulation | Source |
|---|---|---|
| Vidéo | Thumbnail statique avec icône ▶ superposée + durée "1:23" | Screenshot de vraies vidéos LinkedIn de conférences/talks |
| Carrousel | Slide 1 statique avec indicateur "1/6 ›" | Screenshot de vrais carrousels pédagogiques |
| Texte seul | 3-4 lignes de texte + "...voir plus" | Vrais posts texte anonymisés |
| Lien externe | Preview card avec titre + mini-thumbnail + nom de domaine | Screenshots de vrais link previews |
| Photo | Photo de conférence / labo / équipe | Photos libres de droits thème science |

Ces distracteurs sont des **images statiques** dans le feed scrollant — pas de vidéo qui joue, pas de carrousel qui slide. Le but est la *concurrence visuelle*, pas l'interactivité. Le cerveau du participant voit un feed hétérogène et doit discriminer "quel post mérite mon attention" — c'est la condition écologique réelle.

**Coût de production des distracteurs :**

Chaque style de feed (LinkedIn, TOC, Twitter) requiert une bibliothèque de distracteurs :
- 15-20 distracteurs par style (pour éviter la répétition entre sessions)
- Chaque distracteur = 1 screenshot + metadata (type, titre, auteur fictif)
- Estimation : 2h de travail agent pour constituer la bibliothèque initiale de 20 distracteurs LinkedIn
- Les distracteurs sont réutilisables entre sessions (mélangés par seed)

**Feed TOC Journal — layout différent :**

La TOC journal n'est pas un feed vertical de posts. C'est une **grille** ou une **liste** :

```
┌─────────────────────────────────────────────────────┐
│  MDPI Children — Table of Contents — Vol. 12, No. 3 │
├─────────────────────────────────────────────────────┤
│  ┌─────┐  Immunomodulators for Recurrent RTIs      │
│  │ GA₁ │  Chen, S. et al. · Received: 12 Mar 2026  │
│  └─────┘  [PDF] [HTML] [GA]                         │
├─────────────────────────────────────────────────────┤
│  ┌─────┐  Machine Learning in Pediatric Radiology   │
│  │ GA₂ │  Kumar, R. et al. · Received: 28 Feb 2026 │
│  └─────┘  [PDF] [HTML] [GA]                         │
├─────────────────────────────────────────────────────┤
│  ┌─────┐  CRISPR-Based Diagnostics for Rare...      │
│  │ GA₃ │  Dubois, A. et al. · Received: 5 Mar 2026 │
│  └─────┘  [PDF] [HTML]                              │
├─────────────────────────────────────────────────────┤
│  ...                                                 │
└─────────────────────────────────────────────────────┘
```

Le GA est un thumbnail de ~200px dans une liste sobre. Pas de boutons sociaux. Pas de vidéo. Le scroll est vertical et lent. C'est le stress test ultime de P6 (mobile-first) et V7 (lisibilité au downscale).

Le style est taggé dans `test_results` (`stimulus_frame` et `stream_feed_style`). Les résultats par style sont analysés séparément.

#### Données additionnelles en mode stream

En plus des données standard (S9a/S9b/S9c/RT), le mode stream enregistre :

```
stream_feed_style,          -- 'linkedin' | 'twitter' | 'toc_journal'
stream_scroll_speed_px_s,   -- vitesse effective du scroll
stream_post_count,          -- nombre de posts dans le feed
stream_target_position,     -- position du post cible (1-indexed)
stream_target_dwell_ms,     -- temps pendant lequel le post cible était dans le viewport
stream_selected_id,         -- quel post le participant a sélectionné
s10_hit,                    -- 1 si le post sélectionné est le post cible
```

`stream_target_dwell_ms` est critique : c'est le temps réel pendant lequel le GA cible était visible dans le viewport du participant. Mesuré par `IntersectionObserver API` — quand le post entre dans le viewport et quand il en sort. Si le participant a eu 3.2 secondes de dwell time et que S9b=1, le GA a encodé la hiérarchie en 3.2 secondes de scan passif. C'est la preuve écologique la plus forte.

**Justification (paper)** : La simulation de feed avec auto-scroll et chrome de plateforme suit la méthodologie des études d'eye-tracking sur les réseaux sociaux (Bakhshi et al., 2014, *CHI* ; Pew Research Center, 2021). Le scroll automatique à vitesse fixe élimine la variance due au comportement de scroll individuel (certains scrollent vite, d'autres lentement) tout en maintenant la condition d'attention ambiante. L'`IntersectionObserver API` (W3C) fournit une mesure précise du dwell time sans recourir à un eye-tracker matériel. La présence du titre + chrome dans le stimulus suit le principe de validité écologique de Brunswik (1956) : omettre le contexte dans lequel le stimulus est naturellement rencontré invalide la généralisation des résultats au monde réel.

### Ce que le Stream ajoute au modèle

**Nouvelle métrique : Saillance (S10)**

```
S10(GA) = P(participant sélectionne le post cible parmi 3 posts)
```

Le participant voit 6-10 posts défiler et on lui en montre 3 après le flux (titre + mini-GA). S10 mesure la probabilité que le post contenant le GA cible soit celui dont il se souvient le mieux. Le taux de chance est 1/3 = 0.33.

Note : S10 mesure la saillance du *post complet* (titre + GA + chrome), pas du GA seul. C'est voulu — en condition écologique, le GA n'est jamais isolé. La comparaison S9b(spotlight nude) vs S9b(stream) isole la contribution du GA vs celle du titre.

| S10 | Interprétation |
|-----|---------------|
| > 0.70 | Le GA capture l'attention dans un flux — scroll-stopping validé |
| 0.33-0.70 | Le GA n'est pas plus mémorable que les distracteurs |
| < 0.33 | Le GA est activement ignoré (pire que le hasard) |

S10 mesure ce que les altmetrics prétendent mesurer (engagement, scroll-stopping) mais avec un protocole contrôlé. C'est le pont entre l'attention (que la littérature documente) et la compréhension (que nous mesurons).

**Couplage S10 × S9b : La Chaîne Complète**

```
Saillance (S10) → Reconnaissance (S9a) → Hiérarchie (S9b) → Action (S9c)
     "je l'ai vu"       "je sais ce que         "je sais qui      "je ferais
                          c'est"                  est le mieux"     autrement"
```

Pour qu'un GA produise un impact clinique, TOUTE la chaîne doit tenir. Un GA avec S10=0.90 et S9b=0.30 est un piège : il arrête le scroll mais trompe le lecteur (spin). Un GA avec S10=0.40 et S9b=0.95 est invisible : il encode parfaitement mais personne ne le regarde.

Le VEC doit maximiser le produit : `S10 × S9b`.

**Justification du choix (paper)** : Le paradigme de flux avec distracteurs est l'adaptation au contexte digital du paradigme RSVP (Rapid Serial Visual Presentation) utilisé en psychologie de l'attention depuis Potter (1975, *Cognitive Psychology*). Potter a montré que les images présentées brièvement (~250ms) dans un flux peuvent être identifiées mais pas mémorisées, tandis qu'à 2-5 secondes la mémorisation est robuste — ce qui correspond à notre fenêtre d'exposition. L'insertion d'un stimulus cible parmi des distracteurs écologiquement valides suit le paradigme du "attentional blink" (Raymond, Shapiro & Arnell, 1992) adapté aux durées longues. La sélection post-flux (reconnaissance parmi 3 thumbnails) est un test de reconnaissance standard (Mandler, 1980), plus écologique que le rappel forcé car il simule le moment où le lecteur décide de "revenir" à un élément aperçu dans son scroll. La mesure combinée S10 × S9b est analogue au framework Signal Detection Theory (Green & Swets, 1966) appliqué en deux étapes : d'abord détecter le signal (S10 = hit rate de la saillance), puis le décoder (S9b = accuracy de l'interprétation).

### Deux modes, une plateforme

| Mode | Stimulus | Titre | Chrome | Ce qu'il mesure | Validité |
|------|----------|-------|--------|----------------|----------|
| **Spotlight nude** | GA seul, 5s chrono | Non | Non | Performance pure du design (ceiling) | Interne — borne supérieure |
| **Stream feed** | Post complet (titre + GA + boutons), auto-scroll | **Oui, toujours** | **Oui** (LinkedIn/Twitter/TOC) | Compréhension en attention ambiante (écologique) | Externe — généralisable |

Le mode est taggé dans `test_results` (`exposure_mode`). Les deux modes produisent des données comparables (mêmes S9a/S9b/S9c) mais ne doivent jamais être agrégés ensemble — ils mesurent des conditions cognitives fondamentalement différentes.

**La comparaison entre les deux modes est elle-même informative :**
- Si S9b(stream) ≈ S9b(spotlight) → le titre et le chrome ne changent rien, le GA porte seul
- Si S9b(stream) >> S9b(spotlight) → le titre spoile, le GA seul ne suffit pas
- Si S9b(stream) << S9b(spotlight) → le contexte distrait, le GA ne survit pas au bruit du feed

**Implémentation** : Le mode spotlight reste pour le MVP localhost (rapide à coder, rapide à tester). Le mode stream est la V2 — il requiert une bibliothèque de distracteurs et un moteur de randomisation de position. Mais la DB et le scoring sont identiques.

### Mise à jour de la durée d'exposition

La justification des 5000ms tient pour les deux modes :

**Contrainte écologique** : Les études d'eye-tracking sur le scroll mobile montrent un temps de fixation moyen de 2-5 secondes par élément (Liu et al., 2020). En mode stream, la durée par élément varie entre 3-5s pour empêcher le comptage et simuler le rythme naturel du scroll.

**Contrainte cognitive** : Le modèle PH1 prédit 3 phases (T=1s flux chromatique, T=2s ancrage/fracture, T=3s décision). 5 secondes donnent 2 secondes de marge, permettant au Système 1 de compléter son traitement.

**Contrainte statistique** : En mode spotlight, la durée fixe élimine la variance inter-sujets. En mode stream, la variance contrôlée (3-5s) est documentée et analysable comme covariable.

---

## 9. Résumé des Métriques

### Métriques de Scoring

| Métrique | Formule | Ce qu'elle mesure | Seuil |
|----------|---------|------------------|-------|
| **S10** | **P(sélection du GA cible)** | **Le GA capture-t-il l'attention dans un flux ?** | **>0.70** |
| Taux_S9a | Σ S9a / N | Le GA est-il identifiable ? | ≥0.60 |
| **Taux_S9b** | **Σ S9b / N** | **La hiérarchie est-elle perçue ?** | **≥0.80** |
| Score_S9c | Σ S9c / N | Le GA déclenche-t-il l'action ? | ≥0.40 |
| **S10 × S9b** | **Saillance × Hiérarchie** | **La chaîne complète tient-elle ?** | **>0.56** |
| **Fluence** | **S9b / log₂(RT₂)** | **Exactitude × vitesse (métrique continue)** | **plus élevé = meilleur** |
| Score_S2b | 0.2·S9a + 0.5·S9b + 0.3·S9c | Score composite | ≥0.70 |
| Δ̄_S9b | S9b(VEC) - S9b(ctrl) | Le VEC bat-il l'industrie ? | >+0.30 |
| **Δ_spoiler** | **S9b(title_only) - S9b(nude)** | **Le titre porte-t-il l'info à la place du GA ?** | **<+0.10** |

### Métriques Temporelles

| Métrique | Formule | Ce qu'elle mesure | Seuil | Mode |
|----------|---------|------------------|-------|------|
| Médiane_RT₂ | median(q2_rt) | Fluence de la décision hiérarchique | <3000ms | tous |
| Latence_Q1 | q1_first_keystroke_ms / q1_first_utterance_ms | Vitesse d'accès mémoire | <1500ms = ancrage fort | text / voice |
| Production_Q1 | q1_last - q1_first | Richesse du souvenir encodé | informatif | text / voice |
| Validation_Q1 | q1_rt - q1_last | Confiance subjective | informatif | text / voice |
| **Word_count_Q1** | **len(q1_text.split())** | **Volume du rappel** | **voice > text attendu** | **tous** |

### Métriques d'Intégrité, Saillance, Modalité et Effort

| Métrique | Formule | Ce qu'elle mesure | Seuil |
|----------|---------|------------------|-------|
| Taux_invalidation | Σ tab_switched / N_total | Fiabilité du flux de test | <0.20 |
| **S10 (stream only)** | **P(sélection GA cible)** | **Capture attentionnelle en flux** | **>0.70** |
| S10 × S9b | Saillance × Hiérarchie | Chaîne complète attention→compréhension | >0.56 |
| **Δ_modalité** | **S9a_raw(voice) - S9a_raw(text)** | **La voice capture-t-elle mieux le rappel ?** | **>0 attendu (H5)** |
| **q1_filter_ratio** | **phrases_retenues / phrases_totales** | **Effort cognitif du rappel (voice only)** | **plus élevé = plus fluent** |

---

## 9b. Visual Channel Scoring — The Explainability Layer

The GLANCE score (S9b) tells you WHETHER a GA transfers comprehension. The channel scoring tells you WHY.

### The Channel Ontology

75 visual properties organized in 7 categories (pre-attentive, encoding, social, typography, image-level, layout, emotional). Each channel has:

- **weight**: perceptual importance (Cleveland & McGill ranking)
- **stability**: literature backing
- **beta**: Stevens power law exponent (where applicable)

### GA Node Scoring

Each information vector in the GA maps to an L3 node. Each node is scored by:

```
coverage(node) = max(effectiveness(channel_i)) for all channels encoding this node
```

Where effectiveness follows Cleveland & McGill: position (β≈1.0) > length (β≈1.0) > angle (β≈0.85) > area (β≈0.7) > volume (β≈0.6) > saturation (β≈0.3)

### Upgrade Paths

For each suboptimal encoding, a specific upgrade is recommended:

| From | To | Expected ΔS9b | Mechanism |
|------|-----|--------------|-----------|
| area | length | +20-30% | Stevens β: 0.7 → 1.0 |
| volume | length | +30-40% | Stevens β: 0.6 → 1.0 |
| saturation | luminance | +15-25% | MacEachren 2012 |
| hue alone | hue + length | +10-20% | Redundant encoding (P32) |

### Data Feedback Loop

After N≥20 tests, the scoring updates empirically:

- Channels that correlate with S9b PASS gain weight
- Channels that correlate with S9b FAIL gain friction
- The graph converges: designer estimates → measured reality

---

## 10. Schéma DB mis à jour

Colonnes additionnelles pour `test_results` :

```sql
-- Condition d'exposition
ALTER TABLE test_results ADD COLUMN exposure_mode TEXT DEFAULT 'spotlight';        -- 'spotlight' | 'stream'
ALTER TABLE test_results ADD COLUMN exposure_condition TEXT DEFAULT 'nude';         -- 'nude' | 'title_only' | 'toc_sim' | 'social_sim'
ALTER TABLE test_results ADD COLUMN stimulus_frame TEXT;                            -- 'none' | 'mdpi_grid' | 'twitter_card' | 'linkedin_card'
ALTER TABLE test_results ADD COLUMN stimulus_text TEXT;                             -- texte accompagnant (null si nude)
ALTER TABLE test_results ADD COLUMN stimulus_image_width INTEGER;                   -- px effectifs (200, 500, 550)

-- Intégrité
ALTER TABLE test_results ADD COLUMN tab_switched INTEGER DEFAULT 0;                -- 0|1
ALTER TABLE test_results ADD COLUMN exposure_actual_ms INTEGER;                     -- ≤5000

-- Keystroke dynamics (Q1) — mode text
ALTER TABLE test_results ADD COLUMN q1_first_keystroke_ms INTEGER;                  -- ms
ALTER TABLE test_results ADD COLUMN q1_last_keystroke_ms INTEGER;                   -- ms

-- Voice input (Q1) — mode voice
ALTER TABLE test_results ADD COLUMN q1_input_mode TEXT DEFAULT 'text';              -- 'text' | 'voice'
ALTER TABLE test_results ADD COLUMN q1_raw_transcript TEXT;                         -- STT avant édition user (null si text)
ALTER TABLE test_results ADD COLUMN q1_edit_distance INTEGER;                       -- Levenshtein(raw, validated) — mesure erreur STT
ALTER TABLE test_results ADD COLUMN q1_audio_path TEXT;                             -- chemin audio blob (null si text)
ALTER TABLE test_results ADD COLUMN q1_first_utterance_ms INTEGER;                  -- voice: onset de la première détection vocale
ALTER TABLE test_results ADD COLUMN q1_last_utterance_ms INTEGER;                   -- voice: fin du dernier segment vocal
ALTER TABLE test_results ADD COLUMN q1_word_count INTEGER;                          -- nombre de mots dans q1_text final

-- Stream mode
ALTER TABLE test_results ADD COLUMN stream_position INTEGER;                        -- position GA cible dans le flux
ALTER TABLE test_results ADD COLUMN stream_length INTEGER;                          -- nombre d'éléments total
ALTER TABLE test_results ADD COLUMN stream_selected_id TEXT;                        -- GA choisi par le participant
ALTER TABLE test_results ADD COLUMN s10_hit INTEGER;                                -- 1 si sélection correcte
ALTER TABLE test_results ADD COLUMN stream_scroll_type TEXT DEFAULT 'inertial_flick'; -- 'constant' | 'inertial_flick' | 'free'
ALTER TABLE test_results ADD COLUMN stream_flick_seed TEXT;                         -- seed de la séquence (reproductibilité)
ALTER TABLE test_results ADD COLUMN stream_target_dwell_ms INTEGER;                 -- dwell time effectif (IntersectionObserver)
ALTER TABLE test_results ADD COLUMN stream_feed_style TEXT;                         -- 'linkedin' | 'twitter' | 'toc_journal'
ALTER TABLE test_results ADD COLUMN stream_show_title INTEGER DEFAULT 1;            -- 0 = stream nude (titre masqué), 1 = titre visible
ALTER TABLE test_results ADD COLUMN stream_target_enter_ts REAL;                    -- timestamp entrée viewport (performance.now)
ALTER TABLE test_results ADD COLUMN stream_target_exit_ts REAL;                     -- timestamp sortie viewport
ALTER TABLE test_results ADD COLUMN exposure_valid INTEGER DEFAULT 1;               -- 0 si dwell hors tolérance (±500ms du target)

-- Résolution d'écran (covariable)
ALTER TABLE test_results ADD COLUMN screen_width INTEGER;                           -- window.innerWidth (px CSS)
ALTER TABLE test_results ADD COLUMN screen_height INTEGER;                          -- window.innerHeight (px CSS)
ALTER TABLE test_results ADD COLUMN screen_dpr REAL;                                -- window.devicePixelRatio
ALTER TABLE test_results ADD COLUMN screen_user_agent TEXT;                         -- navigator.userAgent
ALTER TABLE test_results ADD COLUMN screen_is_mobile INTEGER;                       -- 1 si mobile natif, 0 si desktop avec phone frame

-- Embedding (S9a sémantique)
ALTER TABLE test_results ADD COLUMN s9a_raw REAL;                                   -- cos_sim brute ∈ [-1, 1]

-- Diagnostic adaptatif post-test (Q4-Q5)
ALTER TABLE test_results ADD COLUMN q4_dimension_id TEXT;                            -- from sidecar critical_dimensions[0].id
ALTER TABLE test_results ADD COLUMN q4_pattern TEXT;                                 -- ex: "P21", "V14"
ALTER TABLE test_results ADD COLUMN q4_response TEXT;                                -- user's answer
ALTER TABLE test_results ADD COLUMN q4_rt INTEGER;                                   -- ms
ALTER TABLE test_results ADD COLUMN q5_dimension_id TEXT;                            -- from sidecar critical_dimensions[1].id
ALTER TABLE test_results ADD COLUMN q5_pattern TEXT;                                 -- ex: "V14", "V3"
ALTER TABLE test_results ADD COLUMN q5_response TEXT;                                -- user's answer
ALTER TABLE test_results ADD COLUMN q5_rt INTEGER;                                   -- ms

-- Channel scoring (section 9b)
ALTER TABLE test_results ADD COLUMN channel_score REAL;                               -- overall channel coverage
ALTER TABLE test_results ADD COLUMN channel_weakest TEXT;                              -- weakest channel node id
```

Côté JS (`arena.js`), les events à capturer :

```javascript
// Intégrité
document.addEventListener('visibilitychange', () => {
    if (document.hidden && state === 'EXPOSURE') {
        data.tab_switched = true;
        data.exposure_actual_ms = performance.now() - exposureStart;
    }
});

// Keystroke timing Q1
const q1Input = document.getElementById('q1-text');
q1Input.addEventListener('keydown', (e) => {
    const now = performance.now() - q1Start;
    if (!data.q1_first_keystroke_ms) data.q1_first_keystroke_ms = now;
    data.q1_last_keystroke_ms = now;
});

// Tous les timestamps via performance.now() (sub-ms, W3C HR Time Level 2)
// Pas Date.now() (~15ms résolution)
```

---

*La beauté n'a aucune corrélation avec la compréhension.*
*Seuls les chiffres savent si l'information a survécu au transfert.*
