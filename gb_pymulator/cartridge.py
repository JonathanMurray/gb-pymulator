from gb_pymulator.cartridge_header import CartridgeType
from gb_pymulator import logger


class Cartridge:
    def __init__(self, data, ram):
        self._cartridge_type = CartridgeType(data[0x147])

        self._data = data
        self._ram_enabled = False
        self._memory_bank_offset = 0
        self._ram = ram
        self._ram_offset = 0

    def read(self, address):
        if address < 0x4000:
            value = self._data[address]
            return value
        elif 0x4000 <= address < 0x8000:
            value = self._data[self._memory_bank_offset + address]
            return value
        elif 0xA000 <= address < 0xC000:
            return self._ram[self._ram_offset + address - 0xA000]
        else:
            raise ValueError(f"TODO: read from cartridge {hex(address)}")

    def write(self, address, value):
        if 0x0000 <= address < 0x2000:
            if value & 0b1111 == 0xA:
                self._ram_enabled = True
            else:
                self._ram_enabled = False
        elif 0x2000 <= address < 0x4000:
            if self._cartridge_type == CartridgeType.ROM_ONLY:
                pass
            elif self._cartridge_type in [CartridgeType.MBC1, CartridgeType.MBC3_BATTERY_BUFFERED_RAM]:
                if value == 0:
                    self._memory_bank_offset = 0
                else:
                    self._memory_bank_offset = (value - 1) * 0x4000
            else:
                raise ValueError(f"TODO Handle write to cartridge type {self._cartridge_type}")
        elif 0x4000 <= address < 0x6000:
            self._ram_offset = value * 0x2000
            logger.info(f"Select RAM bank: {value}")
        elif 0x6000 <= address < 0x8000:
            pass
            logger.warn(f"TODO: RTC registers (clock). Writing {value} to {hex(address)}")
        elif 0xA000 <= address < 0xC000:
            if self._ram:
                self._ram[self._ram_offset + address - 0xA000] = value
        else:
            raise ValueError(f"Write to ROM. rom[{hex(address)}] = {hex(value)}")
