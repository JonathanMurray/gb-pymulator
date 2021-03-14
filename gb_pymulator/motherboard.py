# cython: profile=True

from gb_pymulator.cartridge import Cartridge
from gb_pymulator.display import Display
from gb_pymulator.joypad import JoyPad
from gb_pymulator import logger
from gb_pymulator.timer import Timer


class Memory:

    def __init__(self, cartridge: Cartridge, joypad: JoyPad, timer: Timer, display: Display):

        # This flag tells us which interrupts have been "requested" by the hardware (they are "pending")
        self.IF_flag = 0

        # This flag tells us which interrupts are enabled (typically enabled/disabled by the program code)
        self.IE_flag = 0

        self._internal_ram = [0] * 0x2000
        self._high_internal_ram = [0] * 127

        self._timer = timer
        self._display = display
        self._cartridge = cartridge
        self._joypad = joypad

    def write(self, address, value):

        if address < 0:
            raise ValueError(f"Trying to write negative address {address} (value:{value})")

        if value is None:
            raise ValueError(f"Trying to write None to {hex(address)}")

        if 0x0000 <= address < 0x8000:
            # Cartridge ROM or memory bank
            self._cartridge.write(address, value)
        elif 0x8000 <= address < 0xA000:
            self._display.VRAM[address - 0x8000] = value
        elif 0xA000 <= address < 0xC000:
            # Switchable RAM bank
            self._cartridge.write(address, value)
        elif 0xC000 <= address < 0xE000:
            self._internal_ram[address - 0xC000] = value
        elif 0xFE00 <= address < 0xFEA0:
            self._display.OAM[address - 0xFE00] = value
        elif 0xFEA0 <= address < 0xFF00:
            # Unused area
            pass
        elif address == 0xFF00:
            self._joypad.register_write(value)
            return
        elif 0xFF01 <= address <= 0xFF02:
            # Serial transfer IO registers
            pass
        elif 0xFF04 <= address <= 0xFF07:
            self._timer.write(address, value)
        elif address == 0xFF0F:
            self.IF_flag = value
        elif 0xFF10 <= address <= 0xFF26:
            pass
            # info("Writing to sound register")
        elif 0xFF30 <= address <= 0xFF3F:
            pass
            # info("Writing to Waveform RAM")
        elif 0xFF40 <= address <= 0xFF45:
            self._display.write_reg(address, value)
        elif address == 0xFF46:
            # DMA
            transfer_source_address = value * 0x100
            for i in range(0xA0):
                self._display.OAM[i] = self.read(transfer_source_address + i)
        elif 0xFF47 <= address <= 0xFF4B:
            self._display.write_reg(address, value)
        elif 0xFF4C <= address < 0xFF50:
            # unused memory area
            pass
        elif address == 0xFF50:
            raise Exception("TODO: disable boot rom")
        elif 0xFF51 <= address < 0xFF80:
            # unused memory area
            pass
        elif 0xFF80 <= address < 0xFFFF:
            self._high_internal_ram[address - 0xFF80] = value
        elif address == 0xFFFF:
            self.IE_flag = value
        else:
            raise ValueError(f"Disallowed write ({value}) to {hex(address)}")

    def read(self, address):
        if address < 0x8000:
            # Cartridge ROM or memory bank
            return self._cartridge.read(address)
        elif address < 0xA000:
            return self._display.VRAM[address - 0x8000]
        elif address < 0xC000:
            # Switchable RAM bank
            return self._cartridge.read(address)
        elif address < 0xE000:
            # info("Read from internal RAM")
            return self._internal_ram[address - 0xC000]
        elif address < 0xFE00:
            # Echo of internal RAM. Not supported
            raise ValueError(f"Disallowed read from {hex(address)}")
        elif address < 0xFEA0:
            return self._display.OAM[address - 0xFE00]
        elif address < 0xFF00:
            # Empty unusable area
            raise ValueError(f"Disallowed read from {hex(address)}")
        elif address == 0xFF00:
            return self._joypad.register_read()
        elif 0xFF04 <= address <= 0xFF07:
            return self._timer.read(address)
        elif address == 0xFF0F:
            return self.IF_flag
        elif 0xFF10 <= address <= 0xFF26:
            # info(f"Reading from sound register {hex(address)}")
            return 0
        elif 0xFF40 <= address <= 0xFF4B:
            return self._display.read_reg(address)
        elif 0xFF80 <= address < 0xFFFF:
            return self._high_internal_ram[address - 0xFF80]
        elif address == 0xFFFF:
            return self.IE_flag
        else:
            raise ValueError(f"Disallowed read from {hex(address)}")


