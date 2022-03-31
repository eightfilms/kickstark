from starkware.starknet.business_logic.state import BlockInfo


def to_uint(a):
    """Takes in value, returns uint256-ish tuple."""
    return (a & ((1 << 128) - 1), a >> 128)


def uint(a):
    return (a, 0)


def str_to_felt(text):
    b_text = bytes(text, "UTF-8")
    return int.from_bytes(b_text, "big")
