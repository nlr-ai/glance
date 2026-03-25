# GLANCE — Graphical Literacy Assessment for Naïve Comprehension Evaluation

**The first standardized benchmark for measuring whether scientific Graphical Abstracts communicate their message under real-world conditions.**

🔗 **Live:** [glance.scisense.fr](https://glance.scisense.fr)
📄 **Paper:** [Pre-print (PLOS ONE, in preparation)](https://glance.scisense.fr/static/GLANCE_Paper_Draft.pdf)

## What is GLANCE?

GLANCE measures whether a Graphical Abstract (GA) transfers its key information to a reader who scrolls past it in 5 seconds — the way scientific content is actually consumed on LinkedIn, Twitter, and journal TOCs.

### Two viewing modes

- **Stream Mode** — GA embedded in a simulated LinkedIn feed with inertial scroll. Measures comprehension under ambient attention (ecological validity).
- **Spotlight Mode** — GA shown in isolation for 5 seconds. Measures ceiling comprehension (focused attention).

### Three comprehension metrics

| Metric | What it measures |
|--------|-----------------|
| **S9a** | Subject identification — can the reader tell what the GA is about? |
| **S9b** | Evidence hierarchy — can the reader identify the key finding? (4AFC, chance = 25%) |
| **S9c** | Actionability — does the GA trigger an intention to act? |

### System 2 Deep Analysis

After the 5-second exposure, participants describe everything they understand from the GA with an open microphone (90s). Verbal chunks are mapped to the GA's information graph, revealing exactly **which information survives the scroll and which is lost**.

## Features

- 📊 **47 GAs** across 15 scientific domains
- 🎤 **Voice input** with semantic filtering (removes meta-talk)
- 📱 **Phone emulation** (iPhone 14 frame, inertial scroll physics)
- 🧠 **AI-powered GA analysis** — upload your GA, get instant scoring + recommendations (Gemini Pro Vision)
- 📈 **Domain leaderboards** — how does your GA rank against others?
- 🔬 **L3 graph scoring** — 3-type graph (space/narrative/thing), 75 visual channels, reader simulation with Z-pattern attention propagation
- 💡 **Actionable recommendations** — reader simulation diagnoses which messages survive the scroll, auto-improve prompts with FACT → PROBLEM → QUESTION

## Quick Start

```bash
# Clone
git clone https://github.com/nlr-ai/glance.git
cd glance

# Install
pip install -r deploy/requirements.txt

# Run
python -c "from db import init_db; init_db()"
uvicorn app:app --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000`

## Tech Stack

- **Backend:** FastAPI + SQLite
- **Scoring:** sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **Vision AI:** Gemini Pro (GA auto-analysis)
- **Frontend:** Jinja2 templates, vanilla JS, Chart.js
- **Deployment:** Render.com (auto-deploy from GitHub)

## Evidence Chain

GLANCE validates through 6 levels of evidence:

| Level | Proof | Status |
|-------|-------|--------|
| 0 | The test discriminates (σ > 0.15) | Validating (N=10) |
| 1 | The test measures comprehension | Pending |
| 2 | Stream mode is ecologically valid | Pending |
| 3 | Scoring explains WHY a GA fails | Pending |
| 4 | Recommendations improve GAs | Pending |
| 5 | The model generalizes across domains | Pending |

## Team

- **Dr. Aurore Inchauspé** — PhD Virology, SciSense founder. Scientific direction.
- **Silas** — AI citizen (Mind Protocol). Engineering & analysis.
- **Nicolas Lazzari** — Mind Protocol co-founder. Architecture & strategy.

## Citation

```
Inchauspé, A., Lazzari, N. (2026). GLANCE: A Standardized Protocol for Measuring
Graphical Abstract Comprehension Under Ecological Viewing Conditions.
PLOS ONE (in preparation).
```

## License

MIT — see [LICENSE](LICENSE)

---

*SciSense SASU — Making Science Make Sense*
