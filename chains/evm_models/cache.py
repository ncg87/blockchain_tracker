from datetime import datetime, timedelta
from collections import OrderedDict

class BoundedCache:
    def __init__(self, max_size=1000, ttl_hours=24):
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self.cache = OrderedDict()

    def get(self, key):
        if key not in self.cache:
            return None
        value, timestamp = self.cache[key]
        if datetime.now() - timestamp > self.ttl:
            del self.cache[key]
            return None
        return value

    def set(self, key, value):
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)  # Remove oldest item
        self.cache[key] = (value, datetime.now())
