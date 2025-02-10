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
get_isZeroToOne = itemgetter('isZeroToOne')
get_txCount = itemgetter('txCount')
get_user = itemgetter('user')
get_payToken = itemgetter('payToken')
get_receiveToken = itemgetter('receiveToken')
get_payAmount = itemgetter('payAmount')
get_receiveAmount = itemgetter('receiveAmount')
get_feeAmount = itemgetter('feeAmount')
get_id = itemgetter('id')
get_exactIn = itemgetter('exactIn')
get_zeroForOne = itemgetter('zeroForOne')
get_inputAmount = itemgetter('inputAmount')
get_outputAmount = itemgetter('outputAmount')
get_sqrtPriceX96 = itemgetter('sqrtPriceX96')
get_tick = itemgetter('tick')

get_log_index = itemgetter('log_index')








# TODO: Add more protocol mappings
# TODO: Determine the type of the protocol so we can map to DEX or Aggregator, etc.

class SwapProcessor(EventProcessor):
    def __init__(self, db_operator, chain):
        super().__init__(db_operator, chain)
        self.logger.info("SwapProcessor initialized")
        # Define special signatures we want to track
        self.special_signatures = {
            # Cross-Chain
            "34660fc8af304464529f48a778e03d03e4d34bcd5f9b6f0cfbf3cd238c642f7f", # Stargate cross-chain
            # Aggregators
            "0fe977d619f8172f7fdbe8bb8928ef80952817d96936509f67d66346bc4cd10f",
            "823eaf01002d7353fbcadb2ea3305cc46fa35d799cb0914846d185ac06f8ad05",
            "fc431937278b84c6fa5b23bcc58f673c647fea974d3656e766b22d8c1412e544", # Smart Vault (0xa7Ca2C8673bcFA5a26d8ceeC2887f2CC2b0Db22A)
            "0fe977d619f8172f7fdbe8bb8928ef80952817d96936509f67d66346bc4cd10f",
            "20efd6d5195b7b50273f01cd79a27989255356f9f13293edc53ee142accfdb75",
            "823eaf01002d7353fbcadb2ea3305cc46fa35d799cb0914846d185ac06f8ad05",
            
            "beee1e6e7fe307ddcf84b0a16137a4430ad5e2480fc4f4a8e250ab56ccd7630d", # Metamask Swap Router (0x881D40237659C251811CEC9c364ef91dC08D300C)
            "45f377f845e1cc76ae2c08f990e15d58bcb732db46f92a4852b956580c3a162f", # Bridger
            "0874b2d545cb271cdbda4e093020c452328b24af12382ed62c4d00f5c26709db", # Vault
            "c528cda9e500228b16ce84fadae290d9a49aecb17483110004c5af0a07f6fd73",
            "015fc8ee969fd902d9ebd12a31c54446400a2b512a405366fe14defd6081d220",
            
            # Prob a DEX
            "cd42809a29fc60d050d9e34a2f48fe30855a6451eca6c8a61ca7f21e1881644d",
            "d44b536c8222cd875ef4b7f421435c474a3e1035e29c64e5f039af6944de4bea",
            # Interesting Native Swap
            "d44b536c8222cd875ef4b7f421435c474a3e1035e29c64e5f039af6944de4bea",
            # Yield Swaps?
            "829000a5bc6a12d46e30cdcecd7c56b1efd88f6d7d059da6734a04f3764557c4",
            # DEX tax?
            "49138cfc883446ed694cc43b8a3a702d1734f9c3a87125875f3be98a414d7e60",
            # ??? off chain system?
            "5303f139d7aacabb0b5c8741d56c117c63c6ee5ba97a9d1c50cb09c423c26c2f",
            # Options Swapping
            "df687d99441e912d2d671affc60d50f37d0f0128dcdaef03dc2952ec6e144c52", 
            # Order Book?
            "4a6de6fb74140040ff5f8a230383d4ce15312512a98da513ec606b8c60c45314",
            "562c219552544ec4c9d7a8eb850f80ea152973e315372bf4999fe7c953ea004f",
            # something with routing
            "39fded47e0083893073674c7057018a2eeea09c81036ddad3666cdf954351f43",
            # ??
            "976ffbca84869d39bddd7057048dffc33e97641e3c7fe06fd7fc2b039c17b6e5",
            # cant determine no contract abi stored
            "b3822e221d737fbfd984649052a302a883d38a40f7ae591e3bcb5069eedc2a59",
            "3cdf650a4f51a08d31e2bcbce65dcf40f71b46d22989e2a093e8c618cf7221ed",
            "e7525d00e88ec2fe4949364ebcdf61f80247212b853f121457da56e0df239589",
            "e1d4504fa5e661f80f16e8d613b5bc290ee6afe00a96b833a972d8e4490976e1",
            
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
            
            log_index = get_log_index(event)
            
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
            
            self.db_operator.sql.insert.evm.swap(self.chain, swap_info, address, tx_hash, log_index, timestamp)
            
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
            "fa2dda1cc1b86e41239702756b13effbc1a092b5c57e3ad320fbe4f3b13fe235" : self.tokenIn_tokenOut_amountIn_amountOut,
            "d78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822" : self.sender_amount0In_amount1In_amount0Out_amount1Out_to,
            "dba43ee9916cb156cc32a5d3406e87341e568126a46815294073ba25c9400246" : self.assetIn_assetOut_sender_receiver_amountIn_amountOut_referralCode,
            "19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83" : self.sender_recipient_amount0_amount1_sqrtPriceX96_liquidity_tick_protocolFeesToken0_protocolFeesToken1,
            "0874b2d545cb271cdbda4e093020c452328b24af12382ed62c4d00f5c26709db" : self.account_tokenIn_tokenOut_amountIn_amountOut_amountOutAfterFees_feeBasisPoints,
            "121cb44ee54098b1a04743c487e7460d8dd429b27f88b1f4d4767396e1a59f79" : self.sender_recipient_amount0_amount1_price_liquidity_tick_overrideFee_pluginFee,
            "cd3829a3813dc3cdd188fd3d01dcf3268c16be2fdd2dd21d0665418816e46062" : self.recipient_tokenIn_tokenOut_amountIn_amountOut,
            "dc004dbca4ef9c966218431ee5d9133d337ad018dd5b5c5493722803f75c64f7" : self.swap0to1_amountIn_amountOut_to,
            "cd3829a3813dc3cdd188fd3d01dcf3268c16be2fdd2dd21d0665418816e46062" : self.recipient_tokenIn_tokenOut_amountIn_amountOut,
            "40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f" : self.id_sender_amount0_amount1_sqrtPriceX96_liquidity_tick_fee,
            "176648f1f11cda284c124490086be42a926ddf0ae887ebe7b1d6b337d8942756" : self.sender_isZeroToOne_amountIn_fee_amountOut,
            "49926bbebe8474393f434dfa4f78694c0923efa07d19f2284518bfabd06eb737" : self.sender_amount0In_amount1In_amount0Out_amount1Out,
            "40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f" : self.id_sender_amount0_amount1_sqrtPriceX96_liquidity_tick_fee,
            "cd3829a3813dc3cdd188fd3d01dcf3268c16be2fdd2dd21d0665418816e46062" : self.recipient_tokenIn_tokenOut_amountIn_amountOut,
            "0874b2d545cb271cdbda4e093020c452328b24af12382ed62c4d00f5c26709db" : self.account_tokenIn_tokenOut_amountIn_amountOut_amountOutAfterFees_feeBasisPoints,
            "cd42809a29fc60d050d9e34a2f48fe30855a6451eca6c8a61ca7f21e1881644d" : self.id_sender_exactIn_zeroForOne_inputAmount_outputAmount_sqrtPriceX96_tick_fee_totalLiquidity,
            "d44b536c8222cd875ef4b7f421435c474a3e1035e29c64e5f039af6944de4bea" : self.sender_amountTokenIn_amountNativeIn_amountTokenOut_amountNativeOut_flashSwap,
            "cd3829a3813dc3cdd188fd3d01dcf3268c16be2fdd2dd21d0665418816e46062" : self.recipient_tokenIn_tokenOut_amountIn_amountOut,
            "0874b2d545cb271cdbda4e093020c452328b24af12382ed62c4d00f5c26709db" : self.account_tokenIn_tokenOut_amountIn_amountOut_amountOutAfterFees_feeBasisPoints,
            
            

            # Cross-Chain
            "34660fc8af304464529f48a778e03d03e4d34bcd5f9b6f0cfbf3cd238c642f7f" : self.chainId_dstPoolId_from_amountSD_eqReward_eqFee_protocolFee_lpFee,
            
            # Aggregator
            "0fe977d619f8172f7fdbe8bb8928ef80952817d96936509f67d66346bc4cd10f" : self.tokenX_tokenY_fee_sellXEarnY_amountX_amountY_currentPoint,
            "823eaf01002d7353fbcadb2ea3305cc46fa35d799cb0914846d185ac06f8ad05" : self.sender_inputAmount_inputToken_amountOut_outputToken_slippage_referralCode,
            "20efd6d5195b7b50273f01cd79a27989255356f9f13293edc53ee142accfdb75" : self.fromAddress_toAddress_fromAssetAddress_toAssetAddress_amountIn_amountOut,
            "fc431937278b84c6fa5b23bcc58f673c647fea974d3656e766b22d8c1412e544" : self.source_tokenIn_tokenOut_amountIn_amountOut_minAmountOut_minAmountOut_fee_data,
            "0fe977d619f8172f7fdbe8bb8928ef80952817d96936509f67d66346bc4cd10f" : self.tokenX_tokenY_fee_sellXEarnY_amountX_amountY_currentPoint,
            "823eaf01002d7353fbcadb2ea3305cc46fa35d799cb0914846d185ac06f8ad05" : self.sender_inputAmount_inputToken_amountOut_outputToken_slippage_referralCode,
            "beee1e6e7fe307ddcf84b0a16137a4430ad5e2480fc4f4a8e250ab56ccd7630d" : self.aggregatorId_sender,
            "45f377f845e1cc76ae2c08f990e15d58bcb732db46f92a4852b956580c3a162f" : self.fromToken_toToken_sender_destination_fromAmount_minReturnAmount,
            "829000a5bc6a12d46e30cdcecd7c56b1efd88f6d7d059da6734a04f3764557c4" : self.caller_reveiver_netPtOut_netSyOut_netSyFee_netSyToReserve,
            "0874b2d545cb271cdbda4e093020c452328b24af12382ed62c4d00f5c26709db" : self.account_tokenIn_tokenOut_amountIn_amountOut_amountOutAfterFees_feeBasisPoints,
            "c528cda9e500228b16ce84fadae290d9a49aecb17483110004c5af0a07f6fd73" : self.sender_recipient_id_swapForY_amountIn_amountOut_votatilityAccumulated_fees,
            "cd3829a3813dc3cdd188fd3d01dcf3268c16be2fdd2dd21d0665418816e46062" : self.recipient_tokenIn_tokenOut_amountIn_amountOut,
            "976ffbca84869d39bddd7057048dffc33e97641e3c7fe06fd7fc2b039c17b6e5" : self.inputToken_inputAmount_outputAmount_slippageProtection_user_computeOutput,
            
            # Dex with a tax, special type of dex tax   
            "49138cfc883446ed694cc43b8a3a702d1734f9c3a87125875f3be98a414d7e60" : self._user_cId_tokenIn_tokenOut_buyAmount_realOutAmount_taxToken_taxAmount,
            
            # Stablecoin focused AMM
            "2ad8739d64c070ab4ae9d9c0743d56550b22c3c8c96e7a6045fac37b5b8e89e3" : self.sender_recipient_baseIn_quoteIn_baseOut_quoteOut_fee_adminFee_oraclePrice,
            
            # Internal bot
            "015fc8ee969fd902d9ebd12a31c54446400a2b512a405366fe14defd6081d220" : self.botToBuy_usdtToPay,
            
            # Off chain system
            "5303f139d7aacabb0b5c8741d56c117c63c6ee5ba97a9d1c50cb09c423c26c2f" : self.txCount_user_payToken_receiveToken_payAmount_payAmount_receiveAmount_feeAmount,
            
            # Swapping options contract
            "df687d99441e912d2d671affc60d50f37d0f0128dcdaef03dc2952ec6e144c52" : self.optionPoolHash_recipient_amount0_amount1_sqrtPriceX96_liquidity_tick,
            
            # Order Book?
            "4a6de6fb74140040ff5f8a230383d4ce15312512a98da513ec606b8c60c45314" : self.swapHash_maker_taker_recipient_inputToken_inputAmount_outputToken_outputAmount,
            
            "562c219552544ec4c9d7a8eb850f80ea152973e315372bf4999fe7c953ea004f" : self.token_amount,
            
            # Routing
            "39fded47e0083893073674c7057018a2eeea09c81036ddad3666cdf954351f43" : self.swapRouter

            
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
    
    def sender_amount0In_amount1In_amount0Out_amount1Out(self, parameters) -> ArbitarySwap:
        sender = get_value(get_sender(parameters))
        amount0In = get_value(get_amount0In(parameters))
        amount1In = get_value(get_amount1In(parameters))
        amount0Out = get_value(get_amount0Out(parameters))
        amount1Out = get_value(get_amount1Out(parameters))
        
        if amount0In > 0:
            return ArbitarySwap(
                amount0 = amount0In,
                amount1 = amount1In,
                isAmount0In = True
            )
        else:
            return ArbitarySwap(
                amount0 = amount0Out,
                amount1 = amount1Out,
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
        #sender = get_value(get_sender(parameters))
        #recipient = get_value(get_recipient(parameters))
        baseIn = get_value(get_baseIn(parameters))
        quoteIn = get_value(get_quoteIn(parameters))
        baseOut = get_value(get_baseOut(parameters))

        quoteOut = get_value(get_quoteOut(parameters))
        fee = get_value(get_fee(parameters))
        adminFee = get_value(get_adminFee(parameters))
        oraclePrice = get_value(get_oraclePrice(parameters))
        
        return None


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
    
    def sender_isZeroToOne_amountIn_fee_amountOut(self, parameters) -> ArbitarySwap:
        sender = get_value(get_sender(parameters))
        isZeroToOne = get_value(get_isZeroToOne(parameters))
        amountIn = get_value(get_amountIn(parameters))
        fee = get_value(get_fee(parameters))
        amountOut = get_value(get_amountOut(parameters))
        
        return ArbitarySwap(
            amount0 = amountIn,
            amount1 = amountOut,
            isAmount0In = isZeroToOne
        )
    
    def txCount_user_payToken_receiveToken_payAmount_payAmount_receiveAmount_feeAmount(self, parameters) -> TokenSwap:
        #txCount = get_value(get_txCount(parameters))
        #user = get_value(get_user(parameters))
        payToken = get_value(get_payToken(parameters))
        receiveToken = get_value(get_receiveToken(parameters))
        payAmount = get_value(get_payAmount(parameters))
        receiveAmount = get_value(get_receiveAmount(parameters))
        #feeAmount = get_value(get_feeAmount(parameters))
        

        return BaseTokenSwap(
            amount0 = payAmount,
            amount1 = receiveAmount,
            isAmount0In = True,
            token0_address = payToken,
            token1_address = receiveToken
        )
    
    def id_sender_exactIn_zeroForOne_inputAmount_outputAmount_sqrtPriceX96_tick_fee_totalLiquidity(self, parameters) -> ArbitarySwap:
        #id = get_value(get_id(parameters))
        sender = get_value(get_sender(parameters))
        exactIn = get_value(get_exactIn(parameters))
        zeroForOne = get_value(get_zeroForOne(parameters))
        inputAmount = get_value(get_inputAmount(parameters))
        outputAmount = get_value(get_outputAmount(parameters))
        
        return ArbitarySwap( 
            amount0 = inputAmount,
            amount1 = outputAmount,
            isAmount0In = zeroForOne
        )
        
    def inputToken_inputAmount_outputAmount_slippageProtection_user_computeOutput(self, parameters) -> TokenSwap:
        #inputToken = get_value(get_inputToken(parameters))
        #inputAmount = get_value(get_inputAmount(parameters))
        #outputAmount = get_value(get_outputAmount(parameters))
        #slippageProtection = get_value(get_slippageProtection(parameters))
        #user = get_value(get_user(parameters))
        return None
        
    def sender_amountTokenIn_amountNativeIn_amountTokenOut_amountNativeOut_flashSwap(self, parameters) -> ArbitarySwap:
        #sender = get_value(get_sender(parameters))
        #amountTokenIn = get_value(get_amountTokenIn(parameters))
        #amountNativeIn = get_value(get_amountNativeIn(parameters))
        #amountTokenOut = get_value(get_amountTokenOut(parameters))
        #amountNativeOut = get_value(get_amountNativeOut(parameters))
        #flashSwap = get_value(get_flashSwap(parameters))

        return None
    
    def optionPoolHash_recipient_amount0_amount1_sqrtPriceX96_liquidity_tick(self, parameters) -> ArbitarySwap:
        #optionPoolHash = get_value(get_optionPoolHash(parameters))
        #recipient = get_value(get_recipient(parameters))
        #amount0 = get_value(get_amount0(parameters))
        #amount1 = get_value(get_amount1(parameters))
        #sqrtPriceX96 = get_value(get_sqrtPriceX96(parameters))
        #liquidity = get_value(get_liquidity(parameters))
        
        return None


    def token_amount(self, parameters) -> TokenSwap:
        #token = get_value(get_token(parameters))
        #amount = get_value(get_amount(parameters))
        
        return None
    
    
    # Tax Dex, all variables start with _ ex. _user, _cId, _tokenIn, _tokenOut, _buyAmount, _realOutAmount, _taxToken, _taxAmount

    def _user_cId_tokenIn_tokenOut_buyAmount_realOutAmount_taxToken_taxAmount(self, parameters) -> TokenSwap:
        return None
        

    
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
    
    # Aggregator
    def sender_recipient_id_swapForY_amountIn_amountOut_votatilityAccumulated_fees(self, parameters) -> TokenSwap:
        #sender = get_value(get_sender(parameters))
        #recipient = get_value(get_recipient(parameters))
        #id = get_value(get_id(parameters))
        #amountIn = get_value(get_amountIn(parameters))
        #amountOut = get_value(get_amountOut(parameters))
        
        return None
        
    
    # Aggregator event
    def aggregatorId_sender(self, parameters) -> TokenSwap:
        #aggregatorId = get_value(get_aggregatorId(parameters))
        #sender = get_value(get_sender(parameters))
        
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
    
    def botToBuy_usdtToPay(self, parameters) -> TokenSwap:
        #botToBuy = get_value(get_botToBuy(parameters))
        #usdtToPay = get_value(get_usdtToPay(parameters))
        
        return None
    # Order Book
    def swapHash_maker_taker_recipient_inputToken_inputAmount_outputToken_outputAmount(self, parameters) -> TokenSwap:
        #swapHash = get_value(get_swapHash(parameters))
        #maker = get_value(get_maker(parameters))
        #taker = get_value(get_taker(parameters))
        #recipient = get_value(get_recipient(parameters))
        #inputToken = get_value(get_inputToken(parameters))
        
        return None
    
    def swapRouter(self, parameters) -> TokenSwap:
        #swapRouter = get_value(get_swapRouter(parameters))
        
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
