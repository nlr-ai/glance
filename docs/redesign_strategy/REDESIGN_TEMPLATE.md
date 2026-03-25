# GLANCE Redesign Template

Use this template for each redesign document. Save as `ga_library/redesigns/{slug}_diagnosis.md`.

---

```markdown
# [Paper Title] -- GLANCE Redesign #[N]

**Paper:** [Full citation: Authors (Year) Journal Volume:Pages. DOI]
**Category:** [A: Famous / B: Worst scored / C: Never had a GA]
**Voice:** [Aurore / Nicolas]
**Week:** [N]

---

## Before

- **Score GLANCE:** [X]%
- **Archetype:** [archetype name from channel_analyzer]
- **Key issues:** [2-4 bullet points from recommender.py output]
  - [e.g., "Area encoding compresses perceived magnitude (Stevens beta 0.7)"]
  - [e.g., "No clear visual hierarchy between treatment and placebo"]
  - [e.g., "Color-only differentiation fails for 8% of male viewers"]

## Diagnosis

[200 words max. What GLANCE detected and why it matters.]

[Structure: hook sentence -> what the pipeline found -> what the encoding does wrong perceptually -> one metaphor -> transition to the fix.]

[Never blame the authors. Always blame the format.]

## After (Redesign)

- **Score GLANCE:** [Y]%
- **Archetype:** [archetype name]
- **Delta:** +[Z]%

## What Changed

- [Specific visual change 1, e.g., "Replaced pie chart with horizontal bars (Stevens beta 0.7 -> 1.0)"]
- [Specific visual change 2, e.g., "Added luminance gradient for uncertainty encoding"]
- [Specific visual change 3, e.g., "Reduced text to 28 words (under 30-word budget)"]
- [Specific visual change 4, e.g., "Sorted bars by magnitude (strongest evidence on top)"]

## Channel Analysis

| Channel | Before | After |
|---------|--------|-------|
| Primary magnitude | [e.g., area (bubble)] | [e.g., length (bar)] |
| Hierarchy signal | [e.g., color only] | [e.g., length + position] |
| Uncertainty | [e.g., absent] | [e.g., luminance gradient] |
| Text load | [e.g., 67 words] | [e.g., 24 words] |

## Assets

- Side-by-side: `{slug}_sidebyside.png` (1200x628)
- Redesign GA: `{slug}_after.png`
- Original GA: `{slug}_before.png`
- Graph (before): `{slug}_before_graph.yaml`
- Graph (after): `{slug}_after_graph.yaml`
- Layout config: `{slug}_layout.yaml`
- Palette config: `{slug}_palette.yaml`

## Template

Download the GLANCE scoring template: [glance.scisense.fr/template](https://glance.scisense.fr/template) (29 EUR)
```

---

## Notes on usage

- Fill all fields before publishing. No placeholders in published content.
- The diagnosis text is the LinkedIn/Twitter post body. Write it to be publishable as-is.
- The "What Changed" section is internal reference -- it does not appear in the social post.
- The channel analysis table feeds the diagnosis but is not published directly.
- Keep the diagnosis under 200 words. If it needs more, the hook is not sharp enough.
