# from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from io import BytesIO


class CartridgeType(Enum):
    # MBC = memory bank controller
    ROM_ONLY = 0x00
    MBC1 = 0x01
    MBC1_BATTERY_BUFFERED_RAM = 0x03
    MBC3_BATTERY_BUFFERED_RAM = 0x13


@dataclass
class CartridgeHeader:
    entry_point: bytes
    logo: bytes
    title: str
    manufacturer_code: str
    color_gameboy: int
    new_license_code: bytes
    super_gameboy: bool
    cartridge_type: CartridgeType
    rom_size: str
    ram_size: str
    destination_code: str
    old_license_code: int
    version_number: int
    header_checksum: int
    global_checksum: int

    @staticmethod
    def parse(b: bytes):
        file = BytesIO(b)
        entry_point = file.read(4)
        logo = file.read(0x30)
        title = file.read(11).decode("utf-8").replace("\x00", "")
        manufacturer_code = file.read(4).decode("utf-8").replace("\x00", "") or None
        color_gameboy = file.read(1)[0]
        new_license_code = file.read(2)
        new_license_code = new_license_code if new_license_code != b"\x00\x00" else None
        super_gameboy = file.read(1)[0] == 3
        cartridge_type = CartridgeType(file.read(1)[0])
        rom_size = ROM_Size(file.read(1)[0])
        ram_size = RAM_Size(file.read(1)[0])
        destination_code = "Japanese" if file.read(1)[0] == 0 else "Non-Japanese"
        old_license_code = file.read(1)[0]
        version_number = file.read(1)[0]
        header_checksum = file.read(1)[0]
        global_checksum = int.from_bytes(file.read(2), byteorder="big")

        CartridgeHeader._validate_checksum(b, header_checksum)

        return CartridgeHeader(
            entry_point=entry_point,
            logo=logo,
            title=title,
            manufacturer_code=manufacturer_code,
            color_gameboy=color_gameboy,
            new_license_code=new_license_code,
            super_gameboy=super_gameboy,
            cartridge_type=cartridge_type,
            rom_size=rom_size,
            ram_size=ram_size,
            destination_code=destination_code,
            old_license_code=old_license_code,
            version_number=version_number,
            header_checksum=header_checksum,
            global_checksum=global_checksum,
        )

    @staticmethod
    def _validate_checksum(header: bytes, header_checksum: int):
        computed = 0
        for i, byte in enumerate(header[52:-3]):
            computed = computed - byte - 1
        computed %= 256
        if computed != header_checksum:
            raise ValueError(
                f"Invalid header checksum. Value in header: {header_checksum}, computed: {computed}"
            )


class ROM_Size(Enum):
    ROM_32KB = 0x00
    ROM_64KB_4_BANKS = 0x01
    ROM_512KB_32_BANKS = 0x04
    ROM_1MB_64_BANKS = 0x05


class RAM_Size(Enum):
    NONE = 0x00
    RAM_8KB = 0x02
    RAM_32KB = 0x03
    RAM_128KB = 0x04
    RAM_64KB = 0x05
