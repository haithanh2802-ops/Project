# FairValue Agent

FairValue Agent is an educational fundamental valuation assistant for beginner retail investors. It takes a stock ticker and market, collects public Yahoo Finance data, and generates a beginner-friendly valuation report with assumptions, risks, DCF scenarios, a P/E cross-check, and a conservative valuation label.

## Current Status

The project is in Phase 3 prototype status: the core app works, and the next focus is reliability, tests, notebook presentation, and UI polish.

- Package structure is created.
- Shared data models are created.
- Ticker validation is implemented.
- Yahoo Finance data collection is implemented.
- Market-aware Yahoo Finance ticker resolution is implemented for the US, Canada, Vietnam, China, Hong Kong, Japan, Korea, Taiwan, Singapore, India, Indonesia, Malaysia, Thailand, Australia, New Zealand, the UK, selected European markets, selected Latin American markets, South Africa, Israel, and Turkey.
- The Data Agent performs basic data-quality checks.
- The Fundamental Analysis Agent summarizes profitability, cash-flow quality, and leverage.
- The Valuation Agent calculates DCF scenarios, P/E valuation, fair value range, confidence, and valuation label.
- The Risk Agent checks data-quality, financial-health, valuation, and model risks.
- The Report Agent generates a Markdown valuation report.
- The Discovery Agent helps users find tickers, markets, sectors, and industries before valuation.
- The CLI can run a data collection and valuation smoke test.
- The Streamlit app provides a simple web interface.
- Offline unit tests cover core valuation, market, currency, label, and discovery logic.
- A Kaggle-friendly demo notebook is included.

## Kaggle / Portfolio Demo

For a Kaggle-style walkthrough, open:

```text
FairValue_Agent_Demo.ipynb
```

Before submitting, run:

```bash
python -m unittest discover -s tests
```

See [Kaggle submission checklist](KAGGLE_SUBMISSION.md) for suggested files, cleanup steps, and limitation wording.

## Architecture

The system uses a simple five-agent pipeline:

```text
Company/search query
    -> optional Discovery Agent
    -> Ticker + market
    -> Data Agent
    -> Fundamental Analysis Agent
    -> Valuation Agent
    -> Risk Agent
    -> Report Agent
    -> CLI output, Streamlit UI, Markdown report
```

Detailed documentation:

- [Architecture guide](docs/architecture.md)
- [Code walkthrough](docs/code_walkthrough.md)

## Setup

```bash
pip install -r requirements.txt
```

## CLI Usage

```bash
python cli.py AAPL
```

If you do not know the ticker or market, search first:

```bash
python cli.py --search "HSBC"
python cli.py --search "HSBC" --search-market UK
python cli.py --search "Toyota"
python cli.py --search "semiconductors"
```

Use `--market` for non-US markets:

```bash
python cli.py VNM --market VN
python cli.py 600519 --market CN_SH
python cli.py 700 --market HK
python cli.py HSBA --market UK
python cli.py OR --market FR
python cli.py SHOP --market CA
python cli.py 7203 --market JP
python cli.py 005930 --market KR
python cli.py INFY --market IN_NS
python cli.py BHP --market AU
python cli.py VALE3 --market BR
```

The CLI prints:

- Company summary
- Current price
- Revenue and free cash flow
- Data-quality status
- Fundamental quality rating
- DCF bear/base/bull scenarios
- P/E valuation range
- Combined fair value range
- Valuation label
- Overall risk rating
- Warnings when data or valuation inputs are unreliable

Reports are saved under `reports/`, for example:

```bash
reports/AAPL_report.md
```

## Streamlit Usage

```bash
python app.py
```

This launches Streamlit for you. You can also run Streamlit directly:

```bash
streamlit run app.py
```

The Streamlit app includes a ticker discovery panel, market selector, and valuation workspace. Use the discovery panel when you know the company, sector, or theme but not the exact ticker or market. Coverage depends on Yahoo Finance availability for each ticker and exchange. London listings are normalized from pence to GBP, and financial statements are converted into the quote currency when Yahoo reports a different financial statement currency.

## Discovery Agent

The Discovery Agent searches Yahoo Finance for matching equity listings and returns candidate symbols, markets, exchanges, sectors, and industries. It is rule-assisted rather than LLM-backed right now, so it does not require an API key. A later LLM-backed version can use these search results as grounding context before suggesting the most likely listing.

## Disclaimer

This project is for educational purposes only. It does not provide financial advice, investment recommendations, or guaranteed returns.
