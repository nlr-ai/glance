"""
GLANCE GA Evolution Animation
Generates a morphing GIF (and MP4 if ffmpeg available) showing V1 → V6 progression.
"""

import os
import sys
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VERSIONS_DIR = Path(__file__).parent / "output" / "versions"
OUTPUT_DIR = Path(__file__).parent / "output"

VERSIONS = [
    {"v": 1, "desc": "Bare bones — title + bars only",          "score": "—"},
    {"v": 2, "desc": "Add scissors graph",                      "score": "—"},
    {"v": 3, "desc": "Add Visual Spin lens + chronometer",      "score": "~30%"},
    {"v": 4, "desc": "Fix labels, add axis scale",              "score": "~50%"},
    {"v": 5, "desc": "Boost contrast, add annotations",         "score": "~60%"},
    {"v": 6, "desc": "Gradient shine, ×7.7, grid lines",        "score": "70%"},
]

FPS = 10
HOLD_SECONDS = 2          # seconds per version hold
TRANSITION_SECONDS = 1    # seconds for cross-fade
END_EXTRA_SECONDS = 3     # extra hold on final version

HOLD_FRAMES = HOLD_SECONDS * FPS
TRANSITION_FRAMES = TRANSITION_SECONDS * FPS
END_EXTRA_FRAMES = END_EXTRA_SECONDS * FPS

CANVAS_W, CANVAS_H = 1200, 628

# Colors
BADGE_BG = (29, 53, 87)        # #1D3557
BADGE_TEXT = (255, 255, 255)
BAR_BG = (0, 0, 0, 160)        # semi-transparent black
BAR_TEXT = (255, 255, 255)
SCORE_COLORS = {
    "—":    (128, 128, 128),
    "~30%": (220, 80, 60),
    "~50%": (230, 160, 40),
    "~60%": (180, 200, 50),
    "70%":  (80, 200, 80),
}
TAGLINE_BG = (29, 53, 87, 200)

# Fonts
def load_font(size):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def load_font_regular(size):
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

FONT_BADGE = load_font(36)
FONT_DESC = load_font_regular(20)
FONT_SCORE_LABEL = load_font(18)
FONT_TAGLINE = load_font(24)
FONT_TAGLINE_SUB = load_font_regular(18)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_version_image(v_num):
    """Load and resize a version image to canvas size. Returns RGBA."""
    path = VERSIONS_DIR / f"v{v_num}_delivery.png"
    if not path.exists():
        return None
    img = Image.open(path).convert("RGBA")
    if img.size != (CANVAS_W, CANVAS_H):
        img = img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
    return img


def draw_badge(overlay_draw, v_num):
    """Draw version pill badge top-left."""
    text = f"V{v_num}"
    bbox = FONT_BADGE.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 18, 10
    x, y = 20, 16
    rx, ry = x + tw + 2 * pad_x, y + th + 2 * pad_y
    # Rounded rectangle
    overlay_draw.rounded_rectangle(
        [x, y, rx, ry], radius=16, fill=(*BADGE_BG, 210)
    )
    overlay_draw.text((x + pad_x, y + pad_y - 2), text, fill=BADGE_TEXT, font=FONT_BADGE)


def draw_bottom_bar(overlay_draw, desc, score):
    """Draw bottom info bar."""
    bar_h = 60
    y0 = CANVAS_H - bar_h
    overlay_draw.rectangle([0, y0, CANVAS_W, CANVAS_H], fill=BAR_BG)

    # Description — left
    overlay_draw.text((20, y0 + 18), desc, fill=BAR_TEXT, font=FONT_DESC)

    # Score — right
    score_color = SCORE_COLORS.get(score, (200, 200, 200))
    score_text = f"GLANCE: {score}"
    bbox = FONT_SCORE_LABEL.getbbox(score_text)
    sw = bbox[2] - bbox[0]
    overlay_draw.text((CANVAS_W - sw - 24, y0 + 20), score_text, fill=score_color, font=FONT_SCORE_LABEL)

    # Score bar indicator
    bar_x = CANVAS_W - sw - 24 - 110
    bar_y = y0 + 22
    bar_w_max = 100
    bar_h_inner = 16
    # Background bar
    overlay_draw.rounded_rectangle(
        [bar_x, bar_y, bar_x + bar_w_max, bar_y + bar_h_inner],
        radius=4, fill=(60, 60, 60, 180)
    )
    # Fill bar
    pct = {"—": 0, "~30%": 0.30, "~50%": 0.50, "~60%": 0.60, "70%": 0.70}.get(score, 0)
    if pct > 0:
        fill_w = max(8, int(bar_w_max * pct))
        overlay_draw.rounded_rectangle(
            [bar_x, bar_y, bar_x + fill_w, bar_y + bar_h_inner],
            radius=4, fill=(*score_color, 220)
        )


