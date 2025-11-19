"""
Verification script to test the fee tracking fix
Compares old (in-memory) vs new (database) fee calculation methods
"""
import sys
import os

# Add both paths
sys.path.insert(0, 'E:\\AutoTrade')
sys.path.insert(0, 'E:\\AutoTrade\\backend')
os.chdir('E:\\AutoTrade\\backend')

from database.db_manager import DatabaseManager
from core.trading_engine import TradingEngine

def format_currency(amount):
    """Format currency"""
    return f"${amount:,.2f}" if amount is not None else "N/A"

def verify_fee_fix():
    """Verify that the fee tracking fix is working"""
    print("="*80)
    print(" FEE TRACKING FIX VERIFICATION")
    print("="*80)

    # Initialize components
    db = DatabaseManager()

    print("\n1. Database Method (NEW - Source of Truth)")
    print("-" * 80)

    # Get total fees from database (NEW METHOD)
    db_total_fees = db.get_total_fees()
    print(f"Total Fees from Database: {format_currency(db_total_fees)}")
    print(f"  Method: SUM(fee) from trades table")
    print(f"  Source: All trades ever recorded")

    print("\n2. Performance Stats Method")
    print("-" * 80)

    # Get fees from performance stats
    perf_stats = db.get_performance_stats()
    if perf_stats:
        perf_fees = perf_stats.get('total_fees', 0)
        print(f"Total Fees from Performance Stats: {format_currency(perf_fees)}")
        print(f"  Method: Uses get_total_fees() internally")
        print(f"  Match: {'YES' if abs(db_total_fees - perf_fees) < 0.01 else 'NO'}")

    print("\n3. Trading Engine Method (OLD - In-Memory Counter)")
    print("-" * 80)

    # Create a trading engine instance to test
    # NOTE: This will have total_fees = 0 because it just started
    trading_engine = TradingEngine(initial_capital=10000)
    in_memory_fees = trading_engine.total_fees
    print(f"In-Memory Total Fees: {format_currency(in_memory_fees)}")
    print(f"  Method: In-memory counter (resets on restart)")
    print(f"  Source: Fees since program started")
    print(f"  Status: UNRELIABLE - This is why we need the database method")

    # Test the new method
    print("\n4. Trading Engine with Database Method (NEW)")
    print("-" * 80)

    actual_fees_from_engine = trading_engine.get_actual_total_fees_from_db()
    print(f"Total Fees via Engine DB Method: {format_currency(actual_fees_from_engine)}")
    print(f"  Method: Calls db.get_total_fees()")
    print(f"  Source: Database (reliable)")
    print(f"  Match with Database: {'YES' if abs(db_total_fees - actual_fees_from_engine) < 0.01 else 'NO'}")

    print("\n5. Summary")
    print("="*80)

    print(f"\nDatabase Total Fees:    {format_currency(db_total_fees)}")
    print(f"In-Memory Total Fees:   {format_currency(in_memory_fees)}")
    print(f"Discrepancy:            {format_currency(db_total_fees - in_memory_fees)}")

    if abs(db_total_fees - in_memory_fees) > 1.0:
        print(f"\n[!] WARNING: Large discrepancy detected!")
        print(f"    This confirms the in-memory counter is unreliable.")
        print(f"    The fix ensures we always use the database value ({format_currency(db_total_fees)})")
    else:
        print(f"\n[OK] No discrepancy detected (program just started)")

    # Check if account summary will use the correct value
    print("\n6. Account Summary Test")
    print("="*80)

    # Get account summary (this should use the NEW method)
    current_prices = {'BTC/USDT': 90000, 'ETH/USDT': 3000, 'SOL/USDT': 140}
    summary = trading_engine.get_account_summary(current_prices)

    print(f"\nAccount Summary total_fees: {format_currency(summary['total_fees'])}")
    print(f"Expected (from database):   {format_currency(db_total_fees)}")
    print(f"Match: {'YES - FIX WORKING!' if abs(summary['total_fees'] - db_total_fees) < 0.01 else 'NO - FIX NOT WORKING'}")

    print("\n7. Conclusion")
    print("="*80)

    if abs(summary['total_fees'] - db_total_fees) < 0.01:
        print("\n[SUCCESS] Fee tracking fix is working correctly!")
        print(f"  - Account snapshots will now show accurate fees: {format_currency(db_total_fees)}")
        print(f"  - This fixes the ${abs(db_total_fees - in_memory_fees):,.2f} discrepancy")
        print(f"  - Total fees are calculated from database, not unreliable in-memory counter")
    else:
        print("\n[FAILED] Fee tracking fix is NOT working!")
        print(f"  - Expected: {format_currency(db_total_fees)}")
        print(f"  - Got: {format_currency(summary['total_fees'])}")
        print(f"  - Check the implementation of get_actual_total_fees_from_db()")

    print("\n" + "="*80)

if __name__ == "__main__":
    try:
        verify_fee_fix()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
