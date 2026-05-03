"""
cli.py — Command-line interface for dolar-flow
Usage: python -m dolar_flow <command> [options]
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

# Allow running as: python cli.py or python -m dolar_flow
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.core.portfolio import Asset, Portfolio, PortfolioStorage
from src.core.dollarization import DollarizationAnalyzer
from src.integrations.prices import PriceFetcher
from src.integrations.alerts import TelegramAlerter


STORAGE = PortfolioStorage()
FETCHER = PriceFetcher()
ALERTER = TelegramAlerter()


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _load() -> Portfolio:
    return STORAGE.load()


def _save(p: Portfolio) -> None:
    STORAGE.save(p)
    print("✅ Portfolio saved.")


def _color(text: str, code: int) -> str:
    return f"\033[{code}m{text}\033[0m"


def green(t: str) -> str: return _color(t, 32)
def red(t: str) -> str:   return _color(t, 31)
def bold(t: str) -> str:  return _color(t, 1)
def cyan(t: str) -> str:  return _color(t, 36)


# ------------------------------------------------------------------ #
# Commands
# ------------------------------------------------------------------ #

def cmd_add(args: argparse.Namespace) -> None:
    portfolio = _load()
    asset = Asset(
        symbol=args.symbol.upper(),
        name=args.name,
        quantity=args.quantity,
        avg_buy_price=args.price,
        avg_buy_price_usd=args.price_usd,
        asset_type=args.type,
        currency=args.currency,
        sector=args.sector,
        notes=args.notes,
    )
    portfolio.add_asset(asset)
    _save(portfolio)
    print(f"➕ Added {asset.quantity}x {asset.symbol} @ R${asset.avg_buy_price:.2f}")


def cmd_remove(args: argparse.Namespace) -> None:
    portfolio = _load()
    ok = portfolio.remove_asset(args.symbol.upper(), args.quantity)
    if ok:
        _save(portfolio)
        print(f"➖ Removed {args.quantity}x {args.symbol}")
    else:
        print(red(f"Asset {args.symbol} not found."))


def cmd_list(args: argparse.Namespace) -> None:
    portfolio = _load()
    if not portfolio.assets:
        print("Portfolio is empty. Use 'add' to insert assets.")
        return

    print(bold(f"\n{'Symbol':<12} {'Name':<25} {'Type':<14} {'Qty':>8} {'Avg Price':>12} {'Total BRL':>14}"))
    print("─" * 90)
    for a in portfolio.assets:
        print(
            f"{cyan(a.symbol):<21} {a.name:<25} {a.asset_type:<14} "
            f"{a.quantity:>8.4f} {a.avg_buy_price:>12.2f} {a.total_invested_brl:>14.2f}"
        )
    print("─" * 90)
    s = portfolio.summary()
    print(bold(f"\nTotal invested: R$ {s['total_invested_brl']:,.2f}"))
    print("Allocation by type:")
    for k, v in s["allocation"].items():
        print(f"  {k:<18} {v:.1f}%")


def cmd_status(args: argparse.Namespace) -> None:
    portfolio = _load()
    if not portfolio.assets:
        print("Portfolio empty.")
        return

    print("⏳ Fetching prices and exchange rate...")
    usd_brl = FETCHER.get_usd_brl()
    analyzer = DollarizationAnalyzer(target_pct=args.target)
    report = analyzer.analyze(portfolio, usd_brl_rate=usd_brl)

    print()
    for line in report.summary_lines():
        print(line)

    print(bold("\n── USD Assets ──────────────────"))
    for a in report.assets_usd:
        pnl = a["pnl_pct"]
        pnl_str = green(f"+{pnl:.1f}%") if pnl >= 0 else red(f"{pnl:.1f}%")
        print(f"  {cyan(a['symbol']):<12} R$ {a['value_brl']:>12,.2f}  {pnl_str}")

    print(bold("\n── BRL Assets ──────────────────"))
    for a in report.assets_brl:
        pnl = a["pnl_pct"]
        pnl_str = green(f"+{pnl:.1f}%") if pnl >= 0 else red(f"{pnl:.1f}%")
        print(f"  {cyan(a['symbol']):<12} R$ {a['value_brl']:>12,.2f}  {pnl_str}")

    if args.notify:
        ALERTER.send_dollarization_alert(report.dollarized_pct, report.target_pct)
        ALERTER.send_portfolio_summary(report.summary_lines())
        print("\n📲 Telegram alert sent.")


def cmd_simulate(args: argparse.Namespace) -> None:
    portfolio = _load()
    usd_brl = FETCHER.get_usd_brl()
    analyzer = DollarizationAnalyzer(target_pct=args.target)
    result = analyzer.simulate_conversion(portfolio, args.amount, usd_brl)

    print(bold(f"\n💱 Simulation: convert R$ {args.amount:,.2f} to USD assets"))
    print(f"  USD equivalent      : $ {result['conversion_usd']:,.2f}")
    print(f"  Dollarization before: {result['before_pct']:.1f}%")
    print(f"  Dollarization after : {result['after_pct']:.1f}%")
    if result["would_reach_target"]:
        print(green(f"  ✅ Would reach {args.target}% target!"))
    else:
        print(red(f"  ❌ Still below {args.target}% target."))


def cmd_rate(args: argparse.Namespace) -> None:
    rate = FETCHER.get_usd_brl()
    print(f"💵 USD/BRL: R$ {rate:.4f}")
    if args.amount:
        print(f"  R$ {args.amount:,.2f} = $ {args.amount / rate:,.2f}")
        print(f"  $ {args.amount:,.2f} = R$ {args.amount * rate:,.2f}")


def cmd_export(args: argparse.Namespace) -> None:
    portfolio = _load()
    out = Path(args.output)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(portfolio.to_dict(), f, indent=2, ensure_ascii=False)
    print(f"📤 Portfolio exported to {out}")


# ------------------------------------------------------------------ #
# Parser
# ------------------------------------------------------------------ #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dolar-flow",
        description="💵 Portfolio tracker focused on asset dollarization",
    )
    sub = parser.add_subparsers(dest="command")

    # add
    p_add = sub.add_parser("add", help="Add or update an asset")
    p_add.add_argument("symbol", help="Ticker symbol (e.g. PETR4, AAPL, bitcoin)")
    p_add.add_argument("name", help="Asset name")
    p_add.add_argument("quantity", type=float)
    p_add.add_argument("price", type=float, help="Average buy price in BRL")
    p_add.add_argument("price_usd", type=float, help="Average buy price in USD")
    p_add.add_argument("--type", default="stock_br",
                       choices=["stock_br", "stock_us", "crypto", "fii", "renda_fixa"])
    p_add.add_argument("--currency", default="BRL", choices=["BRL", "USD"])
    p_add.add_argument("--sector", default=None)
    p_add.add_argument("--notes", default=None)

    # remove
    p_rm = sub.add_parser("remove", help="Remove asset from portfolio")
    p_rm.add_argument("symbol")
    p_rm.add_argument("quantity", type=float)

    # list
    sub.add_parser("list", help="List all assets")

    # status
    p_st = sub.add_parser("status", help="Show dollarization status with live prices")
    p_st.add_argument("--target", type=float, default=30.0,
                      help="Dollarization target %% (default: 30)")
    p_st.add_argument("--notify", action="store_true", help="Send Telegram alert")

    # simulate
    p_sim = sub.add_parser("simulate", help="Simulate converting BRL to USD assets")
    p_sim.add_argument("amount", type=float, help="Amount in BRL to simulate converting")
    p_sim.add_argument("--target", type=float, default=30.0)

    # rate
    p_rate = sub.add_parser("rate", help="Show current USD/BRL rate")
    p_rate.add_argument("--amount", type=float, default=None, help="Convert an amount")

    # export
    p_exp = sub.add_parser("export", help="Export portfolio to JSON")
    p_exp.add_argument("--output", default="portfolio_export.json")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    commands = {
        "add": cmd_add,
        "remove": cmd_remove,
        "list": cmd_list,
        "status": cmd_status,
        "simulate": cmd_simulate,
        "rate": cmd_rate,
        "export": cmd_export,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
