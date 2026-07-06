def get_valuation_label(
    current_price: float | None,
    fair_value_low: float | None,
    fair_value_high: float | None,
) -> str:
    if current_price is None or fair_value_low is None or fair_value_high is None:
        return "Insufficient Data"

    if fair_value_low <= 0 or fair_value_high <= 0 or fair_value_low > fair_value_high:
        return "Insufficient Data"

    if current_price < fair_value_low * 0.90:
        return "Undervalued"
    if current_price > fair_value_high * 1.10:
        return "Overvalued"
    return "Fairly Valued"
