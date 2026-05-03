"""
dollarization.py — Analyze and track asset dollarization progress
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.portfolio import Portfolio, Asset


DOLLARIZED_TYPES = {"stock_us", "crypto"}   # assets denominated in USD
LOCAL_TYPES = {"stock_br", "fii", "renda_fixa"}


@dataclass
class DollarizationReport:
    total_brl: float
    total_usd_equivalent: float        # BRL assets converted to USD
    dollarized_brl: float              # value of USD assets in BRL
    local_brl: float                   # value of BRL assets in BRL
    dollarized_pct: float              # % of portfolio in USD assets
    local_pct: float
    usd_brl_rate: float
    target_pct: float                  # user's dollarization goal
    gap_to_target_brl: float           # how much BRL to convert to reach target
    assets_usd: list[dict]
    assets_brl: list[dict]

    def is_on_target(self) -> bool:
        return self.dollarized_pct >= self.target_pct

    def summary_lines(self) -> list[str]:
        lines = [
            f"💵 USD/BRL rate       : R$ {self.usd_brl_rate:.4f}",
            f"📦 Total portfolio    : R$ {self.total_brl:,.2f}",
            f"🌎 Dollarized (USD)   : R$ {self.dollarized_brl:,.2f}  ({self.dollarized_pct:.1f}%)",
            f"🇧🇷 Local (BRL)        : R$ {self.local_brl:,.2f}  ({self.local_pct:.1f}%)",
            f"🎯 Target             : {self.target_pct:.0f}%",
        ]
        if self.is_on_target():
            lines.append("✅ Target reached!")
        else:
            lines.append(
                f"⚠️  Need to dollarize : R$ {self.gap_to_target_brl:,.2f} more"
            )
        return lines


class DollarizationAnalyzer:
    def __init__(self, target_pct: float = 30.0):
        """
        target_pct: desired percentage of portfolio in USD-denominated assets.
        Default: 30% (a common starting goal for Brazilian investors).
        """
        self.target_pct = target_pct

    def analyze(
        self,
        portfolio: "Portfolio",
        usd_brl_rate: float,
        current_prices: dict | None = None,
    ) -> DollarizationReport:
        """
        Analyze dollarization status of portfolio.
        current_prices: symbol → price (float). If None, uses avg_buy_price.
        """
        current_prices = current_prices or {}

        assets_usd: list[dict] = []
        assets_brl_list: list[dict] = []
        dollarized_brl = 0.0
        local_brl = 0.0

        for asset in portfolio.assets:
            # Determine current value
            raw_price = current_prices.get(asset.symbol, asset.avg_buy_price)
            if asset.currency == "USD":
                price_brl = raw_price * usd_brl_rate
            else:
                price_brl = raw_price

            value_brl = asset.quantity * price_brl
            pnl_pct = ((price_brl / asset.avg_buy_price) - 1) * 100 if asset.avg_buy_price else 0

            record = {
                "symbol": asset.symbol,
                "name": asset.name,
                "type": asset.asset_type,
                "quantity": asset.quantity,
                "current_price": raw_price,
                "value_brl": value_brl,
                "pnl_pct": round(pnl_pct, 2),
            }

            if asset.asset_type in DOLLARIZED_TYPES:
                dollarized_brl += value_brl
                assets_usd.append(record)
            else:
                local_brl += value_brl
                assets_brl_list.append(record)

        total_brl = dollarized_brl + local_brl
        dollarized_pct = (dollarized_brl / total_brl * 100) if total_brl else 0
        local_pct = 100 - dollarized_pct

        target_value = total_brl * (self.target_pct / 100)
        gap = max(0.0, target_value - dollarized_brl)

        return DollarizationReport(
            total_brl=total_brl,
            total_usd_equivalent=total_brl / usd_brl_rate if usd_brl_rate else 0,
            dollarized_brl=dollarized_brl,
            local_brl=local_brl,
            dollarized_pct=round(dollarized_pct, 2),
            local_pct=round(local_pct, 2),
            usd_brl_rate=usd_brl_rate,
            target_pct=self.target_pct,
            gap_to_target_brl=round(gap, 2),
            assets_usd=assets_usd,
            assets_brl=assets_brl_list,
        )

    def simulate_conversion(
        self,
        portfolio: "Portfolio",
        amount_brl: float,
        usd_brl_rate: float,
        current_prices: dict | None = None,
    ) -> dict:
        """
        Simulate what happens to dollarization % if you convert
        `amount_brl` worth of BRL assets to USD assets.
        """
        report = self.analyze(portfolio, usd_brl_rate, current_prices)
        new_dollarized = report.dollarized_brl + amount_brl
        new_pct = (new_dollarized / report.total_brl * 100) if report.total_brl else 0
        return {
            "conversion_brl": amount_brl,
            "conversion_usd": round(amount_brl / usd_brl_rate, 2),
            "before_pct": report.dollarized_pct,
            "after_pct": round(new_pct, 2),
            "would_reach_target": new_pct >= self.target_pct,
        }
