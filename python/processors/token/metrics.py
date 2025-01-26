from typing import List, Dict
from datetime import datetime, timezone

class TokenMetrics:
    @staticmethod
    def calculate_volume_metrics(data_points: List[Dict]) -> Dict:
        """Calculate volume-related metrics"""
        return {
            'volume': sum(point['volume'] for point in data_points),
            'volume_buy': sum(point['volume'] for point in data_points if point['is_buy']),
            'volume_sell': sum(point['volume'] for point in data_points if not point['is_buy']),
            'trade_count': len(data_points),
            'unique_traders': len(set(point['trader'] for point in data_points))
        }

    @staticmethod
    def calculate_price_metrics(data_points: List[Dict]) -> Dict:
        """Calculate price-related metrics"""
        if not data_points:
            return {
                'price_high': 0,
                'price_low': 0,
                'price_open': 0,
                'price_close': 0
            }

        prices = [point['price'] for point in data_points]
        return {
            'price_high': max(prices),
            'price_low': min(prices),
            'price_open': data_points[0]['price'],
            'price_close': data_points[-1]['price']
        }