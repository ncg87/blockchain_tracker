from ..models import ArbitarySwap, TokenSwap, BaseTokenSwap
from typing import Optional, Dict
from operator import itemgetter
from .processors import EventProcessor
from datetime import datetime, timedelta

get_to = itemgetter('to')
get_sender = itemgetter('sender')
get_recipient = itemgetter('recipient')
get_amount0 = itemgetter('amount0')
get_amount1 = itemgetter('amount1')
get_amount0In = itemgetter('amount0In')
get_amount1In = itemgetter('amount1In')
get_amount0Out = itemgetter('amount0Out')
get_amount1Out = itemgetter('amount1Out')
get_sqrtPriceX96 = itemgetter('sqrtPriceX96')
get_poolId = itemgetter('poolId')
get_tokenIn = itemgetter('tokenIn')
get_tokenOut = itemgetter('tokenOut')
get_amountIn = itemgetter('amountIn')
get_amountOut = itemgetter('amountOut')
get_value = itemgetter('value')
get_user = itemgetter('user')
get_liquidity = itemgetter('liquidity')
get_tick = itemgetter('tick')
get_baseIn = itemgetter('baseIn')
get_quoteIn = itemgetter('quoteIn')
get_baseOut = itemgetter('baseOut')
get_quoteOut = itemgetter('quoteOut')
get_fee = itemgetter('fee')
get_adminFee = itemgetter('adminFee')
get_oraclePrice = itemgetter('oraclePrice')
get_assetIn = itemgetter('assetIn')
get_assetOut = itemgetter('assetOut')
get_receiver = itemgetter('receiver')
get_referralCode = itemgetter('referralCode')
get_parameters = itemgetter('parameters')
get_protocolFeesToken0 = itemgetter('protocolFeesToken0')
get_protocolFeesToken1 = itemgetter('protocolFeesToken1')
get_contract = itemgetter('contract')
get_account = itemgetter('account')
get_tokenX = itemgetter('tokenX')
get_tokenY = itemgetter('tokenY')
get_amountX = itemgetter('amountX')
get_amountY = itemgetter('amountY')
get_currentPoint = itemgetter('currentPoint')
get_inputAmount = itemgetter('inputAmount')
get_inputToken = itemgetter('inputToken')
get_amountOut = itemgetter('amountOut')
get_outputToken = itemgetter('outputToken')
get_slippage = itemgetter('slippage')
get_fromAddress = itemgetter('fromAddress')
get_toAddress = itemgetter('toAddress')
get_fromAssetAddress = itemgetter('fromAssetAddress')
get_toAssetAddress = itemgetter('toAssetAddress')
get_swap0to1 = itemgetter('swap0to1')







# TODO: Add more protocol mappings
# TODO: Determine the type of the protocol so we can map to DEX or Aggregator, etc.

