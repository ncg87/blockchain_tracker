parsed_transactions = {}
bad_events = []

for item in query[:500]:
    parsed_transactions[item['transaction_hash']] = []
    for event in item['log_data']:
        contract_address = Web3.to_checksum_address(event['contract'])
        if event['event'] == 'Transfer':
            coin = sql_query_ops.query_evm_token_info('Ethereum', contract_address)
            if coin is None:
                coin = processor._process_coin(event['contract'])
            coin = sql_query_ops.query_evm_token_info('Ethereum', event['contract'])
            try:
                parsed_transactions[item['transaction_hash']].append(
                    Transfer(
                        coin=coin.name,
                        coin_address=coin.address,
                        coin_symbol=coin.symbol,
                        amount=event['parameters']['value']['value'],
                        from_address=event['parameters']['sender']['value'],
                        to_address=event['parameters']['to']['value'],
                        contract_address=event['contract']
                ))
            except Exception as e:
                bad_events.append(['Transfer',event,e])
        # Make a method to process syncs
        elif event['event'] == 'Sync':
            swap = sql_query_ops.query_evm_swap('Ethereum', contract_address)
            if swap is None:
                swap = await processor._process_swaps(contract_address)
            
        elif event['event'] == 'Swap':
            swap = sql_query_ops.query_evm_swap('Ethereum', contract_address)
            if swap is None:
                swap = await processor._process_swaps(contract_address)
            try:
                token0 = swap.token0_name
                token1 = swap.token1_name
                from_address = event['parameters']['sender']['value']
                to_address = event['parameters']['to']['value']
                if event['parameters']['amount0In']['value'] == 0:
                    # If amount0In is 0, then we're taking amount1In and getting amount0Out
                    from_amount = event['parameters']['amount1In']['value']
                    to_amount = event['parameters']['amount0Out']['value']
                    from_token = token1
                    to_token = token0
                else:
                    # If amount0In is not 0, then we're taking amount0In and getting amount1Out
                    from_amount = event['parameters']['amount0In']['value']
                    to_amount = event['parameters']['amount1Out']['value']
                    from_token = token0
                    to_token = token1
                parsed_transactions[item['transaction_hash']].append(
                Swap(
                    from_token = from_token,
                    from_amount = from_amount,
                    from_address = from_address,
                    to_token = to_token,
                    to_amount = to_amount,
                    to_address = to_address
                ))  
            except Exception as e:
                bad_events.append(['Swap',event,e])
            
