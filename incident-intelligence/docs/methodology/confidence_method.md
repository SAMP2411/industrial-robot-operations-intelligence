# Confidence and evidence methodology

The product ranks analyst-authored hypotheses; it does not autonomously determine root cause. The active policy is the versioned configuration in `config/confidence_policy_v1.yaml`.

Each evidence link records its relation, strength, origin group, reviewer state, and provenance. Supporting evidence adds policy-defined weight, contradicting evidence subtracts weight, contextual evidence is non-causal, and missing expected evidence reduces completeness. Evidence from the same origin group is capped so duplicated exports do not masquerade as independent corroboration. A confirmed hypothesis still requires human approval.

Reports disclose the policy version, derivation, alternatives, contradictions, missing evidence, and quality limitations. An unresolved contradiction blocks approval. For medium-or-higher severity, approval requires an alternative hypothesis or an explicit reviewer justification.

Synthetic tests verify deterministic scoring and policy behavior. Calibration against real diagnostic outcomes and inter-reviewer agreement remain external validation work; record them using the forms in `docs/validation/` before changing weights.
