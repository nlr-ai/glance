#!/usr/bin/env python3
"""
OCR Library Scanner for GLANCE GA Library.

Walks through all .png files in ga_library/ (skipping leurres/),
runs easyocr on each image, and:
  1. Saves results to ocr_results.json
  2. Updates each GA's JSON sidecar with an ocr_text field
  3. Generates ocr_summary.md with stats and a table

Requirements: easyocr, Pillow
"""

import json
import os
import sys
import time
from pathlib import Path

try:
    import easyocr
except ImportError:
    print("ERROR: easyocr not installed. Run: pip install easyocr")
    sys.exit(1)

from PIL import Image


GA_DIR = Path(__file__).parent
SKIP_DIRS = {"leurres"}
OCR_RESULTS_FILE = GA_DIR / "ocr_results.json"
OCR_SUMMARY_FILE = GA_DIR / "ocr_summary.md"


def get_png_files(directory: Path) -> list[Path]:
    """Get all .png files in directory, skipping subdirectories in SKIP_DIRS."""
    pngs = []
    for f in sorted(directory.iterdir()):
        if f.is_dir() and f.name in SKIP_DIRS:
            continue
        if f.is_dir():
            continue  # Only process top-level PNGs
        if f.suffix.lower() == ".png":
            pngs.append(f)
    return pngs


def detect_languages(lines: list[str]) -> list[str]:
    """Heuristic language detection based on character patterns."""
    text = " ".join(lines).lower()
    langs = []

    # French indicators
    fr_markers = ["é", "è", "ê", "ë", "à", "â", "ù", "û", "ç", "ô", "î",
                  "des ", "les ", "une ", "du ", "la ", "le ",
                  "réduction", "scientifique", "hiérarchie"]
    if any(m in text for m in fr_markers):
        langs.append("fr")

    # English indicators
    en_markers = ["the ", "and ", "of ", "by ", "in ", "for ",
                  "efficacy", "reduction", "versus", "et al"]
    if any(m in text for m in en_markers):
        langs.append("en")

    if not langs:
        langs.append("en")  # default

    return langs


def run_ocr(reader: easyocr.Reader, png_path: Path) -> dict:
    """Run OCR on a single image and return structured result."""
    img = Image.open(png_path)
    width, height = img.size

    # Run easyocr (detail=0 returns just text strings)
    raw_lines = reader.readtext(str(png_path), detail=0)

    # Filter out noise (very short fragments that are likely artifacts)
    clean_lines = [line.strip() for line in raw_lines if len(line.strip()) >= 2]

    raw_text = "\n".join(clean_lines)
    word_count = len(raw_text.split())
    languages = detect_languages(clean_lines)

    return {
        "raw_text": raw_text,
        "lines": clean_lines,
        "word_count": word_count,
        "languages_detected": languages,
        "image_width": width,
        "image_height": height,
    }


def update_json_sidecar(png_path: Path, ocr_result: dict):
    """Update the JSON sidecar for a PNG with OCR fields.

    - Always writes raw_ocr_text (easyocr output, never curated)
    - Only writes ocr_text if it doesn't already exist (preserves curated text)
    - Always updates ocr_word_count and ocr_languages
    """
    json_path = png_path.with_suffix(".json")
    if not json_path.exists():
        return False

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Always store the raw easyocr output
    data["raw_ocr_text"] = ocr_result["raw_text"]
    data["raw_ocr_lines"] = ocr_result["lines"]

    # Only set ocr_text if it doesn't already exist (preserve curated versions)
    if "ocr_text" not in data:
        data["ocr_text"] = ocr_result["raw_text"]

    data["ocr_word_count"] = ocr_result["word_count"]
    data["ocr_languages"] = ocr_result["languages_detected"]

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return True


def generate_summary(results: dict) -> str:
    """Generate markdown summary report."""
    lines = []
    lines.append("# OCR Results Summary — GLANCE GA Library")
    lines.append("")
    lines.append(f"**Scanned:** {len(results)} images")
    lines.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Stats
    word_counts = [r["word_count"] for r in results.values()]
    if word_counts:
        avg_words = sum(word_counts) / len(word_counts)
        min_words = min(word_counts)
        max_words = max(word_counts)
        lines.append("## Statistics")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total images | {len(results)} |")
        lines.append(f"| Average words/GA | {avg_words:.1f} |")
        lines.append(f"| Min words | {min_words} |")
        lines.append(f"| Max words | {max_words} |")
        lines.append(f"| High text density (>50 words) | {sum(1 for w in word_counts if w > 50)} |")
        lines.append("")

    # Table
    lines.append("## Per-Image Results")
    lines.append("")
    lines.append("| Filename | Words | Languages | Dimensions | First 100 chars |")
    lines.append("|----------|-------|-----------|------------|-----------------|")

    for filename in sorted(results.keys()):
        r = results[filename]
        preview = r["raw_text"][:100].replace("\n", " ").replace("|", "\\|")
        langs = ", ".join(r["languages_detected"])
        dims = f"{r['image_width']}x{r['image_height']}"
        lines.append(f"| {filename} | {r['word_count']} | {langs} | {dims} | {preview} |")

    lines.append("")

    # Flag high text density
    high_density = {k: v for k, v in results.items() if v["word_count"] > 50}
    if high_density:
        lines.append("## High Text Density GAs (>50 words)")
        lines.append("")
        lines.append("These GAs may fail System 1 processing (too much text for rapid comprehension):")
        lines.append("")
        for filename in sorted(high_density.keys()):
            r = high_density[filename]
            lines.append(f"- **{filename}** ({r['word_count']} words): {r['raw_text'][:80].replace(chr(10), ' ')}...")
        lines.append("")

    return "\n".join(lines)


def main():
    print("=== GLANCE GA Library OCR Scanner ===")
    print()

    # Get PNG files
    pngs = get_png_files(GA_DIR)
    print(f"Found {len(pngs)} PNG files to process")
    print()

    # Initialize easyocr reader (supports English and French)
    print("Initializing easyocr reader (en + fr)...")
    reader = easyocr.Reader(["en", "fr"], gpu=False, verbose=False)
    print("Reader ready.")
    print()

    # Process each image
    results = {}
    for i, png_path in enumerate(pngs, 1):
        filename = png_path.name
        print(f"[{i}/{len(pngs)}] Processing {filename}...", end=" ", flush=True)

        try:
            result = run_ocr(reader, png_path)
            results[filename] = result
            print(f"OK ({result['word_count']} words, {', '.join(result['languages_detected'])})")

            # Update JSON sidecar
            if update_json_sidecar(png_path, result):
                print(f"         -> Updated {png_path.with_suffix('.json').name}")
        except Exception as e:
            print(f"FAILED: {e}")
            results[filename] = {
                "raw_text": "",
                "lines": [],
                "word_count": 0,
                "languages_detected": [],
                "image_width": 0,
                "image_height": 0,
                "error": str(e),
            }

    print()

    # Save results JSON
    print(f"Saving results to {OCR_RESULTS_FILE.name}...")
    with open(OCR_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Done.")

    # Generate summary
    print(f"Generating summary to {OCR_SUMMARY_FILE.name}...")
    summary = generate_summary(results)
    with open(OCR_SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write(summary)
    print("Done.")

    print()
    print(f"=== Complete: {len(results)} images processed ===")


if __name__ == "__main__":
    main()
