QUERY_EVM_TRANSACTIONS = """
    SELECT block_number, network, transaction_hash, chain_id, 
           from_address, to_address, value_wei, total_gas, timestamp
    FROM base_evm_transactions 
    WHERE network = %s AND block_number = %s;
"""

QUERY_RECENT_EVM_TRANSACTIONS = """
    SELECT block_number, network, transaction_hash, chain_id, 
           from_address, to_address, value_wei, total_gas, timestamp
    FROM base_evm_transactions 
    WHERE network = %s
    ORDER BY timestamp DESC
    LIMIT %s;
"""

QUERY_ADDRESS_HISTORY = """
    SELECT block_number, transaction_hash, from_address, to_address, 
           value_wei, timestamp
    FROM base_evm_transactions 
    WHERE network = %s
    AND timestamp BETWEEN %s AND %s
    AND (from_address = %s OR to_address = %s)
    ORDER BY timestamp DESC;
"""

QUERY_EVM_EVENT = """
    SELECT *
    FROM evm_known_events
    WHERE network = %s AND signature_hash = %s;
"""

QUERY_EVM_CONTRACT_ABI = """
    SELECT *
    FROM evm_contract_abis
    WHERE network = %s AND contract_address = %s;
"""

QUERY_EVM_SWAP = """
    SELECT contract_address, factory_address, fee, token0_name, token1_name, name
    FROM evm_swap
    WHERE network = %s AND contract_address = %s;
"""

QUERY_EVM_SWAP_ALL_NETWORKS = """
    SELECT contract_address, factory_address, fee, token0_name, token1_name, name
    FROM evm_swap
    WHERE contract_address = %s;
"""

QUERY_EVM_TOKEN_INFO = """
    SELECT contract_address, name, symbol, decimals
    FROM evm_token_info
    WHERE network = %s AND contract_address = %s;
"""

QUERY_EVM_FACTORY_CONTRACT = """
    SELECT *
    FROM evm_contract_to_creator
    WHERE network = %s AND contract_address = %s;
"""

QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS = """
    SELECT *
    FROM evm_known_events
    WHERE network = %s AND contract_address = %s;
"""

QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS_ALL_NETWORKS = """
    SELECT *
    FROM evm_known_events
    WHERE contract_address = %s;
"""

QUERY_ALL_EVM_SWAPS = """
    SELECT *
    FROM evm_swap;
"""

QUERY_ALL_EVM_SWAPS_BY_NETWORK = """
    SELECT *
    FROM evm_swap
    WHERE network = %s;
"""
