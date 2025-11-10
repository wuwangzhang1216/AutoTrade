"""
FastAPI backend for AutoTrade AI
Provides REST API and WebSocket for real-time updates
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
import json
import os

from pydantic import BaseModel
from sqlalchemy import desc

# Import from main system
from database import get_db_manager, get_session, Trade, AIDecision, AccountSnapshot, MarketEventRecord
from data import MarketDataCollector
from config import TradingPairsConfig
from utils.logger import logger, log_error, log_success, log_info
from ai import AIDecisionScheduler
from events import start_event_monitor, stop_event_monitor, get_event_monitor

# Create FastAPI app
app = FastAPI(
    title="AutoTrade AI API",
    description="Real-time trading system API with AI decision making",
    version="1.0.0"
)

# CORS middleware - allow frontend origins from environment variable
allowed_origins = [
    "http://localhost:5888",
    "http://localhost:5173",
]

# Add production frontend URL from environment variable
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)
    logger.info(f"CORS: Added frontend URL from environment: {frontend_url}")

# Fallback to old Heroku URL if FRONTEND_URL not set
if not frontend_url:
    allowed_origins.append("https://autotrade-frontend-wang-1d47c1aff417.herokuapp.com")
    logger.info("CORS: Using fallback Heroku frontend URL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
db = get_db_manager()
market_data = MarketDataCollector()
connected_websockets: List[WebSocket] = []
ai_scheduler: Optional['AIDecisionScheduler'] = None
_scheduler_started = False  # Track if scheduler has been initialized
_event_monitor_instance = None  # Event Monitor instance

# PERFORMANCE: Simple in-memory cache for trades (expires after 60 seconds)
_trades_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 60  # 60 seconds cache (reduced frontend polling means we can cache longer)
}

# PERFORMANCE: Simple in-memory cache for positions (expires after 30 seconds)
_positions_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 30  # 30 seconds cache (batch price fetch is fast, but still cache to reduce load)
}


# Pydantic models for API
class AccountStatus(BaseModel):
    capital: float
    total_equity: float
    total_pnl: float
    total_pnl_percent: float
    unrealized_pnl: float
    open_positions: int
    total_trades: int
    win_rate: float
    winning_trades: int = 0
    losing_trades: int = 0


class PositionInfo(BaseModel):
    symbol: str
    side: str
    amount: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    margin: float
    leverage: int


class TradeInfo(BaseModel):
    id: int
    timestamp: datetime
    symbol: str
    order_type: str
    side: Optional[str]
    amount: float
    price: float
    pnl: Optional[float]
    fee: float


class AIDecisionSummary(BaseModel):
    """Lightweight AI decision for list view - no reasoning text"""
    id: int
    timestamp: datetime
    symbol: str
    model_1_decision: str
    model_1_confidence: float
    model_2_decision: str
    model_2_confidence: float
    final_decision: str
    executed: bool


class AIDecisionInfo(BaseModel):
    """Full AI decision with reasoning - for detail view"""
    id: int
    timestamp: datetime
    symbol: str
    model_1_decision: str
    model_1_confidence: float
    model_1_reasoning: str
    model_2_decision: str
    model_2_confidence: float
    model_2_reasoning: str
    final_decision: str
    executed: bool


class MarketDataResponse(BaseModel):
    symbol: str
    price: float
    change_24h: Optional[float]
    volume: Optional[float]
    timestamp: datetime


# Pagination models
class PaginationMeta(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int


class PaginatedTradesResponse(BaseModel):
    data: List[TradeInfo]
    meta: PaginationMeta


class PaginatedDecisionsResponse(BaseModel):
    data: List[AIDecisionSummary]
    meta: PaginationMeta


class MarketEventInfo(BaseModel):
    """Market event information"""
    id: int
    timestamp: datetime
    symbol: str
    event_type: str
    severity: str
    description: str
    suggested_action: Optional[str]
    metrics: dict


class MarketEventsStatsResponse(BaseModel):
    """Market events statistics"""
    total_events: int
    events_by_severity: dict
    events_by_type: dict


# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a websocket client

        BUG FIX: Check if websocket exists in list before removing
        to avoid ValueError
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected clients

        BUG FIX: Improved error handling with proper logging
        - Logs each broadcast error with connection details
        - Removes disconnected clients gracefully
        - Tracks broadcast success rate
        """
        if not self.active_connections:
            return

        disconnected = []
        success_count = 0
        error_count = 0

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                success_count += 1
            except WebSocketDisconnect:
                # Client disconnected - normal behavior
                logger.debug(f"WebSocket client disconnected during broadcast")
                disconnected.append(connection)
                error_count += 1
            except ConnectionResetError:
                # Connection was reset - client likely closed unexpectedly
                logger.warning(f"WebSocket connection reset during broadcast")
                disconnected.append(connection)
                error_count += 1
            except Exception as e:
                # Other unexpected errors
                log_error(f"WebSocket broadcast error: {type(e).__name__}: {e}")
                disconnected.append(connection)
                error_count += 1

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

        # Log summary if there were any errors
        if error_count > 0:
            logger.warning(
                f"WebSocket broadcast: {success_count} succeeded, {error_count} failed. "
                f"Active connections: {len(self.active_connections)}"
            )