def make_overlaid_frame(base_img, v_info):
    """Composite overlay on top of a base image. Returns RGBA."""
    frame = base_img.copy()
    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw_badge(draw, v_info["v"])
    draw_bottom_bar(draw, v_info["desc"], v_info["score"])
    frame = Image.alpha_composite(frame, overlay)
    return frame


def crossfade(img_a, img_b, alpha):
    """Blend two RGBA images. alpha=0 → img_a, alpha=1 → img_b."""
    return Image.blend(img_a, img_b, alpha)


def add_tagline(base_img):
    """Add end-card tagline overlay."""
    frame = base_img.copy()
    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Centered tagline box
    main_text = "GLANCE"
    sub_text = "The GA that tests itself"

    main_bbox = FONT_TAGLINE.getbbox(main_text)
    sub_bbox = FONT_TAGLINE_SUB.getbbox(sub_text)
    main_w = main_bbox[2] - main_bbox[0]
    sub_w = sub_bbox[2] - sub_bbox[0]
    total_w = max(main_w, sub_w) + 60
    total_h = 80

    x0 = (CANVAS_W - total_w) // 2
    y0 = CANVAS_H - 60 - total_h - 20  # above the bottom bar

    draw.rounded_rectangle(
        [x0, y0, x0 + total_w, y0 + total_h],
        radius=12, fill=TAGLINE_BG
    )
    draw.text(
        (x0 + (total_w - main_w) // 2, y0 + 10),
        main_text, fill=(255, 255, 255), font=FONT_TAGLINE
    )
    draw.text(
        (x0 + (total_w - sub_w) // 2, y0 + 44),
        sub_text, fill=(200, 220, 255), font=FONT_TAGLINE_SUB
    )

    frame = Image.alpha_composite(frame, overlay)
    return frame


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Load images
    images = {}
    missing = []
    for vi in VERSIONS:
        img = load_version_image(vi["v"])
        if img is None:
            missing.append(f"v{vi['v']}_delivery.png")
        else:
            images[vi["v"]] = img

    if missing:
        print(f"Missing version files: {', '.join(missing)}")
        print("Will generate animation with available versions only.")

    # Filter to available versions
    available = [vi for vi in VERSIONS if vi["v"] in images]

    if len(available) < 2:
        print("Need at least 2 version images to create animation. Exiting.")
        sys.exit(1)

    print(f"Generating animation with {len(available)} versions: {[v['v'] for v in available]}")

    # Build frames
    frames = []

    for idx, vi in enumerate(available):
        base = images[vi["v"]]
        overlaid = make_overlaid_frame(base, vi)

        is_last = (idx == len(available) - 1)
        hold = HOLD_FRAMES + (END_EXTRA_FRAMES if is_last else 0)

        # Hold frames
        for _ in range(hold):
            if is_last and _ >= HOLD_FRAMES:
                # Add tagline on end-card extra frames
                frames.append(add_tagline(overlaid))
            else:
                frames.append(overlaid.copy())

        # Transition to next (if not last)
        if not is_last:
            next_vi = available[idx + 1]
            next_base = images[next_vi["v"]]
            next_overlaid = make_overlaid_frame(next_base, next_vi)

            for t in range(TRANSITION_FRAMES):
                alpha = (t + 1) / TRANSITION_FRAMES
                blended = crossfade(overlaid, next_overlaid, alpha)
                frames.append(blended)

    print(f"Total frames: {len(frames)}")

    # Convert to P mode (palette) for GIF — better quality with dithering
    gif_frames = []
    for f in frames:
        rgb = f.convert("RGB")
        gif_frames.append(rgb)

    # Save GIF
    gif_path = OUTPUT_DIR / "glance_ga_evolution.gif"
    gif_frames[0].save(
        gif_path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=int(1000 / FPS),  # ms per frame
        loop=0,
        optimize=False,
    )
    gif_size_mb = gif_path.stat().st_size / (1024 * 1024)
    print(f"GIF saved: {gif_path} ({gif_size_mb:.1f} MB)")

    # Try MP4 via ffmpeg
    try:
        # Write temp frames
        tmp_dir = OUTPUT_DIR / "_anim_tmp"
        tmp_dir.mkdir(exist_ok=True)

        print("Writing temp frames for ffmpeg...")
        for i, f in enumerate(gif_frames):
            f.save(tmp_dir / f"frame_{i:05d}.png")

        mp4_path = OUTPUT_DIR / "glance_ga_evolution.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(tmp_dir / "frame_%05d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "slow",
            str(mp4_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            mp4_size_mb = mp4_path.stat().st_size / (1024 * 1024)
            print(f"MP4 saved: {mp4_path} ({mp4_size_mb:.1f} MB)")
        else:
            print(f"ffmpeg failed: {result.stderr[:500]}")

        # Cleanup temp frames
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
        print("Temp frames cleaned up.")

    except FileNotFoundError:
        print("ffmpeg not found — skipping MP4 generation.")

    print("Done.")


if __name__ == "__main__":
    main()
