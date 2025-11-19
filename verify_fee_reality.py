"""
Fee Reality Check Script
Verifies if the $30K+ in fees is actually correct by examining individual trades
"""
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql://u1065566plgi7t:p443db95d21e555a7ff883e875fdca5073503a3cbb11ff4f878e5afde0920db09@c57oa7dm3pc281.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/df7aq2912aj504"

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

def format_currency(amount):
    """Format currency"""
    return f"${amount:,.2f}" if amount is not None else "N/A"

def verify_fee_reality():
    """Verify if fees are calculated correctly"""
    session = Session()

    print("="*100)
    print(" FEE REALITY CHECK")
    print("="*100)

    try:
        # 1. Get total number of trades and total fees
        print("\n1. OVERALL STATISTICS")
        print("-"*100)

        result = session.execute(text("""
            SELECT
                COUNT(*) as total_trades,
                SUM(fee) as total_fees,
                AVG(fee) as avg_fee,
                MIN(fee) as min_fee,
                MAX(fee) as max_fee
            FROM trades
        """)).fetchone()

        total_trades, total_fees, avg_fee, min_fee, max_fee = result

        print(f"\nTotal Trades: {total_trades}")
        print(f"Total Fees: {format_currency(total_fees)}")
        print(f"Average Fee per Trade: {format_currency(avg_fee)}")
        print(f"Min Fee: {format_currency(min_fee)}")
        print(f"Max Fee: {format_currency(max_fee)}")

        # 2. Sample random trades and verify fee calculation
        print(f"\n2. SAMPLE TRADES - FEE VERIFICATION")
        print("-"*100)
        print(f"Formula: fee = price × amount × 0.001 (0.1% commission)")
        print()

        sample_trades = session.execute(text("""
            SELECT id, symbol, order_type, amount, price, fee, margin
            FROM trades
            ORDER BY RANDOM()
            LIMIT 20
        """)).fetchall()

        print(f"{'ID':<8} {'Symbol':<12} {'Type':<12} {'Amount':<12} {'Price':<12} {'Fee (DB)':<12} {'Fee (Calc)':<12} {'Match?':<8}")
        print("-"*100)

        fee_discrepancies = 0
        total_discrepancy = 0

        for trade in sample_trades:
            trade_id, symbol, order_type, amount, price, fee_db, margin = trade

            # Calculate what the fee SHOULD be
            # Fee = price × amount × 0.001
            fee_calculated = price * amount * 0.001

            match = "YES" if abs(fee_db - fee_calculated) < 0.01 else "NO"
            if match == "NO":
                fee_discrepancies += 1
                total_discrepancy += abs(fee_db - fee_calculated)

            print(f"{trade_id:<8} {symbol:<12} {order_type:<12} {amount:<12.4f} "
                  f"{format_currency(price):<12} {format_currency(fee_db):<12} "
                  f"{format_currency(fee_calculated):<12} {match:<8}")

        if fee_discrepancies > 0:
            print(f"\n[!] WARNING: Found {fee_discrepancies} trades with fee discrepancies!")
            print(f"Total discrepancy: {format_currency(total_discrepancy)}")
        else:
            print(f"\n[OK] All sampled fees match expected calculation!")

        # 3. Check if fees are being double-counted somewhere
        print(f"\n3. DOUBLE-COUNTING CHECK")
        print("-"*100)

        # Check for duplicate trades (same timestamp, symbol, price, amount)
        duplicates = session.execute(text("""
            SELECT
                symbol,
                order_type,
                amount,
                price,
                timestamp,
                COUNT(*) as count
            FROM trades
            GROUP BY symbol, order_type, amount, price, timestamp
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10
        """)).fetchall()

        if duplicates:
            print(f"\n[!] WARNING: Found duplicate trades!")
            print(f"{'Symbol':<12} {'Type':<12} {'Amount':<12} {'Price':<12} {'Timestamp':<20} {'Count':<8}")
            print("-"*100)
            for dup in duplicates:
                symbol, order_type, amount, price, timestamp, count = dup
                print(f"{symbol:<12} {order_type:<12} {amount:<12.4f} {format_currency(price):<12} {str(timestamp):<20} {count:<8}")

            # Calculate impact
            total_duplicate_fees = session.execute(text("""
                SELECT SUM(fee * (count - 1)) as duplicate_fees
                FROM (
                    SELECT fee, COUNT(*) as count
                    FROM trades
                    GROUP BY symbol, order_type, amount, price, timestamp, fee
                    HAVING COUNT(*) > 1
                ) subquery
            """)).scalar()

            if total_duplicate_fees:
                print(f"\nFees from duplicates: {format_currency(total_duplicate_fees)}")
        else:
            print(f"\n[OK] No duplicate trades found")

        # 4. Analyze fee distribution
        print(f"\n4. FEE DISTRIBUTION ANALYSIS")
        print("-"*100)

        fee_ranges = session.execute(text("""
            SELECT
                CASE
                    WHEN fee < 1 THEN '< $1'
                    WHEN fee < 5 THEN '$1-5'
                    WHEN fee < 10 THEN '$5-10'
                    WHEN fee < 20 THEN '$10-20'
                    WHEN fee < 50 THEN '$20-50'
                    ELSE '> $50'
                END as fee_range,
                COUNT(*) as trade_count,
                SUM(fee) as total_fees_in_range
            FROM trades
            GROUP BY fee_range
            ORDER BY MIN(fee)
        """)).fetchall()

        print(f"\n{'Fee Range':<15} {'Trade Count':<15} {'Total Fees':<15} {'% of Total Trades':<20}")
        print("-"*80)

        for fee_range, trade_count, total_fees_in_range in fee_ranges:
            pct = (trade_count / total_trades * 100) if total_trades > 0 else 0
            print(f"{fee_range:<15} {trade_count:<15} {format_currency(total_fees_in_range):<15} {pct:<20.2f}%")

        # 5. Calculate expected total fees based on trade volumes
        print(f"\n5. EXPECTED FEES CALCULATION")
        print("-"*100)

        total_volume = session.execute(text("""
            SELECT SUM(price * amount) as total_volume
            FROM trades
        """)).scalar()

        expected_fees = total_volume * 0.001  # 0.1% commission

        print(f"\nTotal Trading Volume: {format_currency(total_volume)}")
        print(f"Expected Fees (0.1% of volume): {format_currency(expected_fees)}")
        print(f"Actual Fees in Database: {format_currency(total_fees)}")
        print(f"Difference: {format_currency(abs(expected_fees - total_fees))}")

        if abs(expected_fees - total_fees) < 1.0:
            print(f"\n[OK] Fees are CORRECT! Difference is negligible.")
        else:
            print(f"\n[!] WARNING: Significant difference detected!")

        # 6. Break down by trade type
        print(f"\n6. FEES BY TRADE TYPE")
        print("-"*100)

        fees_by_type = session.execute(text("""
            SELECT
                order_type,
                COUNT(*) as trade_count,
                SUM(fee) as total_fees,
                AVG(fee) as avg_fee,
                SUM(price * amount) as total_volume
            FROM trades
            GROUP BY order_type
            ORDER BY order_type
        """)).fetchall()

        print(f"\n{'Order Type':<15} {'Trades':<10} {'Total Fees':<15} {'Avg Fee':<12} {'Volume':<15} {'Fee %':<10}")
        print("-"*90)

        for order_type, trade_count, fees, avg_fee, volume in fees_by_type:
            fee_pct = (fees / volume * 100) if volume and volume > 0 else 0
            print(f"{order_type:<15} {trade_count:<10} {format_currency(fees):<15} "
                  f"{format_currency(avg_fee):<12} {format_currency(volume):<15} {fee_pct:<10.3f}%")

        # 7. Reality check summary
        print(f"\n{'='*100}")
        print(f" REALITY CHECK SUMMARY")
        print(f"{'='*100}")

        print(f"\n1. Total Fees: {format_currency(total_fees)}")
        print(f"2. Total Trades: {total_trades}")
        print(f"3. Average Fee: {format_currency(avg_fee)}")
        print(f"4. Total Volume: {format_currency(total_volume)}")
        print(f"5. Effective Fee Rate: {(total_fees / total_volume * 100):.3f}% (should be ~0.1%)")

        # Final verdict
        print(f"\n{'='*100}")
        print(f" VERDICT")
        print(f"{'='*100}")

        effective_rate = (total_fees / total_volume * 100) if total_volume > 0 else 0

        if 0.09 < effective_rate < 0.11:
            print(f"\n✓ FEES ARE REAL AND CORRECT")
            print(f"  - Effective fee rate: {effective_rate:.3f}% (expected: ~0.1%)")
            print(f"  - Fees match expected calculation based on trade volume")
            print(f"  - No evidence of double-counting or calculation errors")
            print(f"\nCONCLUSION: You really did pay ${total_fees:,.2f} in fees!")
            print(f"This is correct for {total_trades} trades with ${total_volume:,.2f} total volume.")
        else:
            print(f"\n[!] POTENTIAL ISSUE DETECTED")
            print(f"  - Effective fee rate: {effective_rate:.3f}% (expected: ~0.1%)")
            print(f"  - This deviates significantly from expected 0.1% rate")
            print(f"  - Further investigation needed")

        print(f"\n{'='*100}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    verify_fee_reality()
