import asyncio
import json
import websockets
import logging

class SolanaWebSocketHandler:
    """
    A standalone WebSocket handler for Solana to detect new slot updates with duration control.
    """
    def __init__(self, websocket_url):
        self.websocket_url = websocket_url
        self.connection = None
        self.logger = logging.getLogger(__name__)
        self.retry_attempts = 5
        self.retry_delay = 2

    async def connect(self):
        """
        Establish a WebSocket connection with retry logic.
        """
        for attempt in range(self.retry_attempts):
            try:
                self.connection = await websockets.connect(self.websocket_url)
                self.logger.info("Connected to Solana WebSocket.")
                return
            except Exception as e:
                self.logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(self.retry_delay)
        raise ConnectionError("Max retries reached. Unable to connect to Solana WebSocket.")

    async def subscribe(self):
        """
        Send the subscription message to the WebSocket.
        """
        subscription_message = {
            "jsonrpc": "2.0",
            "method": "slotSubscribe",
            "params": [],
            "id": 1
        }
        await self.connection.send(json.dumps(subscription_message))
        self.logger.info("Subscribed to slot updates.")

    async def run(self, duration=None):
        """
        Stream slot updates as they arrive, with an optional duration.
        Yields the slot number for each update.
        """
        await self.connect()
        await self.subscribe()
        start_time = asyncio.get_running_loop().time()

        try:
            while True:
                if duration and asyncio.get_running_loop().time() - start_time > duration:
                    self.logger.info("WebSocket stream duration expired.")
                    break

                message = await self.connection.recv()
                data = json.loads(message)
                if "params" in data and "result" in data["params"]:
                    slot = data["params"]["result"].get("slot")
                    if slot is not None:
                        yield slot
        except websockets.ConnectionClosed:
            self.logger.error("WebSocket connection closed. Reconnecting...")
            await self.connect()
            await self.subscribe()
        except Exception as e:
            self.logger.error(f"Error in WebSocket stream: {e}")
