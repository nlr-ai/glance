#!/usr/bin/env python3
"""
Generate individual post card screenshots for each GA image and leurre.

Renders each item as a LinkedIn-style card PNG at 390px width / 2x DPR
using Playwright. Output: exports/post_screenshots/{slug}_card.png

Usage:
    python generate_post_screenshots.py
"""

import base64
import json
import mimetypes
import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.abspath(__file__))
GA_LIB = os.path.join(BASE, "ga_library")
LEURRES_DIR = os.path.join(GA_LIB, "leurres")
OUTPUT_DIR = os.path.join(BASE, "exports", "post_screenshots")

# Lifted from test_flux.html — the complete card CSS including content-type variants
CARD_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    margin: 0;
    padding: 8px;
    background: #f3f2ef;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    width: 390px;
}
.flux-card {
    background: #fff;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #d1d5db;
    text-align: left;
}
.flux-card-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.75rem 1rem;
}
.flux-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #0a66c2;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 600;
    flex-shrink: 0;
}
.flux-card-header img.flux-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    object-fit: cover;
    flex-shrink: 0;
}
.flux-card-meta {
    min-width: 0;
}
.flux-author {
    font-size: 0.85rem;
    font-weight: 600;
    color: #1a1a1a;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.flux-journal {
    font-size: 0.7rem;
    color: #6b7280;
}
.flux-card-title {
    padding: 0.6rem 1rem;
    font-size: 0.95rem;
    color: #1a1a1a;
    line-height: 1.35;
    font-weight: 700;
}
.flux-card-image {
    position: relative;
    overflow: hidden;
}
.flux-card-image img {
    width: 100%;
    height: auto;
    display: block;
}

/* Text-only posts: hide image, expand text */
.flux-card[data-type="text_only"] .flux-card-image { display: none; }
.flux-card[data-type="text_only"] .flux-card-title {
    font-size: 0.95rem;
    padding: 0.8rem 1rem 1rem;
    min-height: 80px;
    line-height: 1.5;
}

/* Video: constrain height, play button overlay */
.flux-card[data-type="video"] .flux-card-image {
    position: relative;
    max-height: 200px;
    overflow: hidden;
}
.flux-card[data-type="video"] .flux-card-image img {
    max-height: 200px;
    object-fit: cover;
}
.flux-card[data-type="video"] .flux-card-image::after {
    content: '\\25B6';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 48px;
    height: 48px;
    background: rgba(0, 0, 0, 0.6);
    border-radius: 50%;
    color: #fff;
    font-size: 1.3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    padding-left: 4px;
    pointer-events: none;
}

/* Link preview: smaller image, URL-style */
.flux-card[data-type="link_preview"] .flux-card-image img {
    max-height: 150px;
    object-fit: cover;
}
.flux-card[data-type="link_preview"] .flux-card-image {
    border-bottom: 2px solid #e5e7eb;
}
.flux-card[data-type="link_preview"] .flux-card-title {
    font-size: 0.85rem;
    color: #0a66c2;
}

/* Carousel: square-ish with page badge */
.flux-card[data-type="carousel"] .flux-card-image {
    position: relative;
    max-height: 250px;
    overflow: hidden;
}
.flux-card[data-type="carousel"] .flux-card-image img {
    max-height: 250px;
    object-fit: cover;
}
.flux-card[data-type="carousel"] .flux-card-image::after {
    content: '1/6';
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(0, 0, 0, 0.6);
    color: #fff;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    pointer-events: none;
}

.flux-card-actions {
    display: flex;
    justify-content: space-around;
    padding: 0.6rem 0;
    border-top: 1px solid #e5e7eb;
}
.flux-action {
    flex: 1;
    text-align: center;
    font-size: 0.8rem;
    font-weight: 600;
    color: #6b7280;
    cursor: default;
    padding: 0.3rem 0;
}
"""


def data_uri(path: str) -> str:
    """Convert a local image file to a base64 data URI for inline embedding."""
    abs_path = os.path.abspath(path)
    mime, _ = mimetypes.guess_type(abs_path)
    if mime is None:
        mime = "image/png"
    with open(abs_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def generate_card_html(
    image_url: str,
    title: str,
    author: str,
    journal: str,
    likes: int,
    comments: int,
    pfp_url: str | None = None,
    content_type: str = "paper",
    time_ago: str = "2h",
) -> str:
    """Generate standalone HTML for a single post card."""
    if pfp_url:
        pfp_html = f'<img class="flux-avatar" src="{pfp_url}" alt="">'
    else:
        initial = author[0].upper() if author else "R"
        pfp_html = f'<div class="flux-avatar">{initial}</div>'

    img_html = f'<img src="{image_url}" alt="Content">' if content_type != "text_only" else ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{CARD_CSS}
</style>
</head>
<body>
<div class="flux-card" data-type="{content_type}">
    <div class="flux-card-header">
        {pfp_html}
        <div class="flux-card-meta">
            <div class="flux-author">{author}</div>
            <div class="flux-journal">{journal} &middot; {time_ago}</div>
        </div>
    </div>
    <div class="flux-card-image">
        {img_html}
    </div>
    <div class="flux-card-title">{title}</div>
    <div class="flux-card-actions">
        <span class="flux-action">&#9825; {likes}</span>
        <span class="flux-action">&#128172; {comments}</span>
        <span class="flux-action">&#8599; Share</span>
    </div>
</div>
</body>
</html>"""


