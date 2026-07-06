import unittest
from unittest.mock import patch

from fairvalue_agent.agents.discovery_agent import DiscoveryAgent
from fairvalue_agent.models import CompanyData
from fairvalue_agent.tools.label_tools import get_valuation_label
from fairvalue_agent.tools.market_tools import infer_market_code, resolve_yahoo_symbol
from fairvalue_agent.tools.valuation_tools import (
    calculate_dcf_value,
    calculate_pe_valuation,
    estimate_base_growth,
)
from fairvalue_agent.tools.yahoo_finance_tools import (
    _calculate_free_cash_flow,
    _convert_value,
    _quote_currency_settings,
)


class MarketToolTests(unittest.TestCase):
    def test_numeric_hong_kong_ticker_is_padded(self):
        symbol, market = resolve_yahoo_symbol("700", "HK")

        self.assertEqual(symbol, "0700.HK")
        self.assertEqual(market.code, "HK")

    def test_market_inference_from_suffix_and_exchange(self):
        self.assertEqual(infer_market_code("HSBA.L", "LSE"), "UK")
        self.assertEqual(infer_market_code("0005.HK", "HKG"), "HK")
        self.assertEqual(infer_market_code("AAPL", "NMS"), "US")


class CurrencyToolTests(unittest.TestCase):
    def test_london_pence_quote_settings(self):
        currency, price_factor, warnings = _quote_currency_settings("GBp")

        self.assertEqual(currency, "GBP")
        self.assertEqual(price_factor, 0.01)
        self.assertTrue(warnings)

    def test_free_cash_flow_handles_capex_sign(self):
        self.assertEqual(_calculate_free_cash_flow(100.0, -20.0), 80.0)
        self.assertEqual(_calculate_free_cash_flow(100.0, 20.0), 80.0)

    def test_convert_value_keeps_missing_values(self):
        self.assertIsNone(_convert_value(None, 0.8))
        self.assertEqual(_convert_value(100.0, None), 100.0)
        self.assertEqual(_convert_value(100.0, 0.8), 80.0)


class ValuationToolTests(unittest.TestCase):
    def test_dcf_returns_per_share_value_for_valid_inputs(self):
        value, warnings = calculate_dcf_value(
            free_cash_flow=100.0,
            shares_outstanding=10.0,
            total_debt=0.0,
            total_cash=0.0,
            growth_rate=0.03,
            discount_rate=0.10,
            terminal_growth_rate=0.02,
        )

        self.assertIsNotNone(value)
        self.assertGreater(value, 0)
        self.assertEqual(warnings, [])

    def test_dcf_rejects_invalid_inputs(self):
        value, warnings = calculate_dcf_value(
            free_cash_flow=-1.0,
            shares_outstanding=10.0,
            total_debt=0.0,
            total_cash=0.0,
            growth_rate=0.03,
            discount_rate=0.10,
            terminal_growth_rate=0.02,
        )

        self.assertIsNone(value)
        self.assertIn("Free cash flow is negative or zero.", warnings)

    def test_growth_estimate_is_capped(self):
        company = CompanyData(
            ticker="TEST",
            input_ticker="TEST",
            market="United States",
            company_name="Test Co",
            sector="Technology",
            industry="Software",
            current_price=100.0,
            market_cap=None,
            shares_outstanding=100.0,
            trailing_eps=5.0,
            trailing_pe=20.0,
            currency="USD",
            raw_info={"revenueGrowth": 1.0},
        )

        self.assertEqual(estimate_base_growth(company), 0.15)

    def test_pe_valuation_uses_sector_range(self):
        company = CompanyData(
            ticker="TEST",
            input_ticker="TEST",
            market="United States",
            company_name="Test Co",
            sector="Technology",
            industry="Software",
            current_price=100.0,
            market_cap=None,
            shares_outstanding=100.0,
            trailing_eps=5.0,
            trailing_pe=20.0,
            currency="USD",
        )

        result = calculate_pe_valuation(company)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.low_value_per_share, 90.0)
        self.assertEqual(result.high_value_per_share, 140.0)


class LabelToolTests(unittest.TestCase):
    def test_valuation_label_thresholds(self):
        self.assertEqual(get_valuation_label(80.0, 100.0, 120.0), "Undervalued")
        self.assertEqual(get_valuation_label(140.0, 100.0, 120.0), "Overvalued")
        self.assertEqual(get_valuation_label(110.0, 100.0, 120.0), "Fairly Valued")
        self.assertEqual(get_valuation_label(None, 100.0, 120.0), "Insufficient Data")


class DiscoveryAgentTests(unittest.TestCase):
    @patch("fairvalue_agent.agents.discovery_agent.search_yahoo_finance")
    def test_discovery_filters_equities_and_prefers_market(self, mock_search):
        mock_search.return_value = [
            {
                "symbol": "HSBC",
                "quoteType": "EQUITY",
                "exchange": "NYQ",
                "exchDisp": "NYSE",
                "longname": "HSBC Holdings plc",
                "sectorDisp": "Financial Services",
                "industryDisp": "Banks",
                "score": 100.0,
            },
            {
                "symbol": "HSBA.L",
                "quoteType": "EQUITY",
                "exchange": "LSE",
                "exchDisp": "London",
                "longname": "HSBC Holdings plc",
                "sectorDisp": "Financial Services",
                "industryDisp": "Banks",
                "score": 50.0,
            },
            {
                "symbol": "HSBCETF",
                "quoteType": "ETF",
                "exchange": "NYQ",
                "score": 1000.0,
            },
        ]

        result = DiscoveryAgent().run("HSBC", preferred_market="UK")

        self.assertEqual([candidate.symbol for candidate in result.candidates], ["HSBA.L", "HSBC"])
        self.assertEqual(result.candidates[0].market_code, "UK")


if __name__ == "__main__":
    unittest.main()
