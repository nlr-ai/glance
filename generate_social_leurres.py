"""Generate social/professional leurre images for GLANCE flux mode.

Creates 10 diverse, social-media-style placeholder images at 1100x560px.
These simulate LinkedIn/X/ResearchGate posts: personal announcements,
job listings, news, and events — making the flux feed ecologically valid.

Run once: python generate_social_leurres.py
"""

import json
import os
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
import matplotlib.patheffects as pe

OUT_DIR = os.path.join(os.path.dirname(__file__), "ga_library", "leurres")
os.makedirs(OUT_DIR, exist_ok=True)

DPI = 100
W_PX, H_PX = 1100, 560
W_IN, H_IN = W_PX / DPI, H_PX / DPI

# Color palette — dark theme matching test platform
BG_DARK = "#0f172a"
CARD_BG = "#1e293b"
CARD_BORDER = "#334155"
TEXT_PRIMARY = "#f1f5f9"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED = "#64748b"
ACCENT_BLUE = "#3b82f6"
ACCENT_GREEN = "#22c55e"
ACCENT_ORANGE = "#f97316"
ACCENT_PURPLE = "#a855f7"
ACCENT_RED = "#ef4444"
ACCENT_CYAN = "#06b6d4"
ACCENT_PINK = "#ec4899"
ACCENT_AMBER = "#f59e0b"

GENERATED = []


def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.0,
                facecolor=fig.get_facecolor())
    plt.close(fig)
    GENERATED.append(name)
    print(f"  saved {name}")


def draw_avatar(ax, x, y, radius, initials, color):
    """Draw a colored circle with initials as avatar placeholder."""
    circle = Circle((x, y), radius, facecolor=color, edgecolor="white",
                    linewidth=1.5, transform=ax.transAxes, zorder=5)
    ax.add_patch(circle)
    ax.text(x, y, initials, color="white", fontsize=11, fontweight="bold",
            ha="center", va="center", transform=ax.transAxes, zorder=6)


def draw_card_bg(ax):
    """Draw rounded card background."""
    ax.add_patch(FancyBboxPatch(
        (0.02, 0.02), 0.96, 0.96,
        boxstyle="round,pad=0.02",
        facecolor=CARD_BG, edgecolor=CARD_BORDER, linewidth=1.5
    ))


def draw_footer(ax, likes, comments, shares=None):
    """Draw like/comment/share footer bar."""
    y = 0.07
    # Divider line
    ax.plot([0.05, 0.95], [0.13, 0.13], color=CARD_BORDER, linewidth=0.8)

    # Like / comment / share counters (text-only, no emoji — DejaVu lacks them)
    ax.text(0.08, y, f"Likes {likes}", color=TEXT_MUTED, fontsize=9,
            va="center")
    ax.text(0.25, y, f"Comments {comments}", color=TEXT_MUTED, fontsize=9,
            va="center")
    if shares:
        ax.text(0.48, y, f"Shares {shares}", color=TEXT_MUTED, fontsize=9,
                va="center")


def draw_header(ax, name, title, platform, timestamp, avatar_initials,
                avatar_color, y_top=0.92):
    """Draw post header: avatar, name, title, timestamp."""
    draw_avatar(ax, 0.07, y_top - 0.02, 0.028, avatar_initials, avatar_color)
    ax.text(0.12, y_top, name, color=TEXT_PRIMARY, fontsize=11,
            fontweight="bold", va="center")
    ax.text(0.12, y_top - 0.045, title, color=TEXT_SECONDARY, fontsize=8,
            va="center")
    ax.text(0.95, y_top, f"{timestamp}  \u00b7  {platform}", color=TEXT_MUTED,
            fontsize=8, va="center", ha="right")


def wrap_text(ax, text, x, y, fontsize=11, color=TEXT_PRIMARY, width=75,
              linespacing=1.6, **kwargs):
    """Render word-wrapped text."""
    wrapped = textwrap.fill(text, width=width)
    ax.text(x, y, wrapped, color=color, fontsize=fontsize,
            va="top", linespacing=linespacing, **kwargs)


# ═══════════════════════════════════════════════════════════════════════
# PERSONAL POSTS (4)
# ═══════════════════════════════════════════════════════════════════════