class SwapProcessor(EventProcessor):
    def __init__(self, db_operator, chain):
        super().__init__(db_operator, chain)
        self.logger.info("SwapProcessor initialized")
        # Define special signatures we want to track
        self.special_signatures = {
            # Cross-Chain
            "34660fc8af304464529f48a778e03d03e4d34bcd5f9b6f0cfbf3cd238c642f7f",
            # Aggregators
            "0fe977d619f8172f7fdbe8bb8928ef80952817d96936509f67d66346bc4cd10f",
            "823eaf01002d7353fbcadb2ea3305cc46fa35d799cb0914846d185ac06f8ad05",
            "20efd6d5195b7b50273f01cd79a27989255356f9f13293edc53ee142accfdb75",
            "fc431937278b84c6fa5b23bcc58f673c647fea974d3656e766b22d8c1412e544",
            "0fe977d619f8172f7fdbe8bb8928ef80952817d96936509f67d66346bc4cd10f",
            "20efd6d5195b7b50273f01cd79a27989255356f9f13293edc53ee142accfdb75",
            "823eaf01002d7353fbcadb2ea3305cc46fa35d799cb0914846d185ac06f8ad05",
            "beee1e6e7fe307ddcf84b0a16137a4430ad5e2480fc4f4a8e250ab56ccd7630d",
            "45f377f845e1cc76ae2c08f990e15d58bcb732db46f92a4852b956580c3a162f",
            "0874b2d545cb271cdbda4e093020c452328b24af12382ed62c4d00f5c26709db",
            # Yield Swaps?
            "829000a5bc6a12d46e30cdcecd7c56b1efd88f6d7d059da6734a04f3764557c4",
        }

    def process_event(self, event : dict, signature: str, tx_hash: str, index: int, timestamp: int):
        
        # Check if signature is provided, if not, get it from the event
        
        try:
            # Track special signatures before processing
            if signature in self.special_signatures:
                contract_address = get_contract(event)
                self.increment_known_protocol(signature, contract_address)
            
            protocol_info = self.protocol_map[signature]
            
            parameters = get_parameters(event)
            swap_info = protocol_info(parameters)
            
            address = get_contract(event)
            
            contract_info = self.db_operator.sql.query.evm.swap_info_by_chain(self.chain, address)
            
            if contract_info is None:
                return None
            
            # Get the token info if the address for the tokens are already given, multi pool swap
            if isinstance(swap_info, BaseTokenSwap):
                token_0_info = self.db_operator.sql.query.evm.token_info_by_chain(self.chain, swap_info.token0_address)
                token_1_info = self.db_operator.sql.query.evm.token_info_by_chain(self.chain, swap_info.token1_address)
                swap_info = TokenSwap.from_token_info(swap_info, token_0_info, token_1_info)
            
            # Get the info about the contract if just the amounts are given, two pool swap (Majority of the swaps)
            if isinstance(swap_info, ArbitarySwap):
                swap_info = TokenSwap.from_swap_info(swap_info, contract_info)
            
            self.db_operator.sql.insert.evm.swap(self.chain, swap_info, address, tx_hash, index, timestamp)
            
            return swap_info
        except KeyError:
            self.increment_unknown_protocol(signature)
            self.logger.error(f"Unknown protocol: {signature}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing event for {self.chain} - {e}", exc_info=True)
            return None


    # Create a better way of loading and updating it in a custom protocol file
    def create_protocol_map(self):
        return {
            "a4228e1eb11eb9b31069d9ed20e7af9a010ca1a02d4855cee54e08e188fcc32c" : self.sender_to_amount0_amount1,
            "b3e2773606abfd36b5bd91394b3a54d1398336c65005baf7bf7a05efeffaf75b" : self.sender_to_amount0In_amount1In_amount0Out_amount1Out,
            "c42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67" : self.sender_recipient_amount0_amount1_sqrtPriceX96_liquidity_tick,
            "298c349c742327269dc8de6ad66687767310c948ea309df826f5bd103e19d207" : self.amount0In_amount0Out_amount1In_amount1Out,
            "2170c741c41531aec20e7c107c24eecfdd15e69c9bb0a8dd37b1840b9e0b207b" : self.poolId_tokenIn_tokenOut_amountIn_amountOut,
            "c4f8d05cabc2df63321bad93015119eee7b8384aef73af9b606eab919e48ba8a" : self.poolId_tokenIn_tokenOut_amountIn_amountOut_user,
            #"2ad8739d64c070ab4ae9d9c0743d56550b22c3c8c96e7a6045fac37b5b8e89e3" : self.sender_recipient_baseIn_quoteIn_baseOut_quoteOut_fee_adminFee_oraclePrice
            "fa2dda1cc1b86e41239702756b13effbc1a092b5c57e3ad320fbe4f3b13fe235" : self.tokenIn_tokenOut_amountIn_amountOut,
            "d78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822" : self.sender_amount0In_amount1In_amount0Out_amount1Out_to,
            "dba43ee9916cb156cc32a5d3406e87341e568126a46815294073ba25c9400246" : self.assetIn_assetOut_sender_receiver_amountIn_amountOut_referralCode,
            "19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83" : self.sender_recipient_amount0_amount1_sqrtPriceX96_liquidity_tick_protocolFeesToken0_protocolFeesToken1,
            "0874b2d545cb271cdbda4e093020c452328b24af12382ed62c4d00f5c26709db" : self.account_tokenIn_tokenOut_amountIn_amountOut_amountOutAfterFees_feeBasisPoints,
            "121cb44ee54098b1a04743c487e7460d8dd429b27f88b1f4d4767396e1a59f79" : self.sender_recipient_amount0_amount1_price_liquidity_tick_overrideFee_pluginFee,
            "cd3829a3813dc3cdd188fd3d01dcf3268c16be2fdd2dd21d0665418816e46062" : self.recipient_tokenIn_tokenOut_amountIn_amountOut,
            "fa2dda1cc1b86e41239702756b13effbc1a092b5c57e3ad320fbe4f3b13fe235" : self.tokenIn_tokenOut_amountIn_amountOut,
            "dc004dbca4ef9c966218431ee5d9133d337ad018dd5b5c5493722803f75c64f7" : self.swap0to1_amountIn_amountOut_to,
            "fa2dda1cc1b86e41239702756b13effbc1a092b5c57e3ad320fbe4f3b13fe235" : self.tokenIn_tokenOut_amountIn_amountOut,
            "cd3829a3813dc3cdd188fd3d01dcf3268c16be2fdd2dd21d0665418816e46062" : self.recipient_tokenIn_tokenOut_amountIn_amountOut,
            "40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f" : self.id_sender_amount0_amount1_sqrtPriceX96_liquidity_tick_fee,
            
            # Cross-Chain
            "34660fc8af304464529f48a778e03d03e4d34bcd5f9b6f0cfbf3cd238c642f7f" : self.chainId_dstPoolId_from_amountSD_eqReward_eqFee_protocolFee_lpFee,
            
            # Aggregator
            "0fe977d619f8172f7fdbe8bb8928ef80952817d96936509f67d66346bc4cd10f" : self.tokenX_tokenY_fee_sellXEarnY_amountX_amountY_currentPoint,
            "823eaf01002d7353fbcadb2ea3305cc46fa35d799cb0914846d185ac06f8ad05" : self.sender_inputAmount_inputToken_amountOut_outputToken_slippage_referralCode,
            "20efd6d5195b7b50273f01cd79a27989255356f9f13293edc53ee142accfdb75" : self.fromAddress_toAddress_fromAssetAddress_toAssetAddress_amountIn_amountOut,
            "fc431937278b84c6fa5b23bcc58f673c647fea974d3656e766b22d8c1412e544" : self.source_tokenIn_tokenOut_amountIn_amountOut_minAmountOut_minAmountOut_fee_data,
            "0fe977d619f8172f7fdbe8bb8928ef80952817d96936509f67d66346bc4cd10f" : self.tokenX_tokenY_fee_sellXEarnY_amountX_amountY_currentPoint,
            "20efd6d5195b7b50273f01cd79a27989255356f9f13293edc53ee142accfdb75" : self.fromAddress_toAddress_fromAssetAddress_toAssetAddress_amountIn_amountOut,
            "823eaf01002d7353fbcadb2ea3305cc46fa35d799cb0914846d185ac06f8ad05" : self.sender_inputAmount_inputToken_amountOut_outputToken_slippage_referralCode,
            "beee1e6e7fe307ddcf84b0a16137a4430ad5e2480fc4f4a8e250ab56ccd7630d" : self.aggregatorId_sender,
            "45f377f845e1cc76ae2c08f990e15d58bcb732db46f92a4852b956580c3a162f" : self.fromToken_toToken_sender_destination_fromAmount_minReturnAmount,
            "829000a5bc6a12d46e30cdcecd7c56b1efd88f6d7d059da6734a04f3764557c4" : self.caller_reveiver_netPtOut_netSyOut_netSyFee_netSyToReserve,
            "0874b2d545cb271cdbda4e093020c452328b24af12382ed62c4d00f5c26709db" : self.account_tokenIn_tokenOut_amountIn_amountOut_amountOutAfterFees_feeBasisPoints,
            



            
        }
        
    # Check if correct
    def sender_to_amount0_amount1(self, parameters) -> ArbitarySwap:
        sender = get_value(get_sender(parameters))
        to = get_value(get_to(parameters))
        amount0 = get_value(get_amount0(parameters))
        amount1 = get_value(get_amount1(parameters))
        
        isAmount0In = amount0 < 0
        
        return ArbitarySwap (
            amount0 = amount0,
            amount1 = amount1,
            isAmount0In = isAmount0In
        )

    # Uniswap V2
    def sender_to_amount0In_amount1In_amount0Out_amount1Out(self, parameters) -> ArbitarySwap:
        
        
        sender = get_value(get_sender(parameters))
        to = get_value(get_to(parameters))
        amount0In = get_value(get_amount0In(parameters))
        
        if amount0In > 0:
            amount1 = get_value(get_amount1Out(parameters))
            return ArbitarySwap (
                amount0 =  amount0In,
                amount1 = amount1,
                isAmount0In = True
            )
        else:
            amount0 = get_value(get_amount0Out(parameters))
            amount1 = get_value(get_amount1In(parameters))
            return ArbitarySwap (
                amount0 = amount0,
                amount1 = amount1,
                isAmount0In = False
            )
    # Uniswap V3 type swap
    def sender_recipient_amount0_amount1_sqrtPriceX96_liquidity_tick(self, parameters) -> ArbitarySwap:
        
        

        sender = get_value(get_sender(parameters))
        recipient = get_value(get_recipient(parameters))
        amount0 = get_value(get_amount0(parameters))
        amount1 = get_value(get_amount1(parameters))
        #sqrtPriceX96 = get_value(get_sqrtPriceX96(parameters))         # Can use this to determine price of tokens in the future
        liquidity = get_value(get_liquidity(parameters))
        tick = get_value(get_tick(parameters))

        isAmount0In = amount0 < 0

        return ArbitarySwap (
            amount0 = amount0,
            amount1 = amount1,
            isAmount0In = isAmount0In
        )
    
    # Uniswap V2 fork
    def amount0In_amount0Out_amount1In_amount1Out(self, parameters) -> ArbitarySwap:
        amount0In = get_value(get_amount0In(parameters))

        if amount0In > 0:
            amount1 = get_value(get_amount1Out(parameters))
            return ArbitarySwap (
                amount0 = amount0In,
                amount1 = amount1,
                isAmount0In = True
            )
        else:
            amount0 = get_value(get_amount0Out(parameters))
            amount1 = get_value(get_amount1In(parameters))
            
            return ArbitarySwap (
                amount0 = amount0,
                amount1 = amount1,
                isAmount0In = False
            )
    
    def poolId_tokenIn_tokenOut_amountIn_amountOut(self, parameters) -> TokenSwap:
        
        poolId = get_value(get_poolId(parameters))
        tokenIn = get_value(get_tokenIn(parameters))
        tokenOut = get_value(get_tokenOut(parameters))
        
        amountIn = get_value(get_amountIn(parameters))
        amountOut = get_value(get_amountOut(parameters))
        
        return BaseTokenSwap (
            amount0 = amountIn,
            amount1 = amountOut,
            isAmount0In = True,
            token0_address = tokenIn,
            token1_address = tokenOut
        )
    
    def poolId_tokenIn_tokenOut_amountIn_amountOut_user(self, parameters) -> TokenSwap:

        poolId = get_value(get_poolId(parameters))
        tokenIn = get_value(get_tokenIn(parameters))
        tokenOut = get_value(get_tokenOut(parameters))
        user = get_value(get_user(parameters))

        amountIn = get_value(get_amountIn(parameters))
        amountOut = get_value(get_amountOut(parameters))
        
        return TokenSwap (
            amount0 = amountIn,
            amount1 = amountOut,
            isAmount0In = True,
            token0_address = tokenIn,
            token1_address = tokenOut
        )
    
    def sender_recipient_baseIn_quoteIn_baseOut_quoteOut_fee_adminFee_oraclePrice(self, parameters) -> ArbitarySwap:
        sender = get_value(get_sender(parameters))
        recipient = get_value(get_recipient(parameters))
        baseIn = get_value(get_baseIn(parameters))
        quoteIn = get_value(get_quoteIn(parameters))
        baseOut = get_value(get_baseOut(parameters))
        quoteOut = get_value(get_quoteOut(parameters))
        fee = get_value(get_fee(parameters))
        adminFee = get_value(get_adminFee(parameters))
        oraclePrice = get_value(get_oraclePrice(parameters))
        
        raise Exception("Not implemented")

    def tokenIn_tokenOut_amountIn_amountOut(self, parameters) -> TokenSwap:
        
        tokenIn = get_value(get_tokenIn(parameters))
        tokenOut = get_value(get_tokenOut(parameters))
        amountIn = get_value(get_amountIn(parameters))
        amountOut = get_value(get_amountOut(parameters))
        
        
        
        return BaseTokenSwap(
            amount0=amountIn, 
            amount1=amountOut, 
            isAmount0In=True,
            token0_address = tokenIn,
            token1_address = tokenOut
            )

    def sender_amount0In_amount1In_amount0Out_amount1Out_to(self, parameters) -> ArbitarySwap:
        sender = get_value(get_sender(parameters))
        to = get_value(get_to(parameters))
        amount0In = get_value(get_amount0In(parameters))
        
        if amount0In > 0:
            amount1 = get_value(get_amount1Out(parameters))
            return ArbitarySwap (
                amount0 = amount0In,
                amount1 = amount1,
                isAmount0In = True
            )
        else:
            amount0 = get_value(get_amount0Out(parameters))
            amount1 = get_value(get_amount1In(parameters))
            return ArbitarySwap (
                amount0 = amount0,
                amount1 = amount1,
                isAmount0In = False
            )

    def assetIn_assetOut_sender_receiver_amountIn_amountOut_referralCode(self, parameters) -> TokenSwap:
        assetIn = get_value(get_assetIn(parameters))
        assetOut = get_value(get_assetOut(parameters))
        sender = get_value(get_sender(parameters))
        receiver = get_value(get_receiver(parameters))
        amountIn = get_value(get_amountIn(parameters))
        amountOut = get_value(get_amountOut(parameters))
        referralCode = get_value(get_referralCode(parameters))
        
        return BaseTokenSwap(
            amount0 = amountIn,
            amount1 = amountOut,
            isAmount0In = True,
            token0_address = assetIn,
            token1_address = assetOut
        )
    
    def sender_recipient_amount0_amount1_sqrtPriceX96_liquidity_tick_protocolFeesToken0_protocolFeesToken1(self, parameters) -> ArbitarySwap:
        sender = get_value(get_sender(parameters))
        recipient = get_value(get_recipient(parameters))
        amount0 = get_value(get_amount0(parameters))
        amount1 = get_value(get_amount1(parameters))
        sqrtPriceX96 = get_value(get_sqrtPriceX96(parameters))
        liquidity = get_value(get_liquidity(parameters))
        tick = get_value(get_tick(parameters))
        protocolFeesToken0 = get_value(get_protocolFeesToken0(parameters))
        protocolFeesToken1 = get_value(get_protocolFeesToken1(parameters))

        isAmount0In = amount0 < 0

        return ArbitarySwap(
            amount0 = amount0,
            amount1 = amount1,
            isAmount0In = isAmount0In
        )
    
    def account_tokenIn_tokenOut_amountIn_amountOut_amountOutAfterFees_feeBasisPoints(self, parameters) -> TokenSwap:
        account = get_value(get_account(parameters))
        tokenIn = get_value(get_tokenIn(parameters))
        tokenOut = get_value(get_tokenOut(parameters))
        amountIn = get_value(get_amountIn(parameters))
        amountOut = get_value(get_amountOut(parameters))
        
        return BaseTokenSwap(
            amount0 = amountIn,
            amount1 = amountOut,
            isAmount0In = True,
            token0_address = tokenIn,
            token1_address = tokenOut
        )
    def sender_recipient_amount0_amount1_price_liquidity_tick_overrideFee_pluginFee(self, parameters) -> ArbitarySwap:
        sender = get_value(get_sender(parameters))
        recipient = get_value(get_recipient(parameters))
        amount0 = get_value(get_amount0(parameters))
        amount1 = get_value(get_amount1(parameters))
        
        amount0In = amount0 < 0
        
        return ArbitarySwap(
            amount0 = amount0,
            amount1 = amount1,
            isAmount0In = amount0In
        )
        
    def recipient_tokenIn_tokenOut_amountIn_amountOut(self, parameters) -> TokenSwap:
        recipient = get_value(get_recipient(parameters))
        tokenIn = get_value(get_tokenIn(parameters))
        tokenOut = get_value(get_tokenOut(parameters))
        amountIn = get_value(get_amountIn(parameters))
        amountOut = get_value(get_amountOut(parameters))
        
        return BaseTokenSwap(
            amount0 = amountIn,
            amount1 = amountOut,
            isAmount0In = True,
            token0_address = tokenIn,
            token1_address = tokenOut
        )
    
    def swap0to1_amountIn_amountOut_to(self, parameters) -> TokenSwap:
        swap0to1 = get_value(get_swap0to1(parameters))
        amountIn = get_value(get_amountIn(parameters))
        amountOut = get_value(get_amountOut(parameters))
        to = get_value(get_to(parameters))
        
        return ArbitarySwap(
            amount0 = amountIn,
            amount1 = amountOut,
            isAmount0In = swap0to1
        )
    
    def id_sender_amount0_amount1_sqrtPriceX96_liquidity_tick_fee(self, parameters) -> ArbitarySwap:
        #id = get_value(get_id(parameters))
        sender = get_value(get_sender(parameters))
        amount0 = get_value(get_amount0(parameters))
        amount1 = get_value(get_amount1(parameters))
        #sqrtPriceX96 = get_value(get_sqrtPriceX96(parameters))
        liquidity = get_value(get_liquidity(parameters))
        
        isAmount0In = amount0 < 0
        
        return ArbitarySwap(
            amount0 = amount0,
            amount1 = amount1,
            isAmount0In = isAmount0In
        )

    
    # Cross-Chain
    def chainId_dstPoolId_from_amountSD_eqReward_eqFee_protocolFee_lpFee(self, parameters) -> ArbitarySwap:

        return None
        

    # Aggregator
    def tokenX_tokenY_fee_sellXEarnY_amountX_amountY_currentPoint(self, parameters) -> TokenSwap:
        tokenX = get_value(get_tokenX(parameters))
        tokenY = get_value(get_tokenY(parameters))
        fee = get_value(get_fee(parameters))
        #sellXEarnY = get_value(get_sellXEarnY(parameters))
        amountX = get_value(get_amountX(parameters))
        amountY = get_value(get_amountY(parameters))
        currentPoint = get_value(get_currentPoint(parameters))
        
        return None
    # Aggregator
    def sender_inputAmount_inputToken_amountOut_outputToken_slippage_referralCode(self, parameters) -> TokenSwap:
        sender = get_value(get_sender(parameters))
        inputAmount = get_value(get_inputAmount(parameters))
        inputToken = get_value(get_inputToken(parameters))
        amountOut = get_value(get_amountOut(parameters))
        outputToken = get_value(get_outputToken(parameters))
        
        return None
    # Aggregator
    def fromAddress_toAddress_fromAssetAddress_toAssetAddress_amountIn_amountOut(self, parameters) -> TokenSwap:
        fromAddress = get_value(get_fromAddress(parameters))
        toAddress = get_value(get_toAddress(parameters))
        fromAssetAddress = get_value(get_fromAssetAddress(parameters))
        toAssetAddress = get_value(get_toAssetAddress(parameters))
        amountIn = get_value(get_amountIn(parameters))
        amountOut = get_value(get_amountOut(parameters))
        
        return None
    
    # Aggregator
    def source_tokenIn_tokenOut_amountIn_amountOut_minAmountOut_minAmountOut_fee_data(self, parameters) -> TokenSwap:
        #source = get_value(get_source(parameters))
        tokenIn = get_value(get_tokenIn(parameters))
        tokenOut = get_value(get_tokenOut(parameters))
        amountIn = get_value(get_amountIn(parameters))
        amountOut = get_value(get_amountOut(parameters))
        
        return None
    
    # Aggregator
    def tokenX_tokenY_fee_sellXEarnY_amountX_amountY_currentPoint(self, parameters) -> TokenSwap:
        tokenX = get_value(get_tokenX(parameters))
        tokenY = get_value(get_tokenY(parameters))
        fee = get_value(get_fee(parameters))
        #sellXEarnY = get_value(get_sellXEarnY(parameters))
        amountX = get_value(get_amountX(parameters))
        amountY = get_value(get_amountY(parameters))
        
        return None
    
    # Aggregator
    def fromToken_toToken_sender_destination_fromAmount_minReturnAmount(self, parameters) -> TokenSwap:
        #fromToken = get_value(get_fromToken(parameters))
        #toToken = get_value(get_toToken(parameters))
        sender = get_value(get_sender(parameters))
        #destination = get_value(get_destination(parameters))
        #fromAmount = get_value(get_fromAmount(parameters))
        #minReturnAmount = get_value(get_minReturnAmount(parameters))
        
        return None
    
    # Aggregator event
    def aggregatorId_sender(self, parameters) -> TokenSwap:
        #aggregatorId = get_value(get_aggregatorId(parameters))
        sender = get_value(get_sender(parameters))
        
        return None
    
    # Yield Swaps?
    def caller_reveiver_netPtOut_netSyOut_netSyFee_netSyToReserve(self, parameters) -> TokenSwap:
       # caller = get_value(get_caller(parameters))
       # receiver = get_value(get_receiver(parameters))
       # netPtOut = get_value(get_netPtOut(parameters))
       # netSyOut = get_value(get_netSyOut(parameters))
       # netSyFee = get_value(get_netSyFee(parameters))
       # netSyToReserve = get_value(get_netSyToReserve(parameters))
        
        return None
        
        
    # Updated to use simplified unknown protocols check
    def get_unknown_protocol_counts(self) -> Dict[str, int]:

        return self.get_unknown_protocols()

    def get_known_protocol_key(self, signature: str) -> str:
        """Generate a cache key for known protocols"""
        return f"known_protocols:{signature}"

    def increment_known_protocol(self, signature: str, contract_address: str) -> int:
        """Increment counter for specific contract address under a signature with 24h TTL"""
        cache_key = self.get_known_protocol_key(signature)
        pipe = self.redis_client.pipeline()
        
        # Increment the counter for this specific contract
        pipe.hincrby(cache_key, contract_address, 1)
        pipe.expire(cache_key, timedelta(days=1))
        
        result = pipe.execute()
        return result[0]  # Return new counter value
