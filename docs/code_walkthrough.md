# Code Walkthrough

## Entry Points

### `cli.py`

`cli.py` is the command-line entry point. It parses the ticker and optional market, then runs the five-agent pipeline:

```python
data_result = DataAgent().run(args.ticker, market=args.market)
fundamentals = FundamentalAnalysisAgent().run(data_result)
valuation = ValuationAgent().run(data_result)
risk_assessment = RiskAgent().run(data_result, valuation)
report = ReportAgent().run(data_result, fundamentals, valuation, risk_assessment, output_dir="reports")
```

The CLI prints a compact summary and saves a Markdown report.

The CLI can also search for possible tickers before valuation:

```python
python cli.py --search "HSBC"
```

### `app.py`

`app.py` is the Streamlit entry point. It uses the same agent pipeline as `cli.py`, then displays the result in tabs:

- Valuation
- Fundamentals
- Risks
- Report

The `run_analysis()` function is cached for 15 minutes with `st.cache_data(ttl=900)` to avoid repeated Yahoo Finance requests for the same ticker and market. Running `python app.py` launches Streamlit automatically; `streamlit run app.py` still works.

The sidebar also includes a discovery form. `run_discovery()` calls the Discovery Agent so users can search by company, ticker, sector, or market before selecting a listing for analysis.

## Agent Details

### Discovery Agent

The Discovery Agent searches Yahoo Finance and returns possible equity listings:

- Symbol
- Company name
- Exchange
- Inferred market code
- Sector
- Industry

It filters out non-equity results by default so valuation starts from common stocks rather than funds or ETFs.

### Data Agent

The Data Agent starts by resolving the ticker:

```python
yahoo_symbol, market_config = resolve_yahoo_symbol(ticker, market)
raw = fetch_yahoo_finance_data(yahoo_symbol)
```

It separates missing data into two groups:

- Required data: needed for basic usability, such as current price and shares outstanding.
- Optional data: useful for valuation and reports, but not always available.

It returns normalized dataclasses:

```python
return DataAgentResult(company=company, financials=financials)
```

### Fundamental Analysis Agent

The Fundamental Analysis Agent computes ratios from the normalized financial snapshot:

- Net margin
- Free cash flow margin
- Operating cash flow divided by net income
- Debt divided by free cash flow
- Cash divided by debt

It avoids division errors by using `_safe_ratio()`. If a denominator is missing or zero, the metric is skipped instead of guessed.

The quality label is score-based:

- `Strong`: at least 75% of scored checks pass.
- `Mixed`: at least 40% pass.
- `Weak`: below 40%.
- `Insufficient Data`: no usable checks.

### Valuation Agent

The Valuation Agent delegates the math to `valuation_tools.py`.

DCF assumptions:

- Five projected years.
- Growth capped between -5% and 15%.
- Discount rates from 8.5% to 11.0%.
- Terminal growth from 1.5% to 3.0%.
- Terminal growth must be lower than discount rate.

P/E valuation:

- Uses sector-specific P/E ranges when available.
- Falls back to a default range when the sector is unavailable.
- Is invalid when trailing EPS is missing or negative.

Range combination:

- If DCF and P/E are valid, use `70% DCF + 30% P/E`.
- If only DCF is valid, use DCF only.
- If only P/E is valid, use P/E only and mark confidence low.
- If neither is valid, return insufficient valuation data.

### Risk Agent

The Risk Agent creates structured risk items from four sources:

- Data quality risks
- Financial health risks
- Valuation risks
- Model risks

Each risk has:

- Category
- Severity
- Message

The overall risk is the highest severity found.

### Report Agent

The Report Agent builds Markdown sections in `_build_markdown()`:

- Summary
- Valuation scenarios
- P/E valuation check
- Fundamental analysis
- Fundamental snapshot
- Key assumptions
- Risks and data warnings
- Methodology
- Educational disclaimer

If `output_dir` is provided, the report is saved as:

```text
reports/<TICKER>_report.md
```

## Tool Details

### Yahoo Finance Tool

`fetch_yahoo_finance_data()` uses `yfinance.Ticker` and extracts a stable subset of fields. It also sets the yfinance cache location to `.cache/yfinance` so the app can run in this workspace without writing to restricted system folders.

### Market Tool

`resolve_yahoo_symbol()` applies Yahoo Finance suffixes:

```text
US:    AAPL
VN:    VNM.VN
CN_SH: 600519.SS
CN_SZ: 000001.SZ
HK:    0700.HK
UK:    HSBA.L
FR:    OR.PA
```

If the user already includes a suffix, the code preserves it. Numeric Hong Kong tickers are padded to four digits before appending `.HK`.

### Label Tool

`get_valuation_label()` compares current price with the fair value range:

```python
if current_price < fair_value_low * 0.90:
    return "Undervalued"
if current_price > fair_value_high * 1.10:
    return "Overvalued"
return "Fairly Valued"
```

The 10% buffer prevents the app from overreacting when price is close to the estimated range.

## Known Limitations

- Yahoo Finance data may be incomplete, delayed, or unavailable.
- Non-US financial statement coverage is inconsistent.
- The DCF model is intentionally simple.
- Sector P/E ranges are rough defaults, not live market comps.
- Banks, insurers, REITs, and commodity companies may need specialized valuation methods later.
- The app does not make investment recommendations.
