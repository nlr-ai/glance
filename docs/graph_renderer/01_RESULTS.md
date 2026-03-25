# Results — Graph Renderer

## R1: Overlay Image
For any GA with a graph + reader sim, produce a PNG overlay showing the attention mechanism:
- Elemental spheres on top of the GA image at bbox positions
- Gold filaments between connected spheres
- Color-coded by attention (gold→green→blue→grey)
- Dead zones visually marked

**Measurement:** overlay PNG exists for every GA that has a graph in DB.

## R2: Overlay Available on ga-detail
The overlay is displayed on the ga-detail page, toggleable by the user.

**Measurement:** `/ga-detail/{slug}` shows an overlay toggle button. Clicking it renders the overlay on top of the GA image.

## R3: Overlay Generated Automatically
When `save_graph()` fires, the overlay is generated async alongside the reader sim.

**Measurement:** `save_graph()` → async thread generates overlay PNG → stored in DB or filesystem. No manual trigger needed.

## R4: Reader Sim Scanpath Auto-play
The overlay auto-animates the reader's scanpath on page load — spheres light up in sequence over 5 seconds. No click required.

**Measurement:** page load triggers JS animation. After 5s, final state holds + "Rejouer" button appears.

## R5: OG Card Diagonal Split
The OG sharing card shows a diagonal split: original GA (top-left) / overlay render (bottom-right).

**Measurement:** `/og/ga/{id}.png` returns a composite image with diagonal split when overlay exists.

## R6: Share Video
The user can share a short video (5-10s MP4) of the scanpath animation playing over their GA. One click → video generated server-side → shareable URL.

**Measurement:** "Partager la video" button on ga-detail generates `/video/ga/{slug}.mp4` and copies share link to clipboard.
