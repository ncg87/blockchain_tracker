from ..base_models import BaseWebSocketHandler
import asyncio
import json
import time
from collections import deque

class SolanaWebSocketHandler(BaseWebSocketHandler):
    def __init__(self, websocket_url):
        super().__init__("Solana", websocket_url)
        self.logger.info(f"Initializing SolanaWebSocketHandlerOptimized for Solana")
        self.last_slot = None
        self.message_queue = deque(maxlen=1000)  # Circular buffer to prevent unbounded memory growth

    def get_subscription_message(self):
        """
        Define the subscription message for Solana.
        Subscribes to slot updates with a finalized commitment level.
        """
        return {
            "jsonrpc": "2.0",
            "method": "slotSubscribe",
            "params": [],
            "id": 1
        }

    def parse_message(self, message):
        """
        Parse incoming WebSocket messages for Solana.
        Extract the slot number and filter duplicates.
        """
        try:
            if "params" in message and "result" in message["params"]:
                slot = message["params"].get("result").get("slot")
                if slot and slot != self.last_slot:  # Skip duplicate slots
                    self.last_slot = slot
                    return slot
            return None
        except Exception as e:
            self.logger.error(f"Error parsing WebSocket message: {e}")
            return None

    async def fetch_full_data(self, slot):
        """
        Fetch additional block data based on the parsed slot.
        Returns None if no block exists for the slot.
        """
        try:
            request_message = {
                "jsonrpc": "2.0",
                "method": "getBlock",
                "params": [slot, {"transactionDetails": "full", "rewards": True}],
                "id": 1
            }
            await self.connection.send(json.dumps(request_message))
            response = await self.connection.recv()
            print(response)
            return response
        except Exception as e:
            self.logger.error(f"Failed to fetch block data for slot {slot}: {e}")
            return None

    async def receive(self):
        """
        Receive and process messages from the WebSocket with optimizations.
        """
        throttle_interval = 0.1  # Throttle to process messages every 100ms
        last_processed_time = time.time()

        try:
            while self.running:
                try:
                    message = await self.connection.recv()
                    self.logger.info(f"Raw message received: {message}")
                    parsed_message = self.parse_message(json.loads(message))

                    # Throttle message processing
                    current_time = time.time()
                    if parsed_message and current_time - last_processed_time > throttle_interval:
                        self.message_queue.append(parsed_message)
                        last_processed_time = current_time

                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            self.logger.info("WebSocket receive loop cancelled.")
        except Exception as e:
            self.logger.error(f"Error in receive loop: {e}")
            self.running = False
            await self.reconnect()

    async def run(self, duration=None):
        """
        Run the WebSocket connection with batching and optimized handling.
        """
        try:
            self.running = True
            await self.connect()
            await self.subscribe()

            start_time = time.time()
            while self.running:
                # Exit if duration is specified and exceeded
                if duration and (time.time() - start_time) > duration:
                    break

                if self.message_queue:
                    slot = self.message_queue.popleft()
                    block_data = await self.fetch_full_data(slot)
                    if block_data:
                        self.logger.info(f"Yielding block data for slot: {slot}")
                        yield block_data

                await asyncio.sleep(0.01)  # Prevent tight looping
        finally:
            await self.stop()

    async def reconnect(self):
        """
        Reconnect to the WebSocket and resubscribe after a disconnect.
        """
        await self.connect()
        await self.subscribe()
        self.running = True

    async def stop(self):
        """
        Stop the WebSocket connection.
        """
        self.running = False
        if self.connection:
            await self.connection.close()
        self.logger.info(f"WebSocket connection stopped for {self.network}.")
