import redis
import json
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict


from dataclasses import dataclass
@dataclass
class SwapMetadata:
    contract_address: str
    network: str
    token0: str
    token1: str

# Helper function to serialize Decimal objects
def decimal_serializer(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError

# Helper function to deserialize data back to Decimal
def decimal_deserializer(data):
    for contract in data.values():
        volume = contract['volume']
        volume['token0'] = Decimal(volume['token0'])
        volume['token1'] = Decimal(volume['token1'])
    return data


# Initialize Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_interval_key(timestamp=None):
    """Generate a key for the current 5-minute interval"""
    if timestamp is None:
        timestamp = datetime.now()
    # Round down to nearest 5-minute interval
    interval = timestamp.replace(second=0, microsecond=0)
    interval = interval - timedelta(minutes=interval.minute % 5)
    return f"swap_volumes:{interval.strftime('%Y%m%d:%H%M')}"

def store_swap_volumes(swaps):
    """Store swap volumes for current 5-minute interval"""
    # Calculate volumes as before
    swap_to_volume = {}
    for swap in swaps:
        if swap.get('contract_address') not in swap_to_volume:
            info = SwapMetadata(
                contract_address=swap.get('contract_address'),
                network=swap.get('network'),
                token0=swap.get('token0'),
                token1=swap.get('token1')
            )
            swap_to_volume[swap.get('contract_address')] = {
                'info': asdict(info),
                'volume': {
                    'token0': 0,
                    'token1': 0
                }
            }
        swap_to_volume[swap.get('contract_address')]['volume']['token0'] += abs(swap.get('amount0'))
        swap_to_volume[swap.get('contract_address')]['volume']['token1'] += abs(swap.get('amount1'))
    
    # Store in Redis
    current_key = get_interval_key()
    redis_client.setex(
        current_key,
        3600,  # Keep for 1 hour
        json.dumps(swap_to_volume, default=decimal_serializer)
    )
    
    # Clean up old intervals (keep only last 12 intervals = 1 hour)
    cleanup_old_intervals()

def cleanup_old_intervals():
    """Remove intervals older than 1 hour"""
    current_time = datetime.now()
    all_keys = redis_client.keys("swap_volumes:*")
    for key in all_keys:
        key_str = key.decode('utf-8')
        key_time = datetime.strptime(key_str.split(':')[1], '%Y%m%d:%H%M')
        if current_time - key_time > timedelta(hours=1):
            redis_client.delete(key)

def get_volume_history(hours=1):
    """Get volume history for the specified number of hours"""
    all_keys = redis_client.keys("swap_volumes:*")
    all_keys = sorted([key.decode('utf-8') for key in all_keys])
    
    # Get only the most recent intervals
    num_intervals = int(hours * 12)  # 12 intervals per hour
    recent_keys = all_keys[-num_intervals:] if len(all_keys) > num_intervals else all_keys
    
    history = {}
    for key in recent_keys:
        data = redis_client.get(key)
        if data:
            interval_time = datetime.strptime(key.split(':')[1], '%Y%m%d:%H%M')
            history[interval_time] = decimal_deserializer(json.loads(data))
    
    return history

# Example usage:
in[1]: # Store current interval
store_swap_volumes(swaps)

in[2]: # Get volume history
history = get_volume_history()
for timestamp, data in history.items():
    print(f"\nInterval: {timestamp}")
    for contract, details in data.items():
        print(f"Contract: {contract}")
        print(f"Network: {details['info']['network']}")
        print(f"Volume token0: {details['volume']['token0']}")
        print(f"Volume token1: {details['volume']['token1']}")
        print("---")

# Get volumes for a specific contract across all intervals
def get_contract_history(contract_address, hours=1):
    """Get volume history for a specific contract"""
    history = get_volume_history(hours)
    contract_history = {}
    
    for timestamp, data in history.items():
        if contract_address in data:
            contract_history[timestamp] = data[contract_address]
    
    return contract_history

in[3]: # Example: Get history for specific contract
contract_history = get_contract_history("0x32A5746bA6826828716Cc1A394bC33301eBC7656")
for timestamp, data in contract_history.items():
    print(f"\nTimestamp: {timestamp}")
    print(f"Volume token0: {data['volume']['token0']}")
    print(f"Volume token1: {data['volume']['token1']}")