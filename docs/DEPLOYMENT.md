# GLANCE Premier Regard -- Deployment

## Prerequisites

**Python 3.10+** (tested on 3.12).

**Required packages:**

```
fastapi
uvicorn
jinja2
pyyaml
sentence-transformers
numpy
```

**Optional packages:**

```
matplotlib    # required by generate_library.py and generate_leurres.py
```

`sentence-transformers` pulls in `torch` (~2GB) and `transformers` (~500MB). The embedding model (`paraphrase-multilingual-mpnet-base-v2`, 278M params) is ~470MB, downloaded on first use to `~/.cache/huggingface/`. Total disk footprint: ~3.5GB.

### Install

```bash
pip install fastapi uvicorn jinja2 pyyaml sentence-transformers numpy
```

Or if a `requirements.txt` exists:

```bash
pip install -r requirements.txt
```

---

## Startup

```bash
cd C:\Users\reyno\scisense\glance
python -m uvicorn app:app --host 127.0.0.1 --port 8742 --reload
```

The server is then available at `http://127.0.0.1:8742/`.

### What happens on first run

1. **`init_db()`** creates `data/glance.db` with the 3-table schema if it doesn't exist. The `data/` directory is auto-created via `os.makedirs()`.
2. **`_seed_images()`** scans `ga_library/` for image files (PNG/JPG/JPEG/WEBP). For each image, it reads the sidecar JSON (same base name, `.json` extension) and inserts a row into `ga_images`. This only runs if the table is empty. With 47 images, seeding takes <1 second.
3. **First test submission** triggers lazy loading of the embedding model via `semantic.load_model()`. This downloads `paraphrase-multilingual-mpnet-base-v2` (~470MB) from Hugging Face on first call. Subsequent starts load from cache in ~2-5s.

### Endpoints

| URL | Method | Purpose |
|-----|--------|---------|
| `/` | GET | Landing page |
| `/onboard` | GET | Profile form |
| `/onboard` | POST | Submit profile, set cookie, redirect to `/test` |
| `/test` | GET | Test arena (flux or spotlight, based on `config.yaml`) |
| `/submit` | POST | Submit test answers, score, redirect to `/reveal/{id}` |
| `/reveal/{id}` | GET | Show results for test `{id}` |
| `/dashboard` | GET | Analytics dashboard |
| `/docs` | GET | FastAPI auto-generated OpenAPI docs |
| `/ga/{filename}` | GET | Static GA images from `ga_library/` |
| `/ga/leurres/{filename}` | GET | Static leurre images from `ga_library/leurres/` |
| `/static/{filename}` | GET | Static CSS from `static/` |

---

## Configuration

All configuration lives in `config.yaml` at the project root. It is loaded once and cached by `config_loader.py`.

### Structure

```yaml
timer:                           # Spotlight mode timing
  exposure_ms: 5000
  countdown_seconds: 3

flux:                            # Stream/flux mode
  enabled: true                  # true = flux mode, false = spotlight mode
  n_items: 6                    # total items in feed (including target)
  item_duration_ms: 4000         # each item visible for 4s
  target_position: random        # "random" or fixed int (1-indexed)
  scroll_transition_ms: 300      # CSS transition between items

profile:                         # Options shown in the onboard form
  clinical_domains: [...]
  data_literacy: [...]
  experience_ranges: [...]
  colorblind_options: [...]

domains:                         # Per-domain question wording (15 + generic)
  med:
    label: "Medical"
    q1: "..."
    q2: "..."
    q3: "..."
    q3_choices: [...]
  tech:
    label: "Tech / IA"
    ...
  policy: ...
  education: ...
  climate: ...
  psychology: ...
  economics: ...
  neuroscience: ...
  nutrition: ...
  energy: ...
  epidemiology: ...
  ecology: ...
  transport: ...
  agriculture: ...
  materials: ...
  generic:                       # Fallback for unknown domains
    ...

scoring:
  keywords:                      # Legacy keyword lists (unused by semantic scoring)
    med: [...]

constants:                       # Configurable scoring constants
  semantic_model_name: "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
  s9a_pass_threshold: 0.40
  rt2_fast_slow_ms: 3000
  rt2_hesitant_lost_ms: 8000
  glance_pass_threshold: 0.70
  mcnemar_min_pairs: 10
  cookie_max_age_seconds: 2592000
```

Constants are accessed in Python via:

```python
from config_loader import get_constant
threshold = get_constant("s9a_pass_threshold", 0.40)
```

The second argument is the default if the key is missing from `config.yaml`.

### Switching between Spotlight and Flux mode

```yaml
flux:
  enabled: true    # flux/stream mode (default)
  # enabled: false  # spotlight mode
```

Restart the server after changing. The mode affects which template is rendered at `/test`.

---

## Generating the GA Library

### Full library regeneration

```bash
cd C:\Users\reyno\scisense\glance\ga_library
python generate_library.py
```

Produces 36 PNG + 36 JSON files (18 papers x 2 versions). Overwrites existing files. Does not affect the 11 pre-existing images (immunomod wireframe, immunomod infographic, etc.).

### Generating leurre images

```bash
cd C:\Users\reyno\scisense\glance
python generate_leurres.py
```

Produces 10 PNG images + `leurres.json` manifest in `ga_library/leurres/`. Required for flux mode. If leurres are missing, the feed will have fewer distractor items.

### After generating images

Delete the database and restart to re-seed:

