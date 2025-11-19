"""
Create new initial snapshot with $100K capital
Implements SOFT RESET strategy
"""
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql://u1065566plgi7t:p443db95d21e555a7ff883e875fdca5073503a3cbb11ff4f878e5afde0920db09@c57oa7dm3pc281.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/df7aq2912aj504"

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

def format_currency(amount):
    """Format currency"""
    return f"${amount:,.2f}" if amount is not None else "N/A"

def create_new_snapshot():
    """Create new initial snapshot with $100K capital"""
    session = Session()

    print("="*100)
    print(" CREATING NEW INITIAL SNAPSHOT")
    print("="*100)

    try:
        # Step 1: Check current state
        print("\n1. CURRENT STATE")
        print("-"*100)

        current_snapshot = session.execute(text("""
            SELECT timestamp, capital, total_equity, total_fees, total_trades
            FROM account_snapshots
            ORDER BY timestamp DESC
            LIMIT 1
        """)).fetchone()

        if current_snapshot:
            timestamp, capital, equity, fees, trades = current_snapshot
            print(f"\nMost Recent Snapshot:")
            print(f"  Timestamp: {timestamp}")
            print(f"  Capital: {format_currency(capital)}")
            print(f"  Total Equity: {format_currency(equity)}")
            print(f"  Total Fees: {format_currency(fees)}")
            print(f"  Total Trades: {trades}")

        # Get actual trade statistics
        actual_stats = session.execute(text("""
            SELECT
                COUNT(*) as total_trades,
                SUM(fee) as total_fees
            FROM trades
        """)).fetchone()

        total_trades, total_fees = actual_stats
        print(f"\nActual Database State:")
        print(f"  Total Trades in DB: {total_trades}")
        print(f"  Actual Total Fees: {format_currency(total_fees)}")

        # Step 2: Create new snapshot
        print("\n2. CREATING NEW SNAPSHOT")
        print("-"*100)

        new_capital = 100000.00
        print(f"\nNew Configuration:")
        print(f"  Starting Capital: {format_currency(new_capital)} (10x increase)")
        print(f"  Fee Rate: 0.05% (50% reduction from 0.1%)")
        print(f"  Leverage: 20x (unchanged)")
        print(f"\nStrategy: SOFT RESET")
        print(f"  - Historical trades preserved for AI learning")
        print(f"  - Fresh snapshot for clean performance tracking")
        print(f"  - New fee rate will apply to future trades")

        # Confirm before proceeding
        print(f"\n{'-'*100}")
        print(f"About to create new snapshot. This will:")
        print(f"  [+] Create fresh starting point with $100K")
        print(f"  [+] Reset trade/fee counters to 0")
        print(f"  [+] Keep all {total_trades} historical trades intact")
        print(f"{'-'*100}")

        # Create the new snapshot
        session.execute(text("""
            INSERT INTO account_snapshots (
                timestamp,
                capital,
                total_margin,
                unrealized_pnl,
                total_equity,
                open_positions,
                total_trades,
                winning_trades,
                losing_trades,
                total_fees,
                positions
            ) VALUES (
                NOW(),
                :capital,
                0.00,
                0.00,
                :equity,
                0,
                0,
                0,
                0,
                0.00,
                '{}'
            )
        """), {
            'capital': new_capital,
            'equity': new_capital
        })

        session.commit()

        print(f"\n[SUCCESS] New snapshot created!")

        # Step 3: Verify
        print("\n3. VERIFICATION")
        print("-"*100)

        new_snapshot = session.execute(text("""
            SELECT timestamp, capital, total_equity, total_fees, total_trades, open_positions
            FROM account_snapshots
            ORDER BY timestamp DESC
            LIMIT 1
        """)).fetchone()

        timestamp, capital, equity, fees, trades, positions = new_snapshot
        print(f"\nNew Snapshot Details:")
        print(f"  Timestamp: {timestamp}")
        print(f"  Capital: {format_currency(capital)}")
        print(f"  Total Equity: {format_currency(equity)}")
        print(f"  Total Fees: {format_currency(fees)}")
        print(f"  Total Trades: {trades}")
        print(f"  Open Positions: {positions}")

        # Impact analysis
        print("\n4. IMPACT ANALYSIS")
        print("-"*100)

        print(f"\nWith New Configuration (0.05% fee, $100K capital):")
        print(f"  Old fee per round-trip: ~$43.20")
        print(f"  New fee per round-trip: ~$21.60 (50% savings)")
        print(f"\nIf you had traded with this config:")
        print(f"  Old total fees ({total_trades} trades): {format_currency(total_fees)}")
        print(f"  New total fees (same trades): {format_currency(total_fees * 0.5)}")
        print(f"  Savings: {format_currency(total_fees * 0.5)}")

        print(f"\nBreak-Even Analysis:")
        print(f"  Old config: Need 0.2% price movement per round-trip")
        print(f"  New config: Need 0.1% price movement per round-trip")
        print(f"  Easier to profit: YES (50% lower threshold)")

        print("\n" + "="*100)
        print(" SNAPSHOT CREATION COMPLETE")
        print("="*100)

        print(f"\nNext Steps:")
        print(f"1. Deploy updated settings.py to Heroku")
        print(f"2. Restart Heroku dyno")
        print(f"3. Verify first few trades use 0.05% fee")
        print(f"4. Monitor performance with new configuration")

        print(f"\nExpected Results:")
        print(f"  [+] Lower fees = higher net profitability")
        print(f"  [+] More capital = better position sizing")
        print(f"  [+] Same strategy, better economics")

        print("\n" + "="*100)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    create_new_snapshot()
