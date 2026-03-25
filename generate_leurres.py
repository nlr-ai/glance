"""Generate placeholder leurre images for GLANCE flux mode.

Creates 10 diverse, journal-style placeholder images at 1100x560px.
Run once: python generate_leurres.py
"""

import json
import os
import numpy as np

# matplotlib with non-interactive backend (no display needed)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import matplotlib.gridspec as gridspec

OUT_DIR = os.path.join(os.path.dirname(__file__), "ga_library", "leurres")
os.makedirs(OUT_DIR, exist_ok=True)

DPI = 100
W_PX, H_PX = 1100, 560
W_IN, H_IN = W_PX / DPI, H_PX / DPI

LEURRES = []


def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.05,
                facecolor=fig.get_facecolor())
    plt.close(fig)
    LEURRES.append(name)
    print(f"  saved {name}")


# ── 1. Article title card: dark bg, oncology ──────────────────────────
def make_title_card_1():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor="#1a1a2e")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("#1a1a2e")

    # Journal header bar
    ax.add_patch(Rectangle((0, 0.85), 1, 0.15, facecolor="#e94560", alpha=0.9))
    ax.text(0.05, 0.92, "JOURNAL OF CLINICAL ONCOLOGY", color="white",
            fontsize=14, fontweight="bold", va="center", family="monospace")
    ax.text(0.95, 0.92, "Vol. 44 | No. 7 | 2026", color="white",
            fontsize=10, va="center", ha="right", family="monospace")

    # Title
    ax.text(0.5, 0.62, "Phase III Randomized Trial of Pembrolizumab\nPlus Chemotherapy"
            " in Advanced Gastric Adenocarcinoma",
            color="white", fontsize=16, fontweight="bold", va="center", ha="center",
            linespacing=1.4)

    # Authors
    ax.text(0.5, 0.38, "M. Takahashi, L. Chen, R. Fernandez, K. Okonkwo et al.",
            color="#aaaacc", fontsize=11, va="center", ha="center")

    # DOI line
    ax.text(0.5, 0.28, "DOI: 10.1200/JCO.2025.44.7.1128", color="#666688",
            fontsize=9, va="center", ha="center", family="monospace")

    # Abstract snippet
    ax.text(0.5, 0.14, "BACKGROUND: Combination immunotherapy regimens have shown promise in GI malignancies.\n"
            "We report the primary analysis of KEYNOTE-859 extension cohort.",
            color="#888899", fontsize=9, va="center", ha="center", linespacing=1.5)

    save(fig, "leurre_title_oncology.png")


# ── 2. Article title card: dark bg, neuroscience ─────────────────────
def make_title_card_2():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor="#0d1117")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("#0d1117")

    # Journal header
    ax.add_patch(Rectangle((0, 0.87), 1, 0.13, facecolor="#238636", alpha=0.85))
    ax.text(0.05, 0.93, "NATURE NEUROSCIENCE", color="white",
            fontsize=14, fontweight="bold", va="center")
    ax.text(0.95, 0.93, "March 2026 | Article", color="white",
            fontsize=10, va="center", ha="right")

    ax.text(0.5, 0.62, "Cortical Oscillation Dynamics During\nSleep-Dependent Memory Consolidation"
            "\nin Human Prefrontal Cortex",
            color="#e6edf3", fontsize=15, fontweight="bold", va="center", ha="center",
            linespacing=1.4)

    ax.text(0.5, 0.38, "A. Moretti, S. Nakamura, J. Dubois, F. Al-Rashidi, P. Svensson",
            color="#8b949e", fontsize=11, va="center", ha="center")

    ax.text(0.5, 0.25, "https://doi.org/10.1038/s41593-026-01847-3", color="#58a6ff",
            fontsize=9, va="center", ha="center", family="monospace")

    save(fig, "leurre_title_neuroscience.png")


# ── 3. Article title card: epidemiology ──────────────────────────────
def make_title_card_3():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor="#1c1c1c")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("#1c1c1c")

    ax.add_patch(Rectangle((0, 0.88), 1, 0.12, facecolor="#0077b6", alpha=0.9))
    ax.text(0.05, 0.94, "THE LANCET INFECTIOUS DISEASES", color="white",
            fontsize=13, fontweight="bold", va="center")
    ax.text(0.95, 0.94, "25(3), 312-325", color="white",
            fontsize=10, va="center", ha="right")

    ax.text(0.5, 0.62, "Global Burden of Antimicrobial Resistance\nAttributable to"
            " 23 Bacterial Pathogens:\nA Systematic Analysis for 2024",
            color="#f0f0f0", fontsize=15, fontweight="bold", va="center", ha="center",
            linespacing=1.4)

    ax.text(0.5, 0.35, "GBD 2024 AMR Collaborators", color="#aaaaaa",
            fontsize=12, va="center", ha="center", style="italic")

    ax.text(0.5, 0.22, "DOI: 10.1016/S1473-3099(25)00648-7", color="#777777",
            fontsize=9, va="center", ha="center", family="monospace")

    save(fig, "leurre_title_epidemiology.png")


