"""
Clear all database tables and reset to fresh state
"""
import os
from database.models import (
    get_engine,
    Base,
    Trade,
    AIDecision,
    AccountSnapshot,
    MarketDataCache,
    SystemLog
)

def clear_database():
    """Drop all tables and recreate them"""

    print("=" * 60)
    print("CLEARING DATABASE")
    print("=" * 60)

    # Get database path
    db_path = "E:/AutoTrade/autotrade.db"

    if os.path.exists(db_path):
        print(f"\nDatabase file: {db_path}")
        print(f"File size: {os.path.getsize(db_path) / 1024:.2f} KB")
    else:
        print(f"\nDatabase file not found: {db_path}")
        print("Creating new database...")

    # Get engine
    engine = get_engine()

    # Drop all tables
    print("\nDropping all tables...")
    Base.metadata.drop_all(engine)
    print("  All tables dropped")

    # Recreate all tables
    print("\nRecreating tables...")
    Base.metadata.create_all(engine)
    print("  All tables recreated")

    # Verify
    from database.models import get_session
    session = get_session()

    trade_count = session.query(Trade).count()
    decision_count = session.query(AIDecision).count()
    snapshot_count = session.query(AccountSnapshot).count()

    print("\nVerification:")
    print(f"  Trades: {trade_count}")
    print(f"  AI Decisions: {decision_count}")
    print(f"  Account Snapshots: {snapshot_count}")

    session.close()

    print("\n" + "=" * 60)
    print("DATABASE CLEARED SUCCESSFULLY!")
    print("=" * 60)
    print("\nThe database is now empty and ready for fresh data.")
    print("Restart the trading system to begin with a clean state.")

if __name__ == "__main__":
    import sys

    # Confirm before clearing
    print("\nWARNING: This will DELETE ALL DATA from the database!")
    print("This action cannot be undone.")

    response = input("\nAre you sure you want to clear the database? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        clear_database()
    else:
        print("\nOperation cancelled.")
        sys.exit(0)
