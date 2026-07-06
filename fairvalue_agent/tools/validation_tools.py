import re


TICKER_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.-]{0,14}$")


def normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper()


def validate_ticker(ticker: str) -> str:
    normalized = normalize_ticker(ticker)
    if not TICKER_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Ticker must be 1-15 characters and contain only letters, numbers, dots, or hyphens."
        )
    return normalized