def make_personal_newjob():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_DARK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_DARK)
    draw_card_bg(ax)

    draw_header(ax, "Dr. Elena Vasquez", "Pediatric Infectious Disease | Researcher",
                "LinkedIn", "2h", "EV", ACCENT_BLUE)

    body = ("Excited to announce I've joined CHU Necker-Enfants Malades as "
            "Head of Pediatric Research! After 10 years at Universite Paris-Saclay, "
            "I'm thrilled to lead a team focused on childhood respiratory infections "
            "and vaccine development. Grateful to everyone who supported this journey. "
            "New chapter, same mission: healthier kids worldwide.")
    wrap_text(ax, body, 0.06, 0.78, fontsize=11, width=80)

    # Hashtags
    ax.text(0.06, 0.32, "#NewRole  #PediatricResearch  #VaccineScience  #CHUNecker",
            color=ACCENT_BLUE, fontsize=9)

    # Engagement badge
    ax.add_patch(FancyBboxPatch((0.06, 0.18), 0.35, 0.08,
                                boxstyle="round,pad=0.01",
                                facecolor="#1e3a5f", edgecolor=ACCENT_BLUE,
                                linewidth=0.8))
    ax.text(0.235, 0.22, ">>  Career Update", color=ACCENT_BLUE,
            fontsize=9, ha="center", va="center", fontweight="bold")

    draw_footer(ax, 287, 34, 12)
    save(fig, "leurre_personal_newjob.png")


def make_personal_conference():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_DARK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_DARK)
    draw_card_bg(ax)

    draw_header(ax, "Prof. Marco Rinaldi", "Vaccinology | ESPID Board Member",
                "LinkedIn", "5h", "MR", ACCENT_GREEN)

    body = ("Just presented our work on vaccine hesitancy at #ESPID2025. "
            "Amazing discussions with colleagues from 30+ countries. "
            "Key takeaway: trust is built in communities, not in press conferences. "
            "Grateful for this incredible community of pediatric infectious disease "
            "specialists pushing the field forward every day.")
    wrap_text(ax, body, 0.06, 0.78, fontsize=11, width=80)

    # Image placeholder — conference photo
    ax.add_patch(FancyBboxPatch((0.06, 0.24), 0.88, 0.22,
                                boxstyle="round,pad=0.01",
                                facecolor="#0f2027", edgecolor=CARD_BORDER,
                                linewidth=1))
    ax.text(0.5, 0.35, "[Photo]  Conference presentation — ESPID 2025, Copenhagen",
            color=TEXT_MUTED, fontsize=10, ha="center", va="center")

    ax.text(0.06, 0.20, "#ESPID2025  #VaccineHesitancy  #PediatricID",
            color=ACCENT_GREEN, fontsize=9)

    draw_footer(ax, 156, 22, 8)
    save(fig, "leurre_personal_conference.png")


def make_personal_milestone():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_DARK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_DARK)
    draw_card_bg(ax)

    draw_header(ax, "Dr. Fatima Al-Sayed", "Epidemiologist | Meta-analysis enthusiast",
                "ResearchGate", "1d", "FA", ACCENT_PURPLE)

    body = ("500 citations on our 2019 meta-analysis! Never expected this "
            "when we started the project as a side hustle during my postdoc. "
            "Science is a marathon, not a sprint. To every PhD student feeling "
            "discouraged by reviewer #2 — keep going. Your work matters more "
            "than you think.")
    wrap_text(ax, body, 0.06, 0.78, fontsize=11, width=80)

    # Citation milestone graphic
    ax.add_patch(FancyBboxPatch((0.25, 0.25), 0.50, 0.22,
                                boxstyle="round,pad=0.02",
                                facecolor="#2d1b4e", edgecolor=ACCENT_PURPLE,
                                linewidth=1.5))
    ax.text(0.5, 0.40, "500", color=ACCENT_PURPLE, fontsize=36,
            fontweight="bold", ha="center", va="center")
    ax.text(0.5, 0.30, "citations reached", color=TEXT_SECONDARY,
            fontsize=12, ha="center", va="center")

    draw_footer(ax, 89, 15)
    save(fig, "leurre_personal_milestone.png")


