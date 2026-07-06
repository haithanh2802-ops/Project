from fairvalue_agent.models import CompanyData, DataAgentResult, DataQualityResult, FinancialSnapshot
from fairvalue_agent.tools.market_tools import resolve_yahoo_symbol
from fairvalue_agent.tools.yahoo_finance_tools import fetch_yahoo_finance_data


REQUIRED_FIELDS = {
    "current_price": "current stock price",
    "shares_outstanding": "shares outstanding",
}

OPTIONAL_FIELDS = {
    "annual_revenue": "annual revenue",
    "annual_net_income": "annual net income",
    "annual_operating_cash_flow": "annual operating cash flow",
    "annual_capex": "capital expenditure",
    "annual_free_cash_flow": "free cash flow",
    "total_debt": "total debt",
    "total_cash": "total cash",
    "trailing_eps": "trailing EPS",
    "trailing_pe": "trailing P/E",
}


class DataAgent:
    def run(self, ticker: str, market: str = "US") -> DataAgentResult:
        yahoo_symbol, market_config = resolve_yahoo_symbol(ticker, market)
        raw = fetch_yahoo_finance_data(yahoo_symbol)

        company_payload = raw["company"]
        financial_payload = raw["financials"]

        missing_required = [
            label
            for field_name, label in REQUIRED_FIELDS.items()
            if company_payload.get(field_name) is None
        ]
        missing_optional = [
            label
            for field_name, label in OPTIONAL_FIELDS.items()
            if company_payload.get(field_name) is None and financial_payload.get(field_name) is None
        ]

        warnings = list(financial_payload.get("warnings", []))
        if financial_payload.get("annual_free_cash_flow") is None:
            warnings.append("Free cash flow is unavailable, so DCF valuation may be unreliable.")
        elif financial_payload["annual_free_cash_flow"] <= 0:
            warnings.append("Free cash flow is negative, so DCF valuation should be treated cautiously.")

        if not company_payload.get("company_name"):
            warnings.append("Company name was not returned by Yahoo Finance.")

        data_quality = DataQualityResult(
            is_usable=len(missing_required) == 0,
            missing_required=missing_required,
            missing_optional=missing_optional,
            warnings=warnings,
        )

        company = CompanyData(
            ticker=company_payload["ticker"],
            input_ticker=ticker.strip().upper(),
            market=market_config.label,
            company_name=company_payload.get("company_name"),
            sector=company_payload.get("sector"),
            industry=company_payload.get("industry"),
            current_price=company_payload.get("current_price"),
            market_cap=company_payload.get("market_cap"),
            shares_outstanding=company_payload.get("shares_outstanding"),
            trailing_eps=company_payload.get("trailing_eps"),
            trailing_pe=company_payload.get("trailing_pe"),
            currency=company_payload.get("currency"),
            raw_info=raw["info"],
        )
        financials = FinancialSnapshot(
            annual_revenue=financial_payload.get("annual_revenue"),
            annual_net_income=financial_payload.get("annual_net_income"),
            annual_operating_cash_flow=financial_payload.get("annual_operating_cash_flow"),
            annual_capex=financial_payload.get("annual_capex"),
            annual_free_cash_flow=financial_payload.get("annual_free_cash_flow"),
            total_debt=financial_payload.get("total_debt"),
            total_cash=financial_payload.get("total_cash"),
            data_quality=data_quality,
        )

        return DataAgentResult(company=company, financials=financials)
