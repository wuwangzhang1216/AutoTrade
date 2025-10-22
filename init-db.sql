-- 初始化数据库脚本

-- 启用TimescaleDB扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 创建agents表 - 存储代理信息
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    initial_balance DECIMAL(20, 2) NOT NULL,
    current_balance DECIMAL(20, 2) NOT NULL,
    total_pnl DECIMAL(20, 2) DEFAULT 0,
    trade_count INTEGER DEFAULT 0,
    win_count INTEGER DEFAULT 0,
    loss_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建positions表 - 持仓记录
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 2) NOT NULL,
    current_price DECIMAL(20, 2) NOT NULL,
    unrealized_pnl DECIMAL(20, 2),
    stop_loss DECIMAL(20, 2),
    take_profit DECIMAL(20, 2),
    entry_time TIMESTAMP NOT NULL,
    side VARCHAR(10) DEFAULT 'long',
    leverage DECIMAL(4, 2) DEFAULT 1.0,
    is_closed BOOLEAN DEFAULT FALSE,
    closed_at TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- 创建decisions表 - 决策记录
CREATE TABLE IF NOT EXISTS decisions (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    action VARCHAR(20) NOT NULL,
    symbol VARCHAR(20),
    quantity DECIMAL(20, 8),
    stop_loss DECIMAL(20, 2),
    take_profit DECIMAL(20, 2),
    leverage DECIMAL(4, 2) DEFAULT 1.0,
    reasoning TEXT NOT NULL,
    confidence DECIMAL(3, 2),
    raw_response TEXT,
    current_price DECIMAL(20, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- 创建trades表 - 交易执行记录
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    decision_id INTEGER,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 2) NOT NULL,
    commission DECIMAL(20, 2) DEFAULT 0.0,
    pnl DECIMAL(20, 2),
    executed_at TIMESTAMP NOT NULL,
    is_simulated BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    FOREIGN KEY (decision_id) REFERENCES decisions(id)
);

-- 创建ohlcv表 - K线数据
CREATE TABLE IF NOT EXISTS ohlcv (
    id SERIAL,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(20, 2) NOT NULL,
    high DECIMAL(20, 2) NOT NULL,
    low DECIMAL(20, 2) NOT NULL,
    close DECIMAL(20, 2) NOT NULL,
    volume DECIMAL(30, 8) NOT NULL,
    PRIMARY KEY (id, timestamp)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_positions_agent ON positions(agent_id);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_decisions_agent ON decisions(agent_id);
CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_agent ON trades(agent_id);
CREATE INDEX IF NOT EXISTS idx_trades_executed_at ON trades(executed_at);
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol ON ohlcv(symbol);
CREATE INDEX IF NOT EXISTS idx_ohlcv_timestamp ON ohlcv(timestamp);
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timestamp ON ohlcv(symbol, timestamp);

-- 将ohlcv表转换为Hypertable（TimescaleDB）
SELECT create_hypertable('ohlcv', 'timestamp', if_not_exists => TRUE);

-- 设置数据保留策略（可选：保留最近30天的数据）
-- SELECT add_retention_policy('ohlcv', INTERVAL '30 days', if_not_exists => TRUE);
