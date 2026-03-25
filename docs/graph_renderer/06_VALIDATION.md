# Validation — Graph Renderer

## V1: Every Node Gets a Position
After assembly, every thing node MUST have a position (from bbox or fallback estimation). No node can be rendered at (0,0) by default.

## V2: Color Bounds
All colors MUST be valid RGB tuples with values in [0, 255]. The interpolation function MUST clamp outputs.

## V3: Overlay Dimensions Match Image
The SVG viewBox and PNG dimensions MUST exactly match the GA image display dimensions. A 1px misalignment breaks the spatial mapping.

## V4: No Overlay Without Sim
The overlay MUST NOT render if no reader sim results exist for this graph. An overlay without attention data is meaningless — show nothing rather than misleading colors.

## V5: Narrative Badge Accuracy
Narrative badges (gold/red dots) MUST match the reader sim's narrative_details exactly. A "reached" badge on a missed narrative is worse than no badge.

## V6: Dead Zone Consistency
Spaces marked as dead in the overlay MUST match `sim.dead_spaces` exactly. No false positives (marking visited spaces as dead) or false negatives.

## V7: Link Visibility Threshold
Links with weight < 0.3 MUST be hidden by default. Showing all links creates visual noise that obscures the important transmission paths.

## V8: PNG Composite Integrity
The composite PNG (GA + overlay) MUST preserve the original GA image at full resolution. The overlay is alpha-composited on top, never destructive.

## V9: Toggle State Isolation
Each toggle layer (attention, scanpath, problems) MUST be independently controllable. Toggling one layer MUST NOT affect the visibility of another.
