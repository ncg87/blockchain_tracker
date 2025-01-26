class DexMetrics:
    @staticmethod
    def calculate_swap_metrics(data_points: List[Dict]) -> Dict:
        """Calculate swap-related metrics"""
        return {
            'volume_token0': sum(point['amount0'] for point in data_points),
            'volume_token1': sum(point['amount1'] for point in data_points),
            'volume_usd': sum(point['volume_usd'] for point in data_points),
            'swap_count': len(data_points),
            'unique_traders': len(set(point['trader'] for point in data_points)),
            'fee_usd': sum(point['fee_usd'] for point in data_points)
        }

    @staticmethod
    def calculate_liquidity_metrics(data_points: List[Dict]) -> Dict:
        """Calculate liquidity-related metrics"""
        if not data_points:
            return {
                'liquidity': 0,
                'liquidity_token0': 0,
                'liquidity_token1': 0
            }

        latest = data_points[-1]
        return {
            'liquidity': latest['liquidity_usd'],
            'liquidity_token0': latest['reserve0'],
            'liquidity_token1': latest['reserve1']
        }