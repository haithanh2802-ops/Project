from fairvalue_agent.models import DataAgentResult, ValuationResult
from fairvalue_agent.tools.label_tools import get_valuation_label
from fairvalue_agent.tools.valuation_tools import (
    build_dcf_scenarios,
    calculate_pe_valuation,
    combine_valuation_ranges,
)


class ValuationAgent:
    def run(self, data: DataAgentResult) -> ValuationResult:
        scenarios = build_dcf_scenarios(data.company, data.financials)
        pe_valuation = calculate_pe_valuation(data.company)
        fair_value_low, fair_value_high, confidence, range_warnings = combine_valuation_ranges(
            scenarios, pe_valuation
        )

        valuation_label = get_valuation_label(
            data.company.current_price,
            fair_value_low,
            fair_value_high,
        )

        warnings = list(data.financials.data_quality.warnings)
        warnings.extend(range_warnings)
        for scenario in scenarios:
            warnings.extend(f"{scenario.name} DCF: {warning}" for warning in scenario.warnings)
        warnings.extend(f"P/E valuation: {warning}" for warning in pe_valuation.warnings)

        assumptions = [
            "DCF projects five years of free cash flow and applies a terminal value.",
            "Growth assumptions are capped between -5% and 15%.",
            "Terminal growth is capped between 1.5% and 3.0%.",
            "Discount rates range from 8.5% to 11.0% across scenarios.",
            "When both methods are valid, fair value is weighted 70% DCF and 30% P/E.",
        ]

        return ValuationResult(
            scenarios=scenarios,
            pe_valuation=pe_valuation,
            fair_value_low=fair_value_low,
            fair_value_high=fair_value_high,
            valuation_label=valuation_label,
            confidence=confidence,
            assumptions=assumptions,
            warnings=warnings,
        )
