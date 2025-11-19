-- Create New Initial Snapshot with $100K Capital
-- This implements a SOFT RESET: keeps historical data, creates fresh starting point
-- Generated: 2025-11-18
-- Strategy: Preserve trade history for AI learning while resetting with better config

-- ==============================================================================
-- STEP 1: Verify Current State
-- ==============================================================================

-- Check current snapshot
SELECT
    timestamp,
    capital,
    total_equity,
    total_fees,
    total_trades
FROM account_snapshots
ORDER BY timestamp DESC
LIMIT 5;

-- Check total trades in database
SELECT COUNT(*) as total_trades FROM trades;

-- Check actual total fees from all trades
SELECT SUM(fee) as actual_total_fees FROM trades;

-- ==============================================================================
-- STEP 2: Create New Initial Snapshot
-- ==============================================================================

-- Insert new snapshot with $100,000 starting capital
-- This becomes the new baseline for the trading system
INSERT INTO account_snapshots (
    timestamp,
    capital,              -- Available capital
    total_margin,         -- Margin in open positions (none initially)
    unrealized_pnl,       -- Unrealized profit/loss (none initially)
    total_equity,         -- Total account value
    open_positions,       -- Number of open positions
    total_trades,         -- Cumulative trade count (0 for fresh start)
    winning_trades,       -- Winning trades count
    losing_trades,        -- Losing trades count
    total_fees,           -- Cumulative fees paid (0 for fresh start)
    positions             -- JSON of current positions
) VALUES (
    NOW(),                -- Current timestamp
    100000.00,            -- $100,000 starting capital (10x increase)
    0.00,                 -- No margin used initially
    0.00,                 -- No unrealized PnL
    100000.00,            -- Total equity = capital (no positions)
    0,                    -- No open positions
    0,                    -- Reset trade counter for new configuration
    0,                    -- No winning trades yet
    0,                    -- No losing trades yet
    0.00,                 -- No fees paid yet (will use 0.05% going forward)
    '{}'                  -- Empty positions object
);

-- ==============================================================================
-- STEP 3: Verify New Snapshot Was Created
-- ==============================================================================

-- Check the new snapshot
SELECT
    timestamp,
    capital,
    total_equity,
    total_fees,
    total_trades,
    open_positions
FROM account_snapshots
ORDER BY timestamp DESC
LIMIT 1;

-- ==============================================================================
-- NOTES
-- ==============================================================================
--
-- What This Does:
-- ✓ Creates new baseline snapshot with $100K capital
-- ✓ Resets trade/fee counters for clean performance tracking
-- ✓ Preserves all historical trade data in 'trades' table
-- ✓ System will use new 0.05% fee rate (from settings.py update)
--
-- What This Does NOT Do:
-- ✗ Does not delete historical trades (data preserved for analysis)
-- ✗ Does not modify existing snapshots (all history intact)
-- ✗ Does not change exchange API configuration
--
-- Next Steps After Running This Script:
-- 1. Deploy updated settings.py to Heroku (0.05% fee, $100K capital)
-- 2. Restart Heroku dyno to load new configuration
-- 3. Verify system picks up new snapshot on next run
-- 4. Monitor first few trades to confirm 0.05% fee is being charged
--
-- Expected Impact:
-- - Fee per trade: ~$21.60 average → ~$10.80 average (50% reduction)
-- - With same 1,416 trades: $30,575 → $15,287 in fees (savings: $15,288)
-- - More capital = better position sizing flexibility
-- - Lower fees = need less profit per trade to break even
--
-- Break-Even Analysis:
-- Old config: Need 0.2% price movement per round-trip to cover fees
-- New config: Need 0.1% price movement per round-trip to cover fees
--
-- ==============================================================================
