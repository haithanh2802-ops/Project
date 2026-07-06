from pathlib import Path
import subprocess
import sys

import streamlit as st

from fairvalue_agent.agents.data_agent import DataAgent
from fairvalue_agent.agents.discovery_agent import DiscoveryAgent
from fairvalue_agent.agents.fundamental_agent import FundamentalAnalysisAgent
from fairvalue_agent.agents.report_agent import ReportAgent
from fairvalue_agent.agents.risk_agent import RiskAgent
from fairvalue_agent.agents.valuation_agent import ValuationAgent
from fairvalue_agent.tools.formatting_tools import format_large_number, format_money, format_percent
from fairvalue_agent.tools.market_tools import MARKETS, market_choices, market_label
from fairvalue_agent.tools.validation_tools import normalize_ticker, validate_ticker
from fairvalue_agent.tools.yahoo_finance_tools import fetch_price_history


def running_inside_streamlit() -> bool:
    # Detect whether Streamlit is already running this script.
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except ImportError:
        return False
    return get_script_run_ctx(suppress_warning=True) is not None


def launch_streamlit_when_run_as_script() -> None:
    # Let users run the web app with `python app.py`, not only `streamlit run app.py`.
    if __name__ == "__main__" and not running_inside_streamlit():
        script_path = Path(__file__).resolve()
        command = [sys.executable, "-m", "streamlit", "run", str(script_path)]
        raise SystemExit(subprocess.call(command))


launch_streamlit_when_run_as_script()


# Configure the browser page before rendering any Streamlit widgets.
st.set_page_config(page_title="FairValue Agent", page_icon="chart_with_upwards_trend", layout="wide")


@st.cache_data(ttl=900, show_spinner=False)
def run_discovery(query: str, preferred_market: str | None = None):
    # Search Yahoo Finance for possible listings when the user does not know the ticker.
    return DiscoveryAgent().run(query, preferred_market=preferred_market)


@st.cache_data(ttl=900, show_spinner=False)
def run_analysis(ticker: str, market: str):
    # Run the full five-agent analysis pipeline and cache results for 15 minutes.
    data_result = DataAgent().run(ticker, market=market)
    fundamentals = FundamentalAnalysisAgent().run(data_result)
    valuation = ValuationAgent().run(data_result)
    risk_assessment = RiskAgent().run(data_result, valuation)
    report = ReportAgent().run(
        data_result,
        fundamentals,
        valuation,
        risk_assessment,
        output_dir="reports",
    )
    return data_result, fundamentals, valuation, risk_assessment, report


@st.cache_data(ttl=900, show_spinner=False)
def run_price_history(yahoo_symbol: str, period: str):
    # Cache price history separately because the chart period can change.
    return fetch_price_history(yahoo_symbol, period=period)


def status_badge(label: str) -> str:
    # Convert result labels into small colored HTML badges for quick scanning.
    colors = {
        "Undervalued": "#0f766e",
        "Fairly Valued": "#475569",
        "Overvalued": "#b91c1c",
        "Insufficient Data": "#92400e",
        "Strong": "#0f766e",
        "Mixed": "#92400e",
        "Weak": "#b91c1c",
        "Low": "#0f766e",
        "Medium": "#92400e",
        "High": "#b91c1c",
    }
    color = colors.get(label, "#475569")
    return (
        f"<span style='background:{color};color:white;padding:0.2rem 0.55rem;"
        f"border-radius:6px;font-size:0.85rem;font-weight:600'>{label}</span>"
    )


