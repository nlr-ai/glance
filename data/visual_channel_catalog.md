# Visual Channel Catalog — Complete Inventory of Instantaneous Visual Communication

**SciSense x Mind Protocol — March 2026**
**Purpose:** Exhaustive reference of every visual property that communicates information within the 3-5 second feed-scroll window. Foundation for GLANCE scoring and VEC design.

---

## How to read this catalog

Each entry follows the format:

- **Property** — What it is
- **Communicates** — What information the brain extracts from it
- **Speed** — Pre-attentive (<250ms), rapid attentive (250ms-2s), or cognitive (>2s)
- **GLANCE relevance** — How it connects to S9a/S9b/S9c/S10 scoring
- **Current protocol coverage** — Whether the existing GLANCE/VEC system captures it (YES = captured, PARTIAL = indirectly addressed, NO = gap)

Speed categories are based on the Treisman & Gelade (1980) feature integration theory for pre-attentive features, Kahneman (2011) System 1/System 2 boundary at ~250ms-3s, and the GLANCE 5-second exposure window.

---

## 1. Pre-attentive Features (Treisman & Gelade, <250ms)

These are processed in parallel across the entire visual field. The brain detects them *before* conscious attention is directed. A single target defined by a unique pre-attentive feature "pops out" regardless of the number of distractors (flat search slope). These are the fastest signals in the visual system.

### 1.1 Color

#### 1.1.1 Color hue

- **Communicates:** Category membership, grouping, semantic associations (red = danger/stop/negative, green = safe/go/positive, blue = trust/calm/link, yellow = warning/attention). In data visualization: nominal categories.
- **Speed:** Pre-attentive (<250ms). A single red element among blue elements is detected in constant time regardless of set size.
- **GLANCE relevance:** Hue popout determines what the eye lands on first in a GA. Misuse of hue for ordinal data (e.g., rainbow colormaps for continuous variables) creates false categorical boundaries. Relevant to S9b: if evidence levels are encoded by hue, the viewer perceives them as unordered categories, not a hierarchy.
- **Current protocol coverage:** PARTIAL. Pattern registry covers `color_pair_close` (V14, distinguishability). Hue-as-ordinal misuse is not explicitly flagged.

#### 1.1.2 Color saturation

- **Communicates:** Intuitively perceived as "intensity" or "importance" by naive viewers. In visualization literature: poor channel for encoding magnitude (MacEachren 2012). Kinkeldey et al. (2017) explicitly recommend against saturation for uncertainty.
- **Speed:** Pre-attentive (<250ms) for large saturation differences. Near-threshold differences require attentive comparison (>500ms).
- **GLANCE relevance:** Directly relevant to P34. If a GA encodes evidence strength via saturation, Stevens' law applies with poor exponent. Pattern registry flags this as high-risk.
- **Current protocol coverage:** YES. P34 in pattern_registry.yaml. Diagnostic question generated.

#### 1.1.3 Color luminance (lightness/value)

- **Communicates:** Magnitude, weight, certainty. MacEachren (2012) showed luminance is the *intuitive* channel for uncertainty: dark = certain, light = uncertain. The most natural ordinal color channel.
- **Speed:** Pre-attentive (<250ms). Luminance contrast is the fastest detected color dimension (processed in the magnocellular pathway, which is faster than the parvocellular pathway handling hue/saturation).
- **GLANCE relevance:** Recommended primary channel for encoding evidence certainty in VEC. Dark bars = strong evidence, light bars = weak evidence. If a GA *reverses* this mapping (bright/saturated = strong), it fights the brain's default.
- **Current protocol coverage:** PARTIAL. VEC design system uses luminance for certainty gradation. Not explicitly captured as a pattern_registry channel for diagnostic questions.

### 1.2 Form

#### 1.2.1 Orientation (tilt/angle)

- **Communicates:** Direction, trend (slope in line charts), categorization. A tilted bar among vertical bars pops out instantly.
- **Speed:** Pre-attentive (<250ms). Orientation differences as small as 15-20 degrees are detected pre-attentively (Wolfe 1994).
- **GLANCE relevance:** Relevant for trend perception in line charts within GAs. Misaligned elements create visual noise that slows decoding.
- **Current protocol coverage:** NO. Not in pattern registry.

#### 1.2.2 Size (length, width, area)

- **Communicates:** Magnitude, importance, hierarchy. Larger = more important / more data / stronger effect. Subject to Stevens' power law: perceived size = physical size^beta, where beta ~0.7 for area, ~1.0 for length.
- **Speed:** Pre-attentive (<250ms) for large size differences (>2:1 ratio). Near-threshold differences require attentive processing.
- **GLANCE relevance:** Core to P21 (area encoding risk) and P32 (length encoding accuracy). The single most important perceptual channel for evidence hierarchy in VEC.
- **Current protocol coverage:** YES. P21 and P32 in pattern_registry.yaml.

#### 1.2.3 Shape

- **Communicates:** Category membership (circle vs square vs triangle = different types). Not suitable for ordinal or quantitative data. Shape is a nominal-only channel.
- **Speed:** Pre-attentive (<250ms) for simple shape differences (circle among squares). Complex shapes (star vs cross) require attentive processing (~500ms).
- **GLANCE relevance:** Shape encodes product category in the immunomodulator GA (different shapes for different immunomodulators). If shapes are too similar, category boundaries blur.
- **Current protocol coverage:** NO. Not in pattern registry. Gap: shape confusability is not assessed.

#### 1.2.4 Curvature

- **Communicates:** Organic vs geometric, natural vs artificial. Curved lines are perceived as softer, more natural; straight lines as rigid, technical.
- **Speed:** Pre-attentive (<250ms) for curvature vs straight distinction. Curvature magnitude differences are slower (~500ms).
- **GLANCE relevance:** Low direct relevance to evidence encoding. Relevant to image-level categorization (is this a diagram or an illustration?).
- **Current protocol coverage:** NO.

#### 1.2.5 Line termination / intersection

- **Communicates:** Connectivity, continuation, boundary. A line that ends abruptly signals separation; one that connects signals relationship.
- **Speed:** Pre-attentive (<250ms) for terminators among continuous lines (Julesz & Bergen 1983).
- **GLANCE relevance:** Relevant to flowchart/pathway GAs where connection arrows encode causal or temporal relationships.
- **Current protocol coverage:** NO.

#### 1.2.6 Closure (enclosure)

- **Communicates:** Grouping, containment, boundary. Enclosed elements are perceived as belonging together (Gestalt law of closure).
- **Speed:** Pre-attentive (<250ms). An enclosed region pops out from unenclosed regions.
- **GLANCE relevance:** GAs that use boxes/borders to group related evidence create implicit hierarchies. Missing closure can fragment the message.
- **Current protocol coverage:** NO.

### 1.3 Motion and Temporal

#### 1.3.1 Motion (direction, velocity)

