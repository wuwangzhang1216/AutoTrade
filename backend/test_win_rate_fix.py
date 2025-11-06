"""
Test script to verify win rate calculation fix
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from database import get_session, Trade, AccountSnapshot, init_database
from database.db_manager import DatabaseManager
from datetime import datetime

def test_win_rate_calculation():
    """Test win rate calculation with sample data"""
    print("=" * 60)
    print("WIN RATE CALCULATION TEST")
    print("=" * 60)

    # Initialize database
    init_database()
    session = get_session()
    db = DatabaseManager()

    # Clean up test data
    print("\n1. Cleaning up existing test data...")
    session.query(Trade).filter(Trade.symbol == 'TEST/USDT').delete()
    session.query(AccountSnapshot).delete()
    session.commit()

    # Create test trades
    print("\n2. Creating test trades...")

    # Trade 1: Winning trade (+$100)
    session.add(Trade(
        symbol='TEST/USDT',
        order_type='OPEN_LONG',
        amount=1.0,
        price=1000.0,
        fee=1.0,
        timestamp=datetime.now()
    ))
    session.add(Trade(
        symbol='TEST/USDT',
        order_type='CLOSE_LONG',
        side='LONG',
        amount=1.0,
        price=1100.0,
        fee=1.0,
        pnl=100.0,  # Winning trade
        timestamp=datetime.now()
    ))

    # Trade 2: Losing trade (-$50)
    session.add(Trade(
        symbol='TEST/USDT',
        order_type='OPEN_SHORT',
        amount=1.0,
        price=2000.0,
        fee=2.0,
        timestamp=datetime.now()
    ))
    session.add(Trade(
        symbol='TEST/USDT',
        order_type='CLOSE_SHORT',
        side='SHORT',
        amount=1.0,
        price=2050.0,
        fee=2.0,
        pnl=-50.0,  # Losing trade
        timestamp=datetime.now()
    ))

    # Trade 3: Winning trade (+$200)
    session.add(Trade(
        symbol='TEST/USDT',
        order_type='OPEN_LONG',
        amount=2.0,
        price=1500.0,
        fee=3.0,
        timestamp=datetime.now()
    ))
    session.add(Trade(
        symbol='TEST/USDT',
        order_type='CLOSE_LONG',
        side='LONG',
        amount=2.0,
        price=1600.0,
        fee=3.0,
        pnl=200.0,  # Winning trade
        timestamp=datetime.now()
    ))

    session.commit()
    print("   [OK] Created 3 completed trades (2 wins, 1 loss)")

    # Test the save_account_snapshot calculation
    print("\n3. Testing save_account_snapshot calculation...")

    account_data = {
        'capital': 10000.0,
        'total_equity': 10250.0,
        'total_margin': 0.0,
        'unrealized_pnl': 0.0,
        'open_positions': 0,
        'total_fees': 12.0,
        'positions': {}
    }

    snapshot = db.save_account_snapshot(account_data)

    print(f"\n   Snapshot statistics:")
    print(f"   - Total trades: {snapshot.total_trades}")
    print(f"   - Winning trades: {snapshot.winning_trades}")
    print(f"   - Losing trades: {snapshot.losing_trades}")

    # Verify calculations
    print("\n4. Verifying calculations...")

    expected_total = 3  # 3 CLOSE trades
    expected_winning = 2  # 2 trades with pnl > 0
    expected_losing = 1  # 1 trade with pnl < 0
    expected_win_rate = (2 / 3) * 100  # 66.67%

    actual_win_rate = (snapshot.winning_trades / snapshot.total_trades * 100) if snapshot.total_trades > 0 else 0

    errors = []
    if snapshot.total_trades != expected_total:
        errors.append(f"   [FAIL] Total trades: expected {expected_total}, got {snapshot.total_trades}")
    else:
        print(f"   [OK] Total trades: {snapshot.total_trades} (correct)")

    if snapshot.winning_trades != expected_winning:
        errors.append(f"   [FAIL] Winning trades: expected {expected_winning}, got {snapshot.winning_trades}")
    else:
        print(f"   [OK] Winning trades: {snapshot.winning_trades} (correct)")

    if snapshot.losing_trades != expected_losing:
        errors.append(f"   [FAIL] Losing trades: expected {expected_losing}, got {snapshot.losing_trades}")
    else:
        print(f"   [OK] Losing trades: {snapshot.losing_trades} (correct)")

    if abs(actual_win_rate - expected_win_rate) > 0.1:
        errors.append(f"   [FAIL] Win rate: expected {expected_win_rate:.1f}%, got {actual_win_rate:.1f}%")
    else:
        print(f"   [OK] Win rate: {actual_win_rate:.1f}% (correct)")

    # Clean up
    print("\n5. Cleaning up test data...")
    session.query(Trade).filter(Trade.symbol == 'TEST/USDT').delete()
    session.query(AccountSnapshot).filter(AccountSnapshot.id == snapshot.id).delete()
    session.commit()
    session.close()
    print("   [OK] Test data cleaned up")

    # Summary
    print("\n" + "=" * 60)
    if errors:
        print("TEST FAILED!")
        print("\nErrors found:")
        for error in errors:
            print(error)
        return False
    else:
        print("TEST PASSED!")
        print("\nAll calculations are correct.")
        return True

if __name__ == "__main__":
    success = test_win_rate_calculation()
    sys.exit(0 if success else 1)