def make_personal_opinion():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_DARK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_DARK)
    draw_card_bg(ax)

    draw_header(ax, "Dr. James Whitfield", "Data Viz | SciComm | Biostats",
                "X/Twitter", "8h", "JW", ACCENT_ORANGE)

    body = ("Hot take: we need to stop publishing graphical abstracts that "
            "look like abstract art. If a 5-year-old can't tell what your study "
            "is about from the GA, your GA failed. I reviewed 200 GAs last month "
            "for a meta-research project. 73% had no clear hierarchy. 41% used "
            "more than 6 colors. 28% had text smaller than 8pt. We can do better.")
    wrap_text(ax, body, 0.06, 0.78, fontsize=11, width=80)

    # Poll/engagement bar
    ax.add_patch(FancyBboxPatch((0.06, 0.20), 0.60, 0.08,
                                boxstyle="round,pad=0.01",
                                facecolor="#3b2008", edgecolor=ACCENT_ORANGE,
                                linewidth=0.8))
    ax.text(0.36, 0.24, "~ Trending in #SciComm  \u00b7  847 reposts",
            color=ACCENT_ORANGE, fontsize=9, ha="center", va="center")

    ax.text(0.06, 0.16, "#GraphicalAbstract  #SciComm  #DataViz  #AcademicTwitter",
            color=ACCENT_ORANGE, fontsize=9)

    draw_footer(ax, 234, 41, 847)
    save(fig, "leurre_personal_opinion.png")


# ═══════════════════════════════════════════════════════════════════════
# JOB LISTINGS (2)
# ═══════════════════════════════════════════════════════════════════════

def make_job_postdoc():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_DARK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_DARK)
    draw_card_bg(ax)

    draw_header(ax, "ETH Zurich", "Official University Account",
                "LinkedIn", "3d", "ETH", ACCENT_CYAN)

    # Job badge
    ax.add_patch(FancyBboxPatch((0.06, 0.72), 0.15, 0.06,
                                boxstyle="round,pad=0.01",
                                facecolor="#0e3d3d", edgecolor=ACCENT_CYAN,
                                linewidth=1))
    ax.text(0.135, 0.75, "HIRING", color=ACCENT_CYAN, fontsize=10,
            fontweight="bold", ha="center", va="center")

    ax.text(0.06, 0.67, "Postdoctoral Fellow in Computational Immunology",
            color=TEXT_PRIMARY, fontsize=14, fontweight="bold")

    details = [
        ("Duration:", "2-year position, renewable"),
        ("Salary:", "\u20ac45,000/year + benefits"),
        ("Location:", "Zurich, Switzerland"),
        ("Deadline:", "June 30, 2025"),
    ]
    for i, (label, value) in enumerate(details):
        y = 0.56 - i * 0.07
        ax.text(0.08, y, label, color=TEXT_SECONDARY, fontsize=10,
                fontweight="bold")
        ax.text(0.28, y, value, color=TEXT_PRIMARY, fontsize=10)

    desc = ("We are seeking a postdoctoral researcher with expertise in systems "
            "immunology and computational modeling. The successful candidate will "
            "work on multi-omics integration for vaccine response prediction.")
    wrap_text(ax, desc, 0.06, 0.28, fontsize=9, color=TEXT_SECONDARY, width=85)

    # Apply button
    ax.add_patch(FancyBboxPatch((0.06, 0.14), 0.20, 0.06,
                                boxstyle="round,pad=0.01",
                                facecolor=ACCENT_CYAN, edgecolor=ACCENT_CYAN,
                                linewidth=1))
    ax.text(0.16, 0.17, "Apply Now", color="white", fontsize=10,
            fontweight="bold", ha="center", va="center")

    draw_footer(ax, 67, 12)
    save(fig, "leurre_job_postdoc.png")


def make_job_medwriter():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_DARK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_DARK)
    draw_card_bg(ax)

    draw_header(ax, "Sarah Mitchell", "Talent Acquisition | Top 20 Pharma",
                "LinkedIn", "1d", "SM", ACCENT_PINK)

    # Job badge
    ax.add_patch(FancyBboxPatch((0.06, 0.72), 0.22, 0.06,
                                boxstyle="round,pad=0.01",
                                facecolor="#3b0a2a", edgecolor=ACCENT_PINK,
                                linewidth=1))
    ax.text(0.17, 0.75, "WE'RE HIRING", color=ACCENT_PINK, fontsize=10,
            fontweight="bold", ha="center", va="center")

    ax.text(0.06, 0.66, "Medical Science Liaison",
            color=TEXT_PRIMARY, fontsize=14, fontweight="bold")
    ax.text(0.06, 0.60, "Respiratory / Immunology",
            color=ACCENT_PINK, fontsize=12)

    details = [
        ("Remote:", "EU-based, travel 30%"),
        ("Company:", "Top 20 Global Pharma"),
        ("Requirements:", "PhD or PharmD, 3+ years MSL experience"),
    ]
    for i, (label, value) in enumerate(details):
        y = 0.50 - i * 0.07
        ax.text(0.08, y, label, color=TEXT_SECONDARY, fontsize=10,
                fontweight="bold")
        ax.text(0.30, y, value, color=TEXT_PRIMARY, fontsize=10)

    ax.text(0.06, 0.26, "Interested? DM me for the full job description.",
            color=TEXT_PRIMARY, fontsize=11)
    ax.text(0.06, 0.20, "Referral bonus available for qualified candidates.",
            color=TEXT_SECONDARY, fontsize=9)

    draw_footer(ax, 43, 8)
    save(fig, "leurre_job_medwriter.png")


