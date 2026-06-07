'''Module for interfacing with Redragon mice over USB,
   allowing reading and writing of configuration data.
   Reverse engineered by https://github.com/dokutan/mouse_m908/tree/master'''

import types
from dataclasses import dataclass
from enum import Enum

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

# mouse memory addresses

ADR_SCROLL = (0x20, 0)
ADR_ACTIVE = (0x2c, 0)
ADR_POLLRATE = (0x32, 0)

ADR_DPIS = [(0x42, 0), (0x02, 1), (0xb2, 1), (0x62, 2), (0x12, 3)]

PROFILE_COUNT = 5

ADR_KEYMAPS = [
    [(0x82, 0), (0x86, 0), (0x8a, 0), (0x8e, 0), (0x92, 0), (0x96, 0), (0x9a, 0), (0x9e, 0),
     (0xa2, 0), (0xa6, 0), (0xaa, 0), (0xae, 0), (0xb2, 0), (0xb6, 0), (0xba, 0), (0xbe, 0),
     (0xc2, 0), (0xc6, 0), (0xda, 0), (0xde, 0)],
    [(0x42, 1), (0x46, 1), (0x4a, 1), (0x4e, 1), (0x52, 1), (0x56, 1), (0x5a, 1), (0x5e, 1),
     (0x62, 1), (0x66, 1), (0x6a, 1), (0x6e, 1), (0x72, 1), (0x76, 1), (0x7a, 1), (0x7e, 1),
     (0x82, 1), (0x86, 1), (0x9a, 1), (0x9e, 1)],
    [(0xf2, 1), (0xf6, 1), (0xfa, 1), (0xfe, 1), (0x02, 2), (0x06, 2), (0x0a, 2), (0x0e, 2),
     (0x12, 2), (0x16, 2), (0x1a, 2), (0x1e, 2), (0x22, 2), (0x26, 2), (0x2a, 2), (0x2e, 2),
     (0x32, 2), (0x36, 2), (0x4a, 2), (0x4e, 2)],
    [(0xa2, 2), (0xa6, 2), (0xaa, 2), (0xae, 2), (0xb2, 2), (0xb6, 2), (0xba, 2), (0xbe, 2),
     (0xc2, 2), (0xc6, 2), (0xca, 2), (0xce, 2), (0xd2, 2), (0xd6, 2), (0xda, 2), (0xde, 2),
     (0xe2, 2), (0xe6, 2), (0xfa, 2), (0xfe, 2)],
    [(0x52, 3), (0x56, 3), (0x5a, 3), (0x5e, 3), (0x62, 3), (0x66, 3), (0x6a, 3), (0x6e, 3),
     (0x72, 3), (0x76, 3), (0x7a, 3), (0x7e, 3), (0x82, 3), (0x86, 3), (0x8a, 3), (0x8e, 3),
     (0x92, 3), (0x96, 3), (0xaa, 3), (0xae, 3)],
]

ADR_EFFECTS = [
    (0x49, 4),
    (0x51, 4),
    (0x59, 4),
    (0x61, 4),
    (0x69, 4),
]


class MouseType(Enum):
    '''Enumeration of supported mouse types, identified by USB product ID.'''
    M901 = 0xfc02
    M990 = 0xfc0f
    M709 = 0xfc2a
    M702 = 0xfc2f
    M711 = 0xfc30
    M602 = 0xfc38
    M607 = 0xfc38
    M715 = 0xfc39
    M921 = 0xfc40
    M990_RGB = 0xfc41
    M909 = 0xfc42
    M802 = 0xfc42
    M910 = 0xfc49
    M908 = 0xfc4d
    M719 = 0xfc4f
    M721 = 0xfc5c
    M801 = 0xfc56
    M808 = 0xfc5f
    M612 = 0xfc61
    M811 = 0xfc6d

    @staticmethod
    def from_product_id(product_id: int) -> "MouseType | None":
        '''Get the MouseType corresponding to a given USB product ID, or None if not recognized.'''
        for mouse_type in MouseType:
            if mouse_type.value == product_id:
                return mouse_type
        return None


@dataclass
class UsbDevice:
    '''Representation of a USB device with associated mouse type and access information.'''
    dev: usb.core.Device
    type: MouseType | None
    name: str | None
    supported: bool
    access: bool


