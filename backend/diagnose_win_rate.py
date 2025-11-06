"""
Diagnostic script to check win rate calculation issue
"""
from database import get_session, Trade, AccountSnapshot
from sqlalchemy import desc

def diagnose_win_rate():
    """Check database state for win rate calculation"""
    session = get_session()

    print("=" * 60)
    print("WIN RATE DIAGNOSTIC REPORT")
    print("=" * 60)

    # Check all trades
    all_trades = session.query(Trade).all()
    print(f"\n1. TOTAL TRADES IN DATABASE: {len(all_trades)}")

    # Check OPEN trades
    open_trades = session.query(Trade).filter(
        Trade.order_type.in_(['OPEN_LONG', 'OPEN_SHORT'])
    ).all()
    print(f"   - OPEN trades: {len(open_trades)}")

    # Check CLOSE trades
    close_trades = session.query(Trade).filter(
        Trade.order_type.in_(['CLOSE_LONG', 'CLOSE_SHORT'])
    ).all()
    print(f"   - CLOSE trades: {len(close_trades)}")

    # Analyze CLOSE trades
    print(f"\n2. CLOSE TRADES ANALYSIS:")
    if close_trades:
        trades_with_pnl = [t for t in close_trades if t.pnl is not None]
        trades_without_pnl = [t for t in close_trades if t.pnl is None]

        print(f"   - CLOSE trades with PnL: {len(trades_with_pnl)}")
        print(f"   - CLOSE trades WITHOUT PnL: {len(trades_without_pnl)}")

        if trades_with_pnl:
            winning = [t for t in trades_with_pnl if t.pnl > 0]
            losing = [t for t in trades_with_pnl if t.pnl < 0]
            breakeven = [t for t in trades_with_pnl if t.pnl == 0]

            print(f"\n   PnL Distribution:")
            print(f"   - Winning (PnL > 0): {len(winning)}")
            print(f"   - Losing (PnL < 0): {len(losing)}")
            print(f"   - Breakeven (PnL = 0): {len(breakeven)}")

            if winning:
                print(f"\n   Sample winning trades:")
                for t in winning[:3]:
                    print(f"     {t.symbol} | PnL: ${t.pnl:.2f} | Price: ${t.price:.2f}")

            if losing:
                print(f"\n   Sample losing trades:")
                for t in losing[:3]:
                    print(f"     {t.symbol} | PnL: ${t.pnl:.2f} | Price: ${t.price:.2f}")

        if trades_without_pnl:
            print(f"\n   WARNING: {len(trades_without_pnl)} CLOSE trades have NULL PnL!")
            print(f"   Sample CLOSE trades without PnL:")
            for t in trades_without_pnl[:3]:
                print(f"     {t.symbol} | Type: {t.order_type} | Price: ${t.price:.2f} | PnL: {t.pnl}")
    else:
        print("   No CLOSE trades found!")

    # Check latest snapshot
    print(f"\n3. LATEST ACCOUNT SNAPSHOT:")
    latest = session.query(AccountSnapshot).order_by(desc(AccountSnapshot.timestamp)).first()

    if latest:
        print(f"   - Total trades: {latest.total_trades}")
        print(f"   - Winning trades: {latest.winning_trades}")
        print(f"   - Losing trades: {latest.losing_trades}")
        print(f"   - Win rate: {latest.winning_trades / (latest.winning_trades + latest.losing_trades) * 100 if (latest.winning_trades + latest.losing_trades) > 0 else 0:.1f}%")
        print(f"   - Timestamp: {latest.timestamp}")
    else:
        print("   No snapshots found!")

    # Calculate what SHOULD be
    print(f"\n4. CORRECT CALCULATION:")
    close_trades_with_pnl = [t for t in close_trades if t.pnl is not None]
    winning_count = sum(1 for t in close_trades_with_pnl if t.pnl > 0)
    losing_count = sum(1 for t in close_trades_with_pnl if t.pnl < 0)
    total_completed = winning_count + losing_count

    print(f"   - Total completed trades: {total_completed}")
    print(f"   - Winning: {winning_count}")
    print(f"   - Losing: {losing_count}")
    print(f"   - Win rate: {(winning_count / total_completed * 100) if total_completed > 0 else 0:.1f}%")

    print("\n" + "=" * 60)

    session.close()

if __name__ == "__main__":
    diagnose_win_rate()