```bash
rm data/glance.db
python -m uvicorn app:app --host 127.0.0.1 --port 8742 --reload
```

---

## Database Reset

The SQLite database is at `data/glance.db`.

### When to reset

- After adding or removing images in `ga_library/` (auto-seed only runs on empty table)
- After schema changes in `db.py`
- To clear all test data and start fresh

### How to reset

```bash
rm data/glance.db
```

On next server start, `init_db()` recreates the schema and `_seed_images()` populates `ga_images` from all 47 images in `ga_library/`.

### Partial reset (keep images, clear tests)

```bash
sqlite3 data/glance.db "DELETE FROM tests; DELETE FROM participants;"
```

---

## Adding Images

### Standard process

1. Place `{name}.png` and `{name}.json` in `ga_library/`
2. The JSON must contain at minimum: `domain`, `correct_product`, `products`
3. Strongly recommended: include `version`, `title`, `description`, and `semantic_references`
4. Either delete `data/glance.db` and restart, or manually insert into the database
5. Add an entry to `ga_library/REGISTRY.yaml`

See `docs/PIPELINE.md` for the full ingestion pipeline, JSON format specification, and semantic reference writing guidelines.

### Verifying an image was loaded

After startup, check the dashboard at `/dashboard`. The "Images" table lists all loaded GA images with their ID, title, domain, version, and correct answer.

Or query directly:

```bash
sqlite3 data/glance.db "SELECT id, filename, domain, version FROM ga_images;"
```

---

## Troubleshooting

### Server won't start: `ModuleNotFoundError: No module named 'sentence_transformers'`

Install the dependency:
```bash
pip install sentence-transformers
```

This also installs `torch` and `transformers`. Total disk usage is ~3.5GB.

### Server won't start: `ModuleNotFoundError: No module named 'fastapi'`

```bash
pip install fastapi uvicorn jinja2 pyyaml
```

### First test submission is slow (~15-25s)

This is the embedding model loading. The model (`paraphrase-multilingual-mpnet-base-v2`, 278M params, 768-dim) is loaded lazily on first call to `semantic.embed()`. Subsequent calls are ~80ms. The model is cached in process memory for the lifetime of the server.

If the model is not yet downloaded, the first load also downloads ~470MB from Hugging Face. This only happens once; the model is cached at `~/.cache/huggingface/`.

### S9a always returns 0 / False

Check that:
1. The sidecar JSON file exists and has a `semantic_references` field
2. `sentence-transformers` is installed (S9a falls back to the stub which always returns False without it)
3. The JSON filename matches the image filename (minus extension): `my_image.png` needs `my_image.json`

### New images not appearing in tests

The auto-seeder only runs when `ga_images` is empty. If the table already has rows:
- Delete `data/glance.db` and restart, or
- Manually insert the new image via SQL (see Database Reset section above)

### Participant sees "Vous avez complete tous les tests"

The participant has already been shown every image in the database (one test per participant per image, enforced by the `UNIQUE(participant_id, ga_image_id)` constraint). With 47 images, this takes a while. Add more images or have them re-onboard with a fresh cookie.

### Tab-switch detection not working

The `visibilitychange` event listener is in the inline JS of both `test.html` and `test_flux.html`. It only fires during the exposure/feed phase. Tab-switch detection does not work for:
- Physically covering the screen
- Moving the browser window off-screen
- Using a second monitor

This is by design: the detection catches the most common integrity violation (switching to another tab to look something up) without requiring invasive browser permissions.

### Flux mode shows no images in feed

Check that leurre images exist at `ga_library/leurres/`. Run `python generate_leurres.py` to generate them. The `leurres.json` manifest must exist and list the filenames.

### Dashboard shows wrong GLANCE scores for old tests

Tests created before the GLANCE composite and speed-accuracy columns were added may have null values. The reveal page recomputes these on the fly via `score_s9c_graduated()` and `score_glance_composite()` when stored values are missing. The dashboard uses stored values from `get_all_tests()` -- if these are null, recomputation does not happen automatically.

Fix: delete `data/glance.db` and re-run tests, or manually update via SQL:

```sql
UPDATE tests SET glance_score = (0.2 * s9a_pass) + (0.5 * s9b_pass) + (0.3 * s9c_score);
```

### Port 8742 already in use

Either stop the existing process or use a different port:

```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8743 --reload
```

### Matplotlib not installed (for image generation)

```bash
pip install matplotlib
```

Only needed for `generate_library.py` and `generate_leurres.py`. The server itself does not require matplotlib.

---

## File Locations Summary

| What | Path |
|------|------|
| Server | `C:\Users\reyno\scisense\glance\app.py` |
| Database | `C:\Users\reyno\scisense\glance\data\glance.db` |
| Configuration | `C:\Users\reyno\scisense\glance\config.yaml` |
| GA images (47) | `C:\Users\reyno\scisense\glance\ga_library\` |
| Leurre images (10) | `C:\Users\reyno\scisense\glance\ga_library\leurres\` |
| Batch generator | `C:\Users\reyno\scisense\glance\ga_library\generate_library.py` |
| Leurre generator | `C:\Users\reyno\scisense\glance\generate_leurres.py` |
| Embedding model cache | `~\.cache\huggingface\` |
| CSS | `C:\Users\reyno\scisense\glance\static\style.css` |
| Templates (8) | `C:\Users\reyno\scisense\glance\templates\` |
| Documentation | `C:\Users\reyno\scisense\glance\docs\` |
