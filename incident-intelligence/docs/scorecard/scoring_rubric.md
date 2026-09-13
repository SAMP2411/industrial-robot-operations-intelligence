# Scoring rubric

The scorecard is an evidence index, not a marketing score. Category weights sum to 100. A score may increase only when every new point has a repository evidence reference that exists and the category's stated blocker has genuinely changed.

Technical evidence may be a passing test, generated artifact, deployment verification, or phase report. Commercial points require real, access-controlled evidence references such as anonymised dataset fingerprints, operator review notes, proposals, payment references, written commitments, or security-review outcomes. Synthetic fixtures cannot award commercial points.

`scripts/validate_scorecard.py` validates schema, totals, bounds, evidence paths, and the commercial evidence rule. CI must run it together with product-claim linting and scope regression tests.