class Mouse:
    '''Class representing a connected mouse device,
       providing methods to read and write its configuration.'''
    def __init__(self, product_id: int) -> None:
        results = usb.core.find(idVendor=VENDOR_ID, idProduct=product_id)
        if not isinstance(results, usb.core.Device):
            raise AttributeError(
                f"No USB device with ID {VENDOR_ID:04x}:{product_id:04x}")
        self.dev: usb.core.Device = results

    @classmethod
    def from_device(cls, dev: usb.core.Device) -> "Mouse":
        '''Create a Mouse instance from a usb.core.Device, without checking the product ID.'''
        mouse = cls.__new__(cls)
        mouse.dev = dev
        return mouse

    def get_active_profile(self) -> int:
        '''Get the index of the currently active profile.'''
        self._unlock()
        data = self._read16(ADR_ACTIVE, 1)
        self._lock()
        return data[0]

    def get_poll_rates(self) -> list[int]:
        '''Get the polling rates for all profiles.'''
        self._unlock()
        data = self._read64(ADR_POLLRATE, 10)
        self._lock()
        return [data[i] for i in range(0, 10, 2)]

    def set_poll_rates(self, rates: list[int]) -> None:
        '''Set the polling rates for all profiles.'''
        gapped = [v for r in rates for v in (r, 0)]
        self._unlock()
        self._write64(ADR_POLLRATE, 10, *gapped)
        self._lock()

    def get_effects(self, profile: int) -> list[int]:
        ''''Get the lighting effects for a given profile. Returns a list of 7 integers:
            R, G, B, lightmode_low, speed, lightmode_high, brightness.'''
        self._unlock()
        effects = self._read16(ADR_EFFECTS[profile], 7)
        self._lock()
        return effects

    def set_effects(self, profile: int, effects: list[int]) -> None:
        '''Set the lighting effects for a given profile.
           Expects a list of 7 ints: R, G, B, lightmode_low, speed, lightmode_high, brightness.'''
        self._unlock()
        self._write16(ADR_EFFECTS[profile], 7, *effects)
        self._lock()

    def get_keymap(self, profile: int, size: int) -> list[list[int]]:
        '''Get the keymap for a given profile.
           Returns a list of [up to] 20 lists of 3 integers, representing the button codes for each
           button.'''
        addrs = ADR_KEYMAPS[profile]
        self._unlock()
        codes = [self._read16(addrs[i], 4) for i in range(size)]
        self._lock()
        return codes

    def print_keymap(self, profile: int, size: int) -> None:
        '''Print the keymap for a given profile in a human-readable format.'''
        codes = self.get_keymap(profile, size)
        for i, code in enumerate(codes):
            print(f"{i:02} - 0x{code[0]:02x} 0x{code[1]:02x} 0x{code[2]:02x}")

    def set_keymap(self, profile: int, codes: list[list[int]]) -> None:
        '''Set the keymap for a given profile. Expects a list of [up to] 20 lists of 3 integers,
           representing the button codes for each button.'''
        addrs = ADR_KEYMAPS[profile]
        self._unlock()
        for addr, code in zip(addrs, codes):
            self._write16(addr, 4, *code)
        self._lock()

    def get_dpis(self, profile: int) -> list[list[int]]:
        '''Get the DPI levels for a given profile. Returns a list of 5 lists of 2 integers,
           representing the low and high bytes of the DPI levels.
           Levels that are not set will be returned as [0, 0].'''
        self._unlock()
        dpi_codes = self._read64(ADR_DPIS[profile], 32)
        self._lock()
        # first two bytes skipped, unused
        levels = [dpi_codes[i+1:i+3] for i in range(2, 32, 6)
                  if dpi_codes[i] == 1]
        return levels

    def set_dpis(self, profile: int, levels: list[list[int]]) -> None:
        '''Set the DPI levels for a given profile. Expects a list of [up to] 5 lists of 2 integers,
           representing the low and high bytes of the DPI levels.
           Levels that are not set should be [0, 0].'''
        dpi_codes = [[1, l, h] for l, h in levels]
        while len(dpi_codes) < 5:
            dpi_codes.append([0, 0, 0])
        addr = ADR_DPIS[profile]
        self._unlock()
        for i, data in enumerate(dpi_codes):
            level_addr = addr[0] + 2 + (6 * i), addr[1]
            self._write16(level_addr, 4, *data)
        self._lock()

    def get_scroll_speeds(self) -> list[int]:
        '''Get the scroll wheel speeds for all profiles. Returns a list of 5 integers,
           representing the scroll speeds for each profile.
           Profiles that are not set will be returned as 0.'''
        self._unlock()
        data = self._read64(ADR_SCROLL, 10)
        self._lock()
        return [data[i] for i in range(0, 10, 2)]

    def set_scroll_speeds(self, speeds: list[int]) -> None:
        '''Set the scroll wheel speeds for all profiles.
           Expects a list of 5 integers, representing the scroll speeds for each profile.
           Profiles that are not set should be 0.'''
        gapped = [v for s in speeds for v in (s, 0)]
        self._unlock()
        self._write64(ADR_SCROLL, 10, *gapped)
        self._lock()

    @staticmethod
    def find_devices() -> list[UsbDevice]:
        ''''Find all connected Redragon mice and return a list of UsbDevice objects.'''
        devs = usb.core.find(idVendor=VENDOR_ID, find_all=True)
        assert isinstance(devs, types.GeneratorType)
        result: list[UsbDevice] = []
        for dev in devs:
            assert isinstance(dev, usb.core.Device)
            access = Mouse._test_access(dev)
            for mouse_type in MouseType:
                if dev.idProduct == mouse_type.value:
                    device_type = mouse_type
                    device_name = mouse_type.name
                    supported = True
                    break
            else:
                device_type = None
                try:
                    device_name = f"Unknown {dev.product}"
                except (usb.core.USBError, ValueError):
                    device_name = "Unknown device"
                supported = False
            result.append(UsbDevice(dev, device_type,
                          device_name, supported, access))

        # Find duplicate names
        duplicates: set[str] = set()
        for i, dev_i in enumerate(result):
            for j in range(i + 1, len(result)):
                name = dev_i.name
                if name is not None and name == result[j].name:
                    duplicates.add(name)

        for dev in result:
            if dev.name in duplicates:
                dev.name += f" ({dev.dev.bus}/{dev.dev.address})"

        return result

    @staticmethod
    def _test_access(dev: usb.core.Device) -> bool:
        try:
            if dev.is_kernel_driver_active(INTERFACE):
                dev.detach_kernel_driver(INTERFACE)
            dev.ctrl_transfer(0xA1, 0x01, 0x0302, INTERFACE, 16, TIMEOUT)
            return True
        except usb.core.USBError:
            return False

    def _read16(self, addr: tuple[int, int], n: int) -> list[int]:
        self._set(REPORT_16B, [LEN_16B, OP_SEEK, *addr, n], 16)
        return self._get(REPORT_16B, 16)

    def _read64(self, addr: tuple[int, int], n: int) -> list[int]:
        self._set(REPORT_64B, [LEN_64B, OP_SEEK, *addr, n], 64)
        return self._get(REPORT_64B, 64)

    def _write16(self, addr: tuple[int, int], n: int, *args: int):
        self._set(REPORT_16B, [LEN_16B, OP_WRITE,
                  *addr, n, 0, 0, 0, *args], 16)

    def _write64(self, addr: tuple[int, int], n: int, *args: int):
        self._set(REPORT_64B, [LEN_64B, OP_WRITE,
                  *addr, n, 0, 0, 0, *args], 64)

    def _unlock(self) -> None:
        self._set(REPORT_16B, [LEN_16B, OP_LOCK, 0], 16)

    def _lock(self) -> None:
        self._set(REPORT_16B, [LEN_16B, OP_LOCK, 1], 16)

    def _set(self, report: int, msg: list[int], length: int):
        pad = [0] * (length - len(msg))
        data = bytearray(msg + pad)
        sent = self.dev.ctrl_transfer(
            SET_REQUEST_TYPE, SET_REPORT, report, INTERFACE, data, TIMEOUT)
        assert sent == length

    def _get(self, report: int, length: int) -> list[int]:
        data = self.dev.ctrl_transfer(
            GET_REQUEST_TYPE, GET_REPORT, report, INTERFACE, length, TIMEOUT)
        return list(data[8:])
