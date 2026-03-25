"""Generate diverse LinkedIn content-type leurre images for GLANCE flux mode.

Creates 12 new leurres simulating real LinkedIn content mix:
- 3 video thumbnails (play button overlay)
- 3 carousel/document previews (slide counter)
- 3 text-only posts (no image, just text in card)
- 3 link previews (URL card with favicon + preview)

All 1100x560px, white card LinkedIn style with avatar + name + engagement bar.

Run once: python generate_diverse_leurres.py
"""

import json
import os
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np

OUT_DIR = os.path.join(os.path.dirname(__file__), "ga_library", "leurres")
os.makedirs(OUT_DIR, exist_ok=True)

DPI = 100
W_PX, H_PX = 1100, 560
W_IN, H_IN = W_PX / DPI, H_PX / DPI

# LinkedIn white card palette
BG_WHITE = "#ffffff"
CARD_BORDER = "#e0e0e0"
TEXT_PRIMARY = "#191919"
TEXT_SECONDARY = "#666666"
TEXT_MUTED = "#999999"
LINK_BLUE = "#0a66c2"
DIVIDER = "#e8e8e8"
LIGHT_GRAY_BG = "#f3f2ef"

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
    ax.text(x, y, initials, color="white", fontsize=10, fontweight="bold",
            ha="center", va="center", transform=ax.transAxes, zorder=6)


def draw_linkedin_header(ax, name, title, time_ago, avatar_initials,
                         avatar_color, y_top=0.93):
    """Draw LinkedIn-style post header: avatar, name, title, timestamp."""
    draw_avatar(ax, 0.05, y_top - 0.02, 0.025, avatar_initials, avatar_color)
    ax.text(0.09, y_top, name, color=TEXT_PRIMARY, fontsize=11,
            fontweight="bold", va="center")
    ax.text(0.09, y_top - 0.04, title, color=TEXT_SECONDARY, fontsize=8,
            va="center")
    ax.text(0.09, y_top - 0.075, time_ago, color=TEXT_MUTED,
            fontsize=8, va="center")


def draw_engagement_bar(ax, likes, comments, y=0.04):
    """Draw LinkedIn like/comment/repost/send bar."""
    # Divider line above
    ax.plot([0.03, 0.97], [y + 0.035, y + 0.035], color=DIVIDER, linewidth=0.8)

    # Engagement counts (small, above the divider)
    ax.text(0.04, y + 0.055, f"{likes} likes", color=TEXT_MUTED, fontsize=7.5,
            va="center")
    ax.text(0.25, y + 0.055, f"{comments} comments", color=TEXT_MUTED, fontsize=7.5,
            va="center")

    # Action buttons below divider
    for i, label in enumerate(["Like", "Comment", "Repost", "Send"]):
        ax.text(0.12 + i * 0.22, y, label, color=TEXT_SECONDARY, fontsize=9,
                ha="center", va="center", fontweight="bold")


def wrap_text(ax, text, x, y, fontsize=11, color=TEXT_PRIMARY, width=80,
              linespacing=1.5, **kwargs):
    """Render word-wrapped text."""
    wrapped = textwrap.fill(text, width=width)
    ax.text(x, y, wrapped, color=color, fontsize=fontsize,
            va="top", linespacing=linespacing, **kwargs)


# ═══════════════════════════════════════════════════════════════════════
# VIDEO THUMBNAILS (3) — Static screenshots with play button overlay
# ═══════════════════════════════════════════════════════════════════════

def _draw_play_button(ax, cx, cy, radius=0.06):
    """Draw a semi-transparent play button circle with triangle."""
    # Semi-transparent dark circle
    circle = Circle((cx, cy), radius, facecolor=(0, 0, 0, 0.7),
                    edgecolor="white", linewidth=2,
                    transform=ax.transAxes, zorder=10)
    ax.add_patch(circle)
    # White triangle (play icon)
    tri_x = [cx - radius * 0.35, cx - radius * 0.35, cx + radius * 0.45]
    tri_y = [cy + radius * 0.5, cy - radius * 0.5, cy]
    ax.fill(tri_x, tri_y, color="white", transform=ax.transAxes, zorder=11)