- **Communicates:** Change, urgency, direction of effect. Moving elements capture attention involuntarily (Abrams & Christ 2003).
- **Speed:** Pre-attentive (<100ms). Motion onset is one of the fastest detected features in the visual system.
- **GLANCE relevance:** Not applicable to static GAs. Highly relevant to animated GAs, GIF summaries, and Hypothetical Outcome Plots (HOPs) which Kale et al. (2019) showed improve uncertainty perception. Also relevant to feed simulation: the scroll itself is motion, and the GA must "arrest" it.
- **Current protocol coverage:** NO. Stream mode captures dwell time but not the GA's ability to arrest scroll via visual interruption.

#### 1.3.2 Flicker / onset

- **Communicates:** Novelty, change, alert. Abrupt onset of a new element captures attention involuntarily even when irrelevant to the task (Yantis & Jonides 1984).
- **Speed:** Pre-attentive (<100ms). One of the strongest attention-capture signals.
- **GLANCE relevance:** In feed simulation, the moment a GA enters the viewport is an onset event. The first 100ms of visibility determines whether the scroll is arrested. Relevant to S10 (saliency).
- **Current protocol coverage:** PARTIAL. S10 measures post-hoc recognition, but does not directly measure onset-driven attention capture.

#### 1.3.3 Stereo depth / binocular disparity

- **Communicates:** Layering, depth, figure-ground separation.
- **Speed:** Pre-attentive (<250ms) for coarse depth planes.
- **GLANCE relevance:** Not applicable to 2D screen viewing of GAs. Irrelevant to GLANCE.
- **Current protocol coverage:** N/A.

### 1.4 Spatial Position and Grouping

#### 1.4.1 Spatial position (x, y coordinates)

- **Communicates:** The most accurate encoding channel for quantitative data (Cleveland & McGill rank 1). Position on a common aligned scale enables magnitude comparison with near-perfect accuracy (beta ~1.0).
- **Speed:** Pre-attentive (<250ms) for detecting outlier positions. Magnitude comparison via position requires rapid attentive processing (~500ms).
- **GLANCE relevance:** The gold standard for evidence hierarchy encoding. VEC bars aligned on a common baseline exploit this channel. If a GA scatters evidence indicators across unaligned positions, comparison accuracy drops.
- **Current protocol coverage:** PARTIAL. VEC design uses position-on-common-scale. Pattern registry does not explicitly flag *absence* of common-scale positioning as a risk.

#### 1.4.2 Proximity (Gestalt)

- **Communicates:** Grouping, relatedness. Elements close together are perceived as belonging to the same group (Wertheimer 1923).
- **Speed:** Pre-attentive (<250ms). Proximity grouping happens automatically and cannot be suppressed.
- **GLANCE relevance:** If evidence bars for the same product are spatially separated, the viewer may fail to associate them. If unrelated elements are proximate, false associations form.
- **Current protocol coverage:** NO.

#### 1.4.3 Similarity (Gestalt)

- **Communicates:** Category membership. Elements sharing visual features (color, shape, size) are grouped together perceptually.
- **Speed:** Pre-attentive (<250ms). Operates on any shared feature dimension.
- **GLANCE relevance:** Products encoded with similar visual treatments will be perceived as equivalent. If OM-85 (strong evidence) and CRL1505 (weak evidence) share the same color, the similarity signal contradicts the hierarchy signal.
- **Current protocol coverage:** PARTIAL. V14 (color pair close) catches one instance. General similarity-based false grouping is not assessed.

#### 1.4.4 Continuity (Gestalt)

- **Communicates:** Connection, flow, sequence. Elements arranged along a smooth path are perceived as a continuous group.
- **Speed:** Pre-attentive (<250ms).
- **GLANCE relevance:** Relevant to pathway/mechanism diagrams in GAs. If the visual flow is interrupted, the narrative breaks.
- **Current protocol coverage:** NO.

#### 1.4.5 Common region (Gestalt, Palmer 1992)

- **Communicates:** Grouping by shared enclosure. Elements within a common boundary (box, colored background region) are perceived as a unit, even overriding proximity.
- **Speed:** Pre-attentive (<250ms).
- **GLANCE relevance:** GAs that use background shading or boxes to group evidence create strong perceptual units. This is a design tool the VEC can exploit deliberately.
- **Current protocol coverage:** NO.

#### 1.4.6 Connectedness (Gestalt, Palmer & Rock 1994)

- **Communicates:** Relationship, dependency. Elements connected by a line are perceived as related more strongly than elements that are merely proximate.
- **Speed:** Pre-attentive to rapid attentive (<500ms).
- **GLANCE relevance:** Connecting lines between evidence source and conclusion in a GA create causal perception. Absence of connection implies independence.
- **Current protocol coverage:** NO.

#### 1.4.7 Figure-ground segregation

- **Communicates:** What is the subject (figure) vs what is the background (ground). The brain automatically assigns "figure" status to smaller, enclosed, symmetrical, higher-contrast regions.
- **Speed:** Pre-attentive (<250ms).
- **GLANCE relevance:** A GA where the key message has low figure-ground contrast (e.g., light text on light background) fails before any content is processed. Data elements must be unambiguously "figure."
- **Current protocol coverage:** NO. Gap: figure-ground contrast ratio is not measured.

---

## 2. Perceptual Encoding Channels (Cleveland & McGill Hierarchy)

These are the channels through which quantitative information is decoded. Ordered by perceptual accuracy. The key insight: a designer choosing to encode evidence strength as area instead of length introduces ~30% perceptual compression (Stevens beta 0.7 vs 1.0) — a systematic distortion that the viewer cannot compensate for.

### 2.1 Position on a common aligned scale

- **Communicates:** Magnitude with highest accuracy. The viewer compares distances from a shared baseline.
- **Speed:** Rapid attentive (250ms-1s for simple comparisons). The feature itself (position) is detected pre-attentively; the magnitude *judgment* requires brief attention.
- **Stevens exponent:** beta ~1.0 (near-perfect linearity).
- **GLANCE relevance:** The optimal channel for encoding evidence hierarchy. VEC bars on a common baseline. If S9b fails despite position encoding, the problem is elsewhere (labeling, color interference, etc.).
- **Current protocol coverage:** YES. VEC design principle P32 recommends length/position as primary channel. Pattern registry flags absence of length encoding as "canal sous-optimal."

### 2.2 Position on non-aligned scales

- **Communicates:** Magnitude, but comparison requires memory of one value while looking at the other. Less accurate than aligned scales by ~10-20% (Cleveland & McGill 1984, experiment 2).
- **Speed:** Attentive (500ms-2s). Requires saccade + comparison from memory.
- **Stevens exponent:** beta ~0.95-1.0 (similar to aligned, but with higher variance).
- **GLANCE relevance:** Multi-panel GAs where different evidence categories are in separate regions force non-aligned comparison. This degrades S9b accuracy.
- **Current protocol coverage:** NO. Not flagged as a risk pattern.

### 2.3 Length

- **Communicates:** Magnitude via extent in one dimension. Bar charts, progress bars, evidence bars.
- **Speed:** Rapid attentive (250ms-1s).
- **Stevens exponent:** beta ~1.0 (near-linear perception).
- **GLANCE relevance:** The VEC primary encoding channel. Pattern P32. Low risk per pattern_registry.yaml.
- **Current protocol coverage:** YES. P32 in pattern registry.

