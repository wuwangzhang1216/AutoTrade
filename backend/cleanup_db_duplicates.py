"""
Database cleanup script to remove duplicate account snapshots.
Keeps only one snapshot per minute, removing the rest.
"""
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import get_session, AccountSnapshot
from sqlalchemy import func

def cleanup_duplicate_snapshots():
    """Remove duplicate snapshots, keeping only one per 5-minute interval"""
    session = get_session()

    try:
        # Get all snapshots ordered by timestamp
        all_snapshots = session.query(AccountSnapshot)\
            .order_by(AccountSnapshot.timestamp.asc())\
            .all()

        print(f"Total snapshots in database: {len(all_snapshots)}")

        # Group snapshots by 5-minute interval
        # AI decision cycle is 5 minutes, so keep one snapshot per 5-minute window
        snapshots_by_interval = defaultdict(list)

        for snapshot in all_snapshots:
            # Round timestamp to nearest 5-minute interval
            # Convert to timestamp, round down to 5-minute mark, convert back
            ts = snapshot.timestamp
            minute = (ts.minute // 5) * 5  # Round down to 0, 5, 10, 15, etc.
            interval_key = ts.replace(minute=minute, second=0, microsecond=0)
            snapshots_by_interval[interval_key].append(snapshot)

        # Find duplicates and mark for deletion
        to_delete = []
        duplicates_found = 0

        for interval, snapshots in snapshots_by_interval.items():
            if len(snapshots) > 1:
                duplicates_found += 1
                # Keep the LAST snapshot in each 5-minute interval (most recent data after trades)
                # Delete all others
                to_delete.extend(snapshots[:-1])

                if duplicates_found <= 5:  # Show first 5 examples
                    print(f"\n5-min interval {interval.strftime('%Y-%m-%d %H:%M')}:")
                    print(f"  Found {len(snapshots)} snapshots, keeping latest, deleting {len(snapshots)-1}")
                    for s in snapshots:
                        action = "DELETE" if s in to_delete else "KEEP"
                        print(f"    [{action}] {s.timestamp.strftime('%H:%M:%S')} - Equity: ${s.total_equity:.2f}")

        print(f"\n{'='*80}")
        print(f"Summary:")
        print(f"  Total 5-minute intervals with duplicates: {duplicates_found}")
        print(f"  Total snapshots to delete: {len(to_delete)}")
        print(f"  Snapshots to keep: {len(all_snapshots) - len(to_delete)}")
        print(f"  Reduction: {len(to_delete) / len(all_snapshots) * 100:.1f}%")
        print(f"{'='*80}")

        if len(to_delete) > 0:
            confirm = input(f"\nDelete {len(to_delete)} duplicate snapshots? (yes/no): ")

            if confirm.lower() == 'yes':
                # Delete duplicates
                deleted_count = 0
                for snapshot in to_delete:
                    session.delete(snapshot)
                    deleted_count += 1

                    if deleted_count % 100 == 0:
                        print(f"Deleted {deleted_count}/{len(to_delete)} snapshots...")

                session.commit()
                print(f"\n✓ Successfully deleted {deleted_count} duplicate snapshots")
                print(f"✓ Database now has {len(all_snapshots) - deleted_count} clean snapshots")

                # Verify
                remaining = session.query(AccountSnapshot).count()
                print(f"✓ Verified: {remaining} snapshots remain in database")

            else:
                print("Cleanup cancelled")
        else:
            print("No duplicates found!")

    except Exception as e:
        session.rollback()
        print(f"Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    cleanup_duplicate_snapshots()
