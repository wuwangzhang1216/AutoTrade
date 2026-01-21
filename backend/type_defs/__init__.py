"""
Type definitions for AutoTrade AI system

Provides TypedDict and other type definitions for better type safety and IDE support.
"""
from .trading import (
    AnalysisResult,
    TechnicalSummary,
    FundamentalAnalysis,
    MarketSentiment,
    AccountContext,
    PositionContext,
    HistoricalContext,
    AIDecisionResult,
    AccountSummary,
)

__all__ = [
    "AnalysisResult",
    "TechnicalSummary",
    "FundamentalAnalysis",
    "MarketSentiment",
    "AccountContext",
    "PositionContext",
    "HistoricalContext",
    "AIDecisionResult",
    "AccountSummary",
]