def screenshot_card(browser, html: str, output_path: str) -> bool:
    """Render HTML and screenshot the .flux-card element. Returns True on success."""
    page = browser.new_page(
        viewport={"width": 406, "height": 900},
        device_scale_factor=2,
    )
    try:
        page.set_content(html)
        page.wait_for_load_state("networkidle")
        card = page.query_selector(".flux-card")
        if card:
            card.screenshot(path=output_path)
            return True
        else:
            print(f"  [WARN] No .flux-card found for {output_path}")
            return False
    finally:
        page.close()


def process_ga_images(browser) -> tuple[int, int]:
    """Process all GA library images. Returns (success_count, fail_count)."""
    ok, fail = 0, 0
    json_files = sorted(f for f in os.listdir(GA_LIB) if f.endswith(".json"))

    time_labels = ["2h", "4h", "6h", "1d", "3d", "5h", "8h", "12h"]

    for i, jf in enumerate(json_files):
        json_path = os.path.join(GA_LIB, jf)
        stem = jf.replace(".json", "")
        img_path = os.path.join(GA_LIB, stem + ".png")

        if not os.path.exists(img_path):
            print(f"  [SKIP] No image for {stem}")
            fail += 1
            continue

        with open(json_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        title = meta.get("title", stem)
        domain = meta.get("domain", "science")
        # Map domain to a plausible journal name
        journal_map = {
            "tech": "Nature Machine Intelligence",
            "med": "The Lancet",
            "epidemiology": "NEJM",
            "psych": "Psychological Science",
            "climate": "Nature Climate Change",
            "econ": "American Economic Review",
            "edu": "Science of Learning",
            "nutrition": "JAMA Internal Medicine",
            "ecology": "Nature Ecology & Evolution",
            "energy": "Nature Energy",
            "infrastructure": "Nature Sustainability",
            "neuro": "Nature Neuroscience",
        }
        journal = journal_map.get(domain, "Scientific Reports")
        author = meta.get("version", "Research Team")
        # Make author more readable
        if author and not author.startswith("Dr."):
            author = f"{author} et al."

        html = generate_card_html(
            image_url=data_uri(img_path),
            title=title,
            author=author,
            journal=journal,
            likes=42 + (i * 7) % 200,
            comments=3 + (i * 3) % 30,
            content_type="paper",
            time_ago=time_labels[i % len(time_labels)],
        )

        out_path = os.path.join(OUTPUT_DIR, f"{stem}_card.png")
        if screenshot_card(browser, html, out_path):
            ok += 1
            print(f"  [OK] {stem}_card.png")
        else:
            fail += 1

    return ok, fail


def process_leurres(browser) -> tuple[int, int]:
    """Process all leurre items. Returns (success_count, fail_count)."""
    ok, fail = 0, 0
    leurres_json = os.path.join(LEURRES_DIR, "leurres.json")

    if not os.path.exists(leurres_json):
        print("  [ERROR] leurres.json not found")
        return 0, 1

    with open(leurres_json, "r", encoding="utf-8") as f:
        leurres = json.load(f).get("leurres", [])

    time_labels = ["1h", "3h", "5h", "2d", "6h", "4h", "8h", "1d"]

    for i, leurre in enumerate(leurres):
        if isinstance(leurre, str):
            print(f"  [SKIP] String entry: {leurre}")
            fail += 1
            continue

        filename = leurre.get("filename", "")
        img_path = os.path.join(LEURRES_DIR, filename)

        if not os.path.exists(img_path):
            print(f"  [SKIP] No image for {filename}")
            fail += 1
            continue

        pfp_url = None
        pfp_name = leurre.get("pfp")
        if pfp_name:
            pfp_path = os.path.join(LEURRES_DIR, pfp_name)
            if os.path.exists(pfp_path):
                pfp_url = data_uri(pfp_path)

        content_type = leurre.get("content_type", "paper")
        html = generate_card_html(
            image_url=data_uri(img_path),
            title=leurre.get("title", filename),
            author=leurre.get("author", "Unknown"),
            journal=leurre.get("journal", "Journal"),
            likes=leurre.get("likes", 0),
            comments=leurre.get("comments", 0),
            pfp_url=pfp_url,
            content_type=content_type,
            time_ago=time_labels[i % len(time_labels)],
        )

        slug = filename.rsplit(".", 1)[0]
        out_path = os.path.join(OUTPUT_DIR, f"{slug}_card.png")
        if screenshot_card(browser, html, out_path):
            ok += 1
            print(f"  [OK] {slug}_card.png")
        else:
            fail += 1

    return ok, fail


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    t0 = time.time()
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        print("=== GA Library Images ===")
        ga_ok, ga_fail = process_ga_images(browser)
        print(f"  GA: {ga_ok} OK, {ga_fail} failed/skipped")
        print()

        print("=== Leurres ===")
        lr_ok, lr_fail = process_leurres(browser)
        print(f"  Leurres: {lr_ok} OK, {lr_fail} failed/skipped")
        print()

        browser.close()

    elapsed = time.time() - t0

    # Calculate total output size
    total_bytes = 0
    count = 0
    for fname in os.listdir(OUTPUT_DIR):
        if fname.endswith("_card.png"):
            total_bytes += os.path.getsize(os.path.join(OUTPUT_DIR, fname))
            count += 1

    total_mb = total_bytes / (1024 * 1024)

    print("=== Summary ===")
    print(f"  Total cards: {count} ({ga_ok} GA + {lr_ok} leurres)")
    print(f"  Failures:    {ga_fail + lr_fail}")
    print(f"  Total size:  {total_mb:.1f} MB")
    print(f"  Time:        {elapsed:.1f}s")
    print(f"  Output:      {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
