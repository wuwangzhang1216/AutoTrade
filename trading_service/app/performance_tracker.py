from typing import Dict, List
from datetime import datetime
from collections import deque


class PerformanceTracker:
    """Tracks portfolio value history for charting"""

    def __init__(self, max_points: int = 288):  # 24 hours of 5-minute intervals
        self.max_points = max_points
        # Store snapshots as list of dicts with timestamp and agent values
        self.snapshots: deque = deque(maxlen=max_points)

    def record_snapshot(self, agent_values: Dict[str, float]):
        """
        Record a snapshot of all agent portfolio values

        Args:
            agent_values: Dict mapping agent_id to current portfolio value
        """
        snapshot = {
            'timestamp': datetime.utcnow().isoformat(),
            **agent_values  # Spread agent values into snapshot
        }
        self.snapshots.append(snapshot)

    def get_history(self, limit: int = None) -> List[Dict]:
        """
        Get performance history

        Args:
            limit: Optional limit on number of snapshots to return (most recent)

        Returns:
            List of snapshots with timestamp and agent values
        """
        snapshots_list = list(self.snapshots)

        if limit and limit < len(snapshots_list):
            return snapshots_list[-limit:]

        return snapshots_list

    def get_chart_data(self) -> List[Dict]:
        """
        Get data formatted for chart consumption

        Returns:
            List of dicts with 'date' field and agent values
        """
        chart_data = []

        for snapshot in self.snapshots:
            # Format timestamp as relative time for x-axis
            timestamp = snapshot['timestamp']
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

            # Create readable label
            time_label = dt.strftime('%H:%M')

            point = {'date': time_label}

            # Add all agent values
            for key, value in snapshot.items():
                if key != 'timestamp':
                    point[key] = round(value, 2)

            chart_data.append(point)

        return chart_data