def _draw_duration_badge(ax, duration_str, x=0.92, y=0.15):
    """Draw a video duration badge like '12:34'."""
    ax.add_patch(FancyBboxPatch((x - 0.055, y - 0.02), 0.09, 0.04,
                                boxstyle="round,pad=0.005",
                                facecolor=(0, 0, 0, 0.8), edgecolor="none",
                                transform=ax.transAxes, zorder=10))
    ax.text(x - 0.01, y, duration_str, color="white", fontsize=8,
            fontweight="bold", ha="center", va="center",
            transform=ax.transAxes, zorder=11)


def make_video_talk():
    """Conference talk thumbnail with play button."""
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_WHITE)

    draw_linkedin_header(ax, "Dr. Philippe Laurent", "Oncologist | ESMO Faculty",
                         "3d", "PL", "#1565C0")

    # Video thumbnail area — dark gradient simulating conference
    ax.add_patch(Rectangle((0.03, 0.12), 0.94, 0.58,
                           facecolor="#1a1a2e", edgecolor=CARD_BORDER, linewidth=1))

    # Stage/podium simulation
    ax.add_patch(Rectangle((0.03, 0.12), 0.94, 0.15, facecolor="#0d0d1a"))
    ax.add_patch(Rectangle((0.35, 0.27), 0.30, 0.35, facecolor="#252545"))

    # Simulated slide on screen
    ax.add_patch(Rectangle((0.38, 0.35), 0.24, 0.22, facecolor="#2a2a5a",
                           edgecolor="#4a4a8a", linewidth=1))
    ax.text(0.50, 0.50, "ESMO\n2025", color="#8888cc", fontsize=12,
            ha="center", va="center", fontweight="bold")

    # Speaker silhouette (simple)
    ax.add_patch(Circle((0.25, 0.35), 0.04, facecolor="#333355",
                        transform=ax.transAxes))
    ax.add_patch(Rectangle((0.22, 0.18), 0.06, 0.13, facecolor="#333355"))

    # Title overlay at bottom of video
    ax.add_patch(Rectangle((0.03, 0.12), 0.94, 0.10,
                           facecolor=(0, 0, 0, 0.7)))
    ax.text(0.06, 0.17, "Keynote: The Future of Precision Medicine | ESMO 2025",
            color="white", fontsize=10, fontweight="bold", va="center")

    _draw_play_button(ax, 0.50, 0.45)
    _draw_duration_badge(ax, "12:34")

    draw_engagement_bar(ax, 312, 47)
    save(fig, "leurre_video_talk.png")


def make_video_tutorial():
    """Screen recording style tutorial with play button."""
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_WHITE)

    draw_linkedin_header(ax, "Dr. Maria Santos", "Biostatistician | R Enthusiast",
                         "1w", "MS", "#388E3C")

    # Screen recording area — code editor style
    ax.add_patch(Rectangle((0.03, 0.12), 0.94, 0.58,
                           facecolor="#1e1e1e", edgecolor=CARD_BORDER, linewidth=1))

    # Editor top bar
    ax.add_patch(Rectangle((0.03, 0.64), 0.94, 0.06, facecolor="#2d2d2d"))
    ax.text(0.06, 0.67, "meta_analysis.R  -  RStudio", color="#cccccc",
            fontsize=8, va="center", family="monospace")

    # Line numbers + code
    code_lines = [
        ("1", "library(metafor)"),
        ("2", "library(dplyr)"),
        ("3", ""),
        ("4", "# Load study data"),
        ("5", 'dat <- read.csv("studies.csv")'),
        ("6", ""),
        ("7", "# Random-effects model"),
        ("8", "res <- rma(yi, vi, data=dat,"),
        ("9", '          method="REML")'),
        ("10", ""),
        ("11", "forest(res, slab=dat$study)"),
    ]
    for i, (num, line) in enumerate(code_lines):
        y = 0.60 - i * 0.04
        ax.text(0.06, y, num, color="#555555", fontsize=7.5,
                va="center", family="monospace")
        # Syntax coloring
        if line.startswith("library") or line.startswith("forest"):
            color = "#569cd6"
        elif line.startswith("#"):
            color = "#6a9955"
        elif "read.csv" in line or "rma(" in line:
            color = "#dcdcaa"
        elif '"' in line:
            color = "#ce9178"
        else:
            color = "#d4d4d4"
        ax.text(0.10, y, line, color=color, fontsize=7.5,
                va="center", family="monospace")

    # Title overlay
    ax.add_patch(Rectangle((0.03, 0.12), 0.94, 0.10,
                           facecolor=(0, 0, 0, 0.7)))
    ax.text(0.06, 0.17, "How to Use R for Meta-Analysis -- Step by Step",
            color="white", fontsize=10, fontweight="bold", va="center")

    _draw_play_button(ax, 0.50, 0.45)
    _draw_duration_badge(ax, "8:21")

    draw_engagement_bar(ax, 189, 31)
    save(fig, "leurre_video_tutorial.png")