# ── 4. Article title card: cardiology ────────────────────────────────
def make_title_card_4():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor="#121212")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("#121212")

    ax.add_patch(Rectangle((0, 0.87), 1, 0.13, facecolor="#b22222", alpha=0.85))
    ax.text(0.05, 0.93, "EUROPEAN HEART JOURNAL", color="white",
            fontsize=13, fontweight="bold", va="center")
    ax.text(0.95, 0.93, "2026;47(8):601-614", color="white",
            fontsize=10, va="center", ha="right")

    ax.text(0.5, 0.60, "Long-Term Cardiovascular Outcomes After\nTranscatheter Aortic"
            " Valve Implantation vs.\nSurgical Replacement: 10-Year Follow-Up",
            color="#f5f5f5", fontsize=15, fontweight="bold", va="center", ha="center",
            linespacing=1.4)

    ax.text(0.5, 0.36, "P. Schmidt, M. Rossi, Y. Tanaka, A. Batra, C. Johansson et al.",
            color="#999999", fontsize=11, va="center", ha="center")

    ax.text(0.5, 0.26, "DOI: 10.1093/eurheartj/ehac826", color="#666666",
            fontsize=9, va="center", ha="center", family="monospace")

    save(fig, "leurre_title_cardiology.png")


# ── 5. Scatter plot figure ───────────────────────────────────────────
def make_scatter():
    fig, ax = plt.subplots(figsize=(W_IN, H_IN), facecolor="#fafafa")
    np.random.seed(42)

    for label, color, cx, cy in [("Group A", "#2196F3", 4, 6),
                                   ("Group B", "#FF5722", 7, 3),
                                   ("Group C", "#4CAF50", 5, 5)]:
        x = np.random.normal(cx, 1.2, 40)
        y = np.random.normal(cy, 1.0, 40)
        ax.scatter(x, y, c=color, alpha=0.6, s=50, label=label, edgecolors="white", linewidth=0.5)

    ax.set_xlabel("Biomarker Expression (log2 FC)", fontsize=11)
    ax.set_ylabel("Response Score", fontsize=11)
    ax.set_title("Figure 2. Biomarker-Response Correlation by Treatment Arm", fontsize=13, fontweight="bold")
    ax.legend(framealpha=0.9, fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    save(fig, "leurre_figure_scatter.png")


# ── 6. Line chart figure ────────────────────────────────────────────
def make_line_chart():
    fig, ax = plt.subplots(figsize=(W_IN, H_IN), facecolor="white")
    np.random.seed(7)

    months = np.arange(0, 25)
    for label, color, base, slope in [("Treatment", "#1565C0", 100, -1.8),
                                        ("Placebo", "#E53935", 100, -0.5),
                                        ("SOC", "#FB8C00", 100, -1.0)]:
        vals = base + slope * months + np.random.normal(0, 2, len(months)).cumsum() * 0.3
        ax.plot(months, vals, color=color, linewidth=2.2, label=label, marker="o", markersize=3)

    ax.set_xlabel("Months from Randomization", fontsize=11)
    ax.set_ylabel("Progression-Free Survival (%)", fontsize=11)
    ax.set_title("Figure 3. Kaplan-Meier Estimates of PFS", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.set_ylim(0, 110)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    save(fig, "leurre_figure_line_pfs.png")


# ── 7. Heatmap figure ───────────────────────────────────────────────
def make_heatmap():
    fig, ax = plt.subplots(figsize=(W_IN, H_IN), facecolor="white")
    np.random.seed(99)

    data = np.random.randn(8, 12)
    genes = [f"Gene_{chr(65+i)}" for i in range(8)]
    samples = [f"S{i+1}" for i in range(12)]

    im = ax.imshow(data, cmap="RdBu_r", aspect="auto", vmin=-2.5, vmax=2.5)
    ax.set_xticks(range(12)); ax.set_xticklabels(samples, fontsize=8, rotation=45)
    ax.set_yticks(range(8)); ax.set_yticklabels(genes, fontsize=9)
    ax.set_title("Figure 4. Differential Gene Expression Heatmap", fontsize=13, fontweight="bold")
    fig.colorbar(im, ax=ax, label="Z-score", shrink=0.8)
    fig.tight_layout()
    save(fig, "leurre_figure_heatmap.png")


# ── 8. GA-style: bar chart comparison ────────────────────────────────
def make_ga_bar():
    fig, ax = plt.subplots(figsize=(W_IN, H_IN), facecolor="#f8f9fa")
    np.random.seed(21)

    categories = ["Compound A", "Compound B", "Compound C", "Placebo"]
    efficacy = [72, 58, 65, 31]
    colors = ["#1B5E20", "#388E3C", "#66BB6A", "#BDBDBD"]
    bars = ax.bar(categories, efficacy, color=colors, edgecolor="white", linewidth=1.5, width=0.6)

    for bar, val in zip(bars, efficacy):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f"{val}%", ha="center", fontsize=12, fontweight="bold")

    ax.set_ylabel("Response Rate (%)", fontsize=11)
    ax.set_title("Graphical Abstract: Comparative Efficacy in Phase II", fontsize=13, fontweight="bold")
    ax.set_ylim(0, 95)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    save(fig, "leurre_ga_bar_comparison.png")


# ── 9. GA-style: infographic with icons ──────────────────────────────
def make_ga_infographic():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor="#f0f4f8")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("#f0f4f8")

    # Title bar
    ax.add_patch(Rectangle((0, 0.82), 1, 0.18, facecolor="#1565C0"))
    ax.text(0.5, 0.91, "SYSTEMATIC REVIEW & META-ANALYSIS", color="white",
            fontsize=16, fontweight="bold", ha="center", va="center")
    ax.text(0.5, 0.84, "Dietary Interventions for Type 2 Diabetes Management",
            color="#bbdefb", fontsize=11, ha="center", va="center")

    # Three column boxes
    for i, (title, value, sub, color) in enumerate([
        ("Studies Included", "47", "RCTs", "#43A047"),
        ("Total Patients", "12,840", "across 18 countries", "#FB8C00"),
        ("HbA1c Reduction", "-0.8%", "mean difference", "#E53935"),
    ]):
        cx = 0.18 + i * 0.32
        ax.add_patch(FancyBboxPatch((cx - 0.12, 0.35), 0.24, 0.38,
                                      boxstyle="round,pad=0.02", facecolor="white",
                                      edgecolor="#ddd", linewidth=1.5))
        ax.text(cx, 0.66, title, ha="center", va="center", fontsize=10, color="#555")
        ax.text(cx, 0.54, value, ha="center", va="center", fontsize=24,
                fontweight="bold", color=color)
        ax.text(cx, 0.42, sub, ha="center", va="center", fontsize=9, color="#888")

    # Bottom conclusion bar
    ax.add_patch(Rectangle((0.05, 0.08), 0.9, 0.18, facecolor="#E3F2FD",
                             ec="#90CAF9", linewidth=1))
    ax.text(0.5, 0.17, "CONCLUSION: Mediterranean diet showed the strongest evidence",
            ha="center", va="center", fontsize=12, fontweight="bold", color="#1565C0")
    ax.text(0.5, 0.11, "for sustained glycemic control at 12-month follow-up",
            ha="center", va="center", fontsize=10, color="#1976D2")

    save(fig, "leurre_ga_infographic_meta.png")


