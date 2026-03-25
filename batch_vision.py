"""Batch Vision Analysis — Run all 47 GAs through Gemini Vision pipeline.

Usage:
    python batch_vision.py [--delay 2] [--skip-existing]
"""

import os
import sys
import time
import glob
import json
import argparse

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# Load .env
env_path = os.path.join(BASE, ".env")
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def main():
    parser = argparse.ArgumentParser(description="Batch vision analysis of GA library")
    parser.add_argument("--delay", type=float, default=3.0, help="Seconds between API calls (rate limiting)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip GAs that already have a vision graph")
    args = parser.parse_args()

    from vision_scorer import analyze_ga_image

    ga_dir = os.path.join(BASE, "ga_library")
    data_dir = os.path.join(BASE, "data")

    # Get all GA PNGs (skip leurres)
    ga_files = sorted(glob.glob(os.path.join(ga_dir, "*.png")))
    ga_files = [f for f in ga_files if "leurre" not in os.path.basename(f).lower()]

    print(f"Found {len(ga_files)} GA images")

    results = []
    errors = []

    for i, ga_path in enumerate(ga_files, 1):
        filename = os.path.basename(ga_path)
        stem = filename.rsplit(".", 1)[0]

        # Check if vision graph already exists
        if args.skip_existing:
            existing = glob.glob(os.path.join(data_dir, f"*{stem}*_ga_graph.yaml"))
            # Filter for vision-generated ones (user_ prefix)
            vision_existing = [e for e in existing if "user_" in os.path.basename(e)]
            if vision_existing:
                print(f"[{i}/{len(ga_files)}] SKIP {filename} (already analyzed)")
                continue

        print(f"[{i}/{len(ga_files)}] Analyzing {filename}...", end=" ", flush=True)

        try:
            with open(ga_path, "rb") as f:
                image_bytes = f.read()

            t0 = time.time()
            result = analyze_ga_image(image_bytes, filename)
            elapsed = time.time() - t0

            n_nodes = len(result["graph"]["nodes"])
            n_links = len(result["graph"]["links"])
            chart_type = result["metadata"].get("chart_type", "?")
            word_count = result["metadata"].get("word_count", "?")
            hierarchy = result["metadata"].get("hierarchy_clear", "?")

            print(f"OK ({elapsed:.1f}s) — {n_nodes}n/{n_links}l, {chart_type}, {word_count} words, hierarchy={hierarchy}")

            results.append({
                "filename": filename,
                "nodes": n_nodes,
                "links": n_links,
                "chart_type": chart_type,
                "word_count": word_count,
                "hierarchy_clear": hierarchy,
                "elapsed_s": round(elapsed, 1),
                "graph_path": result["saved_path"],
                "summary": result["metadata"].get("executive_summary_fr", ""),
            })

        except Exception as e:
            print(f"ERROR: {e}")
            errors.append({"filename": filename, "error": str(e)})

        # Rate limiting
        if i < len(ga_files):
            time.sleep(args.delay)

    # Summary
    print(f"\n{'='*60}")
    print(f"Done: {len(results)} analyzed, {len(errors)} errors")

    if results:
        avg_nodes = sum(r["nodes"] for r in results) / len(results)
        avg_links = sum(r["links"] for r in results) / len(results)
        avg_words = sum(r["word_count"] for r in results if isinstance(r["word_count"], int)) / max(1, len([r for r in results if isinstance(r["word_count"], int)]))
        hierarchy_true = sum(1 for r in results if r["hierarchy_clear"] is True)

        print(f"Avg nodes: {avg_nodes:.1f}")
        print(f"Avg links: {avg_links:.1f}")
        print(f"Avg words: {avg_words:.1f}")
        print(f"Hierarchy clear: {hierarchy_true}/{len(results)}")

    if errors:
        print(f"\nErrors:")
        for e in errors:
            print(f"  - {e['filename']}: {e['error']}")

    # Save results
    report_path = os.path.join(BASE, "exports", "batch_vision_results.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "errors": errors, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {report_path}")


if __name__ == "__main__":
    main()