### 2.4 Angle / slope

- **Communicates:** Rate of change, trend direction. Pie chart slices, line chart slopes.
- **Speed:** Rapid attentive (500ms-1.5s). Angle comparison is significantly slower and less accurate than length comparison.
- **Stevens exponent:** beta ~0.85 for angle.
- **GLANCE relevance:** Pie charts in GAs force angle decoding for proportion comparison — a perceptually inferior channel. Known distortion: angles near 0/90/180 are perceived more accurately than intermediate angles (oblique effect).
- **Current protocol coverage:** NO. Pie chart use is not flagged as a risk pattern despite being a known inferior encoding.

### 2.5 Area

- **Communicates:** Magnitude via 2D extent. Bubble charts, treemaps, proportional symbols.
- **Speed:** Rapid attentive (500ms-2s).
- **Stevens exponent:** beta ~0.7. A 10x area difference is perceived as ~5x. Systematic underestimation of large differences, overestimation of small differences.
- **GLANCE relevance:** Central risk pattern P21. If a GA uses bubble size to encode effect size or evidence volume, the viewer systematically compresses the perceived differences. The "illusion de la moyenne ponderee" (IEEE TVCG 2021) further biases perception toward larger, darker elements.
- **Current protocol coverage:** YES. P21 in pattern registry. Diagnostic question generated.

### 2.6 Volume

- **Communicates:** Magnitude via 3D extent. 3D bar charts, spheres.
- **Speed:** Attentive (1-3s). Requires mental estimation of 3D extent from 2D projection.
- **Stevens exponent:** beta ~0.6. Worse than area. 3D charts are universally condemned in visualization literature (Tufte 1983, Few 2004).
- **GLANCE relevance:** A GA using 3D elements to encode magnitude introduces ~40% perceptual compression. This is visual spin by design choice.
- **Current protocol coverage:** NO. Not in pattern registry. Gap: 3D encoding is not flagged despite being the worst quantitative channel.

### 2.7 Color saturation (for magnitude)

- **Communicates:** Intended to communicate magnitude or certainty in many designs. Perceptual reality: saturation is NOT intuitive for magnitude encoding (MacEachren 2012). Viewers do not spontaneously associate "more saturated" with "more certain" or "larger."
- **Speed:** Attentive (500ms-2s) for magnitude judgment. Pre-attentive for mere detection of saturation differences.
- **Stevens exponent:** Not well-characterized for saturation-as-magnitude. High inter-individual variance.
- **GLANCE relevance:** P34 risk pattern. Kinkeldey et al. (2017) explicitly recommend against saturation for uncertainty. A GA using saturation gradients for evidence strength is fighting the brain's wiring.
- **Current protocol coverage:** YES. P34 in pattern registry.

### 2.8 Color hue (for categories)

- **Communicates:** Nominal categories only. Hue is NOT ordinal — there is no natural "more" or "less" along the hue dimension. Red is not "more" than blue.
- **Speed:** Pre-attentive for category detection (<250ms). Ordinal judgment is impossible without learned convention (e.g., traffic light: red > yellow > green only by convention).
- **GLANCE relevance:** If a GA uses a rainbow colormap to encode a continuous variable (e.g., evidence strength from red to violet), it creates false categorical boundaries and prevents ordinal comparison. Correct use: different hues for different immunomodulators (nominal).
- **Current protocol coverage:** PARTIAL. V14 covers distinguishability. Rainbow colormap misuse is not explicitly flagged.

### 2.9 Texture / pattern density

- **Communicates:** Category, density, roughness. Hatching patterns can encode nominal categories without relying on color (accessible to colorblind viewers).
- **Speed:** Pre-attentive for texture boundary detection (<250ms, Julesz 1981). Texture-as-magnitude is attentive (1-2s).
- **GLANCE relevance:** Low current relevance to GA design. Potentially useful as a redundant channel alongside color for accessibility.
- **Current protocol coverage:** NO.

---

## 3. Social / Platform Signals (Feed Chrome)

These are signals that come not from the GA itself but from the platform interface ("chrome") surrounding it. The brain reads these in the first fixation sweep before engaging with content. In GLANCE stream mode, these are part of the stimulus triplet (frame, text, image).

### 3.1 Avatar image

- **Communicates:** Authority (professional headshot vs cartoon), gender, approximate age, ethnicity, institutional affiliation (logo vs person). The brain processes faces in ~170ms via the fusiform face area (FFA). An institutional logo signals "organization" vs a personal photo signaling "individual."
- **Speed:** Pre-attentive to rapid attentive (170-500ms). Face detection is one of the fastest and most mandatory perceptual processes — it cannot be suppressed.
- **GLANCE relevance:** In stream mode, the avatar anchors the viewer's assessment of source credibility *before* they look at the GA. A perceived-expert avatar may boost S9b by priming trust; a perceived-amateur avatar may reduce dwell time (lowering S10).
- **Current protocol coverage:** PARTIAL. Stream simulation includes avatar in the chrome, but its effect on S9b/S10 is not isolated as a variable.

### 3.2 Username / handle / institutional name

- **Communicates:** Source authority, institutional vs personal voice, field membership. "The Lancet" vs "@science_fan_42" triggers different credibility priors. Verified academic/medical institutions prime trust.
- **Speed:** Rapid attentive (250ms-1s for recognition of known entities). Unknown handles are processed as contextual background.
- **GLANCE relevance:** In GLANCE stream mode, the username is part of stimulus_text. A recognizable journal name may inflate S9b through authority bias (participant assumes the content is correct because the source is trusted). This is a potential confound.
- **Current protocol coverage:** PARTIAL. Stimulus text is captured, but username credibility is not controlled or measured as a covariate.

### 3.3 Verified badge

- **Communicates:** Institutional validation, authenticity, authority. Blue checkmark = platform-verified identity.
- **Speed:** Pre-attentive to rapid attentive (<500ms). The badge is a small, high-contrast symbol in a predictable location.
- **GLANCE relevance:** May inflate perceived credibility of GA content in stream mode. Not currently controlled.
- **Current protocol coverage:** NO.

### 3.4 Timestamp / recency

- **Communicates:** Relevance, freshness. "2h ago" = current/relevant. "2 years ago" = potentially outdated. Recency bias: recent content is perceived as more valid.
- **Speed:** Rapid attentive (500ms-1s). Requires reading text.
- **GLANCE relevance:** In stream mode, timestamps are part of the chrome. A GA posted "just now" may receive more attention than one posted "3 months ago." Not currently controlled in GLANCE feed simulation.
- **Current protocol coverage:** NO. Timestamps are present in chrome but not varied or measured.

### 3.5 Engagement counts (likes, shares, comments, views)

