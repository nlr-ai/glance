# Phenomenology — Graph Renderer

## What the Human Sees

The user uploads a GA and receives their analysis. Below the GA image, they see:

**Default state:** The GA image with semi-transparent spheres floating on top of it. Gold spheres on the elements that received the most attention. Blue/grey spheres on elements that were barely or never seen. Gold lines connecting elements that carry the same message. The overall impression: "I can SEE where the reader's attention goes."

**Toggle "Scanpath":** A gold dotted line appears, tracing the reading path from top-left across the image. Timestamps show when each element was fixated. The entry point pulses green. "I can FOLLOW the reader's eye."

**Toggle "Problems":** Red markers appear — dashed borders on fragile elements, dark washes on dead zones, red dots on missed narratives. "I can SEE what's broken."

**Hover:** Hovering a sphere shows its name, weight, attention percentage, and the narratives it carries (with reach status). "I can UNDERSTAND why this element matters."

## What the AI Sees

The overlay is a **sense** — a perceptual channel. When the overlay is available, the system (and future AI agents) can:
- See at a glance which parts of a GA are working and which aren't
- Compare two overlays (before/after improvement) to measure progress
- Feed the overlay image back to Gemini for meta-analysis ("what does this attention map tell you?")

## Emotional Register

- Gold spheres feel **warm, successful** — "this part works"
- Grey spheres feel **cold, concerning** — "this part is invisible"
- Red markers feel **urgent** — "fix this"
- The overall overlay feels like looking through **an expert's eyes** — "now I see what I couldn't see before"
