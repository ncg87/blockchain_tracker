from ..base.base_processor import BaseTimeSeriesProcessor
from .metrics import TokenMetrics

class TokenProcessor(BaseTimeSeriesProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = TokenMetrics()

    async def _process_window(self, window_key: str, window: TimeWindow):
        now = datetime.now(timezone.utc)
        start_time = now - window.duration
        
        active_tokens = await self.db.get_active_tokens()
        
        for token in active_tokens:
            raw_data = await self.db.get_token_data(
                token_address=token['address'],
                start_time=start_time,
                end_time=now
            )
            
            intervals = self._create_intervals(
                raw_data=raw_data,
                interval=window.interval,
                start_time=start_time,
                end_time=now
            )
            
            await self.cache.set_token_intervals(
                token_address=token['address'],
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
            volume_metrics = self.metrics.calculate_volume_metrics(interval_data)
            price_metrics = self.metrics.calculate_price_metrics(interval_data)
            
            # Combine metrics
            interval_metrics = {
                'timestamp': int(current_time.timestamp()),
                **volume_metrics,
                **price_metrics
            }
            
            intervals.append(interval_metrics)
            current_time += interval

        return intervals