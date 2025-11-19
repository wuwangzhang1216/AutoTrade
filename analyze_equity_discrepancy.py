"""
Database Analysis Script - Equity Discrepancy Investigation
Investigates why total equity is showing losses despite positive trade income
"""
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func, desc, asc, text
from sqlalchemy.orm import sessionmaker
import pandas as pd

# Database connection
DATABASE_URL = "postgresql://u1065566plgi7t:p443db95d21e555a7ff883e875fdca5073503a3cbb11ff4f878e5afde0920db09@c57oa7dm3pc281.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/df7aq2912aj504"

# Create engine
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def print_section(title):
    """Print formatted section"""
    print("\n" + "-"*80)
    print(f" {title}")
    print("-"*80)

def format_currency(amount):
    """Format currency"""
    return f"${amount:,.2f}" if amount is not None else "N/A"

def format_percent(value):
    """Format percentage"""
    return f"{value:.2f}%" if value is not None else "N/A"

def analyze_database():
    """Main analysis function"""
    session = Session()

    try:
        print_header("EQUITY DISCREPANCY ANALYSIS")
        print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 1. DATABASE SCHEMA OVERVIEW
        print_section("1. Database Schema Overview")

        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print(f"\nTables in database: {', '.join(tables)}")

        # 2. ACCOUNT SNAPSHOTS ANALYSIS
        print_section("2. Account Snapshots Analysis")

        result = session.execute(text("""
            SELECT
                COUNT(*) as total_snapshots,
                MIN(timestamp) as first_snapshot,
                MAX(timestamp) as last_snapshot,
                MIN(total_equity) as min_equity,
                MAX(total_equity) as max_equity,
                AVG(total_equity) as avg_equity
            FROM account_snapshots
        """)).fetchone()

        print(f"\nTotal Snapshots: {result[0]}")
        print(f"First Snapshot: {result[1]}")
        print(f"Last Snapshot: {result[2]}")
        print(f"Min Equity: {format_currency(result[3])}")
        print(f"Max Equity: {format_currency(result[4])}")
        print(f"Avg Equity: {format_currency(result[5])}")

        # Get latest snapshot details
        latest = session.execute(text("""
            SELECT capital, total_margin, unrealized_pnl, total_equity,
                   open_positions, total_trades, winning_trades, losing_trades, total_fees
            FROM account_snapshots
            ORDER BY timestamp DESC
            LIMIT 1
        """)).fetchone()

        if latest:
            print(f"\nLatest Snapshot Details:")
            print(f"  Capital: {format_currency(latest[0])}")
            print(f"  Total Margin: {format_currency(latest[1])}")
            print(f"  Unrealized PnL: {format_currency(latest[2])}")
            print(f"  Total Equity: {format_currency(latest[3])}")
            print(f"  Open Positions: {latest[4]}")
            print(f"  Total Trades: {latest[5]}")
            print(f"  Winning Trades: {latest[6]}")
            print(f"  Losing Trades: {latest[7]}")
            print(f"  Total Fees: {format_currency(latest[8])}")

            # Verify equity calculation
            calculated_equity = latest[0] + latest[1] + latest[2]
            print(f"\n  Equity Verification:")
            print(f"    Stored Equity: {format_currency(latest[3])}")
            print(f"    Calculated (Capital + Margin + Unrealized PnL): {format_currency(calculated_equity)}")
            print(f"    Difference: {format_currency(latest[3] - calculated_equity)}")

        # 3. TRADES ANALYSIS
        print_section("3. Trades Analysis")

        # Get trade statistics
        trades_stats = session.execute(text("""
            SELECT
                order_type,
                COUNT(*) as count,
                SUM(fee) as total_fees,
                AVG(fee) as avg_fee,
                SUM(CASE WHEN pnl IS NOT NULL THEN pnl ELSE 0 END) as total_pnl,
                SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) as total_profit,
                SUM(CASE WHEN pnl < 0 THEN pnl ELSE 0 END) as total_loss
            FROM trades
            GROUP BY order_type
            ORDER BY order_type
        """)).fetchall()

        print("\nTrades by Order Type:")
        print(f"{'Order Type':<15} {'Count':<8} {'Total Fees':<15} {'Avg Fee':<12} {'Total PnL':<15} {'Profit':<15} {'Loss':<15}")
        print("-" * 110)

        total_fees_all_trades = 0
        total_pnl_all_trades = 0

        for row in trades_stats:
            order_type, count, total_fees, avg_fee, total_pnl, total_profit, total_loss = row
            total_fees_all_trades += total_fees or 0
            total_pnl_all_trades += total_pnl or 0

            print(f"{order_type:<15} {count:<8} {format_currency(total_fees or 0):<15} {format_currency(avg_fee or 0):<12} "
                  f"{format_currency(total_pnl or 0):<15} {format_currency(total_profit or 0):<15} {format_currency(total_loss or 0):<15}")

        print(f"\nTotal Fees (All Trades): {format_currency(total_fees_all_trades)}")
        print(f"Total PnL (From Close Trades): {format_currency(total_pnl_all_trades)}")

        # 4. DETAILED TRADE ANALYSIS
        print_section("4. Recent Trades (Last 20)")

        recent_trades = session.execute(text("""
            SELECT id, timestamp, symbol, order_type, side, amount, price, fee, pnl, margin, leverage
            FROM trades
            ORDER BY timestamp DESC
            LIMIT 20
        """)).fetchall()

        print(f"\n{'ID':<6} {'Timestamp':<20} {'Symbol':<12} {'Type':<12} {'Side':<6} {'Amount':<10} {'Price':<12} {'Fee':<10} {'PnL':<12} {'Margin':<12}")
        print("-" * 140)

        for trade in recent_trades:
            trade_id, ts, symbol, order_type, side, amount, price, fee, pnl, margin, leverage = trade
            print(f"{trade_id:<6} {str(ts):<20} {symbol:<12} {order_type:<12} {str(side):<6} {amount:<10.4f} "
                  f"{format_currency(price):<12} {format_currency(fee):<10} {format_currency(pnl or 0):<12} {format_currency(margin or 0):<12}")

        # 5. FEE ANALYSIS
        print_section("5. Fee Analysis")

        # Calculate fees by operation type
        open_trades = session.execute(text("""
            SELECT COUNT(*), SUM(fee)
            FROM trades
            WHERE order_type IN ('OPEN_LONG', 'OPEN_SHORT')
        """)).fetchone()

        close_trades = session.execute(text("""
            SELECT COUNT(*), SUM(fee)
            FROM trades
            WHERE order_type IN ('CLOSE_LONG', 'CLOSE_SHORT')
        """)).fetchone()

        print(f"\nFees Breakdown:")
        print(f"  Open Trades: {open_trades[0]} trades, Total Fees: {format_currency(open_trades[1] or 0)}")
        print(f"  Close Trades: {close_trades[0]} trades, Total Fees: {format_currency(close_trades[1] or 0)}")
        print(f"  Total: {format_currency((open_trades[1] or 0) + (close_trades[1] or 0))}")

        # 6. EQUITY CHANGE ANALYSIS
        print_section("6. Equity Change Over Time")

        equity_changes = session.execute(text("""
            SELECT
                timestamp,
                total_equity,
                capital,
                total_margin,
                unrealized_pnl,
                total_fees
            FROM account_snapshots
            ORDER BY timestamp ASC
            LIMIT 10
        """)).fetchall()

        print(f"\nFirst 10 Equity Snapshots:")
        print(f"{'Timestamp':<20} {'Equity':<15} {'Capital':<15} {'Margin':<15} {'Unrealized PnL':<15} {'Total Fees':<15}")
        print("-" * 110)

        for row in equity_changes:
            ts, equity, capital, margin, unrealized, fees = row
            print(f"{str(ts):<20} {format_currency(equity):<15} {format_currency(capital):<15} "
                  f"{format_currency(margin):<15} {format_currency(unrealized):<15} {format_currency(fees):<15}")

        # Last 10 snapshots
        equity_changes_recent = session.execute(text("""
            SELECT
                timestamp,
                total_equity,
                capital,
                total_margin,
                unrealized_pnl,
                total_fees
            FROM account_snapshots
            ORDER BY timestamp DESC
            LIMIT 10
        """)).fetchall()

        print(f"\nLast 10 Equity Snapshots:")
        print(f"{'Timestamp':<20} {'Equity':<15} {'Capital':<15} {'Margin':<15} {'Unrealized PnL':<15} {'Total Fees':<15}")
        print("-" * 110)

        for row in equity_changes_recent:
            ts, equity, capital, margin, unrealized, fees = row
            print(f"{str(ts):<20} {format_currency(equity):<15} {format_currency(capital):<15} "
                  f"{format_currency(margin):<15} {format_currency(unrealized):<15} {format_currency(fees):<15}")

        # 7. CAPITAL FLOW ANALYSIS
        print_section("7. Capital Flow Analysis")

        # Get initial and final equity
        initial_snapshot = session.execute(text("""
            SELECT total_equity, capital, total_fees, timestamp
            FROM account_snapshots
            ORDER BY timestamp ASC
            LIMIT 1
        """)).fetchone()

        final_snapshot = session.execute(text("""
            SELECT total_equity, capital, total_fees, timestamp
            FROM account_snapshots
            ORDER BY timestamp DESC
            LIMIT 1
        """)).fetchone()

        if initial_snapshot and final_snapshot:
            initial_equity = initial_snapshot[0]
            final_equity = final_snapshot[0]
            equity_change = final_equity - initial_equity

            initial_fees = initial_snapshot[2]
            final_fees = final_snapshot[2]
            total_fees_paid = final_fees - initial_fees if initial_fees else final_fees

            print(f"\nInitial Snapshot ({initial_snapshot[3]}):")
            print(f"  Equity: {format_currency(initial_equity)}")
            print(f"  Capital: {format_currency(initial_snapshot[1])}")
            print(f"  Cumulative Fees: {format_currency(initial_fees)}")

            print(f"\nFinal Snapshot ({final_snapshot[3]}):")
            print(f"  Equity: {format_currency(final_equity)}")
            print(f"  Capital: {format_currency(final_snapshot[1])}")
            print(f"  Cumulative Fees: {format_currency(final_fees)}")

            print(f"\nOverall Change:")
            print(f"  Equity Change: {format_currency(equity_change)} ({format_percent(equity_change/initial_equity*100 if initial_equity else 0)})")
            print(f"  Fees Paid: {format_currency(total_fees_paid)}")

            # Calculate realized PnL from closed trades
            realized_pnl = session.execute(text("""
                SELECT SUM(pnl)
                FROM trades
                WHERE order_type IN ('CLOSE_LONG', 'CLOSE_SHORT')
                AND pnl IS NOT NULL
            """)).scalar()

            print(f"  Realized PnL (from trades): {format_currency(realized_pnl or 0)}")
            print(f"  Expected Equity (Initial + Realized PnL - Fees): {format_currency(initial_equity + (realized_pnl or 0) - total_fees_paid)}")
            print(f"  Actual Equity: {format_currency(final_equity)}")
            print(f"  Discrepancy: {format_currency(final_equity - (initial_equity + (realized_pnl or 0) - total_fees_paid))}")

        # 8. POSITION ANALYSIS
        print_section("8. Open Positions Analysis")

        if latest and latest[4] > 0:
            # Get positions from latest snapshot
            positions_data = session.execute(text("""
                SELECT positions
                FROM account_snapshots
                ORDER BY timestamp DESC
                LIMIT 1
            """)).scalar()

            if positions_data:
                import json
                print(f"\nOpen Positions (from latest snapshot):")
                print(json.dumps(positions_data, indent=2))
        else:
            print("\nNo open positions currently.")

        # 9. MATCH OPEN/CLOSE TRADES
        print_section("9. Trade Pairs Analysis (Open vs Close)")

        # Get all symbols that have been traded
        symbols_traded = session.execute(text("""
            SELECT DISTINCT symbol FROM trades ORDER BY symbol
        """)).fetchall()

        print(f"\nAnalyzing {len(symbols_traded)} traded symbols...")

        for (symbol,) in symbols_traded:
            open_count = session.execute(text("""
                SELECT COUNT(*) FROM trades
                WHERE symbol = :symbol AND order_type IN ('OPEN_LONG', 'OPEN_SHORT')
            """), {'symbol': symbol}).scalar()

            close_count = session.execute(text("""
                SELECT COUNT(*) FROM trades
                WHERE symbol = :symbol AND order_type IN ('CLOSE_LONG', 'CLOSE_SHORT')
            """), {'symbol': symbol}).scalar()

            if open_count != close_count:
                print(f"  {symbol}: {open_count} opens, {close_count} closes (MISMATCH: {open_count - close_count} unclosed)")

        # 10. DUPLICATE SNAPSHOT ANALYSIS
        print_section("10. Duplicate Snapshot Detection")

        duplicates = session.execute(text("""
            SELECT
                DATE_TRUNC('minute', timestamp) as minute,
                COUNT(*) as count
            FROM account_snapshots
            GROUP BY DATE_TRUNC('minute', timestamp)
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10
        """)).fetchall()

        if duplicates:
            print(f"\nFound {len(duplicates)} minutes with multiple snapshots:")
            for minute, count in duplicates:
                print(f"  {minute}: {count} snapshots")
        else:
            print("\nNo duplicate snapshots found within same minute.")

        # 11. SUMMARY AND RECOMMENDATIONS
        print_section("11. Summary and Potential Issues")

        print("\nKey Findings:")

        # Check for fee double-counting
        if latest:
            fees_in_snapshot = latest[8]
            fees_from_trades = total_fees_all_trades
            if abs(fees_in_snapshot - fees_from_trades) > 0.01:
                print(f"\n[!] FEE DISCREPANCY DETECTED:")
                print(f"    Fees in snapshot: {format_currency(fees_in_snapshot)}")
                print(f"    Fees from trades table: {format_currency(fees_from_trades)}")
                print(f"    Difference: {format_currency(abs(fees_in_snapshot - fees_from_trades))}")
                print(f"    This could indicate fee calculation inconsistency!")

        # Check for missing PnL in close trades
        close_with_null_pnl = session.execute(text("""
            SELECT COUNT(*) FROM trades
            WHERE order_type IN ('CLOSE_LONG', 'CLOSE_SHORT')
            AND pnl IS NULL
        """)).scalar()

        if close_with_null_pnl > 0:
            print(f"\n[!] MISSING PNL DATA:")
            print(f"    {close_with_null_pnl} close trades have NULL PnL")
            print(f"    This could affect equity calculations!")

        # Check equity formula consistency
        if latest:
            capital = latest[0]
            margin = latest[1]
            unrealized = latest[2]
            equity = latest[3]

            expected_equity = capital + margin + unrealized
            if abs(equity - expected_equity) > 0.01:
                print(f"\n[!] EQUITY CALCULATION ERROR:")
                print(f"    Stored equity: {format_currency(equity)}")
                print(f"    Expected equity: {format_currency(expected_equity)}")
                print(f"    Formula: capital ({format_currency(capital)}) + margin ({format_currency(margin)}) + unrealized_pnl ({format_currency(unrealized)})")
                print(f"    This indicates a bug in equity calculation!")

        print("\nAnalysis complete!")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        session.close()

if __name__ == "__main__":
    try:
        analyze_database()
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.")
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
