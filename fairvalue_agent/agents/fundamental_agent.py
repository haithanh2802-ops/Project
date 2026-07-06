from fairvalue_agent.models import DataAgentResult, FundamentalAnalysis, FundamentalMetric
from fairvalue_agent.tools.formatting_tools import format_percent


class FundamentalAnalysisAgent:
    def run(self, data: DataAgentResult) -> FundamentalAnalysis:
        financials = data.financials
        metrics = []
        observations = []
        score = 0
        possible_score = 0

        net_margin = self._safe_ratio(financials.annual_net_income, financials.annual_revenue)
        if net_margin is not None:
            possible_score += 1
            if net_margin >= 0.15:
                score += 1
                interpretation = "Strong profitability."
            elif net_margin >= 0.05:
                interpretation = "Moderate profitability."
            else:
                interpretation = "Thin profitability."
            metrics.append(FundamentalMetric("Net margin", format_percent(net_margin), interpretation))
            observations.append(f"Net margin is {format_percent(net_margin)}, which suggests {interpretation.lower()}")

        fcf_margin = self._safe_ratio(financials.annual_free_cash_flow, financials.annual_revenue)
        if fcf_margin is not None:
            possible_score += 1
            if fcf_margin >= 0.10:
                score += 1
                interpretation = "Strong free cash flow generation."
            elif fcf_margin >= 0.03:
                interpretation = "Acceptable free cash flow generation."
            else:
                interpretation = "Weak free cash flow generation."
            metrics.append(FundamentalMetric("Free cash flow margin", format_percent(fcf_margin), interpretation))
            observations.append(
                f"Free cash flow margin is {format_percent(fcf_margin)}, which indicates {interpretation.lower()}"
            )

        cash_conversion = self._safe_ratio(
            financials.annual_operating_cash_flow,
            financials.annual_net_income,
        )
        if cash_conversion is not None and financials.annual_net_income and financials.annual_net_income > 0:
            possible_score += 1
            if cash_conversion >= 0.98:
                score += 1
                interpretation = "Cash flow supports reported earnings."
            elif cash_conversion >= 0.7:
                interpretation = "Cash flow is somewhat below reported earnings."
            else:
                interpretation = "Cash flow is weak compared with reported earnings."
            metrics.append(
                FundamentalMetric("Operating cash flow / net income", f"{cash_conversion:.2f}x", interpretation)
            )
            observations.append(interpretation)

        debt_to_fcf = self._safe_ratio(financials.total_debt, financials.annual_free_cash_flow)
        if debt_to_fcf is not None and financials.annual_free_cash_flow and financials.annual_free_cash_flow > 0:
            possible_score += 1
            if debt_to_fcf <= 2.5:
                score += 1
                interpretation = "Debt appears manageable relative to free cash flow."
            elif debt_to_fcf <= 5.0:
                interpretation = "Debt is noticeable but not extreme relative to free cash flow."
            else:
                interpretation = "Debt is high relative to free cash flow."
            metrics.append(FundamentalMetric("Debt / free cash flow", f"{debt_to_fcf:.2f}x", interpretation))
            observations.append(interpretation)

        cash_to_debt = self._safe_ratio(financials.total_cash, financials.total_debt)
        if cash_to_debt is not None and financials.total_debt and financials.total_debt > 0:
            metrics.append(
                FundamentalMetric(
                    "Cash / debt",
                    f"{cash_to_debt:.2f}x",
                    "Higher values indicate more balance-sheet flexibility.",
                )
            )

        overall_quality = self._quality_label(score, possible_score)
        summary = self._summary(overall_quality, data, possible_score)

        if not observations:
            observations.append("Not enough financial statement data was available for a reliable fundamental summary.")

        return FundamentalAnalysis(
            overall_quality=overall_quality,
            summary=summary,
            metrics=metrics,
            observations=observations,
        )

    def _safe_ratio(self, numerator: float | None, denominator: float | None) -> float | None:
        if numerator is None or denominator is None or denominator == 0:
            return None
        return numerator / denominator

    def _quality_label(self, score: int, possible_score: int) -> str:
        if possible_score == 0:
            return "Insufficient Data"

        ratio = score / possible_score
        if ratio >= 0.75:
            return "Strong"
        if ratio >= 0.40:
            return "Mixed"
        return "Weak"

    def _summary(self, overall_quality: str, data: DataAgentResult, possible_score: int) -> str:
        company_name = data.company.company_name or data.company.ticker
        if possible_score == 0:
            return f"{company_name} does not have enough available financial data for a reliable fundamental read."
        return f"{company_name} has a {overall_quality.lower()} fundamental profile based on the available profitability, cash-flow, and leverage checks."
