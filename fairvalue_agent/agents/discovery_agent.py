from fairvalue_agent.models import DiscoveryCandidate, DiscoveryResult
from fairvalue_agent.tools.market_tools import infer_market_code
from fairvalue_agent.tools.yahoo_finance_tools import search_yahoo_finance


class DiscoveryAgent:
    def run(
        self,
        query: str,
        max_results: int = 10,
        equities_only: bool = True,
        preferred_market: str | None = None,
    ) -> DiscoveryResult:
        normalized_query = query.strip()
        warnings = []

        if not normalized_query:
            return DiscoveryResult(
                query=query,
                warnings=["Enter a company, ticker, market, or sector search term."],
            )

        try:
            quotes = search_yahoo_finance(normalized_query, max_results=max_results)
        except Exception as exc:
            return DiscoveryResult(
                query=query,
                warnings=[f"Yahoo Finance search failed: {exc}"],
            )

        candidates = []
        for quote in quotes:
            quote_type = quote.get("quoteType") or quote.get("typeDisp")
            if equities_only and quote_type != "EQUITY":
                continue

            symbol = quote.get("symbol")
            if not symbol:
                continue

            candidates.append(
                DiscoveryCandidate(
                    symbol=symbol,
                    name=quote.get("longname") or quote.get("shortname"),
                    quote_type=quote_type,
                    exchange=quote.get("exchange"),
                    exchange_name=quote.get("exchDisp"),
                    market_code=infer_market_code(symbol, quote.get("exchange")),
                    sector=quote.get("sectorDisp") or quote.get("sector"),
                    industry=quote.get("industryDisp") or quote.get("industry"),
                    score=quote.get("score"),
                )
            )

        if preferred_market and candidates and not any(
            candidate.market_code == preferred_market for candidate in candidates
        ):
            warnings.append(
                f"No {preferred_market} listing was found in the Yahoo Finance search results."
            )

        if not candidates:
            warnings.append("No equity listings were found. Try a more specific company name or ticker.")

        candidates.sort(key=lambda candidate: self._candidate_sort_key(candidate, preferred_market))
        return DiscoveryResult(query=query, candidates=candidates, warnings=warnings)

    def _candidate_sort_key(
        self,
        candidate: DiscoveryCandidate,
        preferred_market: str | None = None,
    ) -> tuple[int, int, float]:
        preferred = 0 if preferred_market and candidate.market_code == preferred_market else 1
        has_market = 0 if candidate.market_code else 1
        score = candidate.score or 0.0
        return preferred, has_market, -score
