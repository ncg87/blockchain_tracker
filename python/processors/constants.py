# processors/constants.py
from datetime import timedelta
from typing import Dict, NamedTuple

class TimeWindow(NamedTuple):
    interval: timedelta  # Size of each bucket
    duration: timedelta  # Total window duration
    update_frequency: timedelta  # How often to update

TIME_WINDOWS = {
    '5m': TimeWindow(
        interval=timedelta(minutes=5),
        duration=timedelta(days=1),
        update_frequency=timedelta(minutes=5)
    ),
    '30m': TimeWindow(
        interval=timedelta(minutes=30),
        duration=timedelta(days=7),
        update_frequency=timedelta(minutes=30)
    ),
    '1h': TimeWindow(
        interval=timedelta(hours=1),
        duration=timedelta(days=7),
        update_frequency=timedelta(hours=1)
    ),
    '3h': TimeWindow(
        interval=timedelta(hours=3),
        duration=timedelta(days=14),
        update_frequency=timedelta(hours=3)
    ),
    '12h': TimeWindow(
        interval=timedelta(hours=12),
        duration=timedelta(days=30),
        update_frequency=timedelta(hours=12)
    ),
    '1d': TimeWindow(
        interval=timedelta(days=1),
        duration=timedelta(days=90),
        update_frequency=timedelta(days=1)
    )
}
