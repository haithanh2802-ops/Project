from pathlib import Path

from fairvalue_agent.models import (
    DataAgentResult,
    FundamentalAnalysis,
    ReportResult,
    RiskAssessment,
    ValuationResult,
)
from fairvalue_agent.tools.formatting_tools import (
    format_large_number,
    format_money,
    format_percent,
)


DISCLAIMER = (
    "This report is for educational purposes only. It is not financial advice, "
    "an investment recommendation, or a guarantee of future returns. Valuation "
    "depends on assumptions and incomplete public data."
)


class ReportAgent:
    def run(
        self,
        data: DataAgentResult,
        fundamentals: FundamentalAnalysis,
        valuation: ValuationResult,
        risk_assessment: RiskAssessment,
        output_dir: str | Path | None = None,
    ) -> ReportResult:
        markdown = self._build_markdown(data, fundamentals, valuation, risk_assessment)
        output_path = None

        if output_dir is not None:
            report_dir = Path(output_dir)
            report_dir.mkdir(parents=True, exist_ok=True)
            output_path = report_dir / f"{data.company.ticker}_report.md"
            output_path.write_text(markdown, encoding="utf-8")

        return ReportResult(
            ticker=data.company.ticker,
            markdown=markdown,
            output_path=str(output_path) if output_path else None,
        )

    def _build_markdown(
        self,
        data: DataAgentResult,
        fundamentals: FundamentalAnalysis,
        valuation: ValuationResult,
        risk_assessment: RiskAssessment,
    ) -> str:
        company = data.company
        financials = data.financials
        currency = company.currency or "USD"

        sections = [
            f"# FairValue Agent Report: {company.company_name or company.ticker} ({company.ticker})",
            "## Summary",
            self._summary_table(data, valuation),
            "## Valuation Scenarios",
            self._scenario_table(valuation, currency),
            "## P/E Valuation Check",
            self._pe_section(valuation, currency),
            "## Fundamental Analysis",
            self._fundamental_analysis_section(fundamentals),
            "## Fundamental Snapshot",
            self._fundamental_table(data),
            "## Key Assumptions",
            self._bullet_list(valuation.assumptions),
            "## Risks And Data Warnings",
            self._risk_section(risk_assessment),
            "## Methodology",
            (
                "FairValue Agent estimates a fair value range using a simple discounted cash flow "
                "model, a rough P/E multiple cross-check, and bear/base/bull scenarios. The final "
                "label compares the current stock price with the estimated fair value range using "
                "a 10% buffer."
            ),
            "## Educational Disclaimer",
            DISCLAIMER,
        ]

        return "\n\n".join(sections) + "\n"

    def _summary_table(self, data: DataAgentResult, valuation: ValuationResult) -> str:
        company = data.company
        currency = company.currency or "USD"
        return "\n".join(
            [
                "| Field | Value |",
                "| --- | --- |",
                f"| Current price | {format_money(company.current_price, currency)} |",
                f"| Estimated fair value range | {format_money(valuation.fair_value_low, currency)} - {format_money(valuation.fair_value_high, currency)} |",
                f"| Valuation label | {valuation.valuation_label} |",
                f"| Confidence | {valuation.confidence} |",
                f"| Market | {company.market} |",
                f"| Sector | {company.sector or 'Unavailable'} |",
                f"| Industry | {company.industry or 'Unavailable'} |",
            ]
        )

    def _scenario_table(self, valuation: ValuationResult, currency: str) -> str:
        rows = [
            "| Scenario | Fair Value/Share | Growth | Discount Rate | Terminal Growth |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for scenario in valuation.scenarios:
            rows.append(
                f"| {scenario.name} | {format_money(scenario.fair_value_per_share, currency)} | "
                f"{format_percent(scenario.growth_rate)} | "
                f"{format_percent(scenario.discount_rate)} | "
                f"{format_percent(scenario.terminal_growth_rate)} |"
            )
        return "\n".join(rows)

    def _pe_section(self, valuation: ValuationResult, currency: str) -> str:
        pe = valuation.pe_valuation
        return "\n".join(
            [
                "| Field | Value |",
                "| --- | --- |",
                f"| P/E multiple range | {pe.low_multiple:.1f}x - {pe.high_multiple:.1f}x |",
                f"| P/E value range | {format_money(pe.low_value_per_share, currency)} - {format_money(pe.high_value_per_share, currency)} |",
                f"| Valid | {'Yes' if pe.is_valid else 'No'} |",
            ]
        )

    def _fundamental_table(self, data: DataAgentResult) -> str:
        company = data.company
        financials = data.financials
        currency = company.currency or "USD"
        return "\n".join(
            [
                "| Metric | Value |",
                "| --- | ---: |",
                f"| Market cap | {format_large_number(company.market_cap, currency)} |",
                f"| Annual revenue | {format_large_number(financials.annual_revenue, currency)} |",
                f"| Net income | {format_large_number(financials.annual_net_income, currency)} |",
                f"| Operating cash flow | {format_large_number(financials.annual_operating_cash_flow, currency)} |",
                f"| Capital expenditure | {format_large_number(financials.annual_capex, currency)} |",
                f"| Free cash flow | {format_large_number(financials.annual_free_cash_flow, currency)} |",
                f"| Total debt | {format_large_number(financials.total_debt, currency)} |",
                f"| Total cash | {format_large_number(financials.total_cash, currency)} |",
                f"| Trailing EPS | {format_money(company.trailing_eps, currency)} |",
                f"| Trailing P/E | {company.trailing_pe:.2f}x |" if company.trailing_pe is not None else "| Trailing P/E | Unavailable |",
            ]
        )

    def _fundamental_analysis_section(self, fundamentals: FundamentalAnalysis) -> str:
        rows = [
            f"Overall fundamental quality: **{fundamentals.overall_quality}**",
            "",
            fundamentals.summary,
            "",
            "| Metric | Value | Interpretation |",
            "| --- | ---: | --- |",
        ]
        for metric in fundamentals.metrics:
            rows.append(f"| {metric.name} | {metric.value} | {metric.interpretation} |")

        rows.extend(["", "Key observations:"])
        rows.extend(f"- {observation}" for observation in fundamentals.observations)
        return "\n".join(rows)

    def _risk_section(self, risk_assessment: RiskAssessment) -> str:
        rows = [
            f"Overall risk: **{risk_assessment.overall_risk}**",
            "",
            risk_assessment.summary,
            "",
            "| Category | Severity | Risk |",
            "| --- | --- | --- |",
        ]
        for risk in risk_assessment.risks:
            rows.append(f"| {risk.category} | {risk.severity} | {risk.message} |")
        return "\n".join(rows)

    def _bullet_list(self, items: list[str]) -> str:
        if not items:
            return "- None."
        return "\n".join(f"- {item}" for item in items)
