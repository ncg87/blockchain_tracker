INSERT_EVM_TRANSACTIONS = """
    INSERT INTO evm_transactions
    (block_number, chain, transaction_hash, chain_id, from_address, to_address, amount, total_gas, timestamp)
    VALUES %s
    ON CONFLICT (chain, timestamp, transaction_hash) DO NOTHING
"""

INSERT_EVM_EVENTS = """
    INSERT INTO evm_decoded_events
    (chain, signature_hash, event_name, decoded_signature, input_types, indexed_inputs, input_names, inputs)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (chain, signature_hash) DO UPDATE SET
        event_name = EXCLUDED.event_name,
        decoded_signature = EXCLUDED.decoded_signature,
        input_types = EXCLUDED.input_types,
        indexed_inputs = EXCLUDED.indexed_inputs,
        input_names = EXCLUDED.input_names,
        inputs = EXCLUDED.inputs
"""

INSERT_EVM_CONTRACT_ABI = """
    INSERT INTO evm_contract_abis
    (chain, contract_address, abi)
    VALUES (%s, %s, %s)
    ON CONFLICT (chain, contract_address) DO UPDATE SET
        abi = EXCLUDED.abi
"""

INSERT_EVM_SWAP_INFO = """
    INSERT INTO evm_swap_info
    (contract_address, factory_address, fee, token0_name, token1_name, token0_symbol, token1_symbol, token0_decimals, token1_decimals, token0_address, token1_address, name, chain)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (contract_address, chain) DO UPDATE SET
        factory_address = EXCLUDED.factory_address,
        fee = EXCLUDED.fee,
        token0_name = EXCLUDED.token0_name,
        token1_name = EXCLUDED.token1_name,
        token0_symbol = EXCLUDED.token0_symbol,
        token1_symbol = EXCLUDED.token1_symbol,
        token0_decimals = EXCLUDED.token0_decimals,
        token1_decimals = EXCLUDED.token1_decimals,
        token0_address = EXCLUDED.token0_address,
        token1_address = EXCLUDED.token1_address,
        name = EXCLUDED.name
"""

INSERT_EVM_TOKEN_INFO = """
    INSERT INTO evm_token_info
    (contract_address, name, symbol, decimals, chain)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (contract_address, chain) DO UPDATE SET
        name = EXCLUDED.name,
        symbol = EXCLUDED.symbol,
        decimals = EXCLUDED.decimals
"""

INSERT_EVM_CONTRACT_TO_FACTORY = """
    INSERT INTO evm_contract_to_factory
    (contract_address, factory_address, chain, name)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (contract_address, chain) DO NOTHING
"""

INSERT_EVM_SWAP = """
    INSERT INTO evm_swaps
    (chain, contract_address, transaction_hash, log_index, timestamp, amount0, amount1, token0_address, token1_address, token0_name, token1_name, token0_symbol, token1_symbol, factory_address, name)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (chain, transaction_hash, log_index) DO NOTHING
"""

