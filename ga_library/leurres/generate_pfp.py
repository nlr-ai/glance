"""Generate realistic profile pictures for GLANCE leurres using Ideogram API."""
import json
import time
import urllib.request
import urllib.error
import os
import sys

API_KEY = "K2jwd2gW9mXfev4BRZFj3zeC-Yb_PfSQIlvwFaCDDw2VN-LY-a-T3aZaovvt5xIyS0iuLOigN9hpb9of140ljg"
API_URL = "https://api.ideogram.ai/generate"

LEURRES_DIR = os.path.dirname(os.path.abspath(__file__))
LEURRES_JSON = os.path.join(LEURRES_DIR, "leurres.json")

# Map each leurre filename to a description for the profile picture prompt
AUTHOR_DESCRIPTIONS = {
    "leurre_title_oncology.png": ("pfp_reck.jpg", "a German man in his 50s with salt-and-pepper hair wearing a white medical coat"),
    "leurre_title_neuroscience.png": ("pfp_buzsaki.jpg", "a Hungarian man in his 60s wearing glasses with a warm smile"),
    "leurre_title_epidemiology.png": ("pfp_gbd.jpg", "a professional South Asian woman in her 40s wearing glasses and a navy blazer"),
    "leurre_title_cardiology.png": ("pfp_mcmurray.jpg", "a distinguished British man in his mid-50s wearing a suit and tie"),
    "leurre_figure_scatter.png": ("pfp_ribas.jpg", "a Spanish man in his 50s with dark hair wearing a lab coat"),
    "leurre_figure_line_pfs.png": ("pfp_larkin.jpg", "a friendly British man in his mid-40s wearing a hospital badge"),
    "leurre_figure_heatmap.png": ("pfp_hugo.jpg", "a young East Asian man in his mid-30s with a modern hairstyle wearing a casual blazer"),
    "leurre_ga_bar_comparison.png": ("pfp_reich.jpg", "a German man in his 50s with a well-trimmed beard looking professional"),
    "leurre_ga_infographic_meta.png": ("pfp_schuch.jpg", "a Brazilian man in his 40s with an athletic build and a warm smile"),
    "leurre_ga_flowchart_prisma.png": ("pfp_gerber.jpg", "an American woman in her mid-40s with red hair wearing a pediatrics white coat"),
    "leurre_personal_newjob.png": ("pfp_vasquez.jpg", "a Hispanic woman in her 40s with dark hair wearing a white medical coat"),
    "leurre_personal_conference.png": ("pfp_rinaldi.jpg", "an Italian man in his 50s with silver hair wearing a conference badge"),
    "leurre_personal_milestone.png": ("pfp_alsayed.jpg", "a Middle Eastern woman in her mid-30s wearing a hijab and lab coat"),
    "leurre_personal_opinion.png": ("pfp_whitfield.jpg", "a Black British man in his mid-40s wearing glasses and casual clothing"),
    "leurre_job_postdoc.png": ("pfp_eth.jpg", "a young blonde Swiss woman around 28 years old in a postdoc lab setting"),
    "leurre_job_medwriter.png": ("pfp_recruiter.jpg", "a professional brunette woman in her mid-30s in corporate attire"),
    "leurre_news_who.png": ("pfp_who.jpg", "an African woman in her 50s wearing formal professional attire"),
    "leurre_news_funding.png": ("pfp_eu.jpg", "a European man in his mid-50s wearing a suit in a Brussels office setting"),
    "leurre_event_webinar.png": ("pfp_webinar.jpg", "an East Asian man in his 30s who is a data scientist wearing casual professional clothing"),
    "leurre_event_congress.png": ("pfp_eccmid.jpg", "a Mediterranean woman in her mid-40s who is an infectious disease doctor"),
}

def make_prompt(description: str) -> str:
    return f"Professional LinkedIn headshot portrait photo of {description}, soft studio lighting, neutral background, sharp focus, 1:1 square crop"


def generate_image(prompt: str) -> str | None:
    """Call Ideogram API and return the image URL, or None on failure."""
    payload = json.dumps({
        "image_request": {
            "prompt": prompt,
            "aspect_ratio": "ASPECT_1_1",
            "model": "V_2"
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Api-Key": API_KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["data"][0]["url"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  HTTP {e.code}: {body[:200]}", flush=True)
        return None
    except Exception as e:
        print(f"  Error: {e}", flush=True)
        return None


def download_image(url: str, dest: str) -> bool:
    """Download image from URL to local file."""
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f"  Download error: {e}", flush=True)
        return False


def main():
    # Load leurres.json
    with open(LEURRES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    succeeded = 0
    failed = 0
    pfp_map = {}  # filename -> pfp_filename

    for leurre in data["leurres"]:
        fn = leurre["filename"]
        if fn not in AUTHOR_DESCRIPTIONS:
            print(f"SKIP: No description for {fn}", flush=True)
            failed += 1
            continue

        pfp_filename, description = AUTHOR_DESCRIPTIONS[fn]
        dest_path = os.path.join(LEURRES_DIR, pfp_filename)

        # Skip if already generated
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
            print(f"EXISTS: {pfp_filename} — skipping", flush=True)
            pfp_map[fn] = pfp_filename
            succeeded += 1
            continue

        prompt = make_prompt(description)
        print(f"[{succeeded + failed + 1}/20] Generating {pfp_filename}...", flush=True)
        print(f"  Prompt: {prompt[:80]}...", flush=True)

        url = generate_image(prompt)
        if not url:
            print(f"  FAILED: API returned no URL", flush=True)
            failed += 1
            time.sleep(2)
            continue

        if download_image(url, dest_path):
            size_kb = os.path.getsize(dest_path) / 1024
            print(f"  OK: saved {pfp_filename} ({size_kb:.0f} KB)", flush=True)
            pfp_map[fn] = pfp_filename
            succeeded += 1
        else:
            print(f"  FAILED: download error", flush=True)
            failed += 1

        # Rate limit: 2 second pause between calls
        time.sleep(2)

    # Update leurres.json with pfp field
    for leurre in data["leurres"]:
        fn = leurre["filename"]
        if fn in pfp_map:
            leurre["pfp"] = pfp_map[fn]

    with open(LEURRES_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nDone. Succeeded: {succeeded}, Failed: {failed}", flush=True)
    print(f"Updated {LEURRES_JSON}", flush=True)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
