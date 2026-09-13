#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("proposal_id", "customer_name", "engagement_title", "offer", "scope", "required_sources", "timeline", "price_eur", "acceptance_criteria")


def generate(values: dict) -> str:
    missing = [field for field in REQUIRED if not values.get(field)]
    if missing: raise ValueError("missing proposal fields: " + ", ".join(missing))
    offers = yaml.safe_load((ROOT / "config/commercial_offers.yaml").read_text())
    offer = offers["offers"].get(values["offer"])
    if not offer: raise ValueError("unknown offer")
    def bullets(items): return "\n".join(f"- {item}" for item in items)
    return f"""# Proposal {values['proposal_id']}: {values['engagement_title']}

Date: {values.get('date', date.today().isoformat())}  
Customer: {values['customer_name']}  
Offer: {offer['name']}  
Price: EUR {values['price_eur']:,.2f} excluding applicable taxes

## Scope

{values['scope']}

## Customer responsibilities and required sources

{bullets(values['required_sources'])}

The customer confirms permission to provide the selected exports and identifies applicable handling and retention requirements.

## Exclusions and product boundary

- Historical/read-only diagnostic analysis only.
- No robot commands, mission dispatch, production control, safety function, or automatic causal conclusion.
- Legal, privacy, warranty, and procurement terms require qualified review before signature.
{bullets(values.get('exclusions', []))}

## Deliverables

{bullets(offer['deliverables'])}

## Timeline

{values['timeline']}

## Data handling

{values.get('data_handling', 'Customer-approved transfer, access restriction, evidence hashing, agreed retention, and deletion receipt on request/expiry.')}

## Acceptance criteria

{bullets(values['acceptance_criteria'])}

## Change control

New sources, expanded incident scope, on-site work, or additional report rounds require a written scope/price change accepted by both parties.

## Status

Commercial proposal draft. Pricing and legal terms are subject to buyer testing and qualified review.
"""


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("input", type=Path); parser.add_argument("output", type=Path); args = parser.parse_args()
    values = yaml.safe_load(args.input.read_text()) if args.input.suffix in {".yaml", ".yml"} else json.loads(args.input.read_text())
    content = generate(values); args.output.write_text(content); print(json.dumps({"output": str(args.output), "sha256": __import__('hashlib').sha256(content.encode()).hexdigest()})); return 0


if __name__ == "__main__": raise SystemExit(main())
