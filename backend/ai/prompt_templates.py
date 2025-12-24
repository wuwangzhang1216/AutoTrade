"""
AI prompt templates for trading decisions
"""
from datetime import datetime
from typing import Optional


SYSTEM_PROMPT = """You are an expert cryptocurrency trading AI assistant for a quantitative trading system.

Your role is to analyze market data (both technical and fundamental) and provide clear trading recommendations.

You must respond with a valid JSON object in this exact format:
{
  "decision": "BUY" | "SELL" | "HOLD",
  "confidence": 0.0 to 1.0,
  "reasoning": "Your detailed explanation"
}

Guidelines:
- decision: Must be exactly one of: "BUY", "SELL", or "HOLD"

  POSITION CLOSING MECHANISM (CRITICAL):
  ----------------------------------------
  Your decision automatically manages positions based on current holdings:

  IF YOU HAVE A LONG POSITION:
    - BUY → Add to long position (stack/average up)
    - SELL → CLOSE the long position (take profit or cut loss)
    - HOLD → Keep the long position open

  IF YOU HAVE A SHORT POSITION:
    - BUY → CLOSE the short position (take profit or cut loss)
    - SELL → Add to short position (stack/average down)
    - HOLD → Keep the short position open

  IF YOU HAVE NO POSITION:
    - BUY → Open new long position (expect price to rise)
    - SELL → Open new short position (expect price to fall)
    - HOLD → Stay out of market, wait for better opportunity

  WHEN TO CLOSE POSITIONS:
  - Close losing positions: If P&L is significantly negative (e.g., -5% or worse)
  - Take profit: If P&L meets target (e.g., +10% or better)
  - Market reversal: If technical signals suggest trend has reversed
  - Risk management: If approaching liquidation price or stop loss levels

- confidence: Your confidence level as a decimal number (0.0 to 1.0)
  - 0.8-1.0: Strong signal, high confidence
  - 0.6-0.8: Moderate signal, good confidence
  - 0.4-0.6: Weak signal, low confidence
  - Below 0.4: Very uncertain, recommend HOLD

- reasoning: Explain your decision based on:
  1. Position management (if you have an open position, should you close it?)
  2. Technical indicators (trend, momentum, overbought/oversold)
  3. Fundamental factors (sentiment, news, social activity)
  4. Risk considerations and P&L targets
  5. Market context and timing

IMPORTANT: Return ONLY valid JSON, no additional text before or after the JSON object.
Be concise but thorough in your reasoning. Focus on actionable insights.
"""


def get_trading_session(current_time: datetime) -> str:
    """
    Determine current trading session based on UTC time

    Args:
        current_time: Current datetime in UTC

    Returns:
        Trading session description
    """
    hour = current_time.hour

    if 13 <= hour < 21:  # UTC 13:00-21:00 = US/EU trading hours (9am-5pm EST)
        return "US/European Active Hours (High Liquidity)"
    elif 0 <= hour < 8:   # UTC 00:00-08:00 = Asian trading hours
        return "Asian Trading Hours (Medium Liquidity)"
    else:
        return "Off-Peak Hours (Lower Liquidity)"


