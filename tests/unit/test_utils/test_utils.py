import pytest
from chains.utils import decode_hex, normalize_hex, decode_extra_data
from hexbytes import HexBytes

def test_decode_hex():
    """Test hex decoding function."""
    # Test valid hex string
    assert decode_hex("0x10") == 16
    
    # Test non-hex input
    assert decode_hex("not hex") == "not hex"
    
    # Test None input
    assert decode_hex(None) is None
    
    # Test empty string
    assert decode_hex("") == ""

def test_normalize_hex():
    """Test hex normalization function."""
    # Test HexBytes input
    hex_bytes = HexBytes("0x123")
    assert normalize_hex(hex_bytes) == "0x123"
    
    # Test string input
    assert normalize_hex("0x123") == "0x123"
    
    # Test None input
    assert normalize_hex(None) is None

def test_decode_extra_data():
    """Test extra data decoding."""
    # Test with HexBytes
    block = {"extraData": HexBytes("0x48656c6c6f")}  # "Hello" in hex
    assert decode_extra_data(block) == "Hello"
    
    # Test with hex string
    block = {"extraData": "0x48656c6c6f"}
    assert decode_extra_data(block) == "Hello"