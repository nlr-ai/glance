# GLANCE — Master TODO
## 25 mars 2026

---

## P0 — Blockers (must fix now)

- [ ] Deploy: sitemap + leaderboard redesign + deepen pas encore live (en cours)
- [ ] Images user_upload perdues au deploy — dedup restore pushé mais pas déployé
- [ ] `TG_ADMIN_CHAT_ID=1864364329` — ajouter dans Render env vars (dashboard)
- [ ] `GLANCE_DATA_DIR=/var/data` — vérifier dans Render env vars
- [ ] `GLANCE_ADMIN_PWD` — set dans Render env vars si pas fait
- [ ] Batch analyze: finir les ~30 GAs restants sans graph

---

## P1 — Revenue path (cette semaine)

### Premiers testeurs humains
- [ ] Aurore recrute 10 pédiatres pour les tests GLANCE
- [ ] Préparer l'email de recrutement "Testez votre oeil scientifique"
- [ ] Vérifier que le flow test complet marche E2E (onboard → test → score → partage)
- [ ] 10 testeurs × 5 GAs × 2 conditions = 100 data points minimum

### Stripe (premier revenu)
- [ ] Configurer Stripe account SciSense
- [ ] Brancher Stripe Checkout sur le tier Audit (99€)
- [ ] Bouton "Obtenir l'audit complet" sur ga-detail
- [ ] Page de confirmation post-paiement

### Premier post LinkedIn (Aurore)
- [ ] Préparer le texte du post #1 (insight choquant, pas promo)
- [ ] Générer le GIF scanpath d'un GA parlant
- [ ] Envoyer le kit (texte + GIF + lien) à Aurore sur TG
- [ ] Post #2 (les 7 archetypes) — préparer pour semaine suivante
- [ ] Post #3 (avant/après redesign) — semaine 3

---

## P2 — Product (cette semaine / prochaine)

### UX critiques
- [ ] Animation: vérifier que le loop marche (plus de Rejouer/progress bar)
- [ ] /analyze: checkbox "Rendre visible" fonctionne
- [ ] /analyze: l'auto-improve se lance bien après upload
- [ ] /analyze: le polling met à jour le graph live
- [ ] Overlay: tester le rendu marble + dark halo sur un vrai GA
- [ ] Menu nav: Paper/GitHub cachés sur petit écran (media query)
- [ ] Leaderboard: tester le redesign (hero stats, domain cards, predicted scores)

### Auth
- [ ] Tester le flow magic link complet (login → TG → verify → profil)
- [ ] Page profil: affiche bien "Mes GAs"
- [ ] Session cookie survit aux refreshs

### Search
- [ ] Ajouter un champ de recherche sur la page leaderboard
- [ ] Search accessible depuis le nav (icône loupe ?)

### GA création (le vrai produit)
- [ ] Connecter le compositor paramétrique (vec_lib + compose_*.py) au pipeline web
- [ ] Flow: abstract + données → Gemini génère YAML config → compose_ga → SVG/PNG → score → loop
- [ ] Endpoint /create-ga avec input texte (abstract + key findings)
- [ ] C'est le game changer: GLANCE ne score pas un GA, il le CRÉE

### Multi-résolution
- [ ] Tester deepen() sur un GA réel (immunomod)
- [ ] Bouton 🔬 Approfondir fonctionne
- [ ] Evolution chart montre l'augmentation de nodes après deepening

---

## P3 — Growth (prochaines semaines)

### Reddit
- [ ] Tester l'ingest en prod (r/dataisugly, r/dataisbeautiful)
- [ ] Template auto-rempli → alerte TG avec le commentaire pré-généré
- [ ] Aurore/NLR poste manuellement les meilleurs diagnostics
- [ ] Cron toutes les 6h activé sur Render

### SEO
- [ ] Sitemap.xml live et soumis à Google Search Console
- [ ] robots.txt live
- [ ] JSON-LD sur chaque page GA
- [ ] Meta descriptions dynamiques
- [ ] Google Search Console: soumettre sitemap

### Self-analysis
- [ ] Cron self-analysis toutes les 4h activé sur Render
- [ ] Screenshots des 5 pages principales
- [ ] Analyser les résultats → implémenter les recommandations
- [ ] Loop d'amélioration continue du site

### Contenu
- [ ] Blog post #2: "Comment un lecteur scanne votre GA en 5 secondes" (reader sim)
- [ ] Blog post #3: "Redesigning Ozempic" (case study)
- [ ] "GA de la semaine" — cron hebdo qui sélectionne le meilleur/pire
- [ ] Badge embedable: `<img src="glance.scisense.fr/badge/{slug}.svg">`