def build_context_section(
    current_time: datetime,
    account_summary: dict,
    position_info: Optional[dict],
    last_decision: Optional[dict],
    performance_stats: dict
) -> str:
    """
    Build context information section for AI prompt

    Args:
        current_time: Current datetime
        account_summary: Account status summary
        position_info: Current position for this symbol (if any)
        last_decision: Last AI decision for this symbol (if any)
        performance_stats: Trading performance statistics

    Returns:
        Formatted context string
    """
    # Time context
    weekday = current_time.strftime("%A")
    date_str = current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    session = get_trading_session(current_time)

    # Account context
    total_equity = account_summary.get('total_equity', 0)
    available_capital = account_summary.get('capital', 0)
    total_pnl = account_summary.get('total_pnl', 0)
    total_pnl_percent = account_summary.get('total_pnl_percent', 0)
    open_positions = account_summary.get('open_positions', 0)
    max_positions = account_summary.get('max_positions', 5)

    # Calculate capital utilization
    capital_utilization = (available_capital / total_equity * 100) if total_equity > 0 else 0

    # Position context
    position_text = "No current position for this symbol"
    if position_info:
        side = position_info.get('side', 'UNKNOWN')
        entry_price = position_info.get('entry_price', 0)
        current_pnl = position_info.get('unrealized_pnl', 0)
        pnl_percent = position_info.get('pnl_percent', 0)
        duration = position_info.get('duration_minutes', 0)
        liquidation_price = position_info.get('liquidation_price', 0)
        margin = position_info.get('margin', 0)

        position_text = f"OPEN {side} position"
        position_text += f"\n  - Entry Price: ${entry_price:,.2f}"
        position_text += f"\n  - Current P&L: ${current_pnl:,.2f} ({pnl_percent:+.2f}%)"
        position_text += f"\n  - Margin Used: ${margin:,.2f}"
        position_text += f"\n  - Duration: {duration} minutes"
        position_text += f"\n  - Liquidation Price: ${liquidation_price:,.2f}"

        if pnl_percent > 10:
            position_text += "\n  ⚠️  SIGNIFICANT PROFIT - Consider taking profit"
        elif pnl_percent < -5:
            position_text += "\n  ⚠️  APPROACHING STOP LOSS - Consider risk management"

    # Historical decision context
    history_text = "No previous decision for this symbol"
    if last_decision:
        decision_type = last_decision.get('decision', 'UNKNOWN')
        decision_price = last_decision.get('price', 0)
        time_ago = last_decision.get('time_ago', 'unknown')
        executed = last_decision.get('executed', False)

        history_text = f"Last Decision: {decision_type} at ${decision_price:,.2f} ({time_ago} ago)"
        if executed:
            history_text += " - ✓ EXECUTED"
        else:
            history_text += " - ✗ NOT EXECUTED (confidence too low)"

        # Add model confidences if available
        model_1_conf = last_decision.get('model_1_confidence')
        model_2_conf = last_decision.get('model_2_confidence')
        if model_1_conf and model_2_conf:
            avg_conf = (model_1_conf + model_2_conf) / 2
            history_text += f"\n  - Average Confidence: {avg_conf:.2f}"

    # Performance statistics
    total_trades = performance_stats.get('total_trades', 0)
    win_rate = performance_stats.get('win_rate', 0)
    winning_trades = performance_stats.get('winning_trades', 0)
    losing_trades = performance_stats.get('losing_trades', 0)

    # Performance assessment
    performance_note = ""
    if total_trades >= 5:
        if win_rate >= 70:
            performance_note = "  ✓ STRONG PERFORMANCE - Strategy working well"
        elif win_rate >= 50:
            performance_note = "  ~ MODERATE PERFORMANCE - Profitable but room for improvement"
        elif win_rate >= 30:
            performance_note = "  ⚠️  POOR PERFORMANCE - Consider more conservative approach"
        else:
            performance_note = "  ⚠️  CRITICAL - High loss rate, be very selective"

    # Build complete context section
    context = f"""
═══════════════════════════════════════════════════════════════════
                        TRADING CONTEXT
═══════════════════════════════════════════════════════════════════

CURRENT TIME & MARKET SESSION:
- Date & Time: {date_str}
- Day of Week: {weekday}
- Trading Session: {session}

ACCOUNT STATUS:
- Total Equity: ${total_equity:,.2f}
- Available Capital: ${available_capital:,.2f} ({capital_utilization:.1f}% free)
- Total P&L: ${total_pnl:,.2f} ({total_pnl_percent:+.2f}%)
- Open Positions: {open_positions}/{max_positions} slots used
{"  🚫 NO CAPITAL AVAILABLE - You MUST choose HOLD for this symbol (cannot open new positions)" if available_capital < 100 else ("  ⚠️  LIMITED CAPITAL - Be selective with new positions" if capital_utilization < 30 else "")}

POSITION STATUS FOR THIS SYMBOL:
{position_text}

HISTORICAL CONTEXT:
{history_text}

TRADING PERFORMANCE RECORD:
- Total Completed Trades: {total_trades}
- Win Rate: {win_rate:.1f}% ({winning_trades}W / {losing_trades}L)
{performance_note}

═══════════════════════════════════════════════════════════════════
"""

    return context


