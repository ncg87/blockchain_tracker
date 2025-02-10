from .blocks import INSERT_BLOCK, QUERY_BLOCKS_BY_TIME, QUERY_RECENT_BLOCKS, QUERY_BLOCKS_BY_NETWORK, QUERY_RECENT_BLOCKS_BY_NETWORK

from .evm import (INSERT_EVM_TRANSACTIONS, INSERT_EVM_EVENTS, INSERT_EVM_CONTRACT_ABI, INSERT_EVM_SWAP_INFO, INSERT_EVM_TOKEN_INFO, 
                  INSERT_EVM_CONTRACT_TO_FACTORY, INSERT_EVM_SWAP, INSERT_EVM_SYNC,
                  QUERY_EVM_FACTORY_CONTRACT, QUERY_EVM_TRANSACTIONS,QUERY_ADDRESS_HISTORY, QUERY_EVM_EVENT, 
                  QUERY_EVM_CONTRACT_ABI, QUERY_EVM_SWAP_INFO, QUERY_EVM_TOKEN_INFO, QUERY_EVM_FACTORY_CONTRACT, 

                  QUERY_RECENT_EVM_TRANSACTIONS, QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS, QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS_ALL_NETWORKS, 
                  QUERY_ALL_EVM_SWAP_INFO, QUERY_ALL_EVM_SWAP_INFO_BY_CHAIN, QUERY_EVM_SWAP_INFO_BY_CHAIN, QUERY_EVM_TOKEN_INFO_BY_CHAIN, QUERY_EVM_EVENT_BY_CHAIN)


from .bitcoin import INSERT_BITCOIN_TRANSACTIONS, QUERY_BITCOIN_TRANSACTIONS, QUERY_RECENT_BITCOIN_TRANSACTIONS

from .solana import INSERT_SOLANA_TRANSACTIONS, QUERY_SOLANA_TRANSACTIONS, QUERY_RECENT_SOLANA_TRANSACTIONS

from .xrp import INSERT_XRP_TRANSACTIONS, QUERY_XRP_TRANSACTIONS, QUERY_RECENT_XRP_TRANSACTIONS

from .api import (get_swaps, get_swaps_by_chain)

__all__ = [
    # Block Queries
    INSERT_BLOCK,
    QUERY_BLOCKS_BY_TIME, QUERY_RECENT_BLOCKS, QUERY_BLOCKS_BY_NETWORK, QUERY_RECENT_BLOCKS_BY_NETWORK,
    # EVM Queries
    INSERT_EVM_TRANSACTIONS, INSERT_EVM_EVENTS, INSERT_EVM_CONTRACT_ABI, INSERT_EVM_SWAP_INFO, INSERT_EVM_TOKEN_INFO, INSERT_EVM_CONTRACT_TO_FACTORY, INSERT_EVM_SWAP,
    QUERY_EVM_FACTORY_CONTRACT, QUERY_EVM_TRANSACTIONS, QUERY_ADDRESS_HISTORY, QUERY_EVM_EVENT, 
    QUERY_EVM_CONTRACT_ABI, QUERY_EVM_SWAP_INFO, QUERY_EVM_TOKEN_INFO, QUERY_EVM_FACTORY_CONTRACT, QUERY_RECENT_EVM_TRANSACTIONS, 
    QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS, QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS_ALL_NETWORKS, QUERY_ALL_EVM_SWAP_INFO, QUERY_ALL_EVM_SWAP_INFO_BY_CHAIN,
    QUERY_EVM_SWAP_INFO_BY_CHAIN, QUERY_EVM_TOKEN_INFO_BY_CHAIN, QUERY_EVM_EVENT_BY_CHAIN,
    # Bitcoin Queries
    INSERT_BITCOIN_TRANSACTIONS, 
    QUERY_BITCOIN_TRANSACTIONS, QUERY_RECENT_BITCOIN_TRANSACTIONS,
    # Solana Queries
    INSERT_SOLANA_TRANSACTIONS,
    QUERY_SOLANA_TRANSACTIONS, QUERY_RECENT_SOLANA_TRANSACTIONS,
    # XRP Queries
    INSERT_XRP_TRANSACTIONS,
    QUERY_XRP_TRANSACTIONS, QUERY_RECENT_XRP_TRANSACTIONS,
    # API Queries
    get_swaps, get_swaps_by_chain

]