### Share video
- [ ] Tester /video/ga/{slug}.gif — le GIF se génère correctement
- [ ] Bouton "Partager la vidéo" sur ga-detail
- [ ] OG card diagonal split (original ↗ overlay ↙)

---

## P4 — Platform (Q2 2026)

### Chat UI
- [ ] /analyze → interface chat au lieu de boutons
- [ ] Slash commands (/vision, /channels, /advise, /duck)
- [ ] Historique de conversation par GA
- [ ] Auto-routing: questions → duck, instructions → advise

### Multi-user
- [ ] GA switcher (dropdown "Mes GAs")
- [ ] Permissions: designer peut edit, viewer peut voir
- [ ] Team mode: partager un GA entre collègues
- [ ] Dashboard "Mon équipe"

### Knowledge graph
- [ ] Stocker les abstracts de chaque étude (✅ fait)
- [ ] Cross-study citation map (embedding cosine similarity entre narratives)
- [ ] Systematic review assistant ("montre-moi les études liées")
- [ ] HRI use case: carte de l'évidence homéopathique

### Intégrations
- [ ] API publique documentée (/api/v1/analyze, /api/v1/score)
- [ ] Plugin BioRender
- [ ] Plugin Overleaf
- [ ] Plugin Canva
- [ ] Webhook sur nouveau score

### Paper PLOS ONE
- [ ] N=10 testeurs → données empiriques
- [ ] Résultats: 100 data points minimum
- [ ] Discussion: reader sim vs human testers (calibration)
- [ ] Soumission PLOS ONE

---

## Infrastructure

- [ ] VPS Hetzner (4€/mois) pour des deploys en 3 secondes
- [ ] SMTP pour les magic links (au lieu de TG)
- [ ] Monitoring: error rate, latency, Gemini costs
- [ ] Rate limiting per-user sur les endpoints Gemini
- [ ] Backup DB automatique (cron pg_dump ou sqlite .backup)

---

## Done today (25 mars session 2)

- [x] Reader sim V1 (proportional attention, Z-order, debug trace)
- [x] PHYSICS_VALIDATION.md (13 behaviors, 9 VALID)
- [x] Anti-pattern penalties (incongruent, fragile)
- [x] Reading narrative generator
- [x] System 2 mode (90s, 1.5x attention)
- [x] save_graph() async listener (sim + health + overlay)
- [x] Auto-improve loop refactored (sim via DB)
- [x] Structured recommendations (source-linked)
- [x] DB: reading_simulations, designer→designers, public flag, auth_tokens, abstract
- [x] Admin dashboard: graphs + sims tables
- [x] 6 per-tool endpoints (vision, channels, advise, duck, health, reader_sim)
- [x] /analyze/improve endpoint
- [x] Tool panel on ga-detail (8 buttons with emojis + tooltips)
- [x] Freemium 6 calls (cookie-based)
- [x] prior_graph flag on all Gemini scripts
- [x] Bbox from Gemini + auto-linking by overlap
- [x] Graph overlay renderer (SVG + PNG)
- [x] Live scanpath animation (auto-play, loop, burst particles)
- [x] Animation V2 (link particles, space fills)
- [x] Homepage rewrite + /analyze rewrite
- [x] Verdict scale: Limpide→Clair→Ambigu→Confus→Obscur→Incompréhensible
- [x] Header: dropdown Leaderboards, emojis, gold Analyse mon GA
- [x] Image dedup (SHA-256) + restore missing files
- [x] Upload auto-resize >2000px, limit 20Mo
- [x] Blog as post list + article route
- [x] TG bot @scisense_bot (12 commands)
- [x] Dockerfile + Docker runtime on Render
- [x] Email magic link auth + profile page
- [x] Reddit auto-ingest (JSON public, no credentials)
- [x] /search endpoint
- [x] Dynamic share text (narrative coverage)
- [x] Leaderboard domain emojis + colors
- [x] OG card diagonal split
- [x] Share video GIF
- [x] deepen() multi-resolution
- [x] Sitemap.xml + robots.txt + SEO meta + JSON-LD
- [x] Evolution chart (graph versions over time)
- [x] Graph visual style spec (Pensieve, V4)
- [x] Graph overlay mapping spec
- [x] Live scanpath animation spec (burst, halo, particles, zones)
- [x] Resolution §9i formal spec in Math doc
- [x] Business Plan v2.1
- [x] Paper Draft + Math updated
- [x] Self-analysis cron spec'd
- [x] 70+ GAs batch-analyzed
- [x] Abstract storage + backfill
- [x] Leaderboard redesign
- [x] Loading spinner with per-tool explanations
- [x] Anti-pattern formatted cards