# ═══════════════════════════════════════════════════════════════════════
# NEWS / POPULAR SCIENCE (2)
# ═══════════════════════════════════════════════════════════════════════

def make_news_who():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_DARK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_DARK)
    draw_card_bg(ax)

    draw_header(ax, "WHO", "World Health Organization | Official",
                "X/Twitter", "12h", "WHO", ACCENT_BLUE)

    # News badge
    ax.add_patch(FancyBboxPatch((0.06, 0.73), 0.18, 0.05,
                                boxstyle="round,pad=0.01",
                                facecolor=ACCENT_RED, edgecolor=ACCENT_RED,
                                linewidth=1))
    ax.text(0.15, 0.755, "BREAKING", color="white", fontsize=9,
            fontweight="bold", ha="center", va="center")

    ax.text(0.06, 0.67, "Updated Childhood Vaccination Schedule",
            color=TEXT_PRIMARY, fontsize=14, fontweight="bold")

    body = ("WHO releases updated guidelines on childhood vaccination schedules. "
            "Key change: HPV vaccine now recommended at age 9 instead of 11-12. "
            "The new schedule also consolidates boosters for DTP and introduces "
            "a single-dose malaria vaccine recommendation for endemic regions.")
    wrap_text(ax, body, 0.06, 0.60, fontsize=10.5, width=82)

    # Link preview card
    ax.add_patch(FancyBboxPatch((0.06, 0.17), 0.88, 0.14,
                                boxstyle="round,pad=0.01",
                                facecolor="#0c1929", edgecolor=CARD_BORDER,
                                linewidth=1))
    ax.text(0.10, 0.27, "who.int", color=TEXT_MUTED, fontsize=8)
    ax.text(0.10, 0.22, "Updated Immunization Schedule 2025 — Full Report",
            color=ACCENT_BLUE, fontsize=9, fontweight="bold")

    draw_footer(ax, 412, 38, 1247)
    save(fig, "leurre_news_who.png")


def make_news_funding():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_DARK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_DARK)
    draw_card_bg(ax)

    draw_header(ax, "European Commission", "Research & Innovation",
                "LinkedIn", "6h", "EC", ACCENT_AMBER)

    ax.text(0.06, 0.78, "Horizon Europe: \u20ac2.1B Health Research Call",
            color=TEXT_PRIMARY, fontsize=14, fontweight="bold")

    body = ("The European Commission announces the largest Horizon Europe call "
            "for health research to date: \u20ac2.1 billion across 47 topics. "
            "Priority areas include antimicrobial resistance, rare diseases, "
            "digital health, and pandemic preparedness.")
    wrap_text(ax, body, 0.06, 0.70, fontsize=10.5, width=82)

    # Key details boxes
    details_data = [
        ("\u20ac2.1B", "Total\nfunding", ACCENT_AMBER),
        ("47", "Research\ntopics", ACCENT_GREEN),
        ("Sep 2025", "Application\ndeadline", ACCENT_BLUE),
    ]
    for i, (big, small, color) in enumerate(details_data):
        cx = 0.15 + i * 0.28
        ax.add_patch(FancyBboxPatch((cx - 0.10, 0.30), 0.20, 0.16,
                                    boxstyle="round,pad=0.01",
                                    facecolor="#0c1929", edgecolor=color,
                                    linewidth=1.2))
        ax.text(cx, 0.41, big, color=color, fontsize=16,
                fontweight="bold", ha="center", va="center")
        ax.text(cx, 0.33, small, color=TEXT_SECONDARY, fontsize=8,
                ha="center", va="center", linespacing=1.3)

    ax.text(0.06, 0.24, "#HorizonEurope  #ResearchFunding  #HealthResearch  #EU",
            color=ACCENT_AMBER, fontsize=9)

    draw_footer(ax, 324, 27, 89)
    save(fig, "leurre_news_funding.png")


