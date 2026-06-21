"""Functions to load and save data from and to the mouse"""

import types

import usb.core
import usb.util

VENDOR_ID = 0x04d9  # Holtek

INTERFACE = 2

# HID custom feature report constants

SET_REQUEST_TYPE = usb.util.CTRL_OUT | usb.util.CTRL_TYPE_CLASS | usb.util.CTRL_RECIPIENT_INTERFACE
SET_REPORT = 0x09

GET_REQUEST_TYPE = usb.util.CTRL_IN | usb.util.CTRL_TYPE_CLASS | usb.util.CTRL_RECIPIENT_INTERFACE
GET_REPORT = 0x01

FEATURE_REPORT = 0x0300
LEN_16B = 0x02  # 16 byte payloads
LEN_64B = 0x03  # 64 byte payloads
REPORT_16B = FEATURE_REPORT | LEN_16B
REPORT_64B = FEATURE_REPORT | LEN_64B

OP_SEEK = 0xf2
OP_WRITE = 0xf3
OP_LOCK = 0xf5

TIMEOUT = 1000  # 1 second

class RedragonMouse:
    def __init__(self):
        devs = usb.core.find(idVendor=VENDOR_ID, find_all=True)
        assert isinstance(devs, types.GeneratorType)
        devs = list(devs)
        if not devs:
            raise ValueError("Device not found")
        if len(devs) > 1:
            raise ValueError("Multiple devices found")

        self.dev = devs[0]
        if self.dev.is_kernel_driver_active(INTERFACE):
            self.dev.detach_kernel_driver(INTERFACE)

    def read_all(self) -> bytes:
        self._unlock()
        data = bytearray()
        for i in range(0, 0x1C00, 64):
            data.extend(self._read64(i, 64))
            print('.', end='', flush=True)
        self._lock()
        print()
        return bytes(data)

    def write_diff(self, original: bytes, modified: bytes | bytearray | memoryview) -> None:
        self._unlock()
        for i in range(0, len(original), 64):
            chunk_orig = original[i:i+64]
            if i < len(modified):
                chunk_mod = modified[i:i+64]
            else:
                chunk_mod = bytes()
            if chunk_orig != chunk_mod:
                print(f"Writing bytes {i:04X} to {i+len(chunk_mod):04X}...")
                self._write64(i, len(chunk_mod), *chunk_mod)
        self._lock()

    def _addr_to_tuple(self, addr: int) -> tuple[int, int]:
        return (addr & 0xff, addr >> 8 & 0xff)

    def _read16(self, addr: int, n: int) -> list[int]:
        addr_tuple = self._addr_to_tuple(addr)
        self._set(REPORT_16B, [LEN_16B, OP_SEEK, *addr_tuple, n], 16)
        return self._get(REPORT_16B, 16)

    def _read64(self, addr: int, n: int) -> list[int]:
        addr_tuple = self._addr_to_tuple(addr)
        self._set(REPORT_64B, [LEN_64B, OP_SEEK, *addr_tuple, n], 64)
        return self._get(REPORT_64B, 64)

    def _write16(self, addr: int, n: int, *args: int):
        addr_tuple = self._addr_to_tuple(addr)
        self._set(REPORT_16B, [LEN_16B, OP_WRITE,
                  *addr_tuple, n, 0, 0, 0, *args], 16)

    def _write64(self, addr: int, n: int, *args: int):
        addr_tuple = self._addr_to_tuple(addr)
        self._set(REPORT_64B, [LEN_64B, OP_WRITE,
                  *addr_tuple, n, 0, 0, 0, *args], 64)

    def _unlock(self) -> None:
        self._set(REPORT_16B, [LEN_16B, OP_LOCK, 0], 16)

    def _lock(self) -> None:
        self._set(REPORT_16B, [LEN_16B, OP_LOCK, 1], 16)

    def _set(self, report: int, msg: list[int], length: int):
        pad = [0] * (length - len(msg))
        data = bytearray(msg + pad)
        sent = self.dev.ctrl_transfer(
            SET_REQUEST_TYPE, SET_REPORT, report, INTERFACE, data, TIMEOUT)
        assert sent == length, f"Expected to send {length} bytes, but sent {sent}"

    def _get(self, report: int, length: int) -> list[int]:
        data = self.dev.ctrl_transfer(
            GET_REQUEST_TYPE, GET_REPORT, report, INTERFACE, length, TIMEOUT)
        return list(data[8:])
