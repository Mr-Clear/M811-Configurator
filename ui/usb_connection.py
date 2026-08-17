"""Functions to load and save data from and to the mouse"""

from typing import Callable

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

REPORT_HEADER_LEN = 8
REPORT_64_TOTAL = 64 + REPORT_HEADER_LEN

OP_COMMAND = 0xf1
OP_SEEK = 0xf2
OP_WRITE = 0xf3
OP_LOCK = 0xf5

TIMEOUT = 1000  # 1 second


class UsbConnection:
    def __init__(self, dev: usb.core.Device | None):
        self.dev = dev or UsbConnection.find_device()
        if self.dev.is_kernel_driver_active(INTERFACE):
            self.dev.detach_kernel_driver(INTERFACE)

    @staticmethod
    def find_devices() -> list[usb.core.Device]:
        '''Find all connected Redragon mice and return a list of UsbConnection objects.'''
        devs = usb.core.find(idVendor=VENDOR_ID, find_all=True)
        return [dev for dev in devs]

    @staticmethod
    def find_device() -> usb.core.Device:
        devs = UsbConnection.find_devices()
        if not devs:
            raise ValueError("Device not found")
        if len(devs) > 1:
            raise ValueError("Multiple devices found")
        return devs[0]

    def read_all(self, progress_callback: Callable[[int], None] | None = None) -> bytes:
        self._unlock()
        data = bytearray()
        for i in range(0, 0x1C00, 64):
            data.extend(self._read64(i, 64))
            if progress_callback:
                progress_callback(i + 64)
            else:
                print('.', end='', flush=True)
        self._lock()
        if not progress_callback:
            print()
        return bytes(data)

    def write_diff(self,
                   original: bytes | bytearray | memoryview | None,
                   modified: bytes | bytearray | memoryview,
                   progress_callback: Callable[[int], None] | None = None) -> None:
        self._unlock()
        chunk_size = 64
        for i in range(0, len(modified), chunk_size):
            chunk_mod = modified[i:i+chunk_size]
            if original is not None and i < len(original):
                chunk_orig = original[i:i+chunk_size]
            else:
                chunk_orig = bytes()
            if chunk_orig != chunk_mod:
                if progress_callback:
                    progress_callback(i + len(chunk_mod))
                print(
                    f"Writing bytes 0x{i:04X} to 0x{i+len(chunk_mod)-1:04X}...")
                self._write64(i, len(chunk_mod), *chunk_mod)
        self._apply()
        self._lock()

    @property
    def name(self) -> str:
        from .mouse import MouseType
        type = MouseType.from_product_id(self.dev.idProduct)
        return type.name if type else f"Unknown ({self.dev.idVendor:04x}:{self.dev.idProduct:04x})"

    @property
    def ids(self) -> str:
        return f"{self.dev.idVendor:04x}:{self.dev.idProduct:04x}"

    @property
    def path(self) -> str:
        return f"{self.dev.bus}-{self.dev.address}"

    def _addr_to_tuple(self, addr: int) -> tuple[int, int]:
        return (addr & 0xff, addr >> 8 & 0xff)

    def _read16(self, addr: int, n: int) -> list[int]:
        addr_tuple = self._addr_to_tuple(addr)
        self._set(REPORT_16B, [LEN_16B, OP_SEEK, *addr_tuple, n], 16)
        return self._get(REPORT_16B, 16)

    def _read64(self, addr: int, n: int) -> list[int]:
        addr_tuple = self._addr_to_tuple(addr)
        self._set(REPORT_64B, [LEN_64B, OP_SEEK, *addr_tuple, n], 64)
        # 64-byte payload reports include an 8-byte report header.
        return self._get(REPORT_64B, REPORT_64_TOTAL)

    def _write16(self, addr: int, n: int, *args: int):
        addr_tuple = self._addr_to_tuple(addr)
        self._set(REPORT_16B, [LEN_16B, OP_WRITE,
                  *addr_tuple, n, 0, 0, 0, *args], 16)

    def _write64(self, addr: int, n: int, *args: int):
        addr_tuple = self._addr_to_tuple(addr)
        self._set(REPORT_64B, [LEN_64B, OP_WRITE,
                  *addr_tuple, n, 0, 0, 0, *args], REPORT_64_TOTAL)

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

    def _command(self, cmd: int) -> None:
        self._set(REPORT_16B, [LEN_16B, OP_COMMAND, 0x02, cmd], 0x10)

    def _apply(self) -> None:
        commands = [0x01, 0x04, 0x01, 0x02, 0x08, 0x10]  # Got by Wireshark
        # commands = [0x01, 0x04] # Trial and error
        for cmd in commands:
            self._command(cmd)
