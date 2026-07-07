def decode_utf8(data: bytes, start_index: int) -> tuple[str, int]:
    """Decode a UTF-8 character from the data starting at start_index.

    Returns a tuple of the decoded character and the number of bytes consumed.
    If the sequence is invalid, returns ('�', 1).
    """
    if start_index >= len(data):
        return "�", 0

    first_byte = data[start_index]
    if first_byte < 0x80:
        return chr(first_byte), 1
    elif 0xC2 <= first_byte <= 0xDF:
        length = 2
    elif 0xE0 <= first_byte <= 0xEF:
        length = 3
    elif 0xF0 <= first_byte <= 0xF4:
        length = 4
    else:
        return "�", 1

    if start_index + length > len(data):
        return "�", len(data) - start_index

    seq = data[start_index:start_index + length]
    if any((b & 0xC0) != 0x80 for b in seq[1:]):
        return "�", length

    try:
        char = seq.decode('utf-8')
        return char, length
    except UnicodeDecodeError:
        return "�", length
    
def decode_utf16(data: bytes, start_index: int) -> tuple[str, int]:
    """Decode a UTF-16 character from the data starting at start_index.

    Returns a tuple of the decoded character and the number of bytes consumed.
    If the sequence is invalid, returns ('�', consumed_bytes).
    """
    if start_index + 1 >= len(data):
        return "�", len(data) - start_index

    unit1 = int.from_bytes(data[start_index:start_index + 2], 'little')

    # High-surrogate: requires a following low-surrogate (4 bytes total).
    if 0xD800 <= unit1 <= 0xDBFF:
        if start_index + 3 >= len(data):
            return "�", len(data) - start_index

        unit2 = int.from_bytes(data[start_index + 2:start_index + 4], 'little')
        if not (0xDC00 <= unit2 <= 0xDFFF):
            return "�", 2

        try:
            char = data[start_index:start_index + 4].decode('utf-16le')
            return char, 4
        except UnicodeDecodeError:
            return "�", 4

    # Lone low-surrogate is invalid.
    if 0xDC00 <= unit1 <= 0xDFFF:
        return "�", 2

    try:
        char = data[start_index:start_index + 2].decode('utf-16le')
        return char, 2
    except UnicodeDecodeError:
        return "�", 2
