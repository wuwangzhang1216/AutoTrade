"""
Account Reset Script
Resets the trading account with new initial balance and fee configuration
"""
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql://u1065566plgi7t:p443db95d21e555a7ff883e875fdca5073503a3cbb11ff4f878e5afde0920db09@c57oa7dm3pc281.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/df7aq2912aj504"

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

def reset_account():
    """Reset account with new configuration"""
    session = Session()

    print("="*100)
    print(" ACCOUNT RESET CONFIGURATION")
    print("="*100)

    # Configuration
    NEW_INITIAL_CAPITAL = 100000.0
    NEW_FEE_RATE = 0.0005  # 0.05% (half of previous 0.1%)

    print(f"\nNew Configuration:")
    print(f"  Initial Capital: ${NEW_INITIAL_CAPITAL:,.2f}")
    print(f"  Fee Rate: {NEW_FEE_RATE*100}% (was 0.1%)")
    print(f"  Fee Reduction: 50%")

    try:
        # Get current stats
        current = session.execute(text("""
            SELECT
                COUNT(*) as total_trades,
                SUM(fee) as total_fees,
                (SELECT total_equity FROM account_snapshots ORDER BY timestamp DESC LIMIT 1) as current_equity
            FROM trades
        """)).fetchone()

        total_trades, total_fees, current_equity = current

        print(f"\nCurrent Account Status:")
        print(f"  Total Trades: {total_trades}")
        print(f"  Total Fees Paid: ${total_fees:,.2f}")
        print(f"  Current Equity: ${current_equity:,.2f}")

        print(f"\n{'='*100}")
        print(f" IMPACT ANALYSIS WITH NEW CONFIGURATION")
        print(f"{'='*100}")

        # Calculate what fees would have been with new config
        new_fees = total_fees * 0.5  # 50% reduction
        savings = total_fees - new_fees

        print(f"\nIf you had started with new configuration:")
        print(f"  Old Fees (0.1%): ${total_fees:,.2f}")
        print(f"  New Fees (0.05%): ${new_fees:,.2f}")
        print(f"  Savings: ${savings:,.2f}")
        print(f"  New Equity Would Be: ${current_equity + savings:,.2f}")

        # With higher capital
        fee_percentage_of_capital_old = (total_fees / 10000) * 100
        fee_percentage_of_capital_new = (new_fees / NEW_INITIAL_CAPITAL) * 100

        print(f"\nFee Impact on Capital:")
        print(f"  Old Config ($10K capital, 0.1% fee): {fee_percentage_of_capital_old:.1f}% of capital lost to fees")
        print(f"  New Config ($100K capital, 0.05% fee): {fee_percentage_of_capital_new:.1f}% of capital lost to fees")

        print(f"\n{'='*100}")
        print(f" RESET OPTIONS")
        print(f"{'='*100}")

        print(f"\nOption 1: SOFT RESET (Recommended)")
        print(f"  - Keep all trade history for analysis")
        print(f"  - Create new snapshot with $100K capital")
        print(f"  - Future trades will use 0.05% fee")
        print(f"  - Preserves learning data")

        print(f"\nOption 2: HARD RESET (Clean Slate)")
        print(f"  - Delete ALL trades and snapshots")
        print(f"  - Start fresh with $100K")
        print(f"  - Lose all historical data")
        print(f"  - WARNING: Cannot be undone!")

        print(f"\n{'='*100}")
        print(f" IMPLEMENTATION STEPS")
        print(f"{'='*100}")

        print(f"\nTo implement SOFT RESET:")
        print(f"1. Update backend/core/trading_engine.py:")
        print(f"   - Change initial_capital = 100000")
        print(f"   - Change commission_rate = 0.0005  # 0.05%")
        print(f"")
        print(f"2. Create new initial snapshot:")
        print(f"   INSERT INTO account_snapshots (")
        print(f"     timestamp, capital, total_margin, unrealized_pnl,")
        print(f"     total_equity, open_positions, total_trades,")
        print(f"     winning_trades, losing_trades, total_fees, positions")
        print(f"   ) VALUES (")
        print(f"     NOW(), 100000, 0, 0, 100000, 0, 0, 0, 0, 0, '{{}}'")
        print(f"   );")
        print(f"")
        print(f"3. Restart the backend")

        print(f"\nTo implement HARD RESET:")
        print(f"1. Backup database first!")
        print(f"2. Run: DELETE FROM trades;")
        print(f"3. Run: DELETE FROM account_snapshots;")
        print(f"4. Run: DELETE FROM ai_decisions;")
        print(f"5. Update trading_engine.py as above")
        print(f"6. Restart backend")

        print(f"\n{'='*100}")
        print(f" RECOMMENDATION")
        print(f"{'='*100}")

        print(f"\nI recommend SOFT RESET because:")
        print(f"  ✓ Keeps historical data for AI learning")
        print(f"  ✓ Can analyze old trades vs new configuration")
        print(f"  ✓ Safer (can always do hard reset later)")
        print(f"  ✓ Preserves evidence of fee tracking bug fix")

        print(f"\nWith new config, same 1,428 trades would have cost:")
        print(f"  Old: ${total_fees:,.2f}")
        print(f"  New: ${new_fees:,.2f}")
        print(f"  You save: ${savings:,.2f} ({(savings/total_fees*100):.0f}%)")

        print(f"\n{'='*100}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    reset_account()