def make_video_interview():
    """Interview-style video with two people, play button."""
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_WHITE)

    draw_linkedin_header(ax, "BioTech Weekly", "Science Journalism | 45K followers",
                         "5d", "BW", "#7B1FA2")

    # Interview thumbnail — split screen
    ax.add_patch(Rectangle((0.03, 0.12), 0.94, 0.58,
                           facecolor="#1a1a2e", edgecolor=CARD_BORDER, linewidth=1))

    # Left panel — interviewer
    ax.add_patch(Rectangle((0.03, 0.12), 0.47, 0.58, facecolor="#1e2d3d"))
    ax.add_patch(Circle((0.26, 0.50), 0.06, facecolor="#2a4a6a",
                        transform=ax.transAxes))
    ax.add_patch(Rectangle((0.20, 0.22), 0.12, 0.20, facecolor="#2a4a6a"))
    ax.text(0.26, 0.16, "HOST", color="#6699cc", fontsize=8,
            ha="center", va="center", fontweight="bold")

    # Divider
    ax.plot([0.50, 0.50], [0.12, 0.70], color="#333355", linewidth=2)

    # Right panel — guest
    ax.add_patch(Rectangle((0.50, 0.12), 0.47, 0.58, facecolor="#2d1e2d"))
    ax.add_patch(Circle((0.73, 0.50), 0.06, facecolor="#5a2a5a",
                        transform=ax.transAxes))
    ax.add_patch(Rectangle((0.67, 0.22), 0.12, 0.20, facecolor="#5a2a5a"))
    ax.text(0.73, 0.16, "DR. CHEN", color="#cc66cc", fontsize=8,
            ha="center", va="center", fontweight="bold")

    # Title overlay
    ax.add_patch(Rectangle((0.03, 0.12), 0.94, 0.10,
                           facecolor=(0, 0, 0, 0.7)))
    ax.text(0.06, 0.17,
            "In Conversation: Dr. Sarah Chen on mRNA Vaccines Beyond COVID",
            color="white", fontsize=10, fontweight="bold", va="center")

    _draw_play_button(ax, 0.50, 0.45)
    _draw_duration_badge(ax, "24:56")

    draw_engagement_bar(ax, 534, 82)
    save(fig, "leurre_video_interview.png")


# ═══════════════════════════════════════════════════════════════════════
# CAROUSEL / DOCUMENT PREVIEWS (3) — First slide with page counter
# ═══════════════════════════════════════════════════════════════════════

def _draw_page_badge(ax, page_str, x=0.95, y=0.14):
    """Draw a carousel page counter badge like '1/6'."""
    ax.add_patch(FancyBboxPatch((x - 0.04, y - 0.02), 0.06, 0.04,
                                boxstyle="round,pad=0.005",
                                facecolor=(0, 0, 0, 0.7), edgecolor="none",
                                transform=ax.transAxes, zorder=10))
    ax.text(x - 0.01, y, page_str, color="white", fontsize=8,
            fontweight="bold", ha="center", va="center",
            transform=ax.transAxes, zorder=11)


def _draw_carousel_arrow(ax, x=0.97, y=0.45):
    """Draw a right-arrow indicator for carousel swipe."""
    ax.add_patch(Circle((x, y), 0.025, facecolor=(0, 0, 0, 0.4),
                        edgecolor="white", linewidth=1,
                        transform=ax.transAxes, zorder=10))
    # Right chevron
    ax.text(x, y, ">", color="white", fontsize=12, fontweight="bold",
            ha="center", va="center", transform=ax.transAxes, zorder=11)


