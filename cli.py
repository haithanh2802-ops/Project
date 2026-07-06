import argparse

from fairvalue_agent.agents.data_agent import DataAgent
from fairvalue_agent.agents.discovery_agent import DiscoveryAgent
from fairvalue_agent.agents.fundamental_agent import FundamentalAnalysisAgent
from fairvalue_agent.agents.report_agent import ReportAgent
from fairvalue_agent.agents.risk_agent import RiskAgent
from fairvalue_agent.agents.valuation_agent import ValuationAgent
from fairvalue_agent.tools.formatting_tools import format_money, format_percent
from fairvalue_agent.tools.market_tools import market_choices


def print_discovery_results(query: str, preferred_market: str | None = None) -> None:
    result = DiscoveryAgent().run(query, preferred_market=preferred_market)
    print(f"Search results for: {result.query}")

    for warning in result.warnings:
        print(f"Warning: {warning}")

    if not result.candidates:
        return

    print()
    print("| Symbol | Market | Exchange | Name | Sector | Industry |")
    print("| --- | --- | --- | --- | --- | --- |")
    for candidate in result.candidates:
        print(
            "| "
            f"{candidate.symbol} | "
            f"{candidate.market_code or 'Unknown'} | "
            f"{candidate.exchange_name or candidate.exchange or 'Unavailable'} | "
            f"{candidate.name or 'Unavailable'} | "
            f"{candidate.sector or 'Unavailable'} | "
            f"{candidate.industry or 'Unavailable'} |"
        )


def main() -> None:
    # Define the command-line inputs: one ticker plus an optional market code.
    parser = argparse.ArgumentParser(description="Run FairValue Agent valuation.")
    parser.add_argument("ticker", nargs="?", help="Stock ticker, for example AAPL, 700, or 600519")
    parser.add_argument(
        "--search",
        help="Search Yahoo Finance by company, ticker, sector, or market before valuation.",
    )
    parser.add_argument(
        "--search-market",
        choices=market_choices(),
        help="Prefer search results from this market.",
    )
    parser.add_argument(
        "--market",
        choices=market_choices(),
        default="US",
        help="Market code for resolving Yahoo Finance ticker suffixes.",
    )
    args = parser.parse_args()

    if args.search:
        print_discovery_results(args.search, preferred_market=args.search_market)
        return

    if not args.ticker:
        parser.error("ticker is required unless --search is used")

    print(f"Analyzing {args.ticker.upper()}...")
    print("[1/5] Collecting financial data...")

    # Step 1: Fetch and normalize Yahoo Finance company and financial data.
    data_result = DataAgent().run(args.ticker, market=args.market)
    company = data_result.company
    financials = data_result.financials
    quality = financials.data_quality

    # Steps 2-5: Run the same analysis pipeline used by the Streamlit app.
    print("[2/5] Analyzing fundamentals...")
    fundamentals = FundamentalAnalysisAgent().run(data_result)
    print("[3/5] Running valuation...")
    valuation = ValuationAgent().run(data_result)
    print("[4/5] Checking risks...")
    risk_assessment = RiskAgent().run(data_result, valuation)
    print("[5/5] Generating report...")
    report = ReportAgent().run(
        data_result,
        fundamentals,
        valuation,
        risk_assessment,
        output_dir="reports",
    )

    # Print a compact company and data-quality summary for quick terminal review.
    print()
    print(f"Company: {company.company_name or company.ticker}")
    print(f"Ticker: {company.ticker}")
    print(f"Market: {company.market}")
    print(f"Sector: {company.sector or 'Unavailable'}")
    print(f"Current price: {format_money(company.current_price, company.currency)}")
    print(f"Revenue: {format_money(financials.annual_revenue, company.currency)}")
    print(f"Free cash flow: {format_money(financials.annual_free_cash_flow, company.currency)}")
    print(f"Data usable: {'Yes' if quality.is_usable else 'No'}")
    print(f"Fundamental quality: {fundamentals.overall_quality}")
    print()

    # Show the main conclusion: valuation label, fair value range, confidence, and risk.
    print(f"Valuation label: {valuation.valuation_label}")
    print(
        "Fair value range: "
        f"{format_money(valuation.fair_value_low, company.currency)} - "
        f"{format_money(valuation.fair_value_high, company.currency)}"
    )
    print(f"Confidence: {valuation.confidence}")
    print(f"Overall risk: {risk_assessment.overall_risk}")
    print()

    # Show each DCF scenario so the user can see the assumptions behind the range.
    print("DCF scenarios:")
    for scenario in valuation.scenarios:
        value = format_money(scenario.fair_value_per_share, company.currency)
        print(
            f"- {scenario.name}: {value} "
            f"(growth {format_percent(scenario.growth_rate)}, "
            f"discount {format_percent(scenario.discount_rate)}, "
            f"terminal {format_percent(scenario.terminal_growth_rate)})"
        )

    # Show the P/E valuation cross-check beside the DCF result.
    pe = valuation.pe_valuation
    print(
        "P/E range: "
        f"{format_money(pe.low_value_per_share, company.currency)} - "
        f"{format_money(pe.high_value_per_share, company.currency)} "
        f"({pe.low_multiple:.1f}x-{pe.high_multiple:.1f}x)"
    )

    # Surface missing data and model warnings instead of hiding weak inputs.
    if quality.missing_required:
        print("Missing required data: " + ", ".join(quality.missing_required))
    if quality.missing_optional:
        print("Missing optional data: " + ", ".join(quality.missing_optional))
    if valuation.warnings:
        print("Warnings:")
        for warning in valuation.warnings:
            print(f"- {warning}")

    print()
    print("Risk summary:")
    print(risk_assessment.summary)

    # ReportAgent saves the full Markdown report in the reports folder.
    print()
    print(f"Report saved to {report.output_path}")


# Run the CLI only when this file is executed directly.
if __name__ == "__main__":
    main()
