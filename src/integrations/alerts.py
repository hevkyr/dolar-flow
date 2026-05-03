"""
alerts.py — Telegram alert system for portfolio events
"""

from __future__ import annotations
import os
import requests
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AlertRule:
    symbol: str
    alert_above: Optional[float] = None
    alert_below: Optional[float] = None
    triggered_above: bool = False
    triggered_below: bool = False

    def should_alert_above(self, price: float) -> bool:
        if self.alert_above and not self.triggered_above and price >= self.alert_above:
            self.triggered_above = True
            return True
        if self.alert_above and self.triggered_above and price < self.alert_above:
            self.triggered_above = False  # reset
        return False

    def should_alert_below(self, price: float) -> bool:
        if self.alert_below and not self.triggered_below and price <= self.alert_below:
            self.triggered_below = True
            return True
        if self.alert_below and self.triggered_below and price > self.alert_below:
            self.triggered_below = False  # reset
        return False


class TelegramAlerter:
    """Sends formatted portfolio alerts to a Telegram chat."""

    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        self.token = token or os.getenv("TELEGRAM_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self._base = f"https://api.telegram.org/bot{self.token}"

    def _send(self, text: str) -> bool:
        if not self.token or not self.chat_id:
            print(f"[TELEGRAM DISABLED] {text}")
            return False
        try:
            r = requests.post(
                f"{self._base}/sendMessage",
                json={"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
            return r.status_code == 200
        except Exception as e:
            print(f"[TELEGRAM ERROR] {e}")
            return False

    def send_price_alert(self, symbol: str, price: float, direction: str, target: float) -> bool:
        emoji = "🚀" if direction == "above" else "📉"
        text = (
            f"{emoji} <b>{symbol}</b> price alert\n"
            f"Current: <code>{price:,.4f}</code>\n"
            f"Target {'above' if direction == 'above' else 'below'}: <code>{target:,.4f}</code>"
        )
        return self._send(text)

    def send_dollarization_alert(self, pct: float, target: float) -> bool:
        if pct >= target:
            text = (
                f"✅ <b>Dollarization target reached!</b>\n"
                f"Current: <code>{pct:.1f}%</code> / Target: <code>{target:.1f}%</code>"
            )
        else:
            gap = target - pct
            text = (
                f"⚠️ <b>Dollarization update</b>\n"
                f"Current: <code>{pct:.1f}%</code>\n"
                f"Target: <code>{target:.1f}%</code>\n"
                f"Gap: <code>{gap:.1f}%</code>"
            )
        return self._send(text)

    def send_portfolio_summary(self, summary_lines: list[str]) -> bool:
        text = "📊 <b>Portfolio Summary</b>\n\n" + "\n".join(summary_lines)
        return self._send(text)

    def send_exchange_rate_alert(self, rate: float, threshold: float, direction: str) -> bool:
        emoji = "🔺" if direction == "above" else "🔻"
        text = (
            f"{emoji} <b>USD/BRL rate alert</b>\n"
            f"Rate: <code>R$ {rate:.4f}</code>\n"
            f"Threshold: <code>R$ {threshold:.4f}</code>"
        )
        return self._send(text)
