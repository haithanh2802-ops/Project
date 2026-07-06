from dataclasses import dataclass

from fairvalue_agent.tools.validation_tools import normalize_ticker, validate_ticker


@dataclass(frozen=True)
class MarketConfig:
    code: str
    label: str
    yahoo_suffix: str
    currency_note: str = ""


MARKETS = {
    "US": MarketConfig("US", "United States", ""),
    "CA": MarketConfig("CA", "Canada - Toronto", ".TO"),
    "CA_V": MarketConfig("CA_V", "Canada - TSX Venture", ".V"),
    "VN": MarketConfig("VN", "Vietnam", ".VN", "Yahoo Finance coverage may vary by Vietnamese listing."),
    "CN_SH": MarketConfig("CN_SH", "China - Shanghai", ".SS"),
    "CN_SZ": MarketConfig("CN_SZ", "China - Shenzhen", ".SZ"),
    "HK": MarketConfig("HK", "Hong Kong", ".HK"),
    "JP": MarketConfig("JP", "Japan", ".T"),
    "KR": MarketConfig("KR", "South Korea - KOSPI", ".KS"),
    "KR_KQ": MarketConfig("KR_KQ", "South Korea - KOSDAQ", ".KQ"),
    "TW": MarketConfig("TW", "Taiwan - TWSE", ".TW"),
    "TW_TWO": MarketConfig("TW_TWO", "Taiwan - Taipei Exchange", ".TWO"),
    "SG": MarketConfig("SG", "Singapore", ".SI"),
    "IN_NS": MarketConfig("IN_NS", "India - NSE", ".NS"),
    "IN_BO": MarketConfig("IN_BO", "India - BSE", ".BO"),
    "ID": MarketConfig("ID", "Indonesia", ".JK"),
    "MY": MarketConfig("MY", "Malaysia", ".KL"),
    "TH": MarketConfig("TH", "Thailand", ".BK"),
    "AU": MarketConfig("AU", "Australia", ".AX"),
    "NZ": MarketConfig("NZ", "New Zealand", ".NZ"),
    "UK": MarketConfig("UK", "United Kingdom", ".L", "Some UK quotes may be shown in pence."),
    "FR": MarketConfig("FR", "France", ".PA"),
    "DE": MarketConfig("DE", "Germany", ".DE"),
    "IT": MarketConfig("IT", "Italy", ".MI"),
    "ES": MarketConfig("ES", "Spain", ".MC"),
    "NL": MarketConfig("NL", "Netherlands", ".AS"),
    "BE": MarketConfig("BE", "Belgium", ".BR"),
    "PT": MarketConfig("PT", "Portugal", ".LS"),
    "AT": MarketConfig("AT", "Austria", ".VI"),
    "CH": MarketConfig("CH", "Switzerland", ".SW"),
    "SE": MarketConfig("SE", "Sweden", ".ST"),
    "DK": MarketConfig("DK", "Denmark", ".CO"),
    "FI": MarketConfig("FI", "Finland", ".HE"),
    "NO": MarketConfig("NO", "Norway", ".OL"),
    "PL": MarketConfig("PL", "Poland", ".WA"),
    "GR": MarketConfig("GR", "Greece", ".AT"),
    "IS": MarketConfig("IS", "Iceland", ".IC"),
    "BR": MarketConfig("BR", "Brazil", ".SA"),
    "MX": MarketConfig("MX", "Mexico", ".MX"),
    "AR": MarketConfig("AR", "Argentina", ".BA"),
    "CL": MarketConfig("CL", "Chile", ".SN"),
    "ZA": MarketConfig("ZA", "South Africa", ".JO", "Some South African quotes may be shown in cents."),
    "IL": MarketConfig("IL", "Israel", ".TA"),
    "TR": MarketConfig("TR", "Turkey", ".IS"),
}


SUFFIX_MARKET_CODES = sorted(
    (
        (market.yahoo_suffix, code)
        for code, market in MARKETS.items()
        if market.yahoo_suffix
    ),
    key=lambda item: len(item[0]),
    reverse=True,
)

EXCHANGE_MARKET_CODES = {
    "ASE": "US",
    "NMS": "US",
    "NYQ": "US",
    "PCX": "US",
    "TOR": "CA",
    "VAN": "CA_V",
    "LSE": "UK",
    "LSEIOB": "UK",
    "HKG": "HK",
    "SHH": "CN_SH",
    "SHZ": "CN_SZ",
    "JPX": "JP",
    "KSC": "KR",
    "KOE": "KR_KQ",
    "TAI": "TW",
    "TWO": "TW_TWO",
    "SES": "SG",
    "NSI": "IN_NS",
    "BSE": "IN_BO",
    "JKT": "ID",
    "KLS": "MY",
    "SET": "TH",
    "ASX": "AU",
    "NZE": "NZ",
    "PAR": "FR",
    "GER": "DE",
    "FRA": "DE",
    "MIL": "IT",
    "MCE": "ES",
    "AMS": "NL",
    "BRU": "BE",
    "LIS": "PT",
    "VIE": "AT",
    "SWX": "CH",
    "STO": "SE",
    "CPH": "DK",
    "HEL": "FI",
    "OSL": "NO",
    "WSE": "PL",
    "ATH": "GR",
    "SAO": "BR",
    "MEX": "MX",
    "BUE": "AR",
    "SGO": "CL",
    "JNB": "ZA",
    "TLV": "IL",
    "IST": "TR",
}


def market_choices() -> list[str]:
    return list(MARKETS.keys())


def market_label(code: str) -> str:
    return MARKETS[code].label


def infer_market_code(symbol: str, exchange: str | None = None) -> str | None:
    normalized = normalize_ticker(symbol)

    for suffix, code in SUFFIX_MARKET_CODES:
        if normalized.endswith(suffix):
            return code

    if exchange:
        return EXCHANGE_MARKET_CODES.get(exchange.upper())

    if "." not in normalized:
        return "US"

    return None


def resolve_yahoo_symbol(ticker: str, market_code: str = "US") -> tuple[str, MarketConfig]:
    if market_code not in MARKETS:
        raise ValueError(f"Unsupported market: {market_code}")

    normalized = validate_ticker(ticker)
    market = MARKETS[market_code]

    if "." in normalized:
        return normalized, market

    if market_code == "HK" and normalized.isdigit():
        normalized = normalized.zfill(4)

    return normalize_ticker(normalized + market.yahoo_suffix), market
