"""Claim Extractor — Paper abstract -> structured claims for GA generation.

Sends the abstract to Gemini and extracts claims classified by data family:
- quantitative (proportional values)
- spatial (anatomical/positional)
- ordinal (sequential/causal)
- directional (gradient/transformation)
- semi-quantitative (relative density/intensity)
- categorical (binary/nominal)
"""

import os
import json
import logging
import argparse

logger = logging.getLogger(__name__)
BASE = os.path.dirname(__file__)

# Load API key from .env file (simple key=value parsing, no dotenv dependency)
_env_path = os.path.join(BASE, ".env")
if os.path.exists(_env_path):
    with open(_env_path, encoding="utf-8") as _ef:
        for _line in _ef:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())


EXTRACT_PROMPT = """You are a scientific claim extractor. Given a paper abstract (and optional context), extract ALL factual claims and classify them.

## Instructions

1. **List every factual claim** in the abstract. A claim is any statement that asserts a measurable, observable, or categorical fact.
2. **Classify each claim** by data family:
   - `quantitative`: proportional/numeric values (percentages, ratios, p-values, fold changes)
   - `spatial`: anatomical, positional, or geographic relationships
   - `ordinal`: sequential, temporal, or causal ordering
   - `directional`: gradients, transformations, trends (increase/decrease)
   - `semi-quantitative`: relative density, intensity, expression levels without exact numbers
   - `categorical`: binary (yes/no), nominal classifications, group assignments
3. **Extract exact values** when present (numbers, percentages, p-values, confidence intervals).
4. **Prioritize** each claim:
   - Priority 1: Primary message — the main finding(s) the paper is about
   - Priority 2: Key supporting evidence — data that backs the primary message
   - Priority 3: Context/background — methodological details, known facts restated
5. **Suggest visual encoding** for each claim (e.g., "bar chart", "arrow gradient", "icon comparison", "spatial overlay", "color scale", "pie chart", "flow diagram").
6. **Group related claims into 2-4 GA narratives** — each narrative is a coherent visual story that could be a panel or section of a graphical abstract.

## Output format (strict JSON)

```json
{{
  "claims": [
    {{
      "id": "c1",
      "text": "exact claim text from abstract",
      "data_family": "quantitative|spatial|ordinal|directional|semi-quantitative|categorical",
      "values": ["42%", "p<0.001"],
      "priority": 1,
      "source_sentence": "the full sentence from the abstract containing this claim",
      "encoding_suggestion": "bar chart comparing treatment vs control"
    }}
  ],
  "narratives": [
    {{
      "id": "n1",
      "title": "short narrative title",
      "claim_ids": ["c1", "c2"],
      "description": "how these claims form a coherent visual story",
      "suggested_layout": "left-to-right flow | top-down hierarchy | comparison grid | before-after"
    }}
  ]
}}
```

Return ONLY valid JSON. No markdown fences, no explanation text.

## Abstract

{abstract}

{context_block}"""


def extract_claims(abstract_text, context=None):
    """Extract structured claims from a paper abstract.

    Args:
        abstract_text: the paper abstract
        context: optional additional context (methods, key findings)

    Returns:
        dict with:
          claims: list of {
            id, text, data_family, values, priority (1-3),
            source_sentence, encoding_suggestion
          }
          narratives: list of suggested GA narratives from the claims
    """
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set. Add it to .env file.")

    genai.configure(api_key=api_key)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
    model = genai.GenerativeModel(model_name)

    context_block = ""
    if context:
        context_block = f"## Additional context\n\n{context}"

    prompt = EXTRACT_PROMPT.format(
        abstract=abstract_text,
        context_block=context_block,
    )

    logger.info(f"Extracting claims from abstract ({len(abstract_text)} chars)...")

    response = model.generate_content(
        [prompt],
        generation_config={"temperature": 0.2, "max_output_tokens": 8192},
    )

    raw = response.text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        # Remove first line (```json or ```) and last line (```)
        lines = raw.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        logger.debug(f"Raw response: {raw[:500]}")
        raise ValueError(f"Gemini returned invalid JSON: {e}") from e

    # Validate structure
    if "claims" not in result:
        raise ValueError("Gemini response missing 'claims' key")
    if "narratives" not in result:
        result["narratives"] = []

    # Validate data families
    valid_families = {
        "quantitative", "spatial", "ordinal",
        "directional", "semi-quantitative", "categorical",
    }
    for claim in result["claims"]:
        if claim.get("data_family") not in valid_families:
            logger.warning(
                f"Claim {claim.get('id')} has unknown data_family "
                f"'{claim.get('data_family')}' — keeping as-is"
            )
        # Ensure values is always a list
        if not isinstance(claim.get("values"), list):
            claim["values"] = [claim["values"]] if claim.get("values") else []

    logger.info(
        f"Extracted {len(result['claims'])} claims, "
        f"{len(result['narratives'])} narratives"
    )
    return result


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract structured claims from a paper abstract using Gemini."
    )
    parser.add_argument(
        "--abstract", type=str, default=None,
        help="Abstract text (inline)"
    )
    parser.add_argument(
        "--abstract-file", type=str, default=None,
        help="Path to a text file containing the abstract"
    )
    parser.add_argument(
        "--context", type=str, default=None,
        help="Optional additional context (methods, key findings)"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output file path (JSON). Prints to stdout if not specified."
    )
    args = parser.parse_args()

    # Resolve abstract text
    abstract_text = args.abstract
    if not abstract_text and args.abstract_file:
        if not os.path.exists(args.abstract_file):
            parser.error(f"Abstract file not found: {args.abstract_file}")
        with open(args.abstract_file, encoding="utf-8") as f:
            abstract_text = f.read().strip()

    if not abstract_text:
        parser.error("Provide --abstract or --abstract-file")

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    result = extract_claims(abstract_text, context=args.context)

    output_json = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        logger.info(f"Output written to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