class Motherboard:
    def __init__(self, memory: Memory, program_counter: int):
        self.reg = Registers()
        self.IME_flag = True  # Interrupt Master Enable
        self.memory = memory
        self.program_counter = program_counter
        self.halted: bool = False
        self.stopped: bool = False

        self._ei_countdown = None
        self._di_countdown = None

    def enable_interrupts_after_next_instruction(self):
        self._ei_countdown = 2

    def disable_interrupts_after_next_instruction(self):
        self._di_countdown = 2

    def handle_ime_flag(self):
        if self._ei_countdown is not None:
            self._ei_countdown -= 1
            if self._ei_countdown == 0:
                logger.debug("Enabling interrupts")
                self.IME_flag = True
                self._ei_countdown = None
        if self._di_countdown is not None:
            self._di_countdown -= 1
            if self._di_countdown == 0:
                logger.debug("Disabling interrupts")
                self.IME_flag = False
                self._di_countdown = None

    def push_to_stack(self, value):
        self.memory.write(self.reg.stack_pointer - 1, value >> 8)
        self.memory.write(self.reg.stack_pointer - 2, value & 0xFF)
        self.reg.stack_pointer -= 2

    def pop_from_stack(self) -> int:
        value = self.memory.read(self.reg.stack_pointer)
        value += self.memory.read(self.reg.stack_pointer + 1) << 8
        self.reg.stack_pointer += 2
        return value

    def load_u8(self):
        value = self.memory.read(self.program_counter)
        self.program_counter += 1
        return value

    def load_i8(self):
        value = self.memory.read(self.program_counter)
        self.program_counter += 1
        return int.from_bytes(bytes([value]), byteorder="little", signed=True)

    def load_u16(self):
        b = bytes([self.memory.read(self.program_counter),
                   self.memory.read(self.program_counter + 1)])
        self.program_counter += 2
        return int.from_bytes(b, byteorder="little")


class Registers:
    def __init__(self):
        self.stack_pointer = 0xFFFE  # start value from boot rom
        self._registers = {
            "A": 0,
            "B": 0,
            "C": 0,
            "D": 0,
            "E": 0,
            "F": 0,
            "H": 0,
            "L": 0,
        }
        self._register_pairs = ["AF", "BC", "DE", "HL"]

    def set(self, register_name, value):
        if register_name == "SP":
            self.stack_pointer = value
            return
        if register_name in self._register_pairs:
            self.set(register_name[0], value >> 8)
            self.set(register_name[1], value & 0xFF)
            return
        value = value & 0xFF

        if register_name == "F":
            value = value & 0xF0

        self._registers[register_name] = value

    def get(self, register_name):
        if register_name == "SP":
            return self.stack_pointer
        if register_name in self._register_pairs:
            return (self.get(register_name[0]) << 8) + self.get(register_name[1])
        return self._registers[register_name]

    def decrement(self, register_name):
        self.set(register_name, self.get(register_name) - 1)

    def increment(self, register_name):
        self.set(register_name, self.get(register_name) + 1)

    def set_bit(self, register_name, bit, value):
        if value:
            self._registers[register_name] = self._registers[register_name] | (1 << bit)
        else:
            self._registers[register_name] = self._registers[register_name] & ~(1 << bit)

    def get_bit(self, register_name, bit) -> bool:
        return bool(self._registers[register_name] & (1 << bit))

    def get_flag_condition(self, key):

        if len(key) == 2 and key.startswith("N"):
            return not self.get_flag_condition(key[1:])

        # Zero
        # This bit is set when the result of a math operation is zero
        # or two values match when using the CP instruction.
        if key == "Z":
            return self.get_bit("F", 7)

        # Subtract
        # This bit is set if a subtraction was performed in the last math instruction.
        elif key == "N":
            return self.get_bit("F", 6)

        # Half Carry
        # This bit is set if a carry occurred from the lower nibble in the last math operation.
        elif key == "H":
            return self.get_bit("F", 5)

        # Carry
        # This bit is set if a carry occurred from the last math operation or if register A is the smaller value
        # when executing the CP instruction.
        elif key == "C":
            return self.get_bit("F", 4)

        else:
            raise ValueError(f"Unhandled register flag: '{key}'")
