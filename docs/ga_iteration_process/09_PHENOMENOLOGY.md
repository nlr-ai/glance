# Phenomenology — GA Iteration Process

## PH1: How the researcher perceives the iteration

The researcher (GA author) experiences the process as a guided conversation with their design. They submit an image and receive:

1. **An archetype badge** — an immediately intuitive diagnosis. "Your GA is an Encyclopedie" is understood in one second. No jargon, no score tables. The archetype name and emoji carry the meaning.
2. **A French-language summary** — the `executive_summary_fr` tells them what their GA communicates (or fails to communicate) in 2-3 sentences.
3. **Actionable recommendations in plain language** — not "reduce Stevens beta from 0.7 to 1.0" but "Remplacez les bulles par des barres — vos lecteurs comprendront ~20% mieux les differences."
4. **A before/after comparison** — after applying fixes, the delta table shows concrete improvement. This is the reward signal that sustains engagement across iterations.

The researcher never sees graph YAML, node energy values, or classification confidence scores. They see archetypes, summaries, plain-language fixes, and progress.

## PH2: How Silas perceives the iteration

Silas monitors the quantitative convergence signals:

- **Archetype trajectory** — is it moving toward Cristallin? (R1)
- **hierarchy_clear flip** — did it switch from False to True? (R2)
- **word_count trend** — is it decreasing toward <= 30? (R3)
- **Max node energy** — is it decreasing toward < 0.50? (R4)
- **Delta table** — are all metrics improving or holding? (R5)

These are the vital signs of the iteration. A GA that "feels better" to the researcher but regresses on metrics needs careful review — the perception may be aesthetic, not communicative.

## PH3: The "click" moment

The iteration succeeds when the archetype badge changes. Moving from Encyclopedie to Tresor Enfoui to Cristallin across 3 versions is viscerally satisfying — the badge is a visible medal of progress. Each archetype shift represents a qualitative leap in communication effectiveness, not just a numerical score change.

This is why archetypes exist: they make the iteration loop *feelable*. A score going from 0.42 to 0.68 is abstract. Moving from "Hidden Gem" to "Crystal Clear" is a story.

## PH4: Feedback reinjection

| Observer | Feedback signal | Process adjustment |
|----------|----------------|---------------------|
| Researcher | "I fixed the word count but it still says Encyclopedie" | Check if word_count dropped enough (>50 is the rule trigger). Other factors may dominate: chart_type, hierarchy_clear |
| Researcher | "The recommendations don't match what I see" | Vision-based scores are approximations (T2). Acknowledge the gap, note for calibration |
| Silas | Energy increased after fix | The fix introduced a new unresolved element. Roll back or apply compensating fix |
| Silas | Archetype oscillates (Spectacle -> Tresor -> Spectacle) | Fixes are trading off saliency vs. content. Need to fix both simultaneously (exception to IVN2 2-fix limit) |
| Silas | 5 iterations without convergence | Escalate to redesign (IVN3). The starting point is structurally broken |

## PH5: The iteration as a teaching tool

Beyond fixing a single GA, the iteration process teaches the researcher to see their own work through the lens of visual communication science. After 2-3 iterations, researchers internalize the principles:

- "Ah, area encoding compresses differences — I should use bars"
- "Right, 50 words is too many for a 5-second glance"
- "The hierarchy wasn't clear because I used color alone"

The process is medicine AND education. The GA improves, and so does the researcher's visual literacy. This is the long-term value of the iteration loop.