def make_carousel_tips():
    """Clean slide: 5 tips for graphical abstracts."""
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_WHITE)

    draw_linkedin_header(ax, "Dr. Sophie Martin", "SciComm | Visual Design for Research",
                         "2d", "SM", "#E65100")

    # Carousel slide area
    ax.add_patch(Rectangle((0.03, 0.12), 0.94, 0.58,
                           facecolor="#fff8e1", edgecolor=CARD_BORDER, linewidth=1))

    # Slide title
    ax.text(0.50, 0.65, "5 Tips for Writing a Better\nGraphical Abstract",
            color="#E65100", fontsize=16, fontweight="bold",
            ha="center", va="center", linespacing=1.4)

    # Tip list preview
    tips = [
        "1.  Start with your key message, not your methods",
        "2.  Use max 4 colors (including background)",
        "3.  Left-to-right flow, never circular",
        "4.  Text: 14pt minimum, sans-serif only",
        "5.  Test at 50% zoom -- can you still read it?"
    ]
    for i, tip in enumerate(tips):
        y = 0.54 - i * 0.065
        ax.text(0.12, y, tip, color=TEXT_PRIMARY, fontsize=9.5,
                va="center")

    # Author branding at bottom of slide
    ax.add_patch(Rectangle((0.03, 0.12), 0.94, 0.06, facecolor="#E65100"))
    ax.text(0.50, 0.15, "Dr. Sophie Martin  |  @scidesign  |  Swipe for details >>",
            color="white", fontsize=9, ha="center", va="center")

    _draw_page_badge(ax, "1/6")
    _draw_carousel_arrow(ax)

    draw_engagement_bar(ax, 267, 38)
    save(fig, "leurre_carousel_tips.png")


def make_carousel_stats():
    """Data slide: Global Health Spending 2024."""
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_WHITE)

    draw_linkedin_header(ax, "Global Health Analytics", "Data-Driven Health Policy",
                         "4d", "GH", "#0277BD")

    # Carousel slide area — dark data slide
    ax.add_patch(Rectangle((0.03, 0.12), 0.94, 0.58,
                           facecolor="#0a1929", edgecolor=CARD_BORDER, linewidth=1))

    # Slide title
    ax.text(0.50, 0.66, "Global Health Spending 2024",
            color="white", fontsize=16, fontweight="bold",
            ha="center", va="center")
    ax.text(0.50, 0.61, "Key Figures", color="#90caf9", fontsize=12,
            ha="center", va="center")

    # Simulated bar chart inside the slide
    categories = ["USA", "EU", "China", "India", "Africa"]
    values = [4.3, 3.1, 1.8, 0.4, 0.2]
    colors_bars = ["#42a5f5", "#66bb6a", "#ef5350", "#ffa726", "#ab47bc"]
    bar_width = 0.12
    for i, (cat, val, col) in enumerate(zip(categories, values, colors_bars)):
        x_start = 0.10 + i * 0.17
        bar_h = val / 5.0 * 0.28
        ax.add_patch(Rectangle((x_start, 0.22), bar_width, bar_h,
                               facecolor=col, edgecolor="none"))
        ax.text(x_start + bar_width / 2, 0.22 + bar_h + 0.015,
                f"${val}T", color="white", fontsize=8,
                ha="center", va="center", fontweight="bold")
        ax.text(x_start + bar_width / 2, 0.19,
                cat, color="#90caf9", fontsize=7.5,
                ha="center", va="center")

    # Source line
    ax.text(0.50, 0.14, "Source: WHO Global Health Expenditure Database 2024",
            color="#546e7a", fontsize=7, ha="center", va="center")

    _draw_page_badge(ax, "1/8")
    _draw_carousel_arrow(ax)

    draw_engagement_bar(ax, 421, 56)
    save(fig, "leurre_carousel_stats.png")