- **Communicates:** Social proof. High numbers = "many people found this valuable." Low numbers = "nobody cared." This is one of the most powerful cognitive biases — social proof overrides personal judgment in uncertain situations (Cialdini 2001).
- **Speed:** Rapid attentive (500ms-1s for magnitude perception of numbers). The *presence* of engagement indicators is detected pre-attentively.
- **GLANCE relevance:** A GA shown with "2,847 likes" vs "3 likes" in stream mode would likely produce different S9b scores due to authority-by-popularity bias, not design quality. This is exactly the engagement-comprehension gap the GLANCE paper documents. Must be controlled.
- **Current protocol coverage:** PARTIAL. Stream chrome includes engagement buttons but engagement counts may not be systematically controlled.

### 3.6 Platform chrome identity

- **Communicates:** Context, expected content type, social norms. LinkedIn chrome = professional/career context. Twitter/X chrome = rapid/opinion/news context. Journal TOC = academic/formal context. Each primes different reading strategies.
- **Speed:** Pre-attentive (<250ms for platform recognition from familiar visual patterns — the blue LinkedIn header, the Twitter/X card format).
- **GLANCE relevance:** Central to GLANCE experimental design. The stimulus triplet explicitly models this: same GA shown in LinkedIn chrome vs Twitter chrome vs TOC chrome vs nude. Platform chrome is a controlled independent variable. Affects both S10 (saliency in feed context) and S9b (comprehension may differ by reading strategy primed by platform).
- **Current protocol coverage:** YES. Exposure conditions explicitly model platform chrome (linkedin_card, twitter_card, mdpi_grid, none).

### 3.7 Post type indicators

- **Communicates:** Content category. "Article" vs "Shared" vs "Repost" vs "Sponsored" vs "Ad." The viewer's engagement probability drops sharply for "Sponsored" content.
- **Speed:** Rapid attentive (250ms-1s).
- **GLANCE relevance:** In stream mode, distinguishing organic from promoted content affects dwell time. GLANCE distractors should include a mix to simulate realistic feeds.
- **Current protocol coverage:** PARTIAL. Feed simulation includes distractors but post type categorization is not explicitly controlled.

### 3.8 Post text length (visible above/below image)

- **Communicates:** Effort to read, complexity. A wall of text above the image signals "this will take work" and triggers scroll-past behavior. Short, punchy text signals "quick read." The "3-line rule" on LinkedIn: text is truncated to ~3 lines with "...see more."
- **Speed:** Pre-attentive (<250ms for the gestalt impression of text volume). Reading the text is cognitive (>2s).
- **GLANCE relevance:** In stream mode, the text accompanying the GA (stimulus_text) may anchor comprehension (boosting S9b if it summarizes the key finding) or be ignored if too long. GLANCE captures stimulus_text as a variable.
- **Current protocol coverage:** YES. Stimulus_text is a controlled variable. Nude vs title-only conditions isolate text effects.

### 3.9 Reply/comment thread indicators

- **Communicates:** Engagement depth, controversy (many comments may signal debate), community validation.
- **Speed:** Rapid attentive (500ms-1s). Comment counts are read as social proof metrics.
- **GLANCE relevance:** Low direct relevance. In stream mode, the presence of "47 comments" may increase dwell time (curiosity) but is unlikely to affect S9b.
- **Current protocol coverage:** NO.

---

## 4. Typography Signals

These are processed during the first reading fixation sweep (200-300ms per fixation, 3-5 fixations in a 5-second window). Typography communicates before the *content* of words is processed — the visual form of text carries meaning independent of lexical content.

### 4.1 Font weight (bold vs regular vs light)

