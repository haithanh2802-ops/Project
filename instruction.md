# FairValue Agent Instructions

## Project Idea

FairValue Agent is an educational fundamental analysis and valuation tool for stocks across multiple markets. A user enters a stock ticker and market, the app imports public data from Yahoo Finance, and the system produces a beginner-friendly valuation report.

The project should focus on fundamental analysis, not short-term price prediction.

The app should also help users who do not know the exact ticker or exchange. Users should be able to search by company name, ticker fragment, market, sector, or theme, then choose a candidate listing before running valuation.

## Core Workflow

```text
Ticker + market
    -> collect Yahoo Finance data
    -> optionally discover ticker and market
    -> check data quality
    -> analyze fundamentals
    -> estimate valuation range
    -> identify risks
    -> generate report
```

Both the CLI and Streamlit app should use the same analysis pipeline.

## Data Source

Yahoo Finance is the primary data source through `yfinance`.

Important constraints:

- Data availability varies by market and ticker.
- Non-US listings may have incomplete financial statements.
- Some markets use different quote units or financial statement currencies. For example, London prices may be quoted in pence while financial statements are reported in USD or EUR, so the app should normalize units before valuation.
- The system should show missing data clearly instead of inventing values.
- Cached data should stay inside the project workspace.

## Market Support

The project is intended to support many markets through Yahoo Finance ticker suffixes. Existing support includes the United States, Canada, Vietnam, China, Hong Kong, Japan, Korea, Taiwan, Singapore, India, Indonesia, Malaysia, Thailand, Australia, New Zealand, the United Kingdom, selected European markets, selected Latin American markets, South Africa, Israel, and Turkey.

New markets should be added through `fairvalue_agent/tools/market_tools.py`.

## Valuation Principles

Valuation should remain conservative and transparent:

- Use ranges instead of one exact fair value.
- Show assumptions clearly.
- Warn when data quality is weak.
- Avoid guaranteed-return language.
- Keep the output educational and beginner-friendly.

## Safety And Disclaimer

The app must not present results as financial advice, investment recommendations, or guaranteed outcomes. Every generated report should include an educational disclaimer.

## Development Notes

- Keep shared data contracts in `fairvalue_agent/models.py`.
- Keep external data access in tool modules.
- Keep each agent focused on one responsibility.
- Avoid hardcoding ticker-specific logic.
- Add tests or smoke checks when changing valuation logic, ticker resolution, or report generation.
- Generated folders such as `__pycache__/` and `.cache/` should not be treated as project source.
- The current support agent should stay grounded in available market data. If an LLM is added later, it should explain and rank discovered listings rather than invent tickers.