def make_carousel_career():
    """Career advice carousel: From PhD to Industry."""
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_WHITE)

    draw_linkedin_header(ax, "Dr. Aisha Patel", "Ex-Postdoc | Now Director at Roche",
                         "6d", "AP", "#AD1457")

    # Carousel slide — clean professional
    ax.add_patch(Rectangle((0.03, 0.12), 0.94, 0.58,
                           facecolor="#fce4ec", edgecolor=CARD_BORDER, linewidth=1))

    # Title
    ax.text(0.50, 0.65, "From PhD to Industry",
            color="#880e4f", fontsize=20, fontweight="bold",
            ha="center", va="center")
    ax.text(0.50, 0.59, "What I Wish I'd Known",
            color="#ad1457", fontsize=14, ha="center", va="center")

    # Key points preview
    points = [
        "Your PhD taught you more transferable skills than you think",
        "Networking > Applications (80% of my interviews came from contacts)",
        "\"Overqualified\" is a myth -- reframe as \"deeply specialized\"",
        "Start talking to industry people 12 months before you finish",
    ]
    for i, point in enumerate(points):
        y = 0.50 - i * 0.065
        # Bullet
        ax.add_patch(Circle((0.10, y), 0.006, facecolor="#ad1457",
                            transform=ax.transAxes))
        ax.text(0.13, y, point, color=TEXT_PRIMARY, fontsize=8.5,
                va="center")

    # Bottom bar
    ax.add_patch(Rectangle((0.03, 0.12), 0.94, 0.06, facecolor="#ad1457"))
    ax.text(0.50, 0.15, "Swipe for the full story >>",
            color="white", fontsize=10, ha="center", va="center",
            fontweight="bold")

    _draw_page_badge(ax, "1/5")
    _draw_carousel_arrow(ax)

    draw_engagement_bar(ax, 1247, 193)
    save(fig, "leurre_carousel_career.png")


# ═══════════════════════════════════════════════════════════════════════
# TEXT-ONLY POSTS (3) — No image, just text content in a white card
# ═══════════════════════════════════════════════════════════════════════

def make_textonly_opinion():
    """Long opinion post, no image."""
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=LIGHT_GRAY_BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(LIGHT_GRAY_BG)

    # White card
    ax.add_patch(FancyBboxPatch((0.02, 0.02), 0.96, 0.96,
                                boxstyle="round,pad=0.01",
                                facecolor=BG_WHITE, edgecolor=CARD_BORDER,
                                linewidth=1))

    draw_linkedin_header(ax, "Prof. David Nkomo", "Health Economics | WHO Consultant",
                         "8h", "DN", "#1565C0")

    body = (
        "Unpopular opinion: Impact Factor is dead.\n\n"
        "Here's why your h-index matters more in 2026:\n\n"
        "We just finished a study analyzing 12,000 hiring decisions in "
        "academic medicine across 8 countries. The correlation between "
        "candidate IF scores and hiring outcomes? 0.04.\n\n"
        "Meanwhile, h-index correlated at 0.31 with successful "
        "hires, and citation velocity (citations/year over last 3 years) "
        "correlated at 0.38.\n\n"
        "The journal you publish in matters less than whether anyone "
        "actually reads and builds on your work.\n\n"
        "Search committees are catching on. Are you?\n\n"
        "#AcademicPublishing  #ScienceMetrics  #OpenAccess"
    )
    wrap_text(ax, body, 0.05, 0.80, fontsize=10, width=85,
              linespacing=1.45)

    draw_engagement_bar(ax, 856, 127)
    save(fig, "leurre_textonly_opinion.png")


def make_textonly_question():
    """Short question post, no image."""
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=LIGHT_GRAY_BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(LIGHT_GRAY_BG)

    # White card
    ax.add_patch(FancyBboxPatch((0.02, 0.02), 0.96, 0.96,
                                boxstyle="round,pad=0.01",
                                facecolor=BG_WHITE, edgecolor=CARD_BORDER,
                                linewidth=1))

    draw_linkedin_header(ax, "Dr. Camille Dubois", "Medical Writer | Ex-Pharma",
                         "12h", "CD", "#00838F")

    body = (
        "Quick question for my network:\n\n"
        "Has anyone successfully transitioned from bench science to "
        "medical writing?\n\n"
        "What was your path?\n\n"
        "I'm specifically curious about:\n"
        "- Did you get a certificate (AMWA, EMWA) or learn on the job?\n"
        "- How long did the transition take?\n"
        "- What surprised you the most?\n\n"
        "Asking because I mentor a lot of PhD students who are considering "
        "this path and I want to give them real data, not just my "
        "own experience.\n\n"
        "Please share or tag someone who made this jump!\n\n"
        "#MedicalWriting  #PhDCareers  #ScienceJobs"
    )
    wrap_text(ax, body, 0.05, 0.80, fontsize=10, width=85,
              linespacing=1.4)

    draw_engagement_bar(ax, 145, 89)
    save(fig, "leurre_textonly_question.png")