- **Communicates:** Importance hierarchy. Bold = primary information, emphasis, key term. Regular = body text. Light = secondary, de-emphasized.
- **Speed:** Pre-attentive for popout of bold among regular (<250ms). The *meaning* assignment (this is important because it's bold) is rapid attentive (~500ms).
- **GLANCE relevance:** In a GA, bold labels on evidence bars draw fixation first. If the bold text is the product name (good), the viewer identifies the hierarchy entry point. If bold text is decorative (bad), attention is wasted.
- **Current protocol coverage:** NO. Typography analysis is not part of current GA assessment.

### 4.2 Font size hierarchy

- **Communicates:** Information hierarchy through relative size. Title > subtitle > body > caption > footnote. The brain uses size differences to build a reading priority queue.
- **Speed:** Pre-attentive (<250ms for detecting size differences). The hierarchy interpretation is rapid attentive (~500ms).
- **GLANCE relevance:** A GA with uniform font sizes forces the viewer to read linearly rather than scanning by priority. This wastes the 5-second window on low-priority text. Related to V3 (text density): even 30 words at uniform size are harder to scan than 30 words with clear size hierarchy.
- **Current protocol coverage:** PARTIAL. V3 captures total text density. Size hierarchy quality is not assessed.

### 4.3 Font family

- **Communicates:** Genre, authority, formality. Serif fonts (Times, Garamond) = academic, traditional, authoritative. Sans-serif (Helvetica, Arial) = modern, clean, accessible. Monospace (Courier) = data, code, technical precision. Script/decorative = informal, creative.
- **Speed:** Rapid attentive (250ms-1s). Font family is perceived as a gestalt property of the text block.
- **GLANCE relevance:** A GA using a decorative font for evidence labels signals "informal" and may reduce perceived scientific authority. A serif font in a social media context may signal "academic rigor" or "outdated" depending on the viewer.
- **Current protocol coverage:** NO.

### 4.4 ALL CAPS

- **Communicates:** Shouting, warning, emphasis, or category label. In data visualization, ALL CAPS is often used for axis labels or category names. In social media, ALL CAPS signals urgency or emotion.
- **Speed:** Pre-attentive for the visual texture of ALL CAPS text (<250ms — it creates a distinct rectangular block vs mixed-case with ascenders/descenders). Reading ALL CAPS is ~13-20% slower than mixed case (Tinker 1963).
- **GLANCE relevance:** A GA with ALL CAPS labels slows reading speed within the 5-second window. If used for the key hierarchy label, it may paradoxically reduce S9b by consuming scan time.
- **Current protocol coverage:** NO.

### 4.5 Text color

- **Communicates:** Semantic role through convention. Blue = hyperlink / interactive. Red = alert / error / negative result. Green = success / positive result. Gray = secondary / disabled / metadata. Black = primary content. These are cultural conventions reinforced by decades of UI design.
- **Speed:** Pre-attentive for color detection (<250ms). Convention-based interpretation is rapid attentive (~500ms).
- **GLANCE relevance:** A GA using red text for the strongest evidence fights the "red = danger/negative" convention. The viewer may unconsciously associate strong evidence with a warning signal.
- **Current protocol coverage:** NO. Text color semantics are not assessed.

### 4.6 Text alignment

- **Communicates:** Structure, professionalism. Left-aligned = standard, easy to scan. Center-aligned = titles, emphasis, formal. Right-aligned = captions, secondary. Justified = formal/academic. Ragged alignment = casual/dynamic.
- **Speed:** Rapid attentive (500ms-1s for layout assessment).
- **GLANCE relevance:** Left-aligned text in a GA supports rapid scanning (the eye returns to a consistent left margin). Center-aligned body text slows scanning because the starting x-position varies per line.
- **Current protocol coverage:** NO.

### 4.7 Line spacing / leading

- **Communicates:** Readability, breathing room, density. Tight leading = dense, academic, potentially overwhelming. Generous leading = airy, modern, inviting. Cramped text signals "too much information."
- **Speed:** Rapid attentive (250ms-1s as part of the overall density assessment).
- **GLANCE relevance:** Within the 30-word text budget (V3), line spacing determines whether the text feels scannable or cramped.
- **Current protocol coverage:** PARTIAL. V3 captures word count. Line spacing / leading is not assessed.

### 4.8 Text contrast ratio

- **Communicates:** Readability, importance. High contrast (dark on light, light on dark) = primary. Low contrast (gray on white, light on light) = secondary, decorative, or inaccessible.
- **Speed:** Pre-attentive for contrast detection (<250ms). Low contrast text may not be detected at all in peripheral vision.
- **GLANCE relevance:** Labels on GA elements with insufficient contrast will not be read within 5 seconds, especially at mobile scale (V7). WCAG 2.1 requires 4.5:1 contrast for normal text, 3:1 for large text.
- **Current protocol coverage:** PARTIAL. V7 captures overall readability at mobile scale. Contrast ratio is not separately measured.

---

## 5. Image-Level Signals (Global Scene Categorization, <500ms)

The brain categorizes scenes globally before processing local details. Oliva & Torralba (2006) showed that "spatial envelope" properties (naturalness, openness, roughness, expansion, ruggedness) are computed in a single feedforward sweep (~150ms). For GAs, the relevant dimensions are below.

### 5.1 Image category (photo vs illustration vs chart vs diagram vs infographic)

- **Communicates:** Content type, expected reading strategy. Photo = real-world, concrete. Illustration = conceptual, simplified. Chart = data, quantitative. Diagram = process, relational. Infographic = mixed, designed for scanning. The brain assigns a reading strategy to each category within ~300ms.
- **Speed:** Rapid attentive (200-500ms for scene gist categorization, per Thorpe et al. 1996).
- **GLANCE relevance:** The image category determines what the viewer *expects* from the GA. A chart primes quantitative comparison. An illustration primes narrative understanding. If the GA's actual content mismatches the primed category (e.g., looks like a colorful illustration but contains quantitative evidence hierarchy), the viewer applies the wrong strategy.
- **Current protocol coverage:** NO. GA image category is not tagged or assessed.

### 5.2 Color palette temperature

- **Communicates:** Emotional tone. Warm palette (reds, oranges, yellows) = urgency, energy, attention, alarm. Cool palette (blues, greens, purples) = calm, trust, professionalism, clinical. Neutral (grays, whites, blacks) = technical, serious, data-focused.
- **Speed:** Pre-attentive (<250ms for overall color temperature assessment).
- **GLANCE relevance:** A GA about a serious medical topic using a warm/bright palette may signal "marketing" rather than "science." A cool/neutral palette primes clinical trust. Palette choice affects credibility perception before any content is read.
- **Current protocol coverage:** NO.

### 5.3 Visual density / whitespace ratio

- **Communicates:** Complexity, effort required. High density (>80% filled) = complex, requires study, likely too much for 5 seconds. Generous whitespace (40-60% filled) = clean, scannable, confidence in essential content. Very sparse (<30% filled) = empty, lacking substance.
- **Speed:** Pre-attentive (<250ms for overall density impression).
- **GLANCE relevance:** Directly related to the 5-second scan budget. High density GAs overload the attentional system and likely produce lower S9a (recall) and S9b (hierarchy perception). The pattern registry partially captures this through V3 (text density) but visual density includes non-text elements (icons, decorative graphics, background patterns).
- **Current protocol coverage:** PARTIAL. V3 covers text density (>30 words). Total visual density (including graphical elements) is not measured. Gap: a GA with 20 words but dense illustrations could pass V3 while still being visually overloaded.

### 5.4 Symmetry / asymmetry

- **Communicates:** Order, stability, formality (symmetry) vs dynamism, hierarchy, editorial style (asymmetry). The brain detects bilateral symmetry pre-attentively (Wagemans 1997).
- **Speed:** Pre-attentive (<250ms for bilateral symmetry detection).
- **GLANCE relevance:** A symmetrical GA layout (equal-sized panels, centered elements) signals "no hierarchy" — everything is equally important. An asymmetrical layout (one dominant element, smaller secondary elements) creates visual hierarchy that can guide the eye to the most important evidence first.
- **Current protocol coverage:** NO.

### 5.5 Professional vs amateur style markers

- **Communicates:** Source credibility, production quality. Professional markers: consistent color palette, grid alignment, typographic hierarchy, vector graphics, intentional whitespace. Amateur markers: misaligned elements, inconsistent spacing, raster artifacts, too many fonts, clip art, gradient backgrounds.
- **Speed:** Rapid attentive (500ms-1s for overall quality gestalt). The brain integrates multiple micro-cues into a "production quality" judgment.
- **GLANCE relevance:** A professionally-produced GA primes trust, potentially inflating S9b through authority heuristic. An amateur-looking GA may reduce dwell time (S10) and credibility. This is independent of whether the evidence encoding is perceptually accurate.
- **Current protocol coverage:** NO. Production quality is not assessed. Gap: a beautifully designed GA with poor evidence encoding could score high on perceived quality but low on S9b.

### 5.6 Resolution / rendering quality

- **Communicates:** Production quality, platform fit. High-resolution vector graphics = professional, scalable. Low-resolution raster with compression artifacts = amateur, repurposed, lazy. PDF-to-JPEG conversion artifacts are particularly common in GAs.
- **Speed:** Rapid attentive (250ms-1s). Rendering quality is part of the overall quality gestalt.
- **GLANCE relevance:** At mobile scale (V7), rendering quality determines whether fine labels and small text are legible. A GA rendered at 72 DPI will be unreadable as a 200px TOC thumbnail.
- **Current protocol coverage:** PARTIAL. V7 captures readability at mobile scale, which is partly a resolution issue.

### 5.7 Aspect ratio

- **Communicates:** Platform convention, expected reading pattern. 1:1 (square) = Instagram, compact. 16:9 (landscape) = slides, Twitter cards. 2:3 or 3:4 (portrait) = journal TOC, Pinterest. 1:2+ (tall) = infographic, scrollable. Non-standard ratios signal "not designed for this platform."
- **Speed:** Pre-attentive (<250ms — aspect ratio is part of the spatial envelope).
- **GLANCE relevance:** A GA designed at 1:1 shown in a LinkedIn card (which crops or letterboxes non-standard ratios) loses edge content. GLANCE captures `stimulus_image_width` but not aspect ratio or crop behavior.
- **Current protocol coverage:** PARTIAL. Image width is captured. Aspect ratio and platform-specific cropping behavior are not.

### 5.8 Edge sharpness / blur

- **Communicates:** Focus, certainty, importance. Sharp edges = figure, important, certain. Blurred regions = background, uncertain, secondary. MacEachren (2012) showed blur is the most intuitive signal for uncertainty (but binary only — not graded).
- **Speed:** Pre-attentive (<250ms). The visual system uses edge sharpness for figure-ground segregation at the earliest processing stages.
- **GLANCE relevance:** A GA using blur to de-emphasize weak evidence leverages one of the strongest pre-attentive channels. However, blur is binary (sharp vs blurred) — it cannot encode 4 levels of evidence certainty.
- **Current protocol coverage:** NO.

### 5.9 Presence of a border / frame

- **Communicates:** Containment, completeness, formality. A bordered image says "this is a defined unit." An unbordered image bleeds into the surrounding content. In social media, platform chrome provides the frame; in journal TOC, the image boundary is the frame.
- **Speed:** Pre-attentive (<250ms).
- **GLANCE relevance:** In GLANCE stream mode, the platform chrome (frame component of the stimulus triplet) provides the border. In nude mode, the GA boundary itself is the only frame.
- **Current protocol coverage:** YES. The stimulus triplet explicitly models frame presence/absence.

---

## 6. Layout Signals

Layout determines the reading path — the sequence in which visual elements are scanned. In a 5-second window, the viewer makes ~15-20 saccades. The layout determines which elements receive fixations and in what order.

### 6.1 Visual weight distribution

- **Communicates:** Hierarchy, emphasis, balance. Top-heavy layouts (dominant element at top) follow Western reading conventions (start at top-left). Bottom-heavy layouts force upward scanning against habit. Centered-weight layouts signal "poster" or "hero image."
- **Speed:** Rapid attentive (250ms-1s for weight distribution assessment).
- **GLANCE relevance:** The evidence hierarchy in a GA should be placed where the eye naturally lands first. Top-left in Western reading cultures. If the key evidence bar is bottom-right, it may not be fixated within 5 seconds.
- **Current protocol coverage:** NO. Spatial placement of the evidence hierarchy is not assessed.

### 6.2 Reading direction flow

- **Communicates:** Scanning order, narrative sequence. Z-pattern (top-left → top-right → bottom-left → bottom-right) for image-heavy content. F-pattern (top → scan right, drop down, scan shorter right line, drop down) for text-heavy content. These are empirically validated by eye-tracking (Nielsen 2006).
- **Speed:** The pattern itself is not "seen" — it is the habitual scanning strategy that determines which content gets fixated within the time window.
- **GLANCE relevance:** A GA designed for Z-pattern scanning places the key message at the terminal point (bottom-right). A GA designed for F-pattern places decreasing-priority information in decreasing-scan-length rows. If the GA layout fights the expected pattern, critical elements are missed.
- **Current protocol coverage:** NO.

### 6.3 Grid vs organic layout

- **Communicates:** Structure, predictability. Grid = organized, data-driven, systematic, easy to scan. Organic = narrative, flowing, artistic, harder to predict scan path.
- **Speed:** Pre-attentive (<250ms for grid detection — regular spacing creates a texture).
- **GLANCE relevance:** Grid layouts support faster comparison (all elements at predictable positions). Organic layouts support narrative flow but may scatter evidence across unpredictable locations.
- **Current protocol coverage:** NO.

### 6.4 Negative space (intentional emptiness)

- **Communicates:** Breathing room, emphasis by isolation, sophistication, confidence. "Less is more." An element surrounded by negative space receives more attention than the same element crowded by neighbors.
- **Speed:** Pre-attentive (<250ms). Negative space contributes to figure-ground segregation and pop-out.
- **GLANCE relevance:** Strategic negative space around the key evidence bar makes it pop out. Negative space also reduces overall density (see 5.3), preserving the 5-second scan budget for essential content.
- **Current protocol coverage:** PARTIAL. V3 indirectly captures density. Negative space as a deliberate emphasis tool is not assessed.

### 6.5 Visual hierarchy (number of levels)

- **Communicates:** Complexity of the information structure. 2-3 levels of visual hierarchy (title, main content, supporting detail) are scannable in 5 seconds. 5+ levels overwhelm the viewer.
- **Speed:** Attentive (1-3s to parse the full hierarchy).
- **GLANCE relevance:** A GA with too many visual hierarchy levels forces the viewer to build a complex mental model. Within 5 seconds, only 2-3 levels can be effectively parsed. This is a fundamental constraint on GA complexity.
- **Current protocol coverage:** NO. Number of visual hierarchy levels is not counted or assessed.

### 6.6 Directional cues (arrows, lines, gaze direction)

- **Communicates:** Flow, sequence, causation, "look here." Arrows are one of the strongest attention-directing signals. Human gaze direction in photos directs viewer gaze (gaze-following reflex, Driver et al. 1999).
- **Speed:** Pre-attentive for arrow detection (<250ms). Gaze following is rapid attentive (~300ms, Friesen & Kingstone 1998).
- **GLANCE relevance:** A GA with arrows pointing from evidence to conclusion creates a reading path. A GA without directional cues leaves the viewer to construct their own path, which may miss the hierarchy.
- **Current protocol coverage:** NO.

---

## 7. Emotional / Cognitive Priming Signals

These signals do not encode data directly. They set the emotional and cognitive context within which all subsequent data is interpreted. They operate through associative priming — activating semantic networks that bias interpretation.

### 7.1 Human faces

- **Communicates:** Attention capture (mandatory, cannot be suppressed), emotion (via facial expression), age, gender, ethnicity, health status, authority. Faces are processed by the dedicated fusiform face area (FFA) in ~170ms. Even schematic faces (two dots and a line) activate face processing.
- **Speed:** Pre-attentive (<170ms for face detection). Emotion recognition is rapid attentive (~300ms).
- **GLANCE relevance:** A GA containing a face (patient photo, researcher portrait, medical illustration with faces) will capture the first fixation regardless of where the evidence hierarchy is placed. This can be beneficial (face draws attention to the GA in stream mode, boosting S10) or harmful (face steals fixation time from the evidence bars, reducing S9b).
- **Current protocol coverage:** NO. Face presence in GAs is not assessed or controlled. Gap: face-based attention capture could be a major confound in S9b scoring.

### 7.2 Medical / anatomical imagery

- **Communicates:** Clinical context, seriousness, potential distress. Anatomical illustrations (organs, cells, pathways) prime a "medical" interpretation frame. The viewer expects evidence about health outcomes. Visceral imagery (blood, wounds, disease presentation) triggers empathetic/aversive responses that increase arousal and memorability.
- **Speed:** Rapid attentive (200-500ms for medical scene categorization). Emotional arousal response follows in 500ms-1s.
- **GLANCE relevance:** A GA with prominent medical imagery (lungs, immune cells, pathogens) primes the clinical interpretation context. For S9a (recall), arousing medical imagery may improve encoding (flashbulb memory effect). For S9b (hierarchy), the emotional response may bias toward "this is serious" regardless of actual evidence strength.
- **Current protocol coverage:** NO. Medical imagery presence and arousal level are not assessed.

### 7.3 Data visualization elements (charts, tables, numbers)

- **Communicates:** Quantitative rigor, authority, precision, "this is science." The presence of data visualization signals that claims are evidence-based, even before the viewer reads the actual data.
- **Speed:** Rapid attentive (200-500ms for detecting "this is a chart"). Reading the data is cognitive (>2s).
- **GLANCE relevance:** A GA that *looks* like it contains data (visible axes, bars, numbers) primes analytical processing. This may help S9b if the data actually encodes evidence hierarchy clearly. It may hurt if the data visualization is decorative (data-ink without meaning, per Tufte).
- **Current protocol coverage:** PARTIAL. VEC design system emphasizes meaningful data encoding. Decorative data elements are not explicitly flagged.

### 7.4 Color-emotion associations

- **Communicates:** Emotional valence and arousal via learned color associations. Research-validated associations (Elliot & Maier 2014):
  - Red: danger, urgency, importance, error, stop, passion. Increases arousal.
  - Blue: trust, calm, professionalism, sadness. Decreases arousal.
  - Green: safety, nature, growth, approval, go.
  - Yellow: warning, attention, optimism, caution.
  - Orange: energy, warmth, creativity.
  - Purple: luxury, mystery, spirituality.
  - Black: authority, sophistication, death, formality.
  - White: purity, simplicity, clinical cleanliness.
  - Gray: neutrality, professionalism, boredom.
- **Speed:** Pre-attentive for color detection (<250ms). Emotional association is rapid attentive (~500ms) and partially automatic.
- **GLANCE relevance:** The overall color palette of a GA primes an emotional interpretation before any content is processed. A red-dominated GA about medication safety may amplify perceived risk beyond what the evidence supports. A blue-dominated GA may understate urgency. This is a form of unintentional spin.
- **Current protocol coverage:** NO. Color-emotion interaction is not assessed.

### 7.5 Muted vs saturated palette (overall)

- **Communicates:** Sophistication/trust (muted) vs energy/attention (saturated). High-saturation palettes signal marketing, consumer products, entertainment. Low-saturation/muted palettes signal scientific journals, financial publications, luxury brands.
- **Speed:** Pre-attentive (<250ms for overall saturation assessment).
- **GLANCE relevance:** A GA with a BioRender-style high-saturation palette may signal "designed for engagement" rather than "designed for evidence transfer." This affects perceived credibility before content is processed.
- **Current protocol coverage:** NO.

### 7.6 Icons and pictograms

- **Communicates:** Category, action, concept — via culturally learned symbols. Icons are faster to process than text for common concepts (pill = medication, shield = protection, arrow = direction, clock = time, person = patient).
- **Speed:** Rapid attentive (200-500ms for familiar icon recognition).
- **GLANCE relevance:** Icons in a GA can convey meaning faster than text within the 5-second window. Zikmund-Fisher et al. (2014) showed that icon *type* affects risk perception: person-shaped icons increase perceived risk vs abstract shapes. The immunomodulator GA uses a child pictogram (B7), which primes "pediatric" context.
- **Current protocol coverage:** NO. Icon presence and type are not systematically assessed. Note: Zikmund-Fisher finding (person icons increase perceived risk) is documented in VEC literature analysis but not operationalized in GLANCE.

### 7.7 Numbers and numerical format

- **Communicates:** Precision, magnitude, evidence weight. Natural frequencies ("18 out of 20 trials") are comprehended by >80% of populations vs <50% for probabilistic formats (Gigerenzer; Garcia-Retamero & Cokely 2017). Number magnitude is processed automatically (SNARC effect — small numbers on left, large on right).
- **Speed:** Rapid attentive (500ms-1s for number reading). Magnitude comparison of two numbers takes 500ms-1.5s.
- **GLANCE relevance:** Directly relevant to P33 (natural frequencies in VEC). A GA showing "p < 0.001" communicates precision to experts but is opaque to general audiences. "18 of 20 studies" is universally understood.
- **Current protocol coverage:** PARTIAL. P33 is a VEC design principle. Whether a GA actually uses natural frequencies vs abstract statistics is not assessed in the pattern registry.

### 7.8 Branding / logo presence

- **Communicates:** Source identity, commercial vs academic intent, authority. A journal logo (Nature, Lancet) signals academic authority. A pharma company logo signals commercial interest and potential bias. A design tool logo (BioRender, Canva) signals production method.
- **Speed:** Rapid attentive (500ms-1s for logo recognition).
- **GLANCE relevance:** Logo presence biases credibility assessment. In GLANCE, this is partly captured by the frame component of the stimulus triplet (journal chrome includes journal branding) but within-GA branding (e.g., a BioRender watermark) is not controlled.
- **Current protocol coverage:** PARTIAL. Platform chrome captures journal/platform branding. Within-GA branding is not assessed.

### 7.9 Novelty / surprise / incongruity

- **Communicates:** "This is unexpected." An element that violates expectations (an unusual color in a familiar format, an unexpected element in a standard layout) captures attention involuntarily (Itti & Baldi 2009, Bayesian surprise model).
- **Speed:** Rapid attentive (250ms-1s). Surprise-driven attention capture follows initial scene categorization.
- **GLANCE relevance:** A GA that looks different from typical GAs in the feed may capture more attention (boosting S10) but the novelty may also disrupt the expected reading strategy, potentially reducing S9b.
- **Current protocol coverage:** NO.

---

## 8. Compound / Emergent Signals

These are higher-order perceptions that emerge from combinations of lower-level features. They are not reducible to a single channel but are computed by the brain's scene understanding system.

### 8.1 Information-to-noise ratio (visual signal-to-noise)

- **Communicates:** How much of the visual content carries meaning vs how much is decoration, chrome, or redundancy. Tufte's "data-ink ratio" formalized this: maximize the proportion of ink that represents data.
- **Speed:** Attentive (1-3s for overall assessment). The viewer's subjective sense of "this is clear" vs "this is cluttered" integrates density, whitespace, decoration, and meaningful content.
- **GLANCE relevance:** High visual noise reduces the probability that the evidence hierarchy is perceived within 5 seconds. This is the compound effect of density (5.3), text density (V3), decorative elements, and non-data-bearing visual complexity.
- **Current protocol coverage:** PARTIAL. V3 captures text density. No compound metric for overall visual noise.

### 8.2 Perceived narrative structure

- **Communicates:** "There is a story here" vs "these are disconnected elements." The brain seeks narrative structure (beginning-middle-end, cause-effect, problem-solution) in visual layouts. GAs with clear narrative flow are easier to parse than those with scattered evidence.
- **Speed:** Attentive to cognitive (1-5s). Narrative structure requires integrating spatial layout, directional cues, and temporal/causal inference.
- **GLANCE relevance:** S9a (recall) is strongly influenced by narrative coherence — episodes are easier to recall than isolated facts (Schank 1990). A GA with a clear visual narrative ("pathogen attacks → immune system responds → immunomodulator helps → evidence shows it works") supports both recall and hierarchy perception.
- **Current protocol coverage:** NO.

### 8.3 Cognitive load estimate (overall)

- **Communicates:** "How much mental effort will this require?" The brain estimates cognitive load from visual complexity in the first 500ms and adjusts engagement accordingly. High estimated load in a feed context = scroll past.
- **Speed:** Rapid attentive (250ms-1s for the estimate). The estimate is computed from density, text volume, number of visual elements, color complexity, and layout irregularity.
- **GLANCE relevance:** Cognitive load is the integrative variable. It predicts dwell time (S10), recall (S9a), hierarchy perception (S9b), and actionability (S9c). All VEC design principles ultimately aim to reduce cognitive load for evidence transfer.
- **Current protocol coverage:** PARTIAL. Individual load contributors (text density V3, readability V7) are captured. The compound load estimate is not computed.

### 8.4 Credibility gestalt

- **Communicates:** "Should I trust this?" Integrates production quality, source authority (avatar, username, platform), color palette sophistication, typography quality, presence of data visualization, and absence of marketing signals into a single trust assessment.
- **Speed:** Attentive (1-3s). The gestalt emerges from integrating multiple rapid assessments.
- **GLANCE relevance:** Credibility affects S9c (actionability) directly: "Would you act on this?" requires trust. It also affects S9b: participants may be more likely to accept the hierarchy presented by a credible-looking GA without critical evaluation (authority bias).
- **Current protocol coverage:** NO. Credibility is not measured as a variable or controlled as a covariate.

### 8.5 Aesthetic appeal

- **Communicates:** "This was made with care" / "I want to engage with this." Aesthetic appeal increases dwell time, sharing probability, and perceived credibility (Tractinsky et al. 2000 — "what is beautiful is usable"). This is the visual analog of the engagement-comprehension gap: beauty increases engagement but does not guarantee comprehension.
- **Speed:** Rapid attentive (250ms-1s for the beauty judgment; Lindgaard et al. 2006 showed aesthetic judgments stabilize within 500ms).
- **GLANCE relevance:** Aesthetic appeal is a potential confound. A beautiful GA may receive high S10 (saliency) and high S9c (actionability) due to beauty bias while scoring low on S9b (evidence hierarchy). This is exactly the engagement-comprehension dissociation that GLANCE is designed to detect.
- **Current protocol coverage:** NO. Aesthetic appeal is not measured. Gap: isolating aesthetic appeal from evidence encoding quality would require a beauty rating in the post-test sequence.

---

## 9. Summary: Coverage Analysis

### Channels fully captured by current GLANCE/VEC protocol

| Channel | Pattern/Variable | Diagnostic |
|---------|-----------------|------------|
| Area encoding compression | P21 | Q4/Q5 adaptive question |
| Length encoding accuracy | P32 | Pattern registry (low risk, no question) |
| Color saturation misuse | P34 | Q4/Q5 adaptive question |
| Color pair distinguishability | V14 | Q4/Q5 adaptive question |
| Text density overload | V3 | Q4/Q5 adaptive question |
| Mobile-scale readability | V7 | Q4/Q5 adaptive question |
| Platform chrome effects | Stimulus triplet | Exposure conditions (nude, linkedin, twitter, toc) |
| Text anchoring/spoiler | Stimulus_text | Nude vs title-only delta |

### Channels partially captured (addressed indirectly)

| Channel | Current coverage | Gap |
|---------|-----------------|-----|
| Luminance for certainty | VEC design principle | No pattern registry entry or diagnostic question |
| Hue-as-ordinal misuse | V14 catches distinguishability only | Rainbow colormap misuse not flagged |
| Spatial position accuracy | VEC uses common-scale | Absence of common-scale not flagged as risk |
| Visual density (non-text) | V3 catches text density | Graphical density not measured |
| Resolution at scale | V7 captures readability | DPI / vector-vs-raster not assessed |
| Engagement count bias | Chrome includes counts | Counts not controlled as variable |
| Natural frequency use | P33 VEC principle | GA compliance not assessed in pattern registry |
| Aspect ratio | Image width captured | Crop behavior not modeled |

### Channels NOT captured (identified gaps)

| Channel | Risk level | Recommendation |
|---------|-----------|----------------|
| Human face attention capture | HIGH | Tag GA for face presence; control as covariate |
| Volume (3D) encoding | HIGH | Add to pattern registry as highest-risk channel |
| Angle/pie chart encoding | MEDIUM | Add to pattern registry |
| Figure-ground contrast | MEDIUM | Compute contrast ratio for key elements |
| Visual weight distribution | MEDIUM | Assess whether evidence hierarchy is in high-fixation zone |
| Symmetry signaling "no hierarchy" | MEDIUM | Flag symmetric layouts when hierarchy encoding is the goal |
| Color-emotion priming | MEDIUM | Note dominant palette temperature as metadata |
| Professional vs amateur quality | MEDIUM | Could bias S9b through credibility heuristic |
| Shape confusability | LOW | Add to pattern registry if shapes encode categories |
| Typography analysis | LOW | Font weight/size/family affect scanability |
| Reading direction flow | LOW | Check if evidence hierarchy aligns with Z/F pattern |
| Narrative structure | LOW | Qualitative assessment |
| Aesthetic appeal confound | LOW | Could add beauty rating to post-test |

---

## 10. Temporal Processing Timeline

Summary of what the brain processes, in order, during the 5-second GLANCE exposure window:

| Time | Processing stage | What is computed | Dominant channels |
|------|-----------------|-----------------|-------------------|
| 0-100ms | Edge extraction, luminance contrast | Figure-ground segregation, edge map | Luminance, contrast, spatial frequency |
| 100-200ms | Feature extraction (parallel) | All pre-attentive features simultaneously: color, size, orientation, motion onset | Hue, saturation, luminance, size, shape, orientation |
| 150-250ms | Scene gist / spatial envelope | Global categorization: "this is a chart" / "this is a photo" / "this is an infographic" | Density, color temperature, aspect ratio, grid regularity |
| 170-300ms | Face detection (if present) | Mandatory face processing, emotion detection | FFA activation, face features |
| 200-500ms | Saliency-driven first fixation | Eye lands on highest-salience region (pop-out target, face, largest element, highest contrast element) | All pre-attentive channels compete for first fixation |
| 500ms-1s | Platform/source assessment | Avatar, username, platform chrome identified. Credibility prior formed. | Social signals, typography, branding |
| 500ms-1.5s | Title/text reading (if present) | Key words extracted from title. Topic identified. | Font size, contrast, position (top of card) |
| 1-2s | Data element scanning | Evidence bars, chart elements, numerical values scanned. Hierarchy *detected* if encoding is clear (length/position). | Position, length, luminance, proximity |
| 2-3s | Hierarchy comparison | Magnitudes compared. "This bar is longer than that bar" = this evidence is stronger. | Length, position on common scale |
| 3-5s | Integration and judgment | Full scene model assembled. Evidence hierarchy mapped to semantic meaning. Actionability assessed. | All channels integrated into working memory representation |
| 5s | Exposure ends | Whatever has been encoded is the trace that S9a/S9b/S9c measure. |  |

This timeline is the operational model for GLANCE. Every VEC design decision should optimize for information transfer within this sequence. Channels that operate earlier in the timeline (pre-attentive, <250ms) have more processing time available and are therefore more reliable for encoding the primary message.

---

*Catalog compiled March 2026. To be updated as GLANCE pilot data reveals which channels most strongly predict S9b outcomes.*
