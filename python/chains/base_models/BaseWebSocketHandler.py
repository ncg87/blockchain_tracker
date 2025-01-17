from abc import ABC, abstractmethod
import asyncio
import json
import websockets
import logging


class BaseWebSocketHandler(ABC):
    def __init__(self, network, websocket_url):
        """
        Initialize the BaseWebSocketHandler with the WebSocket URL.
        """
        self.logger = logging.getLogger(__name__)
        self.network = network
        self.websocket_url = websocket_url
        self.running = False
        self.connection = None
        self.retry_attempts = 5
        self.retry_delay = 2
        self.shutting_down = False  # Add flag to track intentional shutdown
        self.logger.info(f"Initializing WebSocketHandler for {network}")

    async def connect(self):
        """
        Establish a WebSocket connection with retry logic.
        """
        for attempt in range(self.retry_attempts):
            try:
                self.connection = await websockets.connect(self.websocket_url)
                self.logger.info(f"Connected to WebSocket: {self.network}")
                return
            except Exception as e:
                self.logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(self.retry_delay)
        raise ConnectionError("Max retries reached. Unable to connect to WebSocket.")

    async def subscribe(self):
        """
        Send the subscription message to the WebSocket.
        """
        subscription_message = self.get_subscription_message()
        await self.connection.send(json.dumps(subscription_message))
        self.logger.info(f"Subscribed to {self.network} updates.")

    async def receive(self):
        """
        Receive and parse messages from the WebSocket.
        """
        try:
            while self.running and not self.shutting_down:
                try:
                    message = await self.connection.recv()
                    parsed_message = self.parse_message(json.loads(message))
                    if parsed_message:
                        full_data = await self.fetch_full_data(parsed_message)
                        yield full_data
                except asyncio.TimeoutError:
                    continue
        except websockets.ConnectionClosed:
            self.logger.info(f"WebSocket connection closed for {self.network}.")
            if not self.shutting_down:  # Only attempt reconnect if not shutting down
                self.logger.info(f"Attempting to reconnect for {self.network}...")
                self.running = False
                await self.reconnect()

    async def reconnect(self):
        """
        Reconnect to the WebSocket and resubscribe.
        """
        await self.connect()
        await self.subscribe()
        self.running = True

    async def run(self, duration=None):
        """
        Run the WebSocket connection for a specified duration or indefinitely.
        """
        try:
            self.running = True
            self.shutting_down = False  # Reset shutdown flag on run
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
        Stop the WebSocket connection.
        """
        self.shutting_down = True  # Set shutdown flag
        self.running = False
        if self.connection:
            try:
                await self.connection.close()
            except Exception as e:
                self.logger.error(f"Error closing WebSocket connection for {self.network}: {e}")
        self.logger.info(f"WebSocket connection stopped for {self.network}.")

    @abstractmethod
    def get_subscription_message(self):
        """
        Abstract method to define the subscription message for the blockchain.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def parse_message(self, message):
        """
        Abstract method to parse incoming WebSocket messages.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    async def fetch_full_data(self, parsed_message):
        """
        Abstract method to fetch full data (e.g., block details) from the blockchain.
        Must be implemented by subclasses.
        """
        pass