def make_textonly_announcement():
    """Celebration post, no image."""
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=LIGHT_GRAY_BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(LIGHT_GRAY_BG)

    # White card
    ax.add_patch(FancyBboxPatch((0.02, 0.02), 0.96, 0.96,
                                boxstyle="round,pad=0.01",
                                facecolor=BG_WHITE, edgecolor=CARD_BORDER,
                                linewidth=1))

    draw_linkedin_header(ax, "Dr. Yuki Tanaka", "Hematologist-Oncologist | Clinical Researcher",
                         "1d", "YT", "#C62828")

    body = (
        "Thrilled to share: our paper on CAR-T cell therapy in "
        "pediatric ALL just got accepted in Blood!\n\n"
        "3 years of work. 47 rejections. And here we are.\n\n"
        "This paper represents the largest real-world cohort study "
        "of tisagenlecleucel outcomes in children under 6 "
        "(n=312, 23 centers, 11 countries).\n\n"
        "Key finding: complete remission rate of 89% at 3 months, "
        "with durable responses in 71% at 24 months.\n\n"
        "Thank you to every co-author, every patient family, every "
        "nurse who collected that extra tube of blood.\n\n"
        "Science is a team sport.\n\n"
        "#CARTcells  #PediatricOncology  #Blood  #OpenAccess"
    )
    wrap_text(ax, body, 0.05, 0.80, fontsize=10, width=85,
              linespacing=1.4)

    draw_engagement_bar(ax, 1893, 214)
    save(fig, "leurre_textonly_announcement.png")


# ═══════════════════════════════════════════════════════════════════════
# LINK PREVIEWS (3) — URL card with favicon + preview image + title
# ═══════════════════════════════════════════════════════════════════════

def _draw_link_card(ax, domain, favicon_color, favicon_text,
                    title, subtitle, thumb_color, thumb_text,
                    y_start=0.14, height=0.30):
    """Draw a LinkedIn-style link preview card."""
    y_end = y_start + height

    # Card background
    ax.add_patch(FancyBboxPatch((0.03, y_start), 0.94, height,
                                boxstyle="round,pad=0.005",
                                facecolor="#f9f9f9", edgecolor=CARD_BORDER,
                                linewidth=1))

    # Thumbnail on left
    ax.add_patch(Rectangle((0.03, y_start), 0.25, height,
                           facecolor=thumb_color))
    ax.text(0.155, y_start + height / 2, thumb_text, color="white",
            fontsize=9, ha="center", va="center", fontweight="bold",
            linespacing=1.3)

    # Text content on right
    # Favicon circle
    ax.add_patch(Circle((0.32, y_end - 0.04), 0.012, facecolor=favicon_color,
                        transform=ax.transAxes))
    ax.text(0.32, y_end - 0.04, favicon_text, color="white", fontsize=5,
            ha="center", va="center", fontweight="bold",
            transform=ax.transAxes)

    # Domain
    ax.text(0.345, y_end - 0.04, domain, color=TEXT_MUTED, fontsize=7.5,
            va="center")

    # Title
    wrapped_title = textwrap.fill(title, width=55)
    ax.text(0.31, y_end - 0.09, wrapped_title, color=TEXT_PRIMARY,
            fontsize=9.5, fontweight="bold", va="top", linespacing=1.4)

    # Subtitle
    if subtitle:
        ax.text(0.31, y_start + 0.04, subtitle, color=TEXT_MUTED,
                fontsize=8, va="center")


