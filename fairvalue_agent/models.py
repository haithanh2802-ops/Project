from dataclasses import dataclass, field
from typing import Any


@dataclass
class DataQualityResult:
    is_usable: bool
    missing_required: list[str] = field(default_factory=list)
    missing_optional: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class CompanyData:
    ticker: str
    input_ticker: str
    market: str
    company_name: str | None
    sector: str | None
    industry: str | None
    current_price: float | None
    market_cap: float | None
    shares_outstanding: float | None
    trailing_eps: float | None
    trailing_pe: float | None
    currency: str | None
    raw_info: dict[str, Any] = field(default_factory=dict)


@dataclass
class FinancialSnapshot:
    annual_revenue: float | None
    annual_net_income: float | None
    annual_operating_cash_flow: float | None
    annual_capex: float | None
    annual_free_cash_flow: float | None
    total_debt: float | None
    total_cash: float | None
    data_quality: DataQualityResult


@dataclass
class DataAgentResult:
    company: CompanyData
    financials: FinancialSnapshot


@dataclass
class DiscoveryCandidate:
    symbol: str
    name: str | None
    quote_type: str | None
    exchange: str | None
    exchange_name: str | None
    market_code: str | None
    sector: str | None
    industry: str | None
    score: float | None = None


@dataclass
class DiscoveryResult:
    query: str
    candidates: list[DiscoveryCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class FundamentalMetric:
    name: str
    value: str
    interpretation: str


@dataclass
class FundamentalAnalysis:
    overall_quality: str
    summary: str
    metrics: list[FundamentalMetric] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)


@dataclass
class ValuationScenario:
    name: str
    growth_rate: float
    discount_rate: float
    terminal_growth_rate: float
    fair_value_per_share: float | None
    is_valid: bool
    warnings: list[str] = field(default_factory=list)


@dataclass
class PeValuation:
    low_multiple: float
    high_multiple: float
    low_value_per_share: float | None
    high_value_per_share: float | None
    is_valid: bool
    warnings: list[str] = field(default_factory=list)


@dataclass
class ValuationResult:
    scenarios: list[ValuationScenario]
    pe_valuation: PeValuation
    fair_value_low: float | None
    fair_value_high: float | None
    valuation_label: str
    confidence: str
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class RiskItem:
    category: str
    severity: str
    message: str


@dataclass
class RiskAssessment:
    overall_risk: str
    risks: list[RiskItem] = field(default_factory=list)
    summary: str = ""


@dataclass
class ReportResult:
    ticker: str
    markdown: str
    output_path: str | None = None