# ═══════════════════════════════════════════════════════════════════════
# EVENTS (2)
# ═══════════════════════════════════════════════════════════════════════

def make_event_webinar():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_DARK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_DARK)
    draw_card_bg(ax)

    draw_header(ax, "MedEd Global", "Medical Education Platform",
                "LinkedIn", "2d", "MG", ACCENT_GREEN)

    # FREE badge
    ax.add_patch(FancyBboxPatch((0.06, 0.73), 0.12, 0.05,
                                boxstyle="round,pad=0.01",
                                facecolor=ACCENT_GREEN, edgecolor=ACCENT_GREEN,
                                linewidth=1))
    ax.text(0.12, 0.755, "FREE", color="white", fontsize=10,
            fontweight="bold", ha="center", va="center")

    ax.text(0.06, 0.67, "Evidence-Based Medicine in the Age of AI",
            color=TEXT_PRIMARY, fontsize=14, fontweight="bold")
    ax.text(0.06, 0.61, "LIVE WEBINAR  \u00b7  March 30, 2026  \u00b7  14:00 CET",
            color=ACCENT_GREEN, fontsize=11)

    # Speakers
    speakers = [
        ("Prof. Ana Torres", "Cochrane Collaboration", "AT", ACCENT_BLUE),
        ("Dr. Raj Patel", "Google Health AI", "RP", ACCENT_PURPLE),
        ("Dr. Ingrid Holm", "Karolinska Institute", "IH", ACCENT_ORANGE),
    ]
    ax.text(0.06, 0.52, "Speakers:", color=TEXT_SECONDARY, fontsize=10,
            fontweight="bold")
    for i, (name, affil, initials, color) in enumerate(speakers):
        y = 0.45 - i * 0.07
        draw_avatar(ax, 0.09, y, 0.018, initials, color)
        ax.text(0.13, y + 0.01, name, color=TEXT_PRIMARY, fontsize=10)
        ax.text(0.13, y - 0.02, affil, color=TEXT_SECONDARY, fontsize=8)

    # Register button
    ax.add_patch(FancyBboxPatch((0.06, 0.14), 0.25, 0.06,
                                boxstyle="round,pad=0.01",
                                facecolor=ACCENT_GREEN, edgecolor=ACCENT_GREEN,
                                linewidth=1))
    ax.text(0.185, 0.17, "Register Now", color="white", fontsize=10,
            fontweight="bold", ha="center", va="center")

    ax.text(0.35, 0.17, "1,247 registered  \u00b7  Free CME credits",
            color=TEXT_SECONDARY, fontsize=9, va="center")

    draw_footer(ax, 78, 9)
    save(fig, "leurre_event_webinar.png")


