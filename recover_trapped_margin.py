"""
Trapped Margin Recovery Script
Analyzes unclosed positions in database and helps recover trapped margin
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add paths
sys.path.insert(0, 'E:\\AutoTrade')
sys.path.insert(0, 'E:\\AutoTrade\\backend')
os.chdir('E:\\AutoTrade\\backend')

# Database connection
DATABASE_URL = "postgresql://u1065566plgi7t:p443db95d21e555a7ff883e875fdca5073503a3cbb11ff4f878e5afde0920db09@c57oa7dm3pc281.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/df7aq2912aj504"

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

def format_currency(amount):
    """Format currency"""
    return f"${amount:,.2f}" if amount is not None else "N/A"

def format_datetime(dt):
    """Format datetime"""
    if dt is None:
        return "N/A"
    return dt.strftime('%Y-%m-%d %H:%M:%S')

class UnclosedPosition:
    """Represents an unclosed position from database"""
    def __init__(self, symbol, side, amount, price, margin, fee, timestamp, trade_id):
        self.symbol = symbol
        self.side = side
        self.amount = amount
        self.price = price
        self.margin = margin
        self.fee = fee
        self.timestamp = timestamp
        self.trade_id = trade_id

    def __repr__(self):
        return f"<UnclosedPosition {self.symbol} {self.side} amt={self.amount} @{self.price}>"

def analyze_unclosed_positions():
    """Analyze all unclosed positions and calculate trapped margin"""
    session = Session()

    print("="*100)
    print(" TRAPPED MARGIN RECOVERY ANALYSIS")
    print("="*100)

    try:
        # Get all symbols with unclosed positions
        symbols_query = text("""
            SELECT
                symbol,
                COUNT(CASE WHEN order_type IN ('OPEN_LONG', 'OPEN_SHORT') THEN 1 END) as opens,
                COUNT(CASE WHEN order_type IN ('CLOSE_LONG', 'CLOSE_SHORT') THEN 1 END) as closes,
                COUNT(CASE WHEN order_type IN ('OPEN_LONG', 'OPEN_SHORT') THEN 1 END) -
                COUNT(CASE WHEN order_type IN ('CLOSE_LONG', 'CLOSE_SHORT') THEN 1 END) as unclosed_count
            FROM trades
            GROUP BY symbol
            HAVING COUNT(CASE WHEN order_type IN ('OPEN_LONG', 'OPEN_SHORT') THEN 1 END) >
                   COUNT(CASE WHEN order_type IN ('CLOSE_LONG', 'CLOSE_SHORT') THEN 1 END)
            ORDER BY unclosed_count DESC
        """)

        symbols_with_unclosed = session.execute(symbols_query).fetchall()

        print(f"\nFound {len(symbols_with_unclosed)} symbols with unclosed positions")
        print("-"*100)

        total_trapped_margin = 0
        total_unclosed = 0
        all_unclosed_positions = []

        for symbol, opens, closes, unclosed_count in symbols_with_unclosed:
            print(f"\n{'='*100}")
            print(f"Symbol: {symbol}")
            print(f"  Opens: {opens} | Closes: {closes} | Unclosed: {unclosed_count}")
            print(f"{'='*100}")

            # Get all open trades for this symbol
            open_trades_query = text("""
                SELECT id, timestamp, order_type, side, amount, price, margin, fee
                FROM trades
                WHERE symbol = :symbol
                AND order_type IN ('OPEN_LONG', 'OPEN_SHORT')
                ORDER BY timestamp ASC
            """)

            open_trades = session.execute(open_trades_query, {'symbol': symbol}).fetchall()

            # Get all close trades for this symbol
            close_trades_query = text("""
                SELECT id, timestamp, order_type, side, amount, price, pnl, fee
                FROM trades
                WHERE symbol = :symbol
                AND order_type IN ('CLOSE_LONG', 'CLOSE_SHORT')
                ORDER BY timestamp ASC
            """)

            close_trades = session.execute(close_trades_query, {'symbol': symbol}).fetchall()

            # Match open and close trades (FIFO basis)
            unclosed_opens = []
            open_index = 0
            close_index = 0

            # Simple FIFO matching
            while open_index < len(open_trades):
                if close_index < len(close_trades):
                    # This open has a corresponding close
                    close_index += 1
                else:
                    # No more closes, this open is unclosed
                    unclosed_opens.append(open_trades[open_index])
                open_index += 1

            if unclosed_opens:
                print(f"\n  UNCLOSED POSITIONS ({len(unclosed_opens)}):")
                print(f"  {'ID':<8} {'Timestamp':<20} {'Type':<12} {'Side':<6} {'Amount':<12} {'Price':<12} {'Margin':<12} {'Fee':<10}")
                print(f"  {'-'*95}")

                symbol_trapped_margin = 0

                for trade in unclosed_opens:
                    trade_id, timestamp, order_type, side, amount, price, margin, fee = trade

                    print(f"  {trade_id:<8} {str(timestamp):<20} {order_type:<12} {side:<6} "
                          f"{amount:<12.4f} {format_currency(price):<12} {format_currency(margin):<12} {format_currency(fee):<10}")

                    symbol_trapped_margin += margin if margin else 0

                    # Store for later analysis
                    unclosed_pos = UnclosedPosition(
                        symbol=symbol,
                        side=side,
                        amount=amount,
                        price=price,
                        margin=margin if margin else 0,
                        fee=fee if fee else 0,
                        timestamp=timestamp,
                        trade_id=trade_id
                    )
                    all_unclosed_positions.append(unclosed_pos)

                print(f"\n  Trapped Margin for {symbol}: {format_currency(symbol_trapped_margin)}")
                total_trapped_margin += symbol_trapped_margin
                total_unclosed += len(unclosed_opens)

        # Summary
        print(f"\n{'='*100}")
        print(f" SUMMARY")
        print(f"{'='*100}")
        print(f"\nTotal Unclosed Positions: {total_unclosed}")
        print(f"Total Trapped Margin: {format_currency(total_trapped_margin)}")
        print(f"Average Margin per Position: {format_currency(total_trapped_margin / total_unclosed if total_unclosed > 0 else 0)}")

        # Age analysis
        print(f"\n{'='*100}")
        print(f" AGE ANALYSIS")
        print(f"{'='*100}")

        now = datetime.now()
        age_categories = {
            '< 1 day': [],
            '1-7 days': [],
            '7-30 days': [],
            '> 30 days': []
        }

        for pos in all_unclosed_positions:
            age = now - pos.timestamp.replace(tzinfo=None) if pos.timestamp.tzinfo else now - pos.timestamp

            if age < timedelta(days=1):
                age_categories['< 1 day'].append(pos)
            elif age < timedelta(days=7):
                age_categories['1-7 days'].append(pos)
            elif age < timedelta(days=30):
                age_categories['7-30 days'].append(pos)
            else:
                age_categories['> 30 days'].append(pos)

        for category, positions in age_categories.items():
            if positions:
                margin = sum(p.margin for p in positions)
                print(f"\n{category}: {len(positions)} positions, {format_currency(margin)} trapped")

        # Recovery recommendations
        print(f"\n{'='*100}")
        print(f" RECOVERY RECOMMENDATIONS")
        print(f"{'='*100}")

        print(f"\n1. RECENT POSITIONS (< 7 days old):")
        recent_positions = age_categories['< 1 day'] + age_categories['1-7 days']
        if recent_positions:
            recent_margin = sum(p.margin for p in recent_positions)
            print(f"   Count: {len(recent_positions)}")
            print(f"   Trapped Margin: {format_currency(recent_margin)}")
            print(f"   Recommendation: These might still exist on exchange - PRIORITY RECOVERY")
            print(f"   Action: Check exchange API for open positions and sync them")
        else:
            print(f"   None found")

        print(f"\n2. OLD POSITIONS (> 7 days old):")
        old_positions = age_categories['7-30 days'] + age_categories['> 30 days']
        if old_positions:
            old_margin = sum(p.margin for p in old_positions)
            print(f"   Count: {len(old_positions)}")
            print(f"   Trapped Margin: {format_currency(old_margin)}")
            print(f"   Recommendation: Likely liquidated or manually closed")
            print(f"   Action: Write these off OR create closing trades to clean database")
        else:
            print(f"   None found")

        # Generate recovery script recommendations
        print(f"\n{'='*100}")
        print(f" NEXT STEPS")
        print(f"{'='*100}")

        print(f"\n1. Verify Current Exchange Positions:")
        print(f"   - Run: Check actual open positions on Binance/exchange")
        print(f"   - Compare with database unclosed positions")
        print(f"   - Identify which positions are truly lost vs still open")

        print(f"\n2. For Positions Still on Exchange:")
        print(f"   - Option A: Manually close them via exchange")
        print(f"   - Option B: Sync them back into trading engine")
        print(f"   - Option C: Let AI system close them naturally")

        print(f"\n3. For Lost/Liquidated Positions:")
        print(f"   - Create compensating CLOSE trades in database")
        print(f"   - Mark PnL as realized loss")
        print(f"   - Clean up database integrity")

        print(f"\n4. Prevent Future Issues:")
        print(f"   - Implement position persistence (save to DB)")
        print(f"   - Add position restoration on restart")
        print(f"   - Add position reconciliation checks")

        # Save detailed report
        print(f"\n{'='*100}")
        print(f" GENERATING DETAILED REPORT...")
        print(f"{'='*100}")

        with open('E:\\AutoTrade\\unclosed_positions_report.txt', 'w') as f:
            f.write("UNCLOSED POSITIONS DETAILED REPORT\n")
            f.write("="*100 + "\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Total Unclosed: {total_unclosed}\n")
            f.write(f"Total Trapped Margin: {format_currency(total_trapped_margin)}\n\n")

            # Group by symbol
            symbol_groups = {}
            for pos in all_unclosed_positions:
                if pos.symbol not in symbol_groups:
                    symbol_groups[pos.symbol] = []
                symbol_groups[pos.symbol].append(pos)

            for symbol, positions in sorted(symbol_groups.items(), key=lambda x: len(x[1]), reverse=True):
                f.write(f"\n{symbol} ({len(positions)} positions)\n")
                f.write("-"*100 + "\n")

                for pos in positions:
                    age = now - (pos.timestamp.replace(tzinfo=None) if pos.timestamp.tzinfo else pos.timestamp)
                    f.write(f"  ID: {pos.trade_id} | ")
                    f.write(f"Time: {format_datetime(pos.timestamp)} | ")
                    f.write(f"Age: {age.days}d {age.seconds//3600}h | ")
                    f.write(f"Side: {pos.side} | ")
                    f.write(f"Amount: {pos.amount:.4f} | ")
                    f.write(f"Price: {format_currency(pos.price)} | ")
                    f.write(f"Margin: {format_currency(pos.margin)} | ")
                    f.write(f"Fee: {format_currency(pos.fee)}\n")

                symbol_margin = sum(p.margin for p in positions)
                f.write(f"  Subtotal: {format_currency(symbol_margin)}\n")

        print(f"\nDetailed report saved to: unclosed_positions_report.txt")

        return all_unclosed_positions, total_trapped_margin

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return [], 0
    finally:
        session.close()

def generate_cleanup_sql(unclosed_positions: List[UnclosedPosition], strategy='write_off'):
    """
    Generate SQL to clean up unclosed positions

    Args:
        unclosed_positions: List of unclosed positions
        strategy: 'write_off' (mark as lost) or 'sync' (sync with exchange)
    """
    print(f"\n{'='*100}")
    print(f" SQL CLEANUP SCRIPT GENERATOR")
    print(f"{'='*100}")

    if strategy == 'write_off':
        print(f"\nStrategy: WRITE OFF (create closing trades with loss)")
        print(f"\nWARNING: This will create CLOSE trades marking these positions as losses!")
        print(f"Only use this if you're SURE these positions no longer exist on exchange.\n")

        sql_file = 'E:\\AutoTrade\\cleanup_unclosed_positions.sql'

        with open(sql_file, 'w') as f:
            f.write("-- SQL Script to Clean Up Unclosed Positions\n")
            f.write("-- Strategy: Write Off Lost Positions\n")
            f.write(f"-- Generated: {datetime.now()}\n")
            f.write("-- REVIEW CAREFULLY BEFORE EXECUTING!\n\n")
            f.write("BEGIN;\n\n")

            for pos in unclosed_positions:
                # Determine close type
                close_type = 'CLOSE_LONG' if pos.side == 'LONG' else 'CLOSE_SHORT'

                # Assume total loss (margin + fee)
                pnl = -(pos.margin + pos.fee)

                f.write(f"-- Closing orphaned {pos.side} position for {pos.symbol}\n")
                f.write(f"-- Original trade ID: {pos.trade_id}, opened at {format_datetime(pos.timestamp)}\n")
                f.write(f"INSERT INTO trades (\n")
                f.write(f"  symbol, order_type, side, amount, price, fee, pnl, margin, leverage,\n")
                f.write(f"  timestamp, reason\n")
                f.write(f") VALUES (\n")
                f.write(f"  '{pos.symbol}',\n")
                f.write(f"  '{close_type}',\n")
                f.write(f"  '{pos.side}',\n")
                f.write(f"  {pos.amount},\n")
                f.write(f"  {pos.price},\n")
                f.write(f"  {pos.fee},\n")
                f.write(f"  {pnl},  -- Total loss: margin + fee\n")
                f.write(f"  0,  -- Margin returned is 0 (lost)\n")
                f.write(f"  20,  -- Leverage\n")
                f.write(f"  NOW(),\n")
                f.write(f"  'CLEANUP: Write off unclosed position from trade #{pos.trade_id}'\n")
                f.write(f");\n\n")

            f.write("-- Review the above inserts carefully!\n")
            f.write("-- If everything looks correct, uncomment the line below:\n")
            f.write("-- COMMIT;\n")
            f.write("-- Otherwise:\n")
            f.write("ROLLBACK;\n")

        print(f"SQL script saved to: {sql_file}")
        print(f"\nTo execute:")
        print(f"1. Review the SQL file carefully")
        print(f"2. Change ROLLBACK to COMMIT if you want to apply changes")
        print(f"3. Run: psql [DATABASE_URL] -f {sql_file}")

    else:
        print(f"\nStrategy: SYNC (not implemented yet)")
        print(f"This would sync positions from exchange API")

if __name__ == "__main__":
    print("Starting trapped margin recovery analysis...\n")

    try:
        unclosed_positions, total_trapped = analyze_unclosed_positions()

        print(f"\n{'='*100}")
        print(f" RECOVERY OPTIONS")
        print(f"{'='*100}")

        if unclosed_positions:
            print(f"\nWould you like to:")
            print(f"1. Generate SQL cleanup script (write off lost positions)")
            print(f"2. Export positions to CSV for manual review")
            print(f"3. Exit (manual recovery)")

            print(f"\nFor now, detailed reports have been generated.")
            print(f"Review 'unclosed_positions_report.txt' and decide next steps.")

            # Optionally generate cleanup script
            # Uncomment below to auto-generate
            # generate_cleanup_sql(unclosed_positions, strategy='write_off')

        else:
            print(f"\nNo unclosed positions found. Database is clean!")

    except KeyboardInterrupt:
        print(f"\n\nAnalysis interrupted by user.")
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
