"""
FastAPI dependency providing the configured MarketProvider - mirrors
payment_provider_dependency.py / weather_provider_dependency.py exactly.
No live-market-API implementation exists yet, so this always returns
DatabaseMarketProvider - the one real, working implementation.
"""
from functools import lru_cache

from app.services.market.database_market_provider import DatabaseMarketProvider
from app.services.market.market_provider import MarketProvider


@lru_cache
def get_market_provider() -> MarketProvider:
    return DatabaseMarketProvider()
