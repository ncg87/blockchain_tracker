INSERT_EVM_TRANSACTIONS = """
    INSERT INTO evm_transactions
    (block_number, chain, transaction_hash, chain_id, from_address, to_address, amount, total_gas, timestamp)
    VALUES %s
    ON CONFLICT (chain, timestamp, transaction_hash) DO NOTHING
"""

INSERT_EVM_EVENTS = """
    INSERT INTO evm_known_events
    (network, signature_hash, name, full_signature, input_types, indexed_inputs, inputs, contract_address)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (network, signature_hash) DO UPDATE SET
        name = EXCLUDED.name,
        full_signature = EXCLUDED.full_signature,
        input_types = EXCLUDED.input_types,
        indexed_inputs = EXCLUDED.indexed_inputs,
        inputs = EXCLUDED.inputs,
        contract_address = COALESCE(evm_known_events.contract_address, EXCLUDED.contract_address)
"""

INSERT_EVM_CONTRACT_ABI = """
    INSERT INTO evm_contract_abis
    (chain, contract_address, abi)
    VALUES (%s, %s, %s)
    ON CONFLICT (chain, contract_address) DO UPDATE SET
        abi = EXCLUDED.abi
"""

INSERT_EVM_SWAP = """
    INSERT INTO evm_swap
    (contract_address, factory_address, fee, token0_name, token1_name, token0_address, token1_address, name, network)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (contract_address, network) DO UPDATE SET
        factory_address = EXCLUDED.factory_address,
        fee = EXCLUDED.fee,
        token0_name = EXCLUDED.token0_name,
        token1_name = EXCLUDED.token1_name,
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
    INSERT INTO evm_contract_to_creator
    (contract_address, factory_address, network)
    VALUES (%s, %s, %s)
    ON CONFLICT (contract_address, network) DO NOTHING
"""

INSERT_EVM_TRANSACTION_SWAP = """
    INSERT INTO evm_transaction_swap
    (network, contract_address, tx_hash, log_index, timestamp, amount0, amount1, token0, token1, amount0_in)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (network, tx_hash, log_index) DO NOTHING
"""