def show_scenario_table(valuation, currency: str) -> None:
    # Display bear/base/bull DCF assumptions and fair value estimates.
    rows = []
    for scenario in valuation.scenarios:
        rows.append(
            {
                "Scenario": scenario.name,
                "Fair Value/Share": format_money(scenario.fair_value_per_share, currency),
                "Growth": format_percent(scenario.growth_rate),
                "Discount Rate": format_percent(scenario.discount_rate),
                "Terminal Growth": format_percent(scenario.terminal_growth_rate),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)


def show_fundamental_metrics(fundamentals) -> None:
    # Display profitability, cash-flow, and leverage checks.
    rows = [
        {
            "Metric": metric.name,
            "Value": metric.value,
            "Interpretation": metric.interpretation,
        }
        for metric in fundamentals.metrics
    ]
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    for observation in fundamentals.observations:
        st.write(f"- {observation}")


def show_risk_table(risk_assessment) -> None:
    # Display structured risks from data quality, financial health, valuation, and model checks.
    rows = [
        {
            "Category": risk.category,
            "Severity": risk.severity,
            "Risk": risk.message,
        }
        for risk in risk_assessment.risks
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def normalize_price_history_units(price_history, raw_currency: str | None):
    # London prices come from Yahoo in pence, while the valuation display uses GBP.
    if raw_currency != "GBp" or price_history is None or price_history.empty:
        return price_history

    normalized = price_history.copy()
    for column in ["Open", "High", "Low", "Close"]:
        if column in normalized.columns:
            normalized[column] = normalized[column] * 0.01
    return normalized


def discovery_option_label(candidate) -> str:
    market = candidate.market_code or "Unknown market"
    exchange = candidate.exchange_name or candidate.exchange or "Unknown exchange"
    name = candidate.name or "Unnamed listing"
    sector = candidate.sector or "Sector unavailable"
    return f"{candidate.symbol} | {market} | {exchange} | {name} | {sector}"


st.title("FairValue Agent")
st.caption("Educational fundamental valuation assistant for supported stock markets.")

# Store default inputs in session state so reruns keep the latest user selection.
if "analysis_ticker" not in st.session_state:
    st.session_state.analysis_ticker = "AAPL"
if "analysis_market" not in st.session_state:
    st.session_state.analysis_market = "US"

# Sidebar form collects the ticker, market, and chart period.
with st.sidebar:
    st.header("Find ticker")
    with st.form("discovery_form"):
        discovery_query = st.text_input(
            "Company, ticker, sector, or market",
            placeholder="Example: HSBC, Toyota, semiconductors",
        )
        discovery_market = st.selectbox(
            "Prefer market",
            options=["Any"] + market_choices(),
            format_func=lambda code: "Any market" if code == "Any" else market_label(code),
        )
        discover = st.form_submit_button("Search", use_container_width=True)

    if discover:
        preferred_market = None if discovery_market == "Any" else discovery_market
        st.session_state.discovery_result = run_discovery(discovery_query, preferred_market)

    discovery_result = st.session_state.get("discovery_result")
    if discovery_result is not None:
        for warning in discovery_result.warnings:
            st.warning(warning)

        if discovery_result.candidates:
            selected_candidate = st.selectbox(
                "Matching listings",
                options=discovery_result.candidates,
                format_func=discovery_option_label,
            )
            if st.button("Use selected listing", use_container_width=True):
                st.session_state.analysis_ticker = selected_candidate.symbol
                st.session_state.analysis_market = selected_candidate.market_code or "US"
                st.rerun()

    st.divider()
    st.header("Analyze")
    with st.form("analysis_form"):
        market_options = market_choices()
        market_index = (
            market_options.index(st.session_state.analysis_market)
            if st.session_state.analysis_market in market_options
            else market_options.index("US")
        )
        ticker_input = st.text_input(
            "Stock ticker",
            value=st.session_state.analysis_ticker,
            max_chars=15,
        )
        market_input = st.selectbox(
            "Market",
            options=market_options,
            format_func=market_label,
            index=market_index,
        )
        period_input = st.selectbox(
            "Price history",
            options=["6mo", "1y", "2y", "5y"],
            index=1,
        )
        analyze = st.form_submit_button("Analyze", type="primary", use_container_width=True)
    st.divider()
    st.caption(
        "This tool uses public Yahoo Finance data and simple assumption-based valuation models."
    )

# Update session state only after the user submits the form.
if analyze:
    st.session_state.analysis_ticker = normalize_ticker(ticker_input)
    st.session_state.analysis_market = market_input
    st.session_state.history_period = period_input
elif "history_period" not in st.session_state:
    st.session_state.history_period = period_input

ticker = st.session_state.analysis_ticker
market = st.session_state.analysis_market
history_period = st.session_state.history_period

# Validate ticker format before making any Yahoo Finance request.
try:
    validated_ticker = validate_ticker(ticker)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

# Run the analysis and stop cleanly if data fetching or valuation fails.
try:
    with st.spinner(f"Analyzing {validated_ticker}..."):
        data_result, fundamentals, valuation, risk_assessment, report = run_analysis(
            validated_ticker,
            market,
        )
except Exception as exc:
    st.error(f"Analysis failed: {exc}")
    st.stop()

company = data_result.company
financials = data_result.financials
quality = financials.data_quality
currency = company.currency or "USD"

# Header area identifies the company and market returned by Yahoo Finance.
st.subheader(f"{company.company_name or company.ticker} ({company.ticker})")
st.write(
    f"{company.market} | {company.sector or 'Sector unavailable'} | "
    f"{company.industry or 'Industry unavailable'}"
)

market_note = MARKETS[market].currency_note
if market_note:
    st.info(market_note)

# Top metrics show the main conclusion before the detailed tabs.
summary_cols = st.columns(5)
summary_cols[0].metric("Current Price", format_money(company.current_price, currency))
summary_cols[1].metric(
    "Fair Value Range",
    f"{format_money(valuation.fair_value_low, currency)} - {format_money(valuation.fair_value_high, currency)}",
)
summary_cols[2].markdown("**Valuation**")
summary_cols[2].markdown(status_badge(valuation.valuation_label), unsafe_allow_html=True)
summary_cols[3].markdown("**Fundamentals**")
summary_cols[3].markdown(status_badge(fundamentals.overall_quality), unsafe_allow_html=True)
summary_cols[4].markdown("**Risk**")
summary_cols[4].markdown(status_badge(risk_assessment.overall_risk), unsafe_allow_html=True)

tabs = st.tabs(["Valuation", "Fundamentals", "Risks", "Report"])

# Valuation tab: price chart, DCF scenarios, P/E check, and key assumptions.
with tabs[0]:
    st.markdown("#### Price History")
    try:
        price_history = run_price_history(company.ticker, history_period)
        price_history = normalize_price_history_units(price_history, company.raw_info.get("currency"))
    except Exception as exc:
        price_history = None
        st.warning(f"Price history unavailable: {exc}")

    if price_history is not None and not price_history.empty and "Close" in price_history.columns:
        st.line_chart(price_history["Close"], use_container_width=True)
    else:
        st.info("Price history is unavailable for this ticker.")

    left, right = st.columns([2, 1])
    with left:
        st.markdown("#### DCF Scenarios")
        show_scenario_table(valuation, currency)
    with right:
        pe = valuation.pe_valuation
        st.markdown("#### P/E Check")
        st.metric(
            "P/E Value Range",
            f"{format_money(pe.low_value_per_share, currency)} - {format_money(pe.high_value_per_share, currency)}",
        )
        st.write(f"Multiple range: {pe.low_multiple:.1f}x - {pe.high_multiple:.1f}x")
        st.write(f"Confidence: {valuation.confidence}")

    st.markdown("#### Key Assumptions")
    for assumption in valuation.assumptions:
        st.write(f"- {assumption}")

# Fundamentals tab: business-quality summary and raw financial snapshot.
with tabs[1]:
    st.markdown(f"#### Overall Quality: {fundamentals.overall_quality}")
    st.write(fundamentals.summary)
    show_fundamental_metrics(fundamentals)

    st.markdown("#### Financial Snapshot")
    st.dataframe(
        [
            {"Metric": "Market cap", "Value": format_large_number(company.market_cap, currency)},
            {"Metric": "Annual revenue", "Value": format_large_number(financials.annual_revenue, currency)},
            {"Metric": "Net income", "Value": format_large_number(financials.annual_net_income, currency)},
            {
                "Metric": "Operating cash flow",
                "Value": format_large_number(financials.annual_operating_cash_flow, currency),
            },
            {"Metric": "Free cash flow", "Value": format_large_number(financials.annual_free_cash_flow, currency)},
            {"Metric": "Total debt", "Value": format_large_number(financials.total_debt, currency)},
            {"Metric": "Total cash", "Value": format_large_number(financials.total_cash, currency)},
            {"Metric": "Trailing EPS", "Value": format_money(company.trailing_eps, currency)},
            {
                "Metric": "Trailing P/E",
                "Value": f"{company.trailing_pe:.2f}x" if company.trailing_pe is not None else "Unavailable",
            },
        ],
        use_container_width=True,
        hide_index=True,
    )

# Risks tab: warnings about missing data, weak financials, valuation, and model limits.
with tabs[2]:
    st.markdown(f"#### Overall Risk: {risk_assessment.overall_risk}")
    st.write(risk_assessment.summary)
    show_risk_table(risk_assessment)

    if quality.missing_required or quality.missing_optional:
        st.markdown("#### Missing Data")
        if quality.missing_required:
            st.warning("Required: " + ", ".join(quality.missing_required))
        if quality.missing_optional:
            st.info("Optional: " + ", ".join(quality.missing_optional))

# Report tab: generated Markdown report plus a download button.
with tabs[3]:
    st.download_button(
        "Download Markdown Report",
        data=report.markdown,
        file_name=f"{company.ticker}_report.md",
        mime="text/markdown",
    )
    st.markdown(report.markdown)

st.caption(
    "Educational use only. This is not financial advice, an investment recommendation, or a guarantee of returns."
)