def create_market_analysis_prompt(
    symbol: str,
    current_price: float,
    technical_summary: dict,
    fundamental_analysis: dict,
    market_sentiment: dict,
    # Enhanced context parameters (optional for backward compatibility)
    current_time: Optional[datetime] = None,
    account_context: Optional[dict] = None,
    position_context: Optional[dict] = None,
    historical_context: Optional[dict] = None,
) -> str:
    """
    Create user prompt with market analysis data

    Args:
        symbol: Trading pair
        current_price: Current market price
        technical_summary: Technical analysis summary
        fundamental_analysis: Fundamental analysis data
        market_sentiment: Market sentiment data
        current_time: Current datetime (optional)
        account_context: Account status info (optional)
        position_context: Current position for this symbol (optional)
        historical_context: Last AI decision for this symbol (optional)

    Returns:
        Formatted prompt string
    """
    # Technical indicators summary
    tech_signals = technical_summary.get('signals', {})
    tech_recommendation = technical_summary.get('recommendation', 'HOLD')
    bullish_percent = technical_summary.get('bullish_percent', 50)

    tech_text = f"""
TECHNICAL ANALYSIS for {symbol}:
- Current Price: ${current_price:,.2f}
- Technical Recommendation: {tech_recommendation}
- Bullish Signals: {bullish_percent:.1f}%
- Key Signals:
  - Moving Average: {tech_signals.get('ma_cross', 'N/A')}
  - MACD: {tech_signals.get('macd', 'N/A')}
  - RSI: {tech_signals.get('rsi', 'N/A')}
  - Bollinger Bands: {tech_signals.get('bb', 'N/A')}
  - Trend Strength: {tech_signals.get('trend_strength', 'N/A')}
"""

    # Support/Resistance
    sr = technical_summary.get('support_resistance', {})
    if sr:
        tech_text += f"""
- Support: ${sr.get('support', 0):,.2f} ({sr.get('distance_to_support', 0):.2f}% below)
- Resistance: ${sr.get('resistance', 0):,.2f} ({sr.get('distance_to_resistance', 0):.2f}% above)
"""

    # Fundamental analysis
    fund_score = fundamental_analysis.get('fundamental_score', 50)
    fund_recommendation = fundamental_analysis.get('recommendation', 'HOLD')

    fund_text = f"""
FUNDAMENTAL ANALYSIS:
- Fundamental Score: {fund_score:.1f}/100
- Fundamental Recommendation: {fund_recommendation}
"""

    # Market sentiment
    sentiment = market_sentiment.get('fear_greed', {})
    if sentiment:
        fund_text += f"""
- Fear & Greed Index: {sentiment.get('value', 50)}/100 ({sentiment.get('classification', 'Neutral')})
  {sentiment.get('interpretation', {}).get('recommendation', '')}
"""

    # News sentiment
    news = fundamental_analysis.get('news_sentiment', {})
    if news:
        fund_text += f"""
- News Sentiment: {news.get('sentiment', 'Neutral')} (Score: {news.get('sentiment_score', 0):.1f})
  Recent News: {news.get('total_news', 0)} articles
"""

    # Social metrics
    social_data = fundamental_analysis.get('coin_fundamentals', {}).get('sources', {}).get('lunarcrush', {})
    if social_data:
        fund_text += f"""
- Social Metrics:
  - Galaxy Score: {social_data.get('galaxy_score', 'N/A')}
  - Social Volume: {social_data.get('social_volume', 'N/A')}
  - Sentiment: {social_data.get('sentiment', 'N/A')}
"""

    # Market context
    global_market = market_sentiment.get('global_market', {})
    if global_market:
        fund_text += f"""
MARKET CONTEXT:
- BTC Dominance: {global_market.get('btc_dominance', 0):.1f}%
- Market Cap Change 24h: {global_market.get('market_cap_change_24h', 0):+.2f}%
"""

    # Build context section if enhanced parameters provided
    context_text = ""
    if current_time and account_context:
        # Extract performance stats from account context
        performance_stats = account_context.get('performance', {
            'total_trades': account_context.get('total_trades', 0),
            'winning_trades': account_context.get('winning_trades', 0),
            'losing_trades': account_context.get('losing_trades', 0),
            'win_rate': account_context.get('win_rate', 0),
        })

        context_text = build_context_section(
            current_time=current_time,
            account_summary=account_context,
            position_info=position_context,
            last_decision=historical_context,
            performance_stats=performance_stats
        )

    # Combine all sections
    full_prompt = f"""{context_text}
{tech_text}
{fund_text}

Based on this comprehensive analysis including your account status and trading history,
what is your trading recommendation for {symbol}?

IMPORTANT DECISION FACTORS:

1. POSITION MANAGEMENT (HIGHEST PRIORITY):

   IF YOU HAVE AN OPEN POSITION FOR THIS SYMBOL:
   - Check the current P&L percentage and absolute value
   - Evaluate if conditions have changed since entry
   - Decide whether to CLOSE the position or HOLD it:

   TO CLOSE A LOSING POSITION (Cut Loss):
     • If LONG and losing → recommend SELL (this closes the long)
     • If SHORT and losing → recommend BUY (this closes the short)
     • Consider closing if: P&L < -5%, trend reversed, or risk too high

   TO CLOSE A WINNING POSITION (Take Profit):
     • If LONG and profitable → recommend SELL (this closes the long)
     • If SHORT and profitable → recommend BUY (this closes the short)
     • Consider closing if: P&L > +10%, overbought/oversold, or reversal signals

   TO HOLD THE POSITION:
     • Recommend HOLD if position is still valid and target not reached
     • Only hold if trend continues and risk is manageable

2. NEW POSITION ENTRY (if no current position):
   - Only recommend BUY/SELL if you see a strong opportunity
   - Check available capital before recommending new positions
   - With limited capital, be highly selective

3. PERFORMANCE AWARENESS:
   - If win rate is low (<50%), be more conservative and focus on closing losers
   - If performing well (>70%), maintain current strategy
   - Learn from past decisions for this symbol

4. MARKET TIMING:
   - High liquidity sessions are better for entries/exits
   - Avoid major position changes during off-peak hours

5. RISK MANAGEMENT:
   - Never let losses grow beyond -10% without closing
   - Always have a clear profit target and stop loss in mind
   - Preserve capital for future opportunities

REMEMBER: Your primary job when you have an open position is to ACTIVELY MANAGE it.
Don't just HOLD losing positions hoping they recover - close them if conditions have worsened.
Don't be afraid to SELL (close LONG) or BUY (close SHORT) to protect profits or cut losses.

Provide your decision in the specified JSON format (decision, confidence, reasoning).
Focus on explaining WHY this is the right action given the FULL context, especially position management.
"""

    return full_prompt


__all__ = ["SYSTEM_PROMPT", "create_market_analysis_prompt", "get_trading_session", "build_context_section"]
