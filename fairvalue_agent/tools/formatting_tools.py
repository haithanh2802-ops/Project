def format_money(value: float | None, currency: str | None = "USD") -> str:
    if value is None:
        return "Unavailable"
    return f"{currency or 'USD'} {value:,.2f}"


def format_large_number(value: float | None, currency: str | None = "USD") -> str:
    if value is None:
        return "Unavailable"

    abs_value = abs(value)
    if abs_value >= 1_000_000_000_000:
        return f"{currency or 'USD'} {value / 1_000_000_000_000:,.2f}T"
    if abs_value >= 1_000_000_000:
        return f"{currency or 'USD'} {value / 1_000_000_000:,.2f}B"
    if abs_value >= 1_000_000:
        return f"{currency or 'USD'} {value / 1_000_000:,.2f}M"
    return format_money(value, currency)


def format_percent(value: float | None) -> str:
    if value is None:
        return "Unavailable"
    return f"{value * 100:.1f}%"