# ── 10. GA-style: flowchart-like diagram ─────────────────────────────
def make_ga_flowchart():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.93, "Study Selection Flow (PRISMA 2020)", fontsize=14,
            fontweight="bold", ha="center", va="center")

    # Boxes
    boxes = [
        (0.5, 0.78, "Records identified\n(n = 3,847)"),
        (0.5, 0.60, "After duplicates removed\n(n = 2,103)"),
        (0.5, 0.42, "Full-text assessed\n(n = 214)"),
        (0.5, 0.22, "Studies included\n(n = 38)"),
    ]
    excluded = [
        (0.85, 0.60, "Excluded on title/abstract\n(n = 1,889)"),
        (0.85, 0.42, "Full-text excluded\n(n = 176)"),
    ]

    for cx, cy, txt in boxes:
        ax.add_patch(FancyBboxPatch((cx - 0.16, cy - 0.07), 0.32, 0.14,
                                      boxstyle="round,pad=0.02", facecolor="#E3F2FD",
                                      edgecolor="#1565C0", linewidth=1.5))
        ax.text(cx, cy, txt, ha="center", va="center", fontsize=10)

    for cx, cy, txt in excluded:
        ax.add_patch(FancyBboxPatch((cx - 0.13, cy - 0.06), 0.26, 0.12,
                                      boxstyle="round,pad=0.02", facecolor="#FFF3E0",
                                      edgecolor="#E65100", linewidth=1))
        ax.text(cx, cy, txt, ha="center", va="center", fontsize=8, color="#BF360C")

    # Arrows (vertical main flow)
    for i in range(len(boxes) - 1):
        ax.annotate("", xy=(0.5, boxes[i+1][1] + 0.07),
                    xytext=(0.5, boxes[i][1] - 0.07),
                    arrowprops=dict(arrowstyle="->", color="#1565C0", lw=1.5))

    # Arrows to excluded
    ax.annotate("", xy=(0.72, 0.60), xytext=(0.66, 0.60),
                arrowprops=dict(arrowstyle="->", color="#E65100", lw=1))
    ax.annotate("", xy=(0.72, 0.42), xytext=(0.66, 0.42),
                arrowprops=dict(arrowstyle="->", color="#E65100", lw=1))

    save(fig, "leurre_ga_flowchart_prisma.png")


if __name__ == "__main__":
    print("Generating leurre images...")
    make_title_card_1()
    make_title_card_2()
    make_title_card_3()
    make_title_card_4()
    make_scatter()
    make_line_chart()
    make_heatmap()
    make_ga_bar()
    make_ga_infographic()
    make_ga_flowchart()

    # Write leurres.json manifest
    manifest = {"leurres": LEURRES}
    manifest_path = os.path.join(OUT_DIR, "leurres.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nWrote {manifest_path} with {len(LEURRES)} entries")
    print("Done.")
