from fairvalue_agent.models import CompanyData, FinancialSnapshot, PeValuation, ValuationScenario


GROWTH_MIN = -0.05
GROWTH_MAX = 0.15

SECTOR_PE_RANGES = {
    "Technology": (18.0, 28.0),
    "Consumer Defensive": (16.0, 24.0),
    "Consumer Cyclical": (12.0, 22.0),
    "Financial Services": (9.0, 15.0),
    "Healthcare": (15.0, 24.0),
    "Industrials": (14.0, 22.0),
    "Utilities": (12.0, 18.0),
    "Energy": (8.0, 14.0),
    "Communication Services": (14.0, 24.0),
}

DEFAULT_PE_RANGE = (12.0, 22.0)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def estimate_base_growth(company: CompanyData) -> float:
    raw_info = company.raw_info or {}
    candidates = [
        raw_info.get("revenueGrowth"),
        raw_info.get("earningsGrowth"),
        raw_info.get("earningsQuarterlyGrowth"),
    ]

    usable = [float(value) for value in candidates if isinstance(value, (int, float))]
    if not usable:
        return 0.04

    return clamp(sum(usable) / len(usable), GROWTH_MIN, GROWTH_MAX)


def calculate_dcf_value(
    free_cash_flow: float | None,
    shares_outstanding: float | None,
    total_debt: float | None,
    total_cash: float | None,
    growth_rate: float,
    discount_rate: float,
    terminal_growth_rate: float,
    years: int = 5,
) -> tuple[float | None, list[str]]:
    warnings = []

    if free_cash_flow is None:
        return None, ["Free cash flow is unavailable."]
    if free_cash_flow <= 0:
        return None, ["Free cash flow is negative or zero."]
    if shares_outstanding is None or shares_outstanding <= 0:
        return None, ["Shares outstanding is unavailable."]
    if terminal_growth_rate >= discount_rate:
        return None, ["Terminal growth rate must be lower than discount rate."]

    present_value = 0.0
    projected_fcf = free_cash_flow
    for year in range(1, years + 1):
        projected_fcf *= 1 + growth_rate
        present_value += projected_fcf / ((1 + discount_rate) ** year)

    terminal_value = projected_fcf * (1 + terminal_growth_rate) / (
        discount_rate - terminal_growth_rate
    )
    present_value += terminal_value / ((1 + discount_rate) ** years)

    equity_value = present_value - (total_debt or 0.0) + (total_cash or 0.0)
    if equity_value <= 0:
        warnings.append("Estimated equity value is negative after debt and cash adjustment.")
        return None, warnings

    return equity_value / shares_outstanding, warnings


def build_dcf_scenarios(
    company: CompanyData,
    financials: FinancialSnapshot,
) -> list[ValuationScenario]:
    base_growth = estimate_base_growth(company)
    scenario_inputs = [
        ("Bear", clamp(base_growth - 0.03, GROWTH_MIN, GROWTH_MAX), 0.11, 0.015),
        ("Base", base_growth, 0.095, 0.025),
        ("Bull", clamp(base_growth + 0.03, GROWTH_MIN, GROWTH_MAX), 0.085, 0.03),
    ]

    scenarios = []
    for name, growth_rate, discount_rate, terminal_growth_rate in scenario_inputs:
        value, warnings = calculate_dcf_value(
            free_cash_flow=financials.annual_free_cash_flow,
            shares_outstanding=company.shares_outstanding,
            total_debt=financials.total_debt,
            total_cash=financials.total_cash,
            growth_rate=growth_rate,
            discount_rate=discount_rate,
            terminal_growth_rate=terminal_growth_rate,
        )
        scenarios.append(
            ValuationScenario(
                name=name,
                growth_rate=growth_rate,
                discount_rate=discount_rate,
                terminal_growth_rate=terminal_growth_rate,
                fair_value_per_share=value,
                is_valid=value is not None,
                warnings=warnings,
            )
        )

    return scenarios


def calculate_pe_valuation(company: CompanyData) -> PeValuation:
    low_multiple, high_multiple = SECTOR_PE_RANGES.get(
        company.sector or "", DEFAULT_PE_RANGE
    )

    warnings = []
    if company.trailing_eps is None:
        return PeValuation(
            low_multiple=low_multiple,
            high_multiple=high_multiple,
            low_value_per_share=None,
            high_value_per_share=None,
            is_valid=False,
            warnings=["Trailing EPS is unavailable."],
        )
    if company.trailing_eps <= 0:
        return PeValuation(
            low_multiple=low_multiple,
            high_multiple=high_multiple,
            low_value_per_share=None,
            high_value_per_share=None,
            is_valid=False,
            warnings=["Trailing EPS is negative or zero."],
        )

    if company.sector not in SECTOR_PE_RANGES:
        warnings.append("Using default P/E range because sector-specific range is unavailable.")

    return PeValuation(
        low_multiple=low_multiple,
        high_multiple=high_multiple,
        low_value_per_share=company.trailing_eps * low_multiple,
        high_value_per_share=company.trailing_eps * high_multiple,
        is_valid=True,
        warnings=warnings,
    )


def combine_valuation_ranges(
    scenarios: list[ValuationScenario],
    pe_valuation: PeValuation,
) -> tuple[float | None, float | None, str, list[str]]:
    warnings = []
    valid_dcf_values = [
        scenario.fair_value_per_share
        for scenario in scenarios
        if scenario.is_valid and scenario.fair_value_per_share is not None
    ]

    dcf_low = min(valid_dcf_values) if valid_dcf_values else None
    dcf_high = max(valid_dcf_values) if valid_dcf_values else None
    pe_low = pe_valuation.low_value_per_share if pe_valuation.is_valid else None
    pe_high = pe_valuation.high_value_per_share if pe_valuation.is_valid else None

    if dcf_low is not None and dcf_high is not None and pe_low is not None and pe_high is not None:
        return (
            (dcf_low * 0.70) + (pe_low * 0.30),
            (dcf_high * 0.70) + (pe_high * 0.30),
            "Medium",
            warnings,
        )

    if dcf_low is not None and dcf_high is not None:
        warnings.append("P/E valuation was unavailable, so fair value uses DCF scenarios only.")
        return dcf_low, dcf_high, "Medium", warnings

    if pe_low is not None and pe_high is not None:
        warnings.append("DCF valuation was unavailable, so fair value uses P/E valuation only.")
        return pe_low, pe_high, "Low", warnings

    warnings.append("Both DCF and P/E valuation were unavailable.")
    return None, None, "Low", warnings
