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
        self.running = False
        self.shutting_down = False

    async def connect(self):
        """
        Establish a WebSocket connection with retry logic.
        """
        for attempt in range(self.retry_attempts):
            try:
                self.connection = await websockets.connect(self.websocket_url)
                self.logger.info("Connected to Solana WebSocket.")
                self.running = True
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
        try:
            self.running = True
            self.shutting_down = False
            await self.connect()
            await self.subscribe()

            if duration:
                # Limit the runtime
                async for message in self._stream_with_timeout(duration):
                    if self.shutting_down:
                        break
                    yield message
            else:
                # Run indefinitely
                async for message in self.receive():
                    if self.shutting_down:
                        break
                    yield message
        finally:
            await self.stop()

    async def receive(self):
        """
        Receive and parse messages from the WebSocket.
        """
        while not self.shutting_down:  # Keep trying as long as we're not shutting down
            try:
                while self.running and not self.shutting_down:
                    try:
                        message = await self.connection.recv()
                        data = json.loads(message)
                        if "params" in data and "result" in data["params"]:
                            slot = data["params"]["result"].get("slot")
                            if slot is not None:
                                yield slot
                    except asyncio.TimeoutError:
                        continue
            except websockets.ConnectionClosed:
                self.logger.info("Solana WebSocket connection closed.")
                if not self.shutting_down:
                    self.logger.info("Attempting to reconnect to Solana WebSocket...")
                    await self.reconnect()
                    continue
            except Exception as e:
                self.logger.error(f"Unexpected error in receive loop: {e}")
                if not self.shutting_down:
                    await asyncio.sleep(self.retry_delay)
                    await self.reconnect()
                    continue

    async def _stream_with_timeout(self, duration):
        """
        Helper function to stream data for a limited time.
        """
        end_time = asyncio.get_running_loop().time() + duration
        async for message in self.receive():
            if self.shutting_down:
                break
            yield message
            if asyncio.get_running_loop().time() >= end_time:
                break

    async def stop(self):
        """
        Close the WebSocket connection.
        """
        self.shutting_down = True
        self.running = False
        if self.connection:
            try:
                await self.connection.close()
            except Exception as e:
                self.logger.error(f"Error closing Solana WebSocket connection: {e}")
        self.logger.info("WebSocket connection closed.")

    async def reconnect(self):
        """
        Reconnect to the WebSocket.
        """
        if not self.shutting_down:
            self.connection = None
            await self.connect()
            await self.subscribe()
            self.running = True

