from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from typing import Set
from datetime import datetime, timedelta
import logging

from .config import get_settings
from .models import MarketSnapshot, MarketData, OHLCV
from .collectors.binance import BinanceCollector
from .storage.redis_cache import RedisCache
from .storage.timescale_db import TimescaleDB
from .processors.indicators import IndicatorCalculator
from .api import routes

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Market Data Service", version="1.0.0")

# Include API routes
app.include_router(routes.router)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket连接池
active_connections: Set[WebSocket] = set()

# 全局组件
redis_cache: RedisCache = None
timescale_db: TimescaleDB = None
collector: BinanceCollector = None
settings = get_settings()


@app.on_event("startup")
async def startup_event():
    """启动时初始化组件"""
    global redis_cache, timescale_db, collector

    logger.info("Initializing Market Data Service...")

    # 初始化Redis
    if settings.REDIS_URL:
        # Heroku deployment
        redis_cache = RedisCache(url=settings.redis_url)
    else:
        # Local development
        redis_cache = RedisCache(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB
        )
    await redis_cache.connect()

    # 初始化TimescaleDB
    timescale_db = TimescaleDB(settings.database_url)
    timescale_db.initialize()

    # Initialize API routes dependencies
    routes.init_dependencies(redis_cache, timescale_db)

    # 初始化数据采集器
    collector = BinanceCollector(symbols=settings.symbols_list)

    logger.info(f"Monitoring symbols: {settings.symbols_list}")

    # 启动后台数据采集任务
    asyncio.create_task(collect_market_data_loop())

    logger.info("Market Data Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    logger.info("Shutting down Market Data Service...")

    if redis_cache:
        await redis_cache.close()

    logger.info("Market Data Service shutdown complete")


async def collect_market_data_loop():
    """持续采集市场数据的主循环"""
    logger.info("Starting market data collection loop...")

    await redis_cache.set_collection_status("running")

    async with collector:
        while True:
            try:
                logger.debug("Collecting market data...")

                # 采集所有交易对数据
                all_data = await collector.collect_all_symbols()

                # 处理每个交易对的数据
                market_snapshot_data = {}

                for symbol, data in all_data.items():
                    try:
                        # 获取历史K线数据
                        historical_klines = data.get('historical_klines', [])

                        # 保存历史数据到数据库
                        if historical_klines:
                            timescale_db.save_ohlcv_batch(historical_klines)

                            # 缓存到Redis用于指标计算
                            for kline in historical_klines[-100:]:
                                await redis_cache.push_price_history(symbol, kline)

                        # 获取最新OHLCV
                        latest_ohlcv = data.get('latest_ohlcv')
                        if not latest_ohlcv:
                            logger.warning(f"No OHLCV data for {symbol}")
                            continue

                        # 计算技术指标
                        indicators = IndicatorCalculator.calculate_all(historical_klines)

                        # 获取ticker数据（包含准确的24小时价格变化百分比）
                        ticker = data.get('ticker')

                        # 构建MarketData
                        market_data = MarketData(
                            symbol=symbol,
                            timestamp=latest_ohlcv.timestamp,
                            ohlcv=latest_ohlcv,
                            indicators=indicators,
                            order_book=data.get('order_book'),
                            ticker=ticker  # 保存ticker数据
                        )

                        market_snapshot_data[symbol] = market_data

                        # 缓存单个交易对数据
                        await redis_cache.cache_market_data(symbol, market_data)
                        await redis_cache.cache_ohlcv(symbol, latest_ohlcv)

                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                        continue

                # 创建市场快照
                if market_snapshot_data:
                    snapshot = MarketSnapshot(
                        timestamp=datetime.now(),
                        data=market_snapshot_data
                    )

                    # 缓存快照到Redis
                    await redis_cache.set_market_snapshot(snapshot)

                    # 广播到所有WebSocket客户端
                    await broadcast_market_data(snapshot)

                    logger.info(f"Market snapshot updated with {len(market_snapshot_data)} symbols")

                # 等待下一次采集
                await asyncio.sleep(settings.DATA_COLLECTION_INTERVAL)

            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                await redis_cache.set_collection_status("error")
                await asyncio.sleep(5)


async def broadcast_market_data(snapshot: MarketSnapshot):
    """广播市场数据到所有WebSocket连接"""
    if not active_connections:
        return

    data = snapshot.model_dump(mode='json')
    disconnected = set()

    for connection in active_connections:
        try:
            await connection.send_json(data)
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            disconnected.add(connection)

    # 移除断开的连接
    active_connections.difference_update(disconnected)
    if disconnected:
        logger.info(f"Removed {len(disconnected)} disconnected WebSocket clients")


@app.websocket("/ws/market")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点 - 实时推送市场数据"""
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"New WebSocket connection. Total connections: {len(active_connections)}")

    try:
        # 先发送最新快照
        snapshot = await redis_cache.get_market_snapshot()
        if snapshot:
            await websocket.send_json(snapshot.model_dump(mode='json'))
            logger.debug("Sent initial snapshot to new client")

        # 保持连接并处理心跳
        while True:
            try:
                # 接收客户端消息（心跳）
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0
                )
                logger.debug(f"Received from client: {message}")

            except asyncio.TimeoutError:
                # 超时，发送ping
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining: {len(active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Market Data Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    redis_ok = await redis_cache.health_check()
    timescale_ok = timescale_db.health_check()

    status = "healthy" if (redis_ok and timescale_ok) else "unhealthy"

    return {
        "status": status,
        "redis": "ok" if redis_ok else "error",
        "timescale": "ok" if timescale_ok else "error",
        "collection_status": await redis_cache.get_collection_status()
    }


@app.get("/api/market/latest")
async def get_latest_market_data():
    """获取最新市场数据（REST API）"""
    snapshot = await redis_cache.get_market_snapshot()
    if snapshot:
        return snapshot.model_dump(mode='json')
    return {"error": "No data available"}


@app.get("/api/market/symbol/{symbol}")
async def get_symbol_data(symbol: str):
    """获取特定交易对的数据"""
    market_data = await redis_cache.get_market_data(symbol)
    if market_data:
        return market_data.model_dump(mode='json')
    return {"error": f"No data for {symbol}"}


@app.get("/api/market/history/{symbol}")
async def get_historical_data(symbol: str, limit: int = 100):
    """获取历史数据"""
    df = timescale_db.get_historical_data(symbol, limit)
    if not df.empty:
        return df.to_dict('records')
    return {"error": f"No historical data for {symbol}"}


@app.get("/api/market/symbols")
async def get_symbols():
    """获取监控的交易对列表"""
    return {
        "symbols": settings.symbols_list,
        "count": len(settings.symbols_list)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.MARKET_DATA_PORT,
        reload=True
    )
