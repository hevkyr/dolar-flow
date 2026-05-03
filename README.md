# 💵 dolar-flow

**Portfolio tracker focused on asset dollarization for Brazilian investors**

🐍 Python · 💰 Finance · 🤖 Automation · 🐧 Linux

---

## 📖 About

`dolar-flow` is a Python CLI tool to track your investment portfolio with a focus on **dollarization of assets** — the strategy of gradually moving wealth from BRL-denominated to USD-denominated assets.

The project:

- Tracks stocks (B3 + US market), crypto, FIIs, and renda fixa
- Calculates your **dollarization percentage** in real time
- Fetches **live USD/BRL rate** via AwesomeAPI
- Fetches **stock prices** via Yahoo Finance (no API key)
- Fetches **crypto prices** via CoinGecko (no API key)
- Sends alerts via **Telegram**
- Simulates how much BRL to convert to hit a dollarization target

---

## ✨ Features

- 📊 Full portfolio view with P&L per asset
- 💵 Real-time USD/BRL exchange rate
- 🌎 Dollarization analysis (% of assets in USD)
- 🎯 Configurable dollarization target (default: 30%)
- 💱 Simulate BRL → USD conversion impact
- 🚨 Telegram alerts (price, dollarization, rate thresholds)
- 📤 JSON export for further analysis
- ✅ CI pipeline with pytest coverage
- 🐧 Runs cleanly on Arch / Fedora / any Linux

---

## 📁 Project Structure

```
dolar-flow/
├── src/
│   ├── core/
│   │   ├── portfolio.py          # Asset & Portfolio models + JSON storage
│   │   └── dollarization.py      # Dollarization analyzer & simulator
│   ├── integrations/
│   │   ├── prices.py             # Yahoo Finance, CoinGecko, AwesomeAPI
│   │   └── alerts.py             # Telegram alert system
│   └── cli/
│       └── cli.py                # Command-line interface
├── tests/
│   └── test_portfolio.py         # Unit tests (pytest)
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions CI
├── .env.example
├── requirements.txt
├── setup.py
└── README.md
```

---

## 🚀 Installation

Clone repository:

```bash
git clone https://github.com/hevkyr/dolar-flow.git
cd dolar-flow
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install as CLI tool (optional):

```bash
pip install -e .
```

---

## ⚙ Configuration

Create `.env` from the example:

```bash
cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

> Telegram is **optional**. All features work without it — alerts just print to stdout.

---

## ▶ Usage

### Add assets

```bash
# B3 stock (BRL)
python -m src.cli.cli add PETR4 "Petrobras" 100 38.50 7.20 --type stock_br --currency BRL

# US stock (USD)
python -m src.cli.cli add AAPL "Apple Inc." 5 1100.00 200.00 --type stock_us --currency USD

# Crypto
python -m src.cli.cli add bitcoin "Bitcoin" 0.05 290000 53000 --type crypto --currency USD
```

### List portfolio

```bash
python -m src.cli.cli list
```

Example output:

```
Symbol       Name                      Type           Qty    Avg Price      Total BRL
──────────────────────────────────────────────────────────────────────────────────────
PETR4        Petrobras                 stock_br    100.0000      38.50       3,850.00
AAPL         Apple Inc.                stock_us      5.0000    1100.00       5,500.00
bitcoin      Bitcoin                   crypto        0.0500  290000.00      14,500.00
──────────────────────────────────────────────────────────────────────────────────────

Total invested: R$ 23,850.00
Allocation by type:
  stock_br           16.1%
  stock_us           23.1%
  crypto             60.8%
```

### Check dollarization status (live prices)

```bash
python -m src.cli.cli status --target 40
```

Example output:

```
💵 USD/BRL rate       : R$ 5.7320
📦 Total portfolio    : R$ 24,100.00
🌎 Dollarized (USD)   : R$ 20,250.00  (84.0%)
🇧🇷 Local (BRL)        : R$  3,850.00  (16.0%)
🎯 Target             : 40%
✅ Target reached!
```

### Simulate conversion

```bash
python -m src.cli.cli simulate 5000 --target 50
```

Example output:

```
💱 Simulation: convert R$ 5,000.00 to USD assets
  USD equivalent      : $    872.48
  Dollarization before: 16.1%
  Dollarization after : 36.9%
  ❌ Still below 50% target.
```

### Check USD/BRL rate

```bash
python -m src.cli.cli rate --amount 1000
```

```
💵 USD/BRL: R$ 5.7320
  R$ 1,000.00 = $ 174.46
  $ 1,000.00  = R$ 5,732.00
```

### Send Telegram report

```bash
python -m src.cli.cli status --target 30 --notify
```

### Export portfolio

```bash
python -m src.cli.cli export --output my_portfolio.json
```

---

## 🤖 Telegram Alerts

Example messages:

```
📊 Portfolio Summary

💵 USD/BRL rate       : R$ 5.7320
📦 Total portfolio    : R$ 24,100.00
🌎 Dollarized (USD)   : R$ 20,250.00  (84.0%)
🇧🇷 Local (BRL)        : R$  3,850.00  (16.0%)
🎯 Target             : 30%
✅ Target reached!
```

```
✅ Dollarization target reached!
Current: 84.0% / Target: 30.0%
```

---

## 🔌 APIs Used

| API | Used For | Key Required |
|-----|----------|-------------|
| [AwesomeAPI](https://docs.awesomeapi.com.br/) | USD/BRL rate | ❌ No |
| [Yahoo Finance](https://finance.yahoo.com/) | Stock prices (BR + US) | ❌ No |
| [CoinGecko](https://www.coingecko.com/en/api) | Crypto prices | ❌ No |
| [Telegram Bot API](https://core.telegram.org/bots/api) | Alerts | ✅ Bot token |

---

## 🧪 Tests

```bash
pytest tests/ -v
```

With coverage:

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

---

## ⚠ Notes

- Yahoo Finance symbols: B3 stocks need `.SA` suffix internally (e.g., `PETR4.SA`)
- CoinGecko uses coin IDs, not tickers (e.g., `bitcoin`, not `BTC`)
- All data is stored locally in `data/portfolio.json` — no cloud, no account
- Keep `.env` out of version control (it's in `.gitignore`)

---

## 📜 License

MIT License

[🇺🇸 English](#) · [🇧🇷 Português](#sobre)

---

## 🇧🇷 Sobre

`dolar-flow` é uma ferramenta CLI em Python para rastrear sua carteira de investimentos com foco em **dolarização de ativos** — estratégia de mover gradualmente patrimônio de ativos em BRL para ativos em USD.

Funcionalidades principais:

- Rastreia ações (B3 + mercado US), cripto, FIIs e renda fixa
- Calcula seu **percentual de dolarização** em tempo real
- Busca **cotação USD/BRL** ao vivo pela AwesomeAPI
- Busca preços de ações via Yahoo Finance (sem API key)
- Busca preços de cripto via CoinGecko (sem API key)
- Envia alertas pelo **Telegram**
- Simula quanto converter de BRL para atingir uma meta de dolarização