def make_event_congress():
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_DARK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_DARK)
    draw_card_bg(ax)

    draw_header(ax, "ESCMID", "European Society of Clinical Microbiology",
                "LinkedIn", "1w", "ES", ACCENT_RED)

    # Event banner
    ax.add_patch(FancyBboxPatch((0.04, 0.45), 0.92, 0.30,
                                boxstyle="round,pad=0.02",
                                facecolor="#1a0a0a", edgecolor=ACCENT_RED,
                                linewidth=2))

    ax.text(0.5, 0.69, "ECCMID 2026", color=TEXT_PRIMARY, fontsize=22,
            fontweight="bold", ha="center", va="center")
    ax.text(0.5, 0.61, "35th European Congress of Clinical Microbiology",
            color=TEXT_SECONDARY, fontsize=10, ha="center", va="center")
    ax.text(0.5, 0.55, "Vienna, Austria  \u00b7  April 12-15, 2026",
            color=ACCENT_RED, fontsize=12, ha="center", va="center",
            fontweight="bold")

    # Stats row
    stats = [
        ("15,000+", "Expected\nattendees"),
        ("3,500+", "Abstract\nsubmissions"),
        ("120+", "Countries\nrepresented"),
    ]
    for i, (num, label) in enumerate(stats):
        cx = 0.20 + i * 0.30
        ax.text(cx, 0.38, num, color=TEXT_PRIMARY, fontsize=14,
                fontweight="bold", ha="center", va="center")
        ax.text(cx, 0.30, label, color=TEXT_MUTED, fontsize=8,
                ha="center", va="center", linespacing=1.2)

    # Early bird callout
    ax.add_patch(FancyBboxPatch((0.20, 0.16), 0.60, 0.07,
                                boxstyle="round,pad=0.01",
                                facecolor="#2a0f0f", edgecolor=ACCENT_ORANGE,
                                linewidth=1))
    ax.text(0.5, 0.195, ">> Early bird registration closes April 15 — Save 30%",
            color=ACCENT_ORANGE, fontsize=10, ha="center", va="center",
            fontweight="bold")

    draw_footer(ax, 198, 14, 45)
    save(fig, "leurre_event_congress.png")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Generating social/professional leurre images...")

    # Personal posts
    make_personal_newjob()
    make_personal_conference()
    make_personal_milestone()
    make_personal_opinion()

    # Job listings
    make_job_postdoc()
    make_job_medwriter()

    # News
    make_news_who()
    make_news_funding()

    # Events
    make_event_webinar()
    make_event_congress()

    print(f"\nGenerated {len(GENERATED)} social leurre images.")

    # ── Update leurres.json ────────────────────────────────────────────
    manifest_path = os.path.join(OUT_DIR, "leurres.json")

    # Load existing
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    existing_filenames = {l["filename"] for l in manifest["leurres"]}

    new_entries = [
        {
            "filename": "leurre_personal_newjob.png",
            "title": "Excited to announce I've joined CHU Necker as Head of Pediatric Research!",
            "author": "Dr. Elena Vasquez",
            "journal": "LinkedIn",
            "likes": 287,
            "comments": 34
        },
        {
            "filename": "leurre_personal_conference.png",
            "title": "Just presented our work on vaccine hesitancy at #ESPID2025",
            "author": "Prof. Marco Rinaldi",
            "journal": "LinkedIn",
            "likes": 156,
            "comments": 22
        },
        {
            "filename": "leurre_personal_milestone.png",
            "title": "500 citations on our 2019 meta-analysis!",
            "author": "Dr. Fatima Al-Sayed",
            "journal": "ResearchGate",
            "likes": 89,
            "comments": 15
        },
        {
            "filename": "leurre_personal_opinion.png",
            "title": "Hot take: we need to stop publishing graphical abstracts that look like abstract art",
            "author": "Dr. James Whitfield",
            "journal": "X/Twitter",
            "likes": 234,
            "comments": 41
        },
        {
            "filename": "leurre_job_postdoc.png",
            "title": "HIRING: Postdoctoral Fellow in Computational Immunology",
            "author": "ETH Zurich",
            "journal": "LinkedIn",
            "likes": 67,
            "comments": 12
        },
        {
            "filename": "leurre_job_medwriter.png",
            "title": "Looking for a Medical Science Liaison — Respiratory/Immunology",
            "author": "Sarah Mitchell",
            "journal": "LinkedIn",
            "likes": 43,
            "comments": 8
        },
        {
            "filename": "leurre_news_who.png",
            "title": "WHO releases updated guidelines on childhood vaccination schedules",
            "author": "WHO",
            "journal": "X/Twitter",
            "likes": 412,
            "comments": 38
        },
        {
            "filename": "leurre_news_funding.png",
            "title": "EU announces \u20ac2.1B Horizon Europe call for health research",
            "author": "European Commission",
            "journal": "LinkedIn",
            "likes": 324,
            "comments": 27
        },
        {
            "filename": "leurre_event_webinar.png",
            "title": "FREE WEBINAR: Evidence-Based Medicine in the Age of AI",
            "author": "MedEd Global",
            "journal": "LinkedIn",
            "likes": 78,
            "comments": 9
        },
        {
            "filename": "leurre_event_congress.png",
            "title": "Don't miss ECCMID 2026 in Vienna! Early bird closes April 15",
            "author": "ESCMID",
            "journal": "LinkedIn",
            "likes": 198,
            "comments": 14
        },
    ]

    # Add only entries that don't already exist
    for entry in new_entries:
        if entry["filename"] not in existing_filenames:
            manifest["leurres"].append(entry)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Updated {manifest_path} — now {len(manifest['leurres'])} total leurres.")
    print("Done.")
