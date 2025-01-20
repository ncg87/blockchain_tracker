from ..base import BaseOperations
from typing import Dict
from decimal import Decimal
from ...queries import (
    get_all_networks_volume_query, 
    get_network_volume_query,
    get_network_fees_query,
    get_all_networks_fees_query,
    get_network_tx_count_query,
    get_all_networks_tx_count_query,
    get_network_historical_data_query
)

class APIQueryOperations(BaseOperations):
    def get_network_volume(self, network: str, interval_seconds: int) -> float:
        """Get volume for a specific network in native units"""
        try:
            query = get_network_volume_query(network, interval_seconds)
            self.db.cursor.execute(query)
            result = self.db.cursor.fetchone()
            
            # Volume is already converted to native units in the SQL query
            return float(result['volume'])
        except Exception as e:
            self.db.logger.error(f"Error getting volume for {network}: {e}")
            return 0.0

    def get_all_networks_volume(self, interval_seconds: int) -> Dict[str, float]:
        """Get volume for all networks"""
        try:
            query = get_all_networks_volume_query(interval_seconds)
            self.db.cursor.execute(query)
            results = self.db.cursor.fetchall()
            
            volumes = {}
            for row in results:
                # Convert Decimal to float for JSON serialization
                volumes[row['network']] = float(row['volume'])
            
            return volumes
        except Exception as e:
            self.db.logger.error(f"Error getting all network volumes: {e}")
            return {}

    def get_network_stats(self, network: str, interval_seconds: int) -> Dict[str, float]:
        """Get comprehensive stats for a network"""
        try:
            if network in ['Ethereum', 'BNB', 'Base']:  # EVM networks
                query = """
                    SELECT 
                        COUNT(*) as tx_count,
                        CAST(SUM(value_wei) / 1e18 AS NUMERIC(36,18)) as volume,
                        CAST(AVG(value_wei) / 1e18 AS NUMERIC(36,18)) as avg_tx_value,
                        CAST(AVG(total_gas) AS NUMERIC(36,18)) as avg_gas
                    FROM base_evm_transactions
                    WHERE network = %s
                    AND timestamp >= extract(epoch from now()) - %s
                """
            elif network == 'Bitcoin':
                query = """
                    SELECT 
                        COUNT(*) as tx_count,
                        CAST(SUM(value_satoshis) / 100000000.0 AS NUMERIC(36,18)) as volume,
                        CAST(AVG(value_satoshis) / 100000000.0 AS NUMERIC(36,18)) as avg_tx_value,
                        CAST(AVG(fee) AS NUMERIC(36,18)) as avg_fee
                    FROM base_bitcoin_transactions
                    WHERE timestamp >= extract(epoch from now()) - %s
                """
            elif network == 'Solana':
                query = """
                    SELECT 
                        COUNT(*) as tx_count,
                        CAST(SUM(value_lamports) / 1000000000.0 AS NUMERIC(36,18)) as volume,
                        CAST(AVG(value_lamports) / 1000000000.0 AS NUMERIC(36,18)) as avg_tx_value,
                        CAST(AVG(fee_lamports) / 1000000000.0 AS NUMERIC(36,18)) as avg_fee
                    FROM base_solana_transactions
                    WHERE timestamp >= extract(epoch from now()) - %s
                """
            
            params = [network, interval_seconds] if network in ['Ethereum', 'BNB', 'Base'] else [interval_seconds]
            self.db.cursor.execute(query, params)
            return dict(self.db.cursor.fetchone())
            
        except Exception as e:
            self.db.logger.error(f"Error getting stats for {network}: {e}")
            return {}

    def get_network_fees(self, network: str, interval_seconds: int) -> float:
        """Get total fees for a specific network in native units"""
        try:
            query = get_network_fees_query(network, interval_seconds)
            if not query:  # Handle unsupported networks
                return 0.0
                
            self.db.cursor.execute(query)
            result = self.db.cursor.fetchone()
            
            return float(result['total_fees'])
        except Exception as e:
            self.db.logger.error(f"Error getting fees for {network}: {e}")
            return 0.0

    def get_all_networks_fees(self, interval_seconds: int) -> Dict[str, float]:
        """Get total fees for all networks"""
        try:
            query = get_all_networks_fees_query(interval_seconds)
            self.db.logger.debug(f"Executing fees query: {query}")  # Add query logging
            
            self.db.cursor.execute(query)
            results = self.db.cursor.fetchall()
            
            # Add results logging
            self.db.logger.debug(f"Query returned {len(results)} rows: {results}")
            
            fees = {}
            for row in results:
                fees[row['network']] = float(row['total_fees'])
            
            return fees
        except Exception as e:
            self.db.logger.error(f"Error getting all network fees: {e}", exc_info=True)  # Add full traceback
            return {}

    def get_network_tx_count(self, network: str, interval_seconds: int) -> int:
        """Get transaction count for a specific network"""
        try:
            query = get_network_tx_count_query(network, interval_seconds)
            if not query:  # Handle unsupported networks
                return 0
                
            self.db.cursor.execute(query)
            result = self.db.cursor.fetchone()
            
            return int(result['tx_count'])
        except Exception as e:
            self.db.logger.error(f"Error getting transaction count for {network}: {e}")
            return 0

    def get_all_networks_tx_count(self, interval_seconds: int) -> Dict[str, int]:
        """Get transaction count for all networks"""
        try:
            query = get_all_networks_tx_count_query(interval_seconds)
            self.db.cursor.execute(query)
            results = self.db.cursor.fetchall()
            
            counts = {}
            for row in results:
                counts[row['network']] = int(row['tx_count'])
            
            return counts
        except Exception as e:
            self.db.logger.error(f"Error getting all network transaction counts: {e}")
            return {}

    def get_network_historical_data(self, network: str, interval_seconds: int, points: int) -> list:
        """Get historical data points for a specific network"""
        try:
            query = get_network_historical_data_query(network, interval_seconds, points)
            if not query:  # Handle unsupported networks
                return []
            
            self.db.cursor.execute(query)
            results = self.db.cursor.fetchall()
            
            return [dict(row) for row in results]
        except Exception as e:
            self.db.logger.error(f"Error getting historical data for {network}: {e}")
            return []