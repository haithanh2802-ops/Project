from fairvalue_agent.models import DataAgentResult, RiskAssessment, RiskItem, ValuationResult


SEVERITY_SCORE = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}


class RiskAgent:
    def run(self, data: DataAgentResult, valuation: ValuationResult) -> RiskAssessment:
        risks = []
        risks.extend(self._data_risks(data))
        risks.extend(self._financial_risks(data))
        risks.extend(self._valuation_risks(data, valuation))
        risks.extend(self._model_risks(valuation))

        if not risks:
            risks.append(
                RiskItem(
                    category="Data Quality",
                    severity="Low",
                    message="No major data-quality or valuation-input risks were detected by the current checks.",
                )
            )

        overall_risk = self._overall_risk(risks)
        summary = self._summary(overall_risk, risks)
        return RiskAssessment(overall_risk=overall_risk, risks=risks, summary=summary)

    def _data_risks(self, data: DataAgentResult) -> list[RiskItem]:
        quality = data.financials.data_quality
        risks = []

        if quality.missing_required:
            risks.append(
                RiskItem(
                    category="Data Quality",
                    severity="High",
                    message="Required data is missing: " + ", ".join(quality.missing_required) + ".",
                )
            )

        if quality.missing_optional:
            risks.append(
                RiskItem(
                    category="Data Quality",
                    severity="Medium",
                    message="Optional data is missing: " + ", ".join(quality.missing_optional) + ".",
                )
            )

        for warning in quality.warnings:
            risks.append(
                RiskItem(category="Data Quality", severity="Medium", message=warning)
            )

        return risks

    def _financial_risks(self, data: DataAgentResult) -> list[RiskItem]:
        financials = data.financials
        risks = []

        if financials.annual_free_cash_flow is not None and financials.annual_free_cash_flow <= 0:
            risks.append(
                RiskItem(
                    category="Financial Health",
                    severity="High",
                    message="Free cash flow is negative or zero, which weakens DCF reliability.",
                )
            )

        if financials.annual_net_income is not None and financials.annual_net_income <= 0:
            risks.append(
                RiskItem(
                    category="Financial Health",
                    severity="High",
                    message="Net income is negative or zero, which may make earnings-based valuation unreliable.",
                )
            )

        if (
            financials.total_debt is not None
            and financials.total_cash is not None
            and financials.total_debt > financials.total_cash * 3
        ):
            risks.append(
                RiskItem(
                    category="Financial Health",
                    severity="Medium",
                    message="Total debt is more than three times cash, so leverage should be reviewed carefully.",
                )
            )

        if (
            financials.annual_operating_cash_flow is not None
            and financials.annual_net_income is not None
            and financials.annual_net_income > 0
            and financials.annual_operating_cash_flow < financials.annual_net_income * 0.7
        ):
            risks.append(
                RiskItem(
                    category="Financial Health",
                    severity="Medium",
                    message="Operating cash flow is meaningfully below net income, which may indicate lower earnings quality.",
                )
            )

        return risks

    def _valuation_risks(
        self,
        data: DataAgentResult,
        valuation: ValuationResult,
    ) -> list[RiskItem]:
        company = data.company
        risks = []

        if valuation.valuation_label == "Overvalued":
            risks.append(
                RiskItem(
                    category="Valuation",
                    severity="Medium",
                    message="The current price is above the estimated fair value range after the 10% buffer.",
                )
            )
        elif valuation.valuation_label == "Insufficient Data":
            risks.append(
                RiskItem(
                    category="Valuation",
                    severity="High",
                    message="The system could not produce a reliable valuation label from available data.",
                )
            )

        if company.trailing_pe is not None and company.trailing_pe > 35:
            risks.append(
                RiskItem(
                    category="Valuation",
                    severity="Medium",
                    message="Trailing P/E is above 35x, so the stock may be sensitive to growth assumptions.",
                )
            )

        if valuation.confidence == "Low":
            risks.append(
                RiskItem(
                    category="Valuation",
                    severity="High",
                    message="Valuation confidence is low because one or more core valuation methods were unavailable.",
                )
            )

        return risks

    def _model_risks(self, valuation: ValuationResult) -> list[RiskItem]:
        risks = []
        for warning in valuation.warnings:
            risks.append(RiskItem(category="Model", severity="Medium", message=warning))
        return risks

    def _overall_risk(self, risks: list[RiskItem]) -> str:
        highest_score = max(SEVERITY_SCORE.get(risk.severity, 1) for risk in risks)
        for severity, score in SEVERITY_SCORE.items():
            if score == highest_score:
                return severity
        return "Low"

    def _summary(self, overall_risk: str, risks: list[RiskItem]) -> str:
        high_count = sum(1 for risk in risks if risk.severity == "High")
        medium_count = sum(1 for risk in risks if risk.severity == "Medium")
        low_count = sum(1 for risk in risks if risk.severity == "Low")
        return (
            f"Overall risk is {overall_risk}. "
            f"Detected {high_count} high, {medium_count} medium, and {low_count} low risk item(s)."
        )
