# FairValue Agent Architecture

## Project Idea

FairValue Agent is an educational fundamental valuation assistant. A user can search for a company or enter a stock ticker and market directly. The system fetches public Yahoo Finance data, checks whether the data is usable, analyzes fundamentals, estimates fair value, identifies risks, and generates a beginner-friendly Markdown report.

The project is intentionally framed as valuation support, not short-term price prediction. It produces assumption-based ranges and labels, not guaranteed investment advice.

## End-To-End Flow

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

Both `cli.py` and `app.py` use this same pipeline. The CLI is useful for repeatable runs and demos. The Streamlit app is useful for interactive review.

## Folder Structure

```text
fairvalue_agent/
  agents/
    discovery_agent.py
    data_agent.py
    fundamental_agent.py
    valuation_agent.py
    risk_agent.py
    report_agent.py
  tools/
    yahoo_finance_tools.py
    market_tools.py
    validation_tools.py
    valuation_tools.py
    label_tools.py
    formatting_tools.py
  models.py

cli.py
app.py
reports/
docs/
```

The source code lives in `fairvalue_agent/`, `cli.py`, and `app.py`. The `reports/` folder contains generated Markdown reports. The `.cache/` and `__pycache__/` folders are runtime/generated artifacts and are not part of the core design.

## Agents

### Discovery Agent

File: `fairvalue_agent/agents/discovery_agent.py`

Purpose:

- Search Yahoo Finance when the user does not know the exact ticker or market.
- Return candidate equity listings with symbol, exchange, inferred market code, sector, and industry.
- Keep suggestions grounded in available Yahoo Finance search results.

Input:

- `query`

Output:

- `DiscoveryResult`
- `DiscoveryCandidate`

### Data Agent

File: `fairvalue_agent/agents/data_agent.py`

Purpose:

- Resolve the user ticker and market into a Yahoo Finance symbol.
- Fetch company profile, price, financial statement, cash flow, and balance sheet data.
- Normalize raw Yahoo Finance data into internal models.
- Mark missing required and optional fields.

Input:

- `ticker`
- `market`

Output:

- `DataAgentResult`
- `CompanyData`
- `FinancialSnapshot`
- `DataQualityResult`

### Fundamental Analysis Agent

File: `fairvalue_agent/agents/fundamental_agent.py`

Purpose:

- Convert raw financial metrics into beginner-readable business-quality observations.
- Score profitability, free cash flow quality, cash conversion, and leverage.
- Produce an overall quality label: `Strong`, `Mixed`, `Weak`, or `Insufficient Data`.

Input:

- `DataAgentResult`

Output:

- `FundamentalAnalysis`
- `FundamentalMetric`

### Valuation Agent

File: `fairvalue_agent/agents/valuation_agent.py`

Purpose:

- Build bear/base/bull DCF scenarios.
- Run a rough P/E valuation cross-check.
- Combine valid valuation methods into a fair value range.
- Assign the valuation label using transparent rule-based logic.

Input:

- `DataAgentResult`

Output:

- `ValuationResult`
- `ValuationScenario`
- `PeValuation`

### Risk Agent

File: `fairvalue_agent/agents/risk_agent.py`

Purpose:

- Convert data, financial, valuation, and model concerns into structured risk items.
- Assign severity to each risk: `Low`, `Medium`, or `High`.
- Produce an overall risk rating and summary.

Input:

- `DataAgentResult`
- `ValuationResult`

Output:

- `RiskAssessment`
- `RiskItem`

### Report Agent

File: `fairvalue_agent/agents/report_agent.py`

Purpose:

- Combine all previous agent outputs into one Markdown report.
- Include summary, valuation scenarios, P/E check, fundamental analysis, raw financial snapshot, assumptions, risks, methodology, and disclaimer.
- Save reports under `reports/`.

Input:

- `DataAgentResult`
- `FundamentalAnalysis`
- `ValuationResult`
- `RiskAssessment`

Output:

- `ReportResult`

## Tools

### `market_tools.py`

Defines supported markets and Yahoo Finance ticker suffixes. For example, `AAPL` in the US remains `AAPL`, while `HSBA` in the UK becomes `HSBA.L`.

### `validation_tools.py`

Normalizes and validates ticker input before any external data call.

### `yahoo_finance_tools.py`

Wraps `yfinance`, configures the local cache folder, fetches raw data, and extracts the fields needed by the agents.

### `valuation_tools.py`

Contains the valuation math:

- Growth assumption capping
- DCF calculation
- Bear/base/bull scenario construction
- Sector-aware P/E ranges
- DCF and P/E range combination

### `label_tools.py`

Contains the valuation label rule:

- `Undervalued` if current price is more than 10% below the fair value range.
- `Overvalued` if current price is more than 10% above the fair value range.
- `Fairly Valued` otherwise.
- `Insufficient Data` when required valuation numbers are missing.

### `formatting_tools.py`

Formats money, large numbers, and percentages consistently for CLI, Streamlit, and reports.

## Data Models

File: `fairvalue_agent/models.py`

The models file defines the shared contract between agents. This is the backbone of the architecture. Agents should exchange structured dataclasses instead of raw dictionaries wherever possible.

Important models:

- `CompanyData`: company profile, ticker, price, sector, market, shares, EPS, P/E.
- `DiscoveryResult`: search query, candidate listings, and warnings.
- `DiscoveryCandidate`: possible symbol, market, exchange, sector, and industry match.
- `FinancialSnapshot`: revenue, income, cash flow, debt, cash, and data quality.
- `FundamentalAnalysis`: quality label, metrics, and observations.
- `ValuationResult`: scenarios, P/E valuation, fair value range, label, confidence, assumptions, warnings.
- `RiskAssessment`: risk items and overall risk.
- `ReportResult`: Markdown report and optional saved path.

## Market Support

The project supports market-aware Yahoo Finance symbol resolution for the US, Canada, Vietnam, China, Hong Kong, Japan, Korea, Taiwan, Singapore, India, Indonesia, Malaysia, Thailand, Australia, New Zealand, the UK, selected European markets, selected Latin American markets, South Africa, Israel, and Turkey.

This does not guarantee equal data quality across markets. Yahoo Finance may return incomplete financial statements for some non-US listings. The Data Agent and Risk Agent are designed to surface those gaps instead of inventing missing data.

London listings need special handling because Yahoo Finance commonly quotes share prices in pence (`GBp`) while financial statements can be reported in currencies such as USD or EUR. The data tool normalizes pence prices to GBP and converts financial statement values into the quote currency before valuation.

## Safety Design

The system uses several guardrails:

- Input ticker validation.
- Data-quality warnings.
- Refusal to force DCF when free cash flow or share count is missing.
- Conservative valuation ranges instead of a single exact value.
- Rule-based labels with a 10% buffer.
- Required educational disclaimer in every report.
- No guaranteed-return language.