def make_link_nature():
    """Link preview: Nature article about CRISPR."""
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_WHITE)

    draw_linkedin_header(ax, "Dr. Hannah Berg", "Genetics Researcher | CRISPR Enthusiast",
                         "3h", "HB", "#2E7D32")

    # Post text above the link card
    body = (
        "This could be the biggest CRISPR breakthrough since 2020. "
        "A new base-editing technique that corrects 90% of known "
        "pathogenic point mutations -- with minimal off-target effects. "
        "The implications for rare genetic diseases are enormous."
    )
    wrap_text(ax, body, 0.05, 0.80, fontsize=10.5, width=85)

    # Link preview card
    _draw_link_card(ax,
                    domain="nature.com",
                    favicon_color="#c62828",
                    favicon_text="N",
                    title="New CRISPR technique corrects 90% of genetic mutations",
                    subtitle="Nature | Original Research Article",
                    thumb_color="#1b5e20",
                    thumb_text="[Figure 1]\nBase editing\nefficiency",
                    y_start=0.14, height=0.38)

    draw_engagement_bar(ax, 743, 98)
    save(fig, "leurre_link_nature.png")


def make_link_bbc():
    """Link preview: BBC Health article on antibiotic resistance."""
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_WHITE)

    draw_linkedin_header(ax, "Dr. Priya Sharma", "Pediatric ID | AMR Advocate",
                         "6h", "PS", "#880E4F")

    body = (
        "This should be front-page news everywhere. Antibiotic resistance "
        "in children under 5 has doubled in Southeast Asia over the last "
        "decade. We need action, not just reports."
    )
    wrap_text(ax, body, 0.05, 0.80, fontsize=10.5, width=85)

    _draw_link_card(ax,
                    domain="bbc.com/health",
                    favicon_color="#bb1919",
                    favicon_text="B",
                    title="WHO warns of rising antibiotic resistance in children under 5",
                    subtitle="BBC Health | World News",
                    thumb_color="#263238",
                    thumb_text="[Photo]\nChild receiving\ntreatment",
                    y_start=0.14, height=0.38)

    draw_engagement_bar(ax, 567, 73)
    save(fig, "leurre_link_bbc.png")


