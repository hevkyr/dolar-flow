"""
portfolio.py — Core portfolio management logic
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Asset:
    symbol: str
    name: str
    quantity: float
    avg_buy_price: float       # Price in BRL
    avg_buy_price_usd: float   # Price in USD at purchase time
    asset_type: str            # 'stock_br', 'stock_us', 'crypto', 'fii', 'renda_fixa'
    currency: str              # 'BRL' or 'USD'
    sector: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def total_invested_brl(self) -> float:
        return self.quantity * self.avg_buy_price

    @property
    def total_invested_usd(self) -> float:
        return self.quantity * self.avg_buy_price_usd

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Portfolio:
    name: str
    assets: list[Asset] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_asset(self, asset: Asset) -> None:
        existing = self._find_asset(asset.symbol)
        if existing:
            # Average down / up position
            total_qty = existing.quantity + asset.quantity
            existing.avg_buy_price = (
                (existing.quantity * existing.avg_buy_price)
                + (asset.quantity * asset.avg_buy_price)
            ) / total_qty
            existing.avg_buy_price_usd = (
                (existing.quantity * existing.avg_buy_price_usd)
                + (asset.quantity * asset.avg_buy_price_usd)
            ) / total_qty
            existing.quantity = total_qty
        else:
            self.assets.append(asset)
        self.last_updated = datetime.now().isoformat()

    def remove_asset(self, symbol: str, quantity: float) -> bool:
        asset = self._find_asset(symbol)
        if not asset:
            return False
        if quantity >= asset.quantity:
            self.assets.remove(asset)
        else:
            asset.quantity -= quantity
        self.last_updated = datetime.now().isoformat()
        return True

    def _find_asset(self, symbol: str) -> Optional[Asset]:
        return next((a for a in self.assets if a.symbol.upper() == symbol.upper()), None)

    def get_by_type(self, asset_type: str) -> list[Asset]:
        return [a for a in self.assets if a.asset_type == asset_type]

    def total_invested_brl(self) -> float:
        return sum(a.total_invested_brl for a in self.assets)

    def total_invested_usd(self) -> float:
        return sum(a.total_invested_usd for a in self.assets)

    def summary(self) -> dict:
        by_type: dict[str, float] = {}
        for asset in self.assets:
            by_type[asset.asset_type] = by_type.get(asset.asset_type, 0) + asset.total_invested_brl
        total = self.total_invested_brl()
        return {
            "name": self.name,
            "total_assets": len(self.assets),
            "total_invested_brl": total,
            "total_invested_usd": self.total_invested_usd(),
            "allocation": {k: round((v / total) * 100, 2) for k, v in by_type.items()} if total else {},
        }

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "assets": [a.to_dict() for a in self.assets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Portfolio":
        assets = [Asset(**a) for a in data.get("assets", [])]
        return cls(
            name=data["name"],
            assets=assets,
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_updated=data.get("last_updated", datetime.now().isoformat()),
        )


class PortfolioStorage:
    """Persists portfolio data to JSON."""

    def __init__(self, path: str | Path = "data/portfolio.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, portfolio: Portfolio) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(portfolio.to_dict(), f, indent=2, ensure_ascii=False)

    def load(self, name: str = "My Portfolio") -> Portfolio:
        if not self.path.exists():
            return Portfolio(name=name)
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        return Portfolio.from_dict(data)
