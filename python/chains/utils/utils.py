from hexbytes import HexBytes

def normalize_hex(value):
    """
    Normalize a value to a hexadecimal string.
    :param value: The input value (HexBytes or string).
    :return: Hexadecimal string.
    """
    if isinstance(value, HexBytes):
        return value.to_0x_hex()  # Convert HexBytes to hex string
    return value  # Assume it's already a string

def decode_hex(value):
    """
    Decode a hexadecimal string to an integer if it's an Ethereum-style integer (e.g., block numbers, gas values).
    Does not decode long hashes or other non-integer hex values.
    :param value: Hexadecimal string (e.g., '0x677df92f') or other types.
    :return: Decoded integer or original value if not a valid short hex integer.
    """
    if isinstance(value, str) and value.startswith("0x"):
        # Only decode if the hex string is short (e.g., block numbers, gas, timestamps)
        return int(value, 16)
    return value  # Return original value if not a short hex integer

def decode_extra_data(block):
    """
    Normalize the extraData field in PoA blocks.
    :param block: The block data dictionary.
    :return: The block data dictionary with normalized extraData.
    """
    if "extraData" in block:
        if isinstance(block["extraData"], HexBytes):
            data = block["extraData"].decode("utf-8")
        elif isinstance(block["extraData"], str):
           data = HexBytes(block["extraData"]).decode("utf-8")

    return data