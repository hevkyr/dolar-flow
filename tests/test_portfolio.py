"""
tests/test_portfolio.py — Unit tests for core portfolio logic
"""

import pytest
from src.core.portfolio import Asset, Portfolio, PortfolioStorage
from src.core.dollarization import DollarizationAnalyzer


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #

def make_asset(
    symbol="AAPL",
    name="Apple Inc.",
    quantity=10.0,
    avg_buy_price=1100.0,
    avg_buy_price_usd=200.0,
    asset_type="stock_us",
    currency="USD",
) -> Asset:
    return Asset(
        symbol=symbol,
        name=name,
        quantity=quantity,
        avg_buy_price=avg_buy_price,
        avg_buy_price_usd=avg_buy_price_usd,
        asset_type=asset_type,
        currency=currency,
    )


@pytest.fixture
def empty_portfolio():
    return Portfolio(name="Test")


@pytest.fixture
def mixed_portfolio():
    p = Portfolio(name="Test Mixed")
    p.add_asset(make_asset("AAPL", "Apple", 10, 1100, 200, "stock_us", "USD"))
    p.add_asset(make_asset("PETR4", "Petrobras", 100, 40, 7.5, "stock_br", "BRL"))
    p.add_asset(make_asset("bitcoin", "Bitcoin", 0.1, 300000, 55000, "crypto", "USD"))
    return p


# ------------------------------------------------------------------ #
# Asset tests
# ------------------------------------------------------------------ #

class TestAsset:
    def test_total_invested_brl(self):
        a = make_asset(quantity=5, avg_buy_price=1000)
        assert a.total_invested_brl == 5000.0

    def test_total_invested_usd(self):
        a = make_asset(quantity=5, avg_buy_price_usd=200)
        assert a.total_invested_usd == 1000.0

    def test_to_dict_contains_symbol(self):
        a = make_asset()
        d = a.to_dict()
        assert d["symbol"] == "AAPL"


# ------------------------------------------------------------------ #
# Portfolio tests
# ------------------------------------------------------------------ #

class TestPortfolio:
    def test_add_new_asset(self, empty_portfolio):
        a = make_asset()
        empty_portfolio.add_asset(a)
        assert len(empty_portfolio.assets) == 1

    def test_add_same_symbol_averages_price(self, empty_portfolio):
        a1 = make_asset(quantity=10, avg_buy_price=100)
        a2 = make_asset(quantity=10, avg_buy_price=200)
        empty_portfolio.add_asset(a1)
        empty_portfolio.add_asset(a2)
        assert len(empty_portfolio.assets) == 1
        assert empty_portfolio.assets[0].quantity == 20
        assert empty_portfolio.assets[0].avg_buy_price == pytest.approx(150.0)

    def test_remove_full_position(self, empty_portfolio):
        empty_portfolio.add_asset(make_asset(quantity=10))
        empty_portfolio.remove_asset("AAPL", 10)
        assert len(empty_portfolio.assets) == 0

    def test_remove_partial_position(self, empty_portfolio):
        empty_portfolio.add_asset(make_asset(quantity=10))
        empty_portfolio.remove_asset("AAPL", 4)
        assert empty_portfolio.assets[0].quantity == 6

    def test_remove_nonexistent_returns_false(self, empty_portfolio):
        result = empty_portfolio.remove_asset("FAKE", 1)
        assert result is False

    def test_summary_allocation_sums_to_100(self, mixed_portfolio):
        summary = mixed_portfolio.summary()
        total = sum(summary["allocation"].values())
        assert abs(total - 100.0) < 0.01

    def test_total_invested_brl_correct(self, mixed_portfolio):
        # AAPL: 10 * 1100 = 11000
        # PETR4: 100 * 40 = 4000
        # BTC: 0.1 * 300000 = 30000
        expected = 11000 + 4000 + 30000
        assert mixed_portfolio.total_invested_brl() == pytest.approx(expected)


# ------------------------------------------------------------------ #
# Dollarization tests
# ------------------------------------------------------------------ #

class TestDollarizationAnalyzer:
    def test_dollarized_pct_correct(self, mixed_portfolio):
        analyzer = DollarizationAnalyzer(target_pct=30.0)
        # USD assets: AAPL (11000) + BTC (30000) = 41000 BRL
        # BRL assets: PETR4 (4000)
        # Total: 45000
        # Dollarized: 41000 / 45000 = 91.1%
        report = analyzer.analyze(mixed_portfolio, usd_brl_rate=5.5)
        assert report.dollarized_pct == pytest.approx(91.1, abs=0.5)

    def test_target_reached_when_above(self, mixed_portfolio):
        analyzer = DollarizationAnalyzer(target_pct=30.0)
        report = analyzer.analyze(mixed_portfolio, usd_brl_rate=5.5)
        assert report.is_on_target() is True

    def test_gap_zero_when_on_target(self, mixed_portfolio):
        analyzer = DollarizationAnalyzer(target_pct=30.0)
        report = analyzer.analyze(mixed_portfolio, usd_brl_rate=5.5)
        assert report.gap_to_target_brl == 0.0

    def test_simulate_conversion(self, mixed_portfolio):
        analyzer = DollarizationAnalyzer(target_pct=30.0)
        result = analyzer.simulate_conversion(mixed_portfolio, 5000, usd_brl_rate=5.5)
        assert result["after_pct"] > result["before_pct"]

    def test_empty_portfolio_no_crash(self, empty_portfolio):
        analyzer = DollarizationAnalyzer()
        report = analyzer.analyze(empty_portfolio, usd_brl_rate=5.5)
        assert report.total_brl == 0
        assert report.dollarized_pct == 0


# ------------------------------------------------------------------ #
# Serialization tests
# ------------------------------------------------------------------ #

class TestSerialization:
    def test_portfolio_roundtrip(self, mixed_portfolio):
        d = mixed_portfolio.to_dict()
        restored = Portfolio.from_dict(d)
        assert restored.name == mixed_portfolio.name
        assert len(restored.assets) == len(mixed_portfolio.assets)
        assert restored.assets[0].symbol == mixed_portfolio.assets[0].symbol
