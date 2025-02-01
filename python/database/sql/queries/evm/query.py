QUERY_EVM_TRANSACTIONS = """
    SELECT block_number, chain, transaction_hash, chain_id, 
           from_address, to_address, amount, total_gas, timestamp
    FROM evm_transactions 
    WHERE chain = %s AND block_number = %s;
"""

QUERY_RECENT_EVM_TRANSACTIONS = """
    SELECT block_number, network, transaction_hash, chain_id, 
           from_address, to_address, amount, total_gas, timestamp
    FROM evm_transactions 
    WHERE chain = %s
    ORDER BY timestamp DESC
    LIMIT %s;
"""

QUERY_ADDRESS_HISTORY = """
    SELECT block_number, transaction_hash, from_address, to_address, 
           amount, timestamp
    FROM evm_transactions 
    WHERE chain = %s
    AND timestamp BETWEEN %s AND %s
    AND (from_address = %s OR to_address = %s)
    ORDER BY timestamp DESC;
"""

QUERY_EVM_EVENT = """
    SELECT *
    FROM evm_decoded_events
    WHERE signature_hash = %s;
"""

QUERY_EVM_EVENT_BY_CHAIN = """
    SELECT *
    FROM evm_decoded_events
    WHERE chain = %s and signature_hash = %s;
"""



QUERY_EVM_CONTRACT_ABI = """
    SELECT *
    FROM evm_contract_abis
    WHERE chain = %s AND contract_address = %s;
"""

QUERY_EVM_SWAP_INFO_BY_CHAIN = """
    SELECT contract_address, factory_address, fee, token0_name, token1_name, token0_symbol, token1_symbol, token0_decimals, token1_decimals, token0_address, token1_address, name
    FROM evm_swap_info
    WHERE chain = %s AND contract_address = %s;
"""

QUERY_EVM_SWAP_INFO = """
    SELECT contract_address, factory_address, fee, token0_name, token1_name, token0_symbol, token1_symbol, token0_decimals, token1_decimals, token0_address, token1_address, name
    FROM evm_swap_info
    WHERE contract_address = %s;
"""

QUERY_EVM_TOKEN_INFO_BY_CHAIN = """
    SELECT contract_address, name, symbol, decimals
    FROM evm_token_info
    WHERE chain = %s AND contract_address = %s;
"""
QUERY_EVM_TOKEN_INFO = """
    SELECT *
    FROM evm_token_info
    WHERE contract_address = %s;
"""

QUERY_EVM_FACTORY_CONTRACT = """
    SELECT *
    FROM evm_contract_to_factory
    WHERE chain = %s AND contract_address = %s;
"""

QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS = """
    SELECT *
    FROM evm_decoded_events
    WHERE chain = %s AND contract_address = %s;
"""

QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS_ALL_NETWORKS = """
    SELECT *
    FROM evm_decoded_events
    WHERE contract_address = %s;
"""

QUERY_ALL_EVM_SWAP_INFO = """
    SELECT *
    FROM evm_swap_info;
"""

QUERY_ALL_EVM_SWAP_INFO_BY_CHAIN = """
    SELECT *
    FROM evm_swap_info
    WHERE chain = %s;
"""
