from ..base.base_processor import BaseTimeSeriesProcessor
from .metrics import DexMetrics

class DexProcessor(BaseTimeSeriesProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = DexMetrics()

    async def _process_window(self, window_key: str, window: TimeWindow):
        now = datetime.now(timezone.utc)
        start_time = now - window.duration
        
        active_pairs = await self.db.get_active_pairs()
        
        for pair in active_pairs:
            raw_data = await self.db.get_pair_data(
                pair_address=pair['address'],
                start_time=start_time,
                end_time=now
            )
            
            intervals = self._create_intervals(
                raw_data=raw_data,
                interval=window.interval,
                start_time=start_time,
                end_time=now
            )
            
            await self.cache.set_pair_intervals(
                pair_address=pair['address'],
                window_key=window_key,
                intervals=intervals
            )

    def _create_intervals(self, raw_data: List[Dict], interval: timedelta,
                         start_time: datetime, end_time: datetime) -> List[Dict]:
        intervals = []
        current_time = start_time

        while current_time < end_time:
            interval_end = min(current_time + interval, end_time)
            
            # Get data points for this interval
            interval_data = [
                point for point in raw_data
                if current_time <= datetime.fromtimestamp(point['timestamp'], timezone.utc) < interval_end
            ]
            
            # Calculate metrics
            swap_metrics = self.metrics.calculate_swap_metrics(interval_data)
            liquidity_metrics = self.metrics.calculate_liquidity_metrics(interval_data)
            
            # Combine metrics
            interval_metrics = {
                'timestamp': int(current_time.timestamp()),
                **swap_metrics,
                **liquidity_metrics
            }
            
            intervals.append(interval_metrics)
            current_time += interval

        return intervals