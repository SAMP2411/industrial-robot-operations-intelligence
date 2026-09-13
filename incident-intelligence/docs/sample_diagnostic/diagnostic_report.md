# SYNTHETIC DEMONSTRATION — NOT CUSTOMER DATA

# Diagnostic report: Door interlock delayed robot route recovery

## Executive summary

A synthetic robot stopped at a controlled door after the fleet route request preceded the door-open confirmation. The available evidence supports an interlock delay as the leading hypothesis, while a Wi-Fi interruption remains an explicitly reviewed alternative.

## Operational impact

One synthetic transport task paused for 214 seconds; no safety event or customer production impact is represented.

## Downtime and recovery

- Unplanned downtime: 214 seconds
- Technical recovery: 151 seconds
- Business recovery: 214 seconds

## Hypotheses
- [HYP-SYN-001] Door interlock response delay: 0.74 (analyst-supported)
- [HYP-SYN-002] Wi-Fi roaming interruption: 0.28 (alternative)

## Evidence and limitations
- [EV-SYN-001] supports: 18-second release-to-open interval overlaps the stop.
- [EV-SYN-002] contradicts: No packet-loss record exists in the available synthetic Wi-Fi window.
- [EV-SYN-003] missing_expected: Door controller diagnostic trace was intentionally omitted from the fixture.

## Reconstructed timeline

See `timeline.csv`; every row cites synthetic raw evidence.

## Provenance

Generated deterministically from `scripts/generate_sample_diagnostic.py`. This artifact demonstrates product format and is not a validated customer outcome.