manager = ConnectionManager()


# REST API Endpoints
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "AutoTrade AI API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint - fast response to verify server is alive

    This endpoint is optimized for speed and doesn't do any heavy operations
    """
    # Start AI scheduler on first request (lazy initialization to avoid boot timeout)
    start_ai_scheduler_if_needed()

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/account", response_model=AccountStatus)
async def get_account_status():
    """
    Get current account status - OPTIMIZED

    Performance improvements:
    - Reuses session connection
    - Caches initial_capital
    - Fast query with indexed timestamp
    """
    # Start AI scheduler on first request (lazy initialization to avoid boot timeout)
    start_ai_scheduler_if_needed()

    try:
        # Get latest snapshot
        session = get_session()

        try:
            latest = session.query(AccountSnapshot)\
                .order_by(desc(AccountSnapshot.timestamp))\
                .first()

            # PERFORMANCE: Get initial capital from settings (cached)
            from config import settings
            if settings and hasattr(settings, 'initial_capital'):
                initial_capital = settings.initial_capital
            else:
                # Fallback: use default
                initial_capital = 10000.0
                logger.warning("Using default initial capital 10000.0")
        finally:
            session.close()

        if not latest:
            # Return default values if no data exists yet
            return AccountStatus(
                capital=initial_capital,
                total_equity=initial_capital,
                total_pnl=0.0,
                total_pnl_percent=0.0,
                unrealized_pnl=0.0,
                open_positions=0,
                total_trades=0,
                win_rate=0.0,
                winning_trades=0,
                losing_trades=0
            )

        # Calculate PnL based on actual initial capital
        total_pnl = latest.total_equity - initial_capital
        total_pnl_percent = (total_pnl / initial_capital) * 100 if initial_capital > 0 else 0.0

        # BUG FIX: Win rate should only consider closed trades, not all trades
        # winning_trades and losing_trades only count CLOSE_LONG/CLOSE_SHORT trades
        # OPEN trades shouldn't be in the denominator
        closed_trades = latest.winning_trades + latest.losing_trades
        win_rate = (latest.winning_trades / closed_trades * 100) if closed_trades > 0 else 0

        return AccountStatus(
            capital=latest.capital,
            total_equity=latest.total_equity,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            unrealized_pnl=latest.unrealized_pnl,
            open_positions=latest.open_positions,
            total_trades=latest.total_trades,
            win_rate=win_rate,
            winning_trades=latest.winning_trades,
            losing_trades=latest.losing_trades
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in get_account_status: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/positions", response_model=List[PositionInfo])
async def get_positions():
    """
    Get current open positions - OPTIMIZED with caching and batch price fetching

    Performance improvements:
    - 3-second cache to reduce database queries
    - Batch price fetching (1 API call instead of N)
    - Reuses snapshot data efficiently
    """
    try:
        from time import time
        now = time()

        # PERFORMANCE: Check cache first
        if (_positions_cache['data'] is not None and
            _positions_cache['timestamp'] is not None and
            (now - _positions_cache['timestamp']) < _positions_cache['ttl']):

            # Return cached data
            logger.debug("Returning cached positions data")
            return _positions_cache['data']

        # Cache miss - fetch from database
        session = get_session()

        latest = session.query(AccountSnapshot)\
            .order_by(desc(AccountSnapshot.timestamp))\
            .first()

        session.close()

        if not latest or not latest.positions:
            # Cache empty result for shorter time
            _positions_cache['data'] = []
            _positions_cache['timestamp'] = now
            return []

        # PERFORMANCE FIX: Batch fetch all prices at once instead of one-by-one
        # This reduces API calls from N to 1 (huge performance improvement)
        symbols = list(latest.positions.keys())
        current_prices = market_data.get_multiple_prices(symbols)

        positions = []
        for symbol, pos_data in latest.positions.items():
            # Use batch-fetched price
            current_price = current_prices.get(symbol)

            if current_price:
                # Calculate PnL based on margin (invested capital)
                margin = pos_data.get('margin', pos_data['entry_price'] * pos_data['amount'] / 10)

                # Recalculate unrealized PnL with current price
                entry_price = pos_data['entry_price']
                amount = pos_data['amount']
                side = pos_data['side']

                if side == 'LONG':
                    price_change_percent = (current_price - entry_price) / entry_price
                else:  # SHORT
                    price_change_percent = (entry_price - current_price) / entry_price

                leverage = pos_data.get('leverage', 10)
                unrealized_pnl = margin * price_change_percent * leverage
                unrealized_pnl_percent = (unrealized_pnl / margin * 100) if margin > 0 else 0.0

                positions.append(PositionInfo(
                    symbol=symbol,
                    side=side,
                    amount=amount,
                    entry_price=entry_price,
                    current_price=current_price,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percent=unrealized_pnl_percent,
                    margin=margin,
                    leverage=leverage
                ))

        # PERFORMANCE: Update cache
        _positions_cache['data'] = positions
        _positions_cache['timestamp'] = now
        logger.debug(f"Cached {len(positions)} positions")

        return positions

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades", response_model=PaginatedTradesResponse)
async def get_trades(
    page: int = 1,
    per_page: int = 20,
    symbol: Optional[str] = None
):
    """
    Get paginated trades with metadata

    Args:
        page: Page number (1-indexed)
        per_page: Items per page (default: 20, max: 100)
        symbol: Optional symbol filter

    Returns:
        Paginated response with trades and metadata
    """
    try:
        # Limit max per_page to prevent abuse
        per_page = min(per_page, 100)
        page = max(page, 1)  # Ensure page is at least 1

        # Calculate offset
        offset = (page - 1) * per_page

        # Get total count
        session = get_session()
        query = session.query(Trade)
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        total = query.count()

        # Get paginated trades
        trades = query.order_by(desc(Trade.timestamp)).offset(offset).limit(per_page).all()

        result = [
            TradeInfo(
                id=trade.id,
                timestamp=trade.timestamp,
                symbol=trade.symbol,
                order_type=trade.order_type,
                side=trade.side,
                amount=trade.amount,
                price=trade.price,
                pnl=trade.pnl,
                fee=trade.fee
            )
            for trade in trades
        ]

        # Calculate pagination metadata
        import math
        total_pages = math.ceil(total / per_page) if per_page > 0 else 0

        session.close()

        return PaginatedTradesResponse(
            data=result,
            meta=PaginationMeta(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages
            )
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai-decisions", response_model=PaginatedDecisionsResponse)
async def get_ai_decisions(
    page: int = 1,
    per_page: int = 20,
    symbol: Optional[str] = None
):
    """
    Get paginated AI decisions with metadata

    Args:
        page: Page number (1-indexed)
        per_page: Items per page (default: 20, max: 100)
        symbol: Optional symbol filter

    Returns:
        Paginated response with AI decisions (summary without reasoning) and metadata
    """
    try:
        # Limit max per_page to prevent abuse
        per_page = min(per_page, 100)
        page = max(page, 1)  # Ensure page is at least 1

        # Calculate offset
        offset = (page - 1) * per_page

        # Get total count
        session = get_session()
        query = session.query(AIDecision)
        if symbol:
            query = query.filter(AIDecision.symbol == symbol)
        total = query.count()

        # Get paginated decisions
        decisions = query.order_by(desc(AIDecision.timestamp)).offset(offset).limit(per_page).all()

        # PERFORMANCE FIX: Return lightweight summary without reasoning
        # This reduces response size by ~80% (reasoning can be several KB per decision)
        result = [
            AIDecisionSummary(
                id=decision.id,
                timestamp=decision.timestamp,
                symbol=decision.symbol,
                model_1_decision=decision.model_1_decision or "N/A",
                model_1_confidence=decision.model_1_confidence or 0,
                model_2_decision=decision.model_2_decision or "N/A",
                model_2_confidence=decision.model_2_confidence or 0,
                final_decision=decision.final_decision,
                executed=decision.executed
            )
            for decision in decisions
        ]

        # Calculate pagination metadata
        import math
        total_pages = math.ceil(total / per_page) if per_page > 0 else 0

        session.close()

        return PaginatedDecisionsResponse(
            data=result,
            meta=PaginationMeta(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages
            )
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai-decisions/{decision_id}", response_model=AIDecisionInfo)
async def get_ai_decision_detail(decision_id: int):
    """Get full AI decision details including reasoning - for expanded view"""
    try:
        session = get_session()
        decision = session.query(AIDecision).filter(AIDecision.id == decision_id).first()
        session.close()

        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")

        return AIDecisionInfo(
            id=decision.id,
            timestamp=decision.timestamp,
            symbol=decision.symbol,
            model_1_decision=decision.model_1_decision or "N/A",
            model_1_confidence=decision.model_1_confidence or 0,
            model_1_reasoning=decision.model_1_reasoning or "",
            model_2_decision=decision.model_2_decision or "N/A",
            model_2_confidence=decision.model_2_confidence or 0,
            model_2_reasoning=decision.model_2_reasoning or "",
            final_decision=decision.final_decision,
            executed=decision.executed
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market-data")
async def get_market_data(symbol: str):
    """Get market data for a symbol"""
    try:
        ticker = market_data.get_ticker(symbol)

        if not ticker:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")

        return ticker

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in get_market_data for {symbol}: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ohlcv")
async def get_ohlcv(symbol: str, timeframe: str = "15m", limit: int = 100):
    """Get OHLCV data for charts"""
    try:
        print(f"Fetching OHLCV for symbol: {symbol}, timeframe: {timeframe}, limit: {limit}")
        df = market_data.get_ohlcv(symbol, timeframe=timeframe, limit=limit)

        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No OHLCV data for {symbol}")

        # Convert to list of dicts for JSON serialization
        data = df.to_dict('records')

        # Validate and filter OHLCV data to prevent null values from reaching frontend
        validated_data = []
        for item in data:
            try:
                # Convert timestamp first
                if hasattr(item['timestamp'], 'timestamp'):
                    # pandas Timestamp object - convert to Unix ms
                    timestamp = int(item['timestamp'].timestamp() * 1000)
                elif isinstance(item['timestamp'], (int, float)):
                    # Already a number - ensure it's in milliseconds
                    timestamp = int(item['timestamp']) if item['timestamp'] > 1e12 else int(item['timestamp'] * 1000)
                else:
                    continue  # Skip invalid timestamp

                # Validate all OHLCV values are present and valid
                if (
                    item.get('open') is not None and
                    item.get('high') is not None and
                    item.get('low') is not None and
                    item.get('close') is not None and
                    item.get('volume') is not None
                ):
                    # Additional validation: ensure numeric values
                    try:
                        open_val = float(item['open'])
                        high_val = float(item['high'])
                        low_val = float(item['low'])
                        close_val = float(item['close'])
                        volume_val = float(item['volume'])

                        # Validate OHLC logic: high should be highest, low should be lowest
                        if (
                            high_val >= low_val and
                            high_val >= open_val and
                            high_val >= close_val and
                            low_val <= open_val and
                            low_val <= close_val and
                            volume_val >= 0
                        ):
                            validated_data.append({
                                'timestamp': timestamp,
                                'open': open_val,
                                'high': high_val,
                                'low': low_val,
                                'close': close_val,
                                'volume': volume_val
                            })
                        else:
                            print(f"Skipping invalid OHLC data point: high={high_val}, low={low_val}, open={open_val}, close={close_val}")
                    except (ValueError, TypeError) as e:
                        print(f"Skipping non-numeric OHLCV data: {e}")
                        continue
            except Exception as e:
                print(f"Error processing OHLCV data point: {e}")
                continue

        if not validated_data:
            raise HTTPException(status_code=404, detail=f"No valid OHLCV data for {symbol}")

        print(f"Returning {len(validated_data)} validated OHLCV points (filtered from {len(data)})")

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": validated_data
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in get_ohlcv for {symbol}: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/equity-curve")
async def get_equity_curve(days: int = 30):
    """Get equity curve data"""
    try:
        import math

        snapshots = db.get_account_history(days=days)

        # Validate and filter equity curve data to prevent null/invalid values
        validated_data = []
        for snapshot in snapshots:
            try:
                # Validate all required fields are present and valid
                if (
                    snapshot.total_equity is not None and
                    snapshot.capital is not None and
                    snapshot.unrealized_pnl is not None and
                    snapshot.timestamp is not None
                ):
                    # Ensure numeric values are valid
                    equity = float(snapshot.total_equity)
                    capital = float(snapshot.capital)
                    unrealized_pnl = float(snapshot.unrealized_pnl)

                    # Validate numbers are finite and not NaN using proper math functions
                    if (
                        math.isnan(equity) or
                        math.isnan(capital) or
                        math.isnan(unrealized_pnl) or
                        math.isinf(equity) or
                        math.isinf(capital) or
                        math.isinf(unrealized_pnl) or
                        equity <= 0  # Equity must be positive
                    ):
                        print(f"Skipping invalid equity data: equity={equity}, capital={capital}, unrealized_pnl={unrealized_pnl}")
                        continue

                    timestamp = int(snapshot.timestamp.timestamp() * 1000)

                    # Final validation: ensure timestamp is valid
                    if timestamp <= 0:
                        print(f"Skipping invalid timestamp: {timestamp}")
                        continue

                    validated_data.append({
                        "timestamp": timestamp,
                        "equity": equity,
                        "capital": capital,
                        "unrealized_pnl": unrealized_pnl
                    })
            except (ValueError, TypeError, AttributeError) as e:
                print(f"Error processing equity snapshot: {e}")
                continue

        print(f"Returning {len(validated_data)} validated equity points (filtered from {len(snapshots)})")
        return validated_data

    except Exception as e:
        import traceback
        print(f"Error in get_equity_curve: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance")
async def get_performance():
    """Get performance statistics"""
    try:
        stats = db.get_performance_stats()
        return stats if stats else {}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trading-pairs")
async def get_trading_pairs():
    """Get list of trading pairs"""
    return {
        "pairs": TradingPairsConfig.DEFAULT_PAIRS,
        "timeframes": TradingPairsConfig.TIMEFRAMES
    }


@app.get("/api/market-events", response_model=List[MarketEventInfo])
async def get_market_events(
    limit: int = 10,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    symbol: Optional[str] = None
):
    """
    Get recent market events

    Args:
        limit: Maximum number of events to return (default 10)
        event_type: Filter by event type (e.g., 'flash_crash', 'volume_spike')
        severity: Filter by severity (e.g., 'critical', 'high', 'medium', 'low')
        symbol: Filter by trading symbol (e.g., 'BTC/USDT')

    Returns:
        List of market events
    """
    try:
        session = get_session()

        # Build query
        query = session.query(MarketEventRecord)

        # Apply filters
        if event_type:
            query = query.filter(MarketEventRecord.event_type == event_type)
        if severity:
            query = query.filter(MarketEventRecord.severity == severity)
        if symbol:
            query = query.filter(MarketEventRecord.symbol == symbol)

        # Order by timestamp descending and limit
        events = query.order_by(desc(MarketEventRecord.timestamp)).limit(limit).all()

        session.close()

        # Convert to response model
        return [
            MarketEventInfo(
                id=event.id,
                timestamp=event.timestamp,
                symbol=event.symbol,
                event_type=event.event_type,
                severity=event.severity,
                description=event.description,
                suggested_action=event.suggested_action,
                metrics=event.metrics or {}
            )
            for event in events
        ]

    except Exception as e:
        log_error(f"Error fetching market events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market-events/stats", response_model=MarketEventsStatsResponse)
async def get_market_events_stats():
    """
    Get market events statistics

    Returns:
        Statistics about detected market events
    """
    try:
        global _event_monitor_instance

        if _event_monitor_instance is None:
            return MarketEventsStatsResponse(
                total_events=0,
                events_by_severity={},
                events_by_type={}
            )

        stats = _event_monitor_instance.get_statistics()

        return MarketEventsStatsResponse(
            total_events=stats.get('total_events', 0),
            events_by_severity=stats.get('events_by_severity', {}),
            events_by_type=stats.get('events_by_type', {})
        )

    except Exception as e:
        log_error(f"Error fetching market events stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cache/stats")
async def get_cache_stats():
    """
    获取市场数据缓存统计信息

    Returns:
        缓存命中率、缓存条目数等统计信息
    """
    try:
        from data.market_data_cache import get_market_data_cache
        cache = get_market_data_cache()
        stats = cache.get_stats()

        return {
            'success': True,
            'data': stats,
            'message': f"缓存命中率: {stats['hit_rate']}%"
        }
    except Exception as e:
        log_error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await manager.connect(websocket)

    try:
        while True:
            try:
                # Send periodic updates
                await asyncio.sleep(5)  # Update every 5 seconds

                # Get current account status
                session = get_session()
                latest = session.query(AccountSnapshot)\
                    .order_by(desc(AccountSnapshot.timestamp))\
                    .first()
                session.close()

                if latest:
                    # Get current prices for positions
                    prices = {}
                    if latest.positions:
                        for symbol in latest.positions.keys():
                            try:
                                price = market_data.get_price(symbol)
                                if price:
                                    prices[symbol] = price
                            except Exception as e:
                                print(f"Failed to get price for {symbol}: {e}")
                                continue

                    # Send update - ensure no null values for numeric fields
                    update = {
                        "type": "account_update",
                        "data": {
                            "timestamp": int(datetime.now().timestamp() * 1000),  # Unix timestamp in milliseconds
                            "equity": latest.total_equity if latest.total_equity is not None else 0.0,
                            "capital": latest.capital if latest.capital is not None else 0.0,
                            "unrealized_pnl": latest.unrealized_pnl if latest.unrealized_pnl is not None else 0.0,
                            "open_positions": latest.open_positions if latest.open_positions is not None else 0,
                            "prices": prices
                        }
                    }

                    # Check if client is still connected before sending
                    if websocket.client_state.name == "CONNECTED":
                        await websocket.send_json(update)
                    else:
                        # Connection not active, exit loop
                        break
                else:
                    # Send heartbeat even if no data
                    # Check if client is still connected before sending
                    if websocket.client_state.name == "CONNECTED":
                        await websocket.send_json({
                            "type": "heartbeat",
                            "timestamp": int(datetime.now().timestamp() * 1000)  # Unix timestamp in milliseconds
                        })
                    else:
                        # Connection not active, exit loop
                        break

            except WebSocketDisconnect:
                # Client disconnected, break out of loop
                raise
            except RuntimeError as e:
                # Handle "Cannot call send after close" errors
                if "close" in str(e).lower() or "send" in str(e).lower():
                    print(f"WebSocket connection closed: {e}")
                    break  # Exit loop, connection is closed
                else:
                    # Other runtime errors - log and break to be safe
                    print(f"WebSocket RuntimeError: {e}")
                    break
            except Exception as e:
                # Log other errors and break the loop to avoid repeated errors
                print(f"Error in WebSocket update loop: {e}")
                # Break instead of continue to avoid sending to a broken connection
                break

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Background task to broadcast updates
async def broadcast_updates():
    """Background task to broadcast updates to all connected clients"""
    while True:
        await asyncio.sleep(10)  # Broadcast every 10 seconds

        if manager.active_connections:
            try:
                # Get latest data
                session = get_session()
                latest = session.query(AccountSnapshot)\
                    .order_by(desc(AccountSnapshot.timestamp))\
                    .first()
                session.close()

                if latest:
                    await manager.broadcast({
                        "type": "update",
                        "timestamp": int(datetime.now().timestamp() * 1000),  # Unix timestamp in milliseconds
                        "equity": latest.total_equity
                    })

            except Exception as e:
                print(f"Broadcast error: {e}")


# Helper function to start AI scheduler (called after first API request)
def start_ai_scheduler_if_needed():
    """Start AI scheduler on first API request to avoid boot timeout"""
    import os
    global ai_scheduler, _scheduler_started

    if _scheduler_started:
        return

    # Check if AI scheduler should be enabled (default: disabled in production)
    enable_ai_scheduler = os.getenv('ENABLE_AI_SCHEDULER', 'false').lower() == 'true'

    if not enable_ai_scheduler:
        log_info("AI Decision Scheduler is DISABLED (set ENABLE_AI_SCHEDULER=true to enable)")
        _scheduler_started = True  # Mark as started to prevent repeated checks
        return

    _scheduler_started = True

    # Start scheduler in background thread to not block the request
    def _start_scheduler():
        import os
        global ai_scheduler

        # CRITICAL: With multiple workers, ensure only ONE worker runs the scheduler
        # Use a simple file lock mechanism
        lock_file = '/tmp/ai_scheduler.lock'
        try:
            # Try to create lock file exclusively
            import fcntl
            lock_fd = open(lock_file, 'w')
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Successfully acquired lock - this worker will run the scheduler
            log_info("This worker acquired scheduler lock - will run AI Decision Scheduler")

            # Get interval from environment (default: 5 minutes for production)
            interval_minutes = int(os.getenv('AI_SCHEDULER_INTERVAL_MINUTES', '5'))

            log_info(f"Starting AI Decision Scheduler after first API request (interval: {interval_minutes} minutes)...")
            ai_scheduler = AIDecisionScheduler(
                broadcast_callback=manager.broadcast,
                enable_trading=True,  # Enable automatic trading execution
                interval_minutes=interval_minutes
            )
            ai_scheduler.start()
            log_info(f"AI Decision Scheduler started successfully - Trading ENABLED (every {interval_minutes} minutes)")

            # Keep lock file open to maintain lock
            # Will be released when process exits

        except (IOError, OSError) as e:
            # Another worker already has the lock
            log_info("Another worker is already running AI Decision Scheduler - this worker will skip it")
            return

    import threading
    threading.Thread(target=_start_scheduler, daemon=True).start()


# 后台任务：定期清理过期缓存
async def cleanup_cache_periodically():
    """
    定期清理过期缓存（每5分钟）

    这可以防止内存无限增长，同时5分钟的间隔足够合理
    """
    from data.market_data_cache import get_market_data_cache

    cache = get_market_data_cache()
    logger.info("缓存清理任务已启动，每5分钟执行一次")

    while True:
        await asyncio.sleep(300)  # 5分钟
        try:
            cache.cleanup_expired()
            stats = cache.get_stats()
            logger.debug(f"缓存统计: 条目数={stats['total_entries']}, 命中率={stats['hit_rate']}%")
        except Exception as e:
            log_error(f"清理缓存失败: {e}")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    log_info("AutoTrade AI API starting...")
    log_info("AI Decision Scheduler will start after first API request to avoid boot timeout")

    # Start Event Monitor immediately (independent monitoring system)
    try:
        from events.event_monitor import EventMonitor

        # ✅ 获取当前事件循环，传递给EventMonitor以实现线程安全的广播
        current_loop = asyncio.get_running_loop()

        # Initialize with WebSocket broadcast callback and event loop
        monitor = EventMonitor(
            broadcast_callback=manager.broadcast,
            event_loop=current_loop
        )
        monitor.start()

        # Store in global for access from API endpoints
        global _event_monitor_instance
        _event_monitor_instance = monitor
        log_success("Event Monitor started successfully with WebSocket support")
    except Exception as e:
        log_error(f"Failed to start Event Monitor: {e}")

    # Start background task for broadcasting
    asyncio.create_task(broadcast_updates())

    # 启动缓存清理后台任务
    asyncio.create_task(cleanup_cache_periodically())
    log_info("缓存清理后台任务已启动")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global ai_scheduler, _event_monitor_instance

    log_info("AutoTrade AI API shutting down...")

    # Stop AI scheduler
    if ai_scheduler:
        ai_scheduler.stop()

    # Stop Event Monitor
    try:
        if _event_monitor_instance:
            _event_monitor_instance.stop()
            log_info("Event Monitor stopped")
    except Exception as e:
        log_error(f"Error stopping Event Monitor: {e}")

    log_info("AutoTrade AI API stopped")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
