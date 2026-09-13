from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.domain_models.models import Asset


@dataclass(frozen=True)
class AssetMatch:
    asset_id: str | None
    status: str
    candidates: tuple[str, ...] = ()


def match_asset(session: Session, external_id: str | None) -> AssetMatch:
    if not external_id:
        return AssetMatch(None, "unknown")
    needle = external_id.casefold()
    assets = session.scalars(select(Asset)).all()
    candidates = [
        asset.id
        for asset in assets
        if needle
        in {
            str(asset.external_asset_id or "").casefold(),
            asset.name.casefold(),
            *(str(alias).casefold() for alias in (asset.aliases or [])),
            *(str(value).casefold() for value in (asset.metadata_json or {}).values()),
        }
    ]
    if len(candidates) == 1:
        return AssetMatch(candidates[0], "matched")
    if len(candidates) > 1:
        return AssetMatch(None, "ambiguous", tuple(candidates))
    return AssetMatch(None, "unknown")

