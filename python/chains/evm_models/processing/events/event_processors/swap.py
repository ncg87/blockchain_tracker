from ..models import ArbitarySwap
from typing import Optional
from operator import itemgetter
from .processors import EventProcessor

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


class SwapProcessor(EventProcessor):
    def __init__(self):
        super().__init__()
        self.logger.info("SwapProcessor initialized")
        

    def process_event(self, event : dict, signature: str) -> Optional[ArbitarySwap]:
        
        # Check if signature is provided, if not, get it from the event
        
        try:
            protocol_info = self.protocol_map[signature]
            
            swap_info = protocol_info(event)
            
            return swap_info
        
        except Exception as e:
            self.logger.error(f"Error processing event {event} - signature: {signature} - {e}", exc_info=True)
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
            #"d78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822" : self.sender_amount0In_amount1In_amount0Out_amount1Out_to,
            "dba43ee9916cb156cc32a5d3406e87341e568126a46815294073ba25c9400246": self.assetIn_assetOut_sender_receiver_amountIn_amountOut_referralCode,
            
            
            
        }
        
    # Check if correct
    def sender_to_amount0_amount1(self, event) -> ArbitarySwap:
        
        sender = get_value(get_sender(event))
        to = get_value(get_to(event))
        amount0 = get_value(get_amount0(event))
        amount1 = get_value(get_amount1(event))
        
        return ArbitarySwap (
            amount0 = amount0,
            amount1 = amount1,
            isAmount0In = True
        )

    # Uniswap V2
    def sender_to_amount0In_amount1In_amount0Out_amount1Out(self, event) -> ArbitarySwap:
        
        
        sender = get_value(get_sender(event))
        to = get_value(get_to(event))
        amount0In = get_value(get_amount0In(event))
        
        if amount0In > 0:
            amount1 = get_value(get_amount1Out(event))
            return ArbitarySwap (
                amount0 = amount0In,
                amount1 = amount1,
                isAmount0In = True
            )
        else:
            amount0 = get_value(get_amount0Out(event))
            amount1 = get_value(get_amount1In(event))
            return ArbitarySwap (
                amount0 = amount0,
                amount1 = amount1,
                isAmount0In = False
            )
    # Uniswap V3 type swap
    def sender_recipient_amount0_amount1_sqrtPriceX96_liquidity_tick(self, event) -> ArbitarySwap:
        
        

        sender = get_value(get_sender(event))
        recipient = get_value(get_recipient(event))
        amount0 = get_value(get_amount0(event))
        amount1 = get_value(get_amount1(event))
        sqrtPriceX96 = get_value(get_sqrtPriceX96(event))         # Can use this to determine price of tokens in the future
        liquidity = get_value(get_liquidity(event))
        tick = get_value(get_tick(event))

        isAmount0In = amount0 > 0

        return ArbitarySwap (
            amount0 = amount0,
            amount1 = amount1,
            isAmount0In = isAmount0In
        )
    
    # Uniswap V2 fork
    def amount0In_amount0Out_amount1In_amount1Out(self, event) -> ArbitarySwap:
        amount0In = get_value(get_amount0In(event))

        if amount0In > 0:
            amount1 = get_value(get_amount1Out(event))
            return ArbitarySwap (
                amount0 = amount0In,
                amount1 = amount1,
                isAmount0In = True
            )
        else:
            amount0 = get_value(get_amount0Out(event))
            amount1 = get_value(get_amount1In(event))
            
            return ArbitarySwap (
                amount0 = amount0,
                amount1 = amount1,
                isAmount0In = False
            )
    
    def poolId_tokenIn_tokenOut_amountIn_amountOut(self, event) -> ArbitarySwap:
        
        poolId = get_value(get_poolId(event))
        tokenIn = get_value(get_tokenIn(event))
        tokenOut = get_value(get_tokenOut(event))
        
        amountIn = get_value(get_amountIn(event))
        amountOut = get_value(get_amountOut(event))
        
        return ArbitarySwap (
            amount0 = amountIn,
            amount1 = amountOut,
            isAmount0In = True
        )
    
    def poolId_tokenIn_tokenOut_amountIn_amountOut_user(self, event) -> ArbitarySwap:

        poolId = get_value(get_poolId(event))
        tokenIn = get_value(get_tokenIn(event))
        tokenOut = get_value(get_tokenOut(event))
        user = get_value(get_user(event))

        amountIn = get_value(get_amountIn(event))
        amountOut = get_value(get_amountOut(event))
        
        return ArbitarySwap (
            amount0 = amountIn,
            amount1 = amountOut,
            isAmount0In = True
        )
    
    def sender_recipient_baseIn_quoteIn_baseOut_quoteOut_fee_adminFee_oraclePrice(self, event) -> ArbitarySwap:
        sender = get_value(get_sender(event))
        recipient = get_value(get_recipient(event))
        baseIn = get_value(get_baseIn(event))
        quoteIn = get_value(get_quoteIn(event))
        baseOut = get_value(get_baseOut(event))
        quoteOut = get_value(get_quoteOut(event))
        fee = get_value(get_fee(event))
        adminFee = get_value(get_adminFee(event))
        oraclePrice = get_value(get_oraclePrice(event))
        
        raise Exception("Not implemented")

    def tokenIn_tokenOut_amountIn_amountOut(self, event) -> ArbitarySwap:
        
        tokenIn = get_value(get_tokenIn(event))
        tokenOut = get_value(get_tokenOut(event))
        amountIn = get_value(get_amountIn(event))
        amountOut = get_value(get_amountOut(event))
        
        return ArbitarySwap(
            amount0=amountIn, 
            amount1=amountOut, 
            isAmount0In=True)

    def sender_amount0In_amount1In_amount0Out_amount1Out_to(self, event) -> ArbitarySwap:
        sender = get_value(get_sender(event))
        to = get_value(get_to(event))
        amount0In = get_value(get_amount0In(event))
        
        if amount0In > 0:
            amount1 = get_value(get_amount1Out(event))
            return ArbitarySwap (
                amount0 = amount0In,
                amount1 = amount1,
                isAmount0In = True
            )
        else:
            amount0 = get_value(get_amount0Out(event))
            amount1 = get_value(get_amount1In(event))
            return ArbitarySwap (
                amount0 = amount0,
                amount1 = amount1,
                isAmount0In = False
            )

    def assetIn_assetOut_sender_receiver_amountIn_amountOut_referralCode(self, event) -> ArbitarySwap:
        assetIn = get_value(get_assetIn(event))
        assetOut = get_value(get_assetOut(event))
        sender = get_value(get_sender(event))
        receiver = get_value(get_receiver(event))
        amountIn = get_value(get_amountIn(event))
        amountOut = get_value(get_amountOut(event))
        referralCode = get_value(get_referralCode(event))
        
        return ArbitarySwap(
            amount0 = amountIn,
            amount1 = amountOut,
            isAmount0In = True
        )

