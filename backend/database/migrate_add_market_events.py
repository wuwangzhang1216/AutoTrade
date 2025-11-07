"""
Database migration: Add market_events table

This script creates the market_events table for Event Monitor functionality.
Can be run independently or as part of the main database initialization.
"""
from database.models import Base, get_engine, MarketEventRecord
from utils.logger import logger, log_success, log_error


def migrate_add_market_events_table():
    """
    Add market_events table to database

    This migration:
    1. Creates the market_events table if it doesn't exist
    2. Adds necessary indexes for performance
    3. Is idempotent (safe to run multiple times)
    """
    try:
        logger.info("Starting database migration: Add market_events table")

        # Get database engine
        engine = get_engine()

        # Create only the MarketEventRecord table
        # Note: create_all() is idempotent - it won't recreate existing tables
        MarketEventRecord.__table__.create(engine, checkfirst=True)

        log_success("✓ Market events table created successfully")
        logger.info("Migration complete")

        # Display table schema
        logger.info("\nTable schema:")
        logger.info("  table: market_events")
        logger.info("  columns:")
        for column in MarketEventRecord.__table__.columns:
            logger.info(f"    - {column.name}: {column.type}")

        return True

    except Exception as e:
        log_error(f"Migration failed: {e}")
        return False


def verify_migration():
    """Verify that the migration was successful"""
    try:
        from database.models import get_session
        from sqlalchemy import inspect

        engine = get_engine()
        inspector = inspect(engine)

        # Check if table exists
        if 'market_events' in inspector.get_table_names():
            log_success("✓ Verification: market_events table exists")

            # Check columns
            columns = inspector.get_columns('market_events')
            column_names = [col['name'] for col in columns]

            expected_columns = [
                'id', 'timestamp', 'symbol', 'event_type',
                'severity', 'description', 'suggested_action',
                'metrics', 'processed'
            ]

            missing_columns = set(expected_columns) - set(column_names)
            if missing_columns:
                log_error(f"✗ Missing columns: {missing_columns}")
                return False

            log_success(f"✓ All {len(expected_columns)} columns present")

            # Check indexes
            indexes = inspector.get_indexes('market_events')
            logger.info(f"✓ Found {len(indexes)} indexes on market_events")

            return True
        else:
            log_error("✗ Verification failed: market_events table not found")
            return False

    except Exception as e:
        log_error(f"Verification error: {e}")
        return False


if __name__ == "__main__":
    """Run migration when executed directly"""
    logger.info("=" * 70)
    logger.info("AutoTrade Event Monitor - Database Migration")
    logger.info("=" * 70)

    # Run migration
    success = migrate_add_market_events_table()

    if success:
        # Verify migration
        logger.info("\nVerifying migration...")
        if verify_migration():
            log_success("\n✓ Migration completed and verified successfully!")
        else:
            log_error("\n✗ Migration verification failed")
    else:
        log_error("\n✗ Migration failed")

    logger.info("=" * 70)
