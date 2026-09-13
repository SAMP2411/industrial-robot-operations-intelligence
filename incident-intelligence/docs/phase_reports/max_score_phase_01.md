# Maximum-score phase 1: scorecard and guardrails

## Purpose

Create an evidence-backed scorecard, scope regression tests, and product-claim linting so technical or commercial points cannot be awarded silently.

## Baseline and final commit

- Baseline: `b7ad4a3`
- Implementation: `b4a55a8`
- Branch: `max-score/01-scorecard-and-guardrails`

## Files changed

- `docs/scorecard/current_score.yaml`
- `docs/scorecard/scoring_rubric.md`
- `docs/scorecard/evidence_ledger.md`
- `scripts/validate_scorecard.py`
- `scripts/lint_product_claims.py`
- `config/disallowed_unverified_claims.yaml`
- `tests/contract/test_scorecard_evidence.py`
- `tests/contract/test_product_scope.py`
- `.github/workflows/quality.yml`

No migration was required.

## Commands and results

```text
python3 -m pytest -q
20 passed, 1 legacy passlib warning

docker compose config --quiet
passed with verification-only environment values

python3 scripts/validate_scorecard.py
Scorecard valid: 82/100

python3 scripts/lint_product_claims.py
Product claim lint passed

python3 -m pytest -q tests/contract/test_scorecard_evidence.py tests/contract/test_product_scope.py
9 passed
```

## Acceptance criteria

- Scorecard is machine-validatable and included in CI: passed.
- Total score is calculated automatically: passed at 82/100.
- Every awarded category links to existing evidence: passed.
- Product-scope tests pass: passed.
- Unverified product claims fail the lint policy: passed.
- Score remains approximately 82 until new evidence exists: passed.

## Evidence and limitations

Evidence is in the scorecard, ledger, scripts, tests, and GitHub Actions workflow. The workflow has been defined but has not yet produced a hosted GitHub Actions run in this local-only repository. No score was increased. Commercial validation remains 1/5 because no real dataset, payment, or commitment exists.