def make_link_preprint():
    """Link preview: bioRxiv preprint."""
    fig = plt.figure(figsize=(W_IN, H_IN), facecolor=BG_WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG_WHITE)

    draw_linkedin_header(ax, "Prof. Li Wei", "Computational Biology | Single-cell Genomics",
                         "1d", "LW", "#4527A0")

    body = (
        "New preprint from our lab! We built a single-cell atlas of human "
        "liver aging across 8 decades of life (n=47 donors, 580K cells). "
        "The stellate cell niche shows the most dramatic age-related "
        "remodeling. Feedback welcome."
    )
    wrap_text(ax, body, 0.05, 0.80, fontsize=10.5, width=85)

    _draw_link_card(ax,
                    domain="biorxiv.org",
                    favicon_color="#8e0000",
                    favicon_text="bR",
                    title="Preprint: Single-cell atlas of human liver aging reveals stellate cell niche remodeling",
                    subtitle="bioRxiv | Genomics | doi: 10.1101/2026.03.14.587291",
                    thumb_color="#311b92",
                    thumb_text="[UMAP]\nCell clusters\n580K cells",
                    y_start=0.14, height=0.38)

    draw_engagement_bar(ax, 198, 34)
    save(fig, "leurre_link_preprint.png")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Generating diverse LinkedIn content-type leurre images...")

    # Video thumbnails
    make_video_talk()
    make_video_tutorial()
    make_video_interview()

    # Carousel/document previews
    make_carousel_tips()
    make_carousel_stats()
    make_carousel_career()

    # Text-only posts
    make_textonly_opinion()
    make_textonly_question()
    make_textonly_announcement()

    # Link previews
    make_link_nature()
    make_link_bbc()
    make_link_preprint()

    print(f"\nGenerated {len(GENERATED)} diverse leurre images.")

    # ── Update leurres.json ────────────────────────────────────────────
    manifest_path = os.path.join(OUT_DIR, "leurres.json")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    existing_filenames = {l["filename"] for l in manifest["leurres"]}

    # Add content_type to existing entries
    for entry in manifest["leurres"]:
        if "content_type" not in entry:
            fn = entry["filename"]
            if any(k in fn for k in ["title_", "figure_", "ga_"]):
                entry["content_type"] = "paper"
            else:
                entry["content_type"] = "social"

    new_entries = [
        # Video thumbnails
        {
            "filename": "leurre_video_talk.png",
            "title": "Keynote: The Future of Precision Medicine | ESMO 2025",
            "author": "Dr. Philippe Laurent",
            "journal": "LinkedIn",
            "likes": 312,
            "comments": 47,
            "content_type": "video"
        },
        {
            "filename": "leurre_video_tutorial.png",
            "title": "How to Use R for Meta-Analysis \u2014 Step by Step",
            "author": "Dr. Maria Santos",
            "journal": "LinkedIn",
            "likes": 189,
            "comments": 31,
            "content_type": "video"
        },
        {
            "filename": "leurre_video_interview.png",
            "title": "In Conversation: Dr. Sarah Chen on mRNA Vaccines Beyond COVID",
            "author": "BioTech Weekly",
            "journal": "LinkedIn",
            "likes": 534,
            "comments": 82,
            "content_type": "video"
        },
        # Carousel/document previews
        {
            "filename": "leurre_carousel_tips.png",
            "title": "5 Tips for Writing a Better Graphical Abstract",
            "author": "Dr. Sophie Martin",
            "journal": "LinkedIn",
            "likes": 267,
            "comments": 38,
            "content_type": "carousel"
        },
        {
            "filename": "leurre_carousel_stats.png",
            "title": "Global Health Spending 2024 \u2014 Key Figures",
            "author": "Global Health Analytics",
            "journal": "LinkedIn",
            "likes": 421,
            "comments": 56,
            "content_type": "carousel"
        },
        {
            "filename": "leurre_carousel_career.png",
            "title": "From PhD to Industry: What I Wish I'd Known",
            "author": "Dr. Aisha Patel",
            "journal": "LinkedIn",
            "likes": 1247,
            "comments": 193,
            "content_type": "carousel"
        },
        # Text-only posts
        {
            "filename": "leurre_textonly_opinion.png",
            "title": "Unpopular opinion: Impact Factor is dead. Here's why your h-index matters more in 2026...",
            "author": "Prof. David Nkomo",
            "journal": "LinkedIn",
            "likes": 856,
            "comments": 127,
            "content_type": "text_only"
        },
        {
            "filename": "leurre_textonly_question.png",
            "title": "Quick question for my network: Has anyone successfully transitioned from bench science to medical writing?",
            "author": "Dr. Camille Dubois",
            "journal": "LinkedIn",
            "likes": 145,
            "comments": 89,
            "content_type": "text_only"
        },
        {
            "filename": "leurre_textonly_announcement.png",
            "title": "Thrilled to share: our paper on CAR-T cell therapy in pediatric ALL just got accepted in Blood!",
            "author": "Dr. Yuki Tanaka",
            "journal": "LinkedIn",
            "likes": 1893,
            "comments": 214,
            "content_type": "text_only"
        },
        # Link previews
        {
            "filename": "leurre_link_nature.png",
            "title": "New CRISPR technique corrects 90% of genetic mutations | Nature",
            "author": "Dr. Hannah Berg",
            "journal": "LinkedIn",
            "likes": 743,
            "comments": 98,
            "content_type": "link_preview"
        },
        {
            "filename": "leurre_link_bbc.png",
            "title": "WHO warns of rising antibiotic resistance in children under 5",
            "author": "Dr. Priya Sharma",
            "journal": "LinkedIn",
            "likes": 567,
            "comments": 73,
            "content_type": "link_preview"
        },
        {
            "filename": "leurre_link_preprint.png",
            "title": "Preprint: Single-cell atlas of human liver aging reveals stellate cell niche remodeling",
            "author": "Prof. Li Wei",
            "journal": "LinkedIn",
            "likes": 198,
            "comments": 34,
            "content_type": "link_preview"
        },
    ]

    for entry in new_entries:
        if entry["filename"] not in existing_filenames:
            manifest["leurres"].append(entry)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Updated {manifest_path} \u2014 now {len(manifest['leurres'])} total leurres.")
    print("Done.")
