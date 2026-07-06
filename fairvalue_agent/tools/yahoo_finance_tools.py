from typing import Any
from pathlib import Path

import pandas as pd
import yfinance as yf


QUOTE_CURRENCY_ALIASES = {
    "GBp": ("GBP", 0.01, "Yahoo Finance quotes this listing in pence; prices were converted to GBP."),
}


def _configure_yfinance_cache() -> None:
    cache_dir = Path.cwd() / ".cache" / "yfinance"
    cache_dir.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(cache_dir))
    yf.cache.set_cache_location(str(cache_dir))


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_available(statement: pd.DataFrame, names: list[str]) -> float | None:
    if statement is None or statement.empty:
        return None

    for name in names:
        if name in statement.index and len(statement.columns) > 0:
            return _safe_float(statement.loc[name].iloc[0])
    return None


def _calculate_free_cash_flow(
    operating_cash_flow: float | None,
    capex: float | None,
) -> float | None:
    if operating_cash_flow is None or capex is None:
        return None
    if capex < 0:
        return operating_cash_flow + capex
    return operating_cash_flow - capex


def _latest_close(symbol: str) -> float | None:
    history = yf.Ticker(symbol).history(period="5d", auto_adjust=False)
    if history is None or history.empty or "Close" not in history.columns:
        return None
    return _safe_float(history["Close"].dropna().iloc[-1])


def _fx_rate(from_currency: str | None, to_currency: str | None) -> tuple[float | None, str | None]:
    if not from_currency or not to_currency:
        return None, "Currency conversion was unavailable because a currency code was missing."
    if from_currency == to_currency:
        return 1.0, None

    direct_symbol = f"{from_currency}{to_currency}=X"
    direct_rate = _latest_close(direct_symbol)
    if direct_rate is not None and direct_rate > 0:
        return direct_rate, None

    inverse_symbol = f"{to_currency}{from_currency}=X"
    inverse_rate = _latest_close(inverse_symbol)
    if inverse_rate is not None and inverse_rate > 0:
        return 1 / inverse_rate, None

    return None, f"Could not convert financial statements from {from_currency} to {to_currency}."


def _convert_value(value: float | None, rate: float | None) -> float | None:
    if value is None or rate is None:
        return value
    return value * rate


def _quote_currency_settings(raw_currency: str | None) -> tuple[str | None, float, list[str]]:
    if raw_currency in QUOTE_CURRENCY_ALIASES:
        currency, price_factor, warning = QUOTE_CURRENCY_ALIASES[raw_currency]
        return currency, price_factor, [warning]
    return raw_currency, 1.0, []


def fetch_yahoo_finance_data(ticker: str) -> dict[str, Any]:
    _configure_yfinance_cache()
    stock = yf.Ticker(ticker)
    info = stock.info or {}

    raw_quote_currency = info.get("currency")
    quote_currency, price_factor, warnings = _quote_currency_settings(raw_quote_currency)
    financial_currency = info.get("financialCurrency") or quote_currency

    financials = stock.financials
    cashflow = stock.cashflow
    balance_sheet = stock.balance_sheet

    revenue = _first_available(financials, ["Total Revenue", "Operating Revenue"])
    net_income = _first_available(financials, ["Net Income"])
    operating_cash_flow = _first_available(
        cashflow, ["Operating Cash Flow", "Total Cash From Operating Activities"]
    )
    capex = _first_available(
        cashflow, ["Capital Expenditure", "Capital Expenditures"]
    )
    total_debt = _first_available(balance_sheet, ["Total Debt"])
    total_cash = _first_available(
        balance_sheet, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"]
    )

    free_cash_flow = _calculate_free_cash_flow(operating_cash_flow, capex)
    fx_rate, fx_warning = _fx_rate(financial_currency, quote_currency)
    if fx_warning:
        warnings.append(fx_warning)
    elif fx_rate is not None and fx_rate != 1.0:
        warnings.append(
            f"Financial statements were converted from {financial_currency} to {quote_currency} for valuation."
        )

    revenue = _convert_value(revenue, fx_rate)
    net_income = _convert_value(net_income, fx_rate)
    operating_cash_flow = _convert_value(operating_cash_flow, fx_rate)
    capex = _convert_value(capex, fx_rate)
    free_cash_flow = _convert_value(free_cash_flow, fx_rate)
    total_debt = _convert_value(total_debt, fx_rate)
    total_cash = _convert_value(total_cash, fx_rate)

    current_price = _safe_float(
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("previousClose")
    )
    if current_price is not None:
        current_price *= price_factor

    return {
        "info": info,
        "company": {
            "ticker": ticker,
            "company_name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "current_price": current_price,
            "market_cap": _safe_float(info.get("marketCap")),
            "shares_outstanding": _safe_float(info.get("sharesOutstanding")),
            "trailing_eps": _safe_float(info.get("trailingEps")),
            "trailing_pe": _safe_float(info.get("trailingPE")),
            "currency": quote_currency,
        },
        "financials": {
            "annual_revenue": revenue,
            "annual_net_income": net_income,
            "annual_operating_cash_flow": operating_cash_flow,
            "annual_capex": capex,
            "annual_free_cash_flow": free_cash_flow,
            "total_debt": total_debt,
            "total_cash": total_cash,
            "warnings": warnings,
        },
    }


def fetch_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    _configure_yfinance_cache()
    stock = yf.Ticker(ticker)
    history = stock.history(period=period, auto_adjust=False)
    if history is None or history.empty:
        return pd.DataFrame()

    columns = [column for column in ["Open", "High", "Low", "Close", "Volume"] if column in history.columns]
    return history[columns].dropna(how="all")


def search_yahoo_finance(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    _configure_yfinance_cache()
    search = yf.Search(
        query,
        max_results=max_results,
        news_count=0,
        lists_count=0,
        include_research=False,
        enable_fuzzy_query=True,
    )
    return list(search.quotes or [])
