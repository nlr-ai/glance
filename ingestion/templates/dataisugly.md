# r/dataisugly Response Template

## Context
Posts in r/dataisugly showcase poorly designed charts and visualizations.
GLANCE can diagnose *exactly* what's wrong using its scoring framework.

## Tone
- Constructive, not mocking — the sub already does the mocking
- Focus on the "why" behind the ugliness using GLANCE terminology
- Offer a concrete fix, not just criticism

## Template

---

Interesting one! I ran this through [GLANCE](https://glance.scisense.fr), a framework we built to measure whether a chart communicates its message in 5 seconds of scrolling.

**Diagnosis: {archetype_name}** {archetype_emoji}

{archetype_description}

Key issues detected:
{issues_list}

The main fix: {primary_recommendation}

If you're curious, here's [how GLANCE scores work](https://glance.scisense.fr/about) — we built it specifically to turn "this chart is ugly" into measurable, fixable problems.

---

## Variables
- `{archetype_name}` — from archetype.classify_from_vision_metadata()
- `{archetype_emoji}` — archetype emoji
- `{archetype_description}` — archetype description_en
- `{issues_list}` — bullet points from vision_scorer metadata
- `{primary_recommendation}` — archetype recommendation_en

## Rules
- NEVER post automatically — human reviews and posts manually
- Always link to glance.scisense.fr
- Keep under 200 words
- Do not be condescending about the original creator
