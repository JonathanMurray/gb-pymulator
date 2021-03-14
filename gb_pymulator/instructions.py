from dataclasses import dataclass
from typing import Any, Optional

from gb_pymulator import logger
from gb_pymulator.motherboard import Motherboard


@dataclass
class Reg:
    register: str

    def read(self, motherboard: Motherboard) -> int:
        return motherboard.reg.get(self.register)

    def write(self, motherboard: Motherboard, value: int):
        motherboard.reg.set(self.register, value)


@dataclass
class Addr:
    address: int

    def read(self, motherboard: Motherboard) -> int:
        return motherboard.memory.read(self.address)

    def write(self, motherboard: Motherboard, value: int):
        motherboard.memory.write(self.address, value)

    def write_16(self, motherboard: Motherboard, value_16: int):
        motherboard.memory.write(self.address, value_16 & 0xFF)
        motherboard.memory.write(self.address + 1, value_16 >> 8)


@dataclass
class AddrReg:
    register: str

    def read(self, motherboard: Motherboard) -> int:
        address = motherboard.reg.get(self.register)
        return motherboard.memory.read(address)

    def write(self, motherboard: Motherboard, value: int):
        address = motherboard.reg.get(self.register)
        motherboard.memory.write(address, value)


@dataclass
class Val:
    value: int

    def read(self, _motherboard: Motherboard) -> int:
        return self.value


@dataclass
class HighPageAddrReg:
    register: str

    def write(self, motherboard: Motherboard, value: int):
        high_page_address = motherboard.reg.get(self.register)
        motherboard.memory.write(0xFF00 + high_page_address, value)

    def read(self, motherboard: Motherboard) -> int:
        high_page_address = motherboard.reg.get(self.register)
        return motherboard.memory.read(0xFF00 + high_page_address)


@dataclass
class HighPageAddr:
    relative_address: int

    def read(self, motherboard: Motherboard) -> int:
        return motherboard.memory.read(0xFF00 + self.relative_address)

    def write(self, motherboard: Motherboard, value: int):
        motherboard.memory.write(0xFF00 + self.relative_address, value)


class Instruction:
    cycles = 4

    def execute(self, motherboard: Motherboard) -> int:
        raise Exception("Not implemented")


@dataclass
class NOP(Instruction):
    """ Noop """

    def execute(self, motherboard: Motherboard):
        return 4


@dataclass
class HALT(Instruction):
    """ Halt CPU until interrupt occurs """

    def execute(self, motherboard: Motherboard):
        motherboard.halted = True
        logger.debug("HALTING...")
        return 4


@dataclass
class JP(Instruction):
    """ Jump """

    cc: Optional[str]
    destination: Any

    def execute(self, motherboard: Motherboard):
        if self.cc is None or motherboard.reg.get_flag_condition(self.cc):
            if type(self.destination) == Addr:
                motherboard.program_counter = self.destination.address
                return 16
            elif type(self.destination) == AddrReg:
                motherboard.program_counter = motherboard.reg.get(self.destination.register)
                return 4
            else:
                raise ValueError(f"Unhandled jump destination: {self.destination}")
        else:
            return 12


@dataclass
class XOR(Instruction):
    """ XOR """

    target: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        motherboard.reg.set("A", self.target.read(motherboard) ^ motherboard.reg.get("A"))
        if motherboard.reg.get("A") == 0:
            motherboard.reg.set("F", 0b1000 << 4)
        else:
            motherboard.reg.set("F", 0)

        return self.cycles


@dataclass
class LD(Instruction):
    """ Load """

    destination: Any
    source: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        value = self.source.read(motherboard)
        self.destination.write(motherboard, value)
        return self.cycles


@dataclass
class LD_16bit(Instruction):
    """ Load """

    destination: Any
    source: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        value = self.source.read(motherboard)
        self.destination.write_16(motherboard, value)
        return self.cycles


@dataclass
class SLA(Instruction):
    """ Shift n left into carry """

    n: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        shifted = self.n.read(motherboard) << 1
        self.n.write(motherboard, shifted)
        motherboard.reg.set_bit("F", 7, shifted & 0xFF == 0)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, False)
        motherboard.reg.set_bit("F", 4, shifted >= 0xFF)
        return self.cycles


@dataclass
class SRA(Instruction):
    """ Shift n right into carry. Bit 7 is kept the same. """

    n: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        value = self.n.read(motherboard)
        old_bit_7 = value & 0b1000_0000
        old_bit_0 = value & 0b1 == 0b1
        shifted = value >> 1
        shifted += old_bit_7
        self.n.write(motherboard, shifted)
        motherboard.reg.set_bit("F", 7, shifted == 0)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, False)
        motherboard.reg.set_bit("F", 4, old_bit_0)

        return self.cycles


@dataclass
class SET(Instruction):
    """ Set bit """

    bit: int
    target: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        value = self.target.read(motherboard)
        bitmask = 1 << self.bit
        self.target.write(motherboard, value | bitmask)

        return self.cycles


@dataclass
class RES(Instruction):
    """ Reset bit"""

    bit: int
    target: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        value = self.target.read(motherboard)
        bitmask = ~(1 << self.bit)
        self.target.write(motherboard, value & bitmask)

        return self.cycles


@dataclass
class LDD(Instruction):
    """ Load decrement """

    destination: Any
    source: Any

    def execute(self, motherboard: Motherboard):
        value = self.source.read(motherboard)
        if type(self.source) == AddrReg:
            motherboard.reg.decrement(self.source.register)

        self.destination.write(motherboard, value)
        if type(self.destination) == AddrReg:
            motherboard.reg.decrement(self.destination.register)

        return 8


@dataclass
class DEC(Instruction):
    """ Decrement register """

    target: Any
    affect_flags: bool
    cycles: int

    def execute(self, motherboard: Motherboard):
        value = self.target.read(motherboard)
        result = value - 1
        self.target.write(motherboard, result)

        if self.affect_flags:
            motherboard.reg.set_bit("F", 7, result == 0)
            motherboard.reg.set_bit("F", 6, True)
            motherboard.reg.set_bit("F", 5, (value & 0xF) - 1 < 0)

        return self.cycles


@dataclass
class SUB(Instruction):
    """ Subtract from A """

    n: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        other_value = self.n.read(motherboard)
        target = motherboard.reg.get("A")
        result = target - other_value

        motherboard.reg.set("A", result)

        motherboard.reg.set_bit("F", 7, result == 0)
        motherboard.reg.set_bit("F", 6, True)
        motherboard.reg.set_bit("F", 5, (target & 0xF) - (other_value & 0xF) < 0)
        motherboard.reg.set_bit("F", 4, target < other_value)

        return self.cycles


@dataclass
class SBC(Instruction):
    """ Subtract n + Carry flag from A """

    n: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        target = motherboard.reg.get("A")
        value = self.n.read(motherboard)

        result = target - value
        lower_result = (target & 0xF) - (value & 0xF)
        if motherboard.reg.get_flag_condition("C"):
            result -= 1
            lower_result -= 1
        motherboard.reg.set("A", result)

        motherboard.reg.set_bit("F", 7, result & 0xFF == 0)
        motherboard.reg.set_bit("F", 6, True)
        motherboard.reg.set_bit("F", 5, lower_result < 0)
        motherboard.reg.set_bit("F", 4, result < 0)

        return self.cycles


@dataclass
class JR(Instruction):
    """ Jump relative """

    cc: Optional[str]
    relative_address: int

    def execute(self, motherboard: Motherboard):
        if self.cc is None or motherboard.reg.get_flag_condition(self.cc):
            motherboard.program_counter += self.relative_address
            return 12
        else:
            return 8


@dataclass
class INC(Instruction):
    """ Increment register or memory """

    target: Any
    affect_flags: bool
    cycles: int

    def execute(self, motherboard: Motherboard):
        target = self.target.read(motherboard)
        incremented = target + 1
        self.target.write(motherboard, incremented)

        if self.affect_flags:
            motherboard.reg.set_bit("F", 7, incremented & 0xFF == 0)
            motherboard.reg.set_bit("F", 6, False)
            motherboard.reg.set_bit("F", 5, (target & 0xF) + 1 > 0xF)
        return self.cycles


@dataclass
class LDH(Instruction):
    """ Load from/to page at the end of the memory """

    destination: Any
    source: Any

    def execute(self, motherboard: Motherboard):
        value = self.source.read(motherboard)
        self.destination.write(motherboard, value)
        return 12


@dataclass
class DI(Instruction):
    """ Disable interrupt """

    def execute(self, motherboard: Motherboard):
        motherboard.disable_interrupts_after_next_instruction()
        logger.debug("Disabling interrupts (after next instruction)")
        return 4


@dataclass
class EI(Instruction):
    """ Enable interrupts """

    def execute(self, motherboard: Motherboard):
        motherboard.enable_interrupts_after_next_instruction()
        logger.debug("Enabling interrupts (after next instruction)")
        return 4


@dataclass
class CP(Instruction):
    """ Compare register with other value """

    register: str
    other: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        target = motherboard.reg.get(self.register)
        other_value = self.other.read(motherboard)

        motherboard.reg.set_bit("F", 7, target == other_value)
        motherboard.reg.set_bit("F", 6, True)
        motherboard.reg.set_bit("F", 5, (target & 0xF) - (other_value & 0xF) < 0)
        motherboard.reg.set_bit("F", 4, target < other_value)

        return self.cycles


@dataclass
class LDI(Instruction):
    """ Load and increment """

    destination: Any
    source: Any

    def execute(self, motherboard: Motherboard):
        value = self.source.read(motherboard)
        if type(self.source) == AddrReg:
            motherboard.reg.increment(self.source.register)

        self.destination.write(motherboard, value)

        if type(self.destination) == AddrReg:
            motherboard.reg.increment(self.destination.register)

        return 8


@dataclass
class CALL(Instruction):
    """ Call subroutine"""

    cc: Optional[str]
    address: int

    def execute(self, motherboard: Motherboard):
        if self.cc is None or motherboard.reg.get_flag_condition(self.cc):
            motherboard.push_to_stack(motherboard.program_counter)
            motherboard.program_counter = self.address
            return 24
        return 12


@dataclass
class OR(Instruction):
    """ OR """

    other: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        motherboard.reg.set("A", motherboard.reg.get("A") | self.other.read(motherboard))

        motherboard.reg.set_bit("F", 7, motherboard.reg.get("A") == 0)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, False)
        motherboard.reg.set_bit("F", 4, False)
        return self.cycles


@dataclass
class AND(Instruction):
    """ AND """

    other: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        motherboard.reg.set("A", motherboard.reg.get("A") & self.other.read(motherboard))

        motherboard.reg.set_bit("F", 7, motherboard.reg.get("A") == 0)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, True)
        motherboard.reg.set_bit("F", 4, False)
        return self.cycles


@dataclass
class RET(Instruction):
    """ Return from subroutine """

    cc: Optional[str]

    def execute(self, motherboard: Motherboard):

        if self.cc is not None:
            if motherboard.reg.get_flag_condition(self.cc):
                return_address = motherboard.pop_from_stack()
                motherboard.program_counter = return_address
                return 20
            else:
                return 8
        else:
            return_address = motherboard.pop_from_stack()
            motherboard.program_counter = return_address
            return 16


@dataclass
class RETI(Instruction):
    """ Return from interrupt """

    def execute(self, motherboard: Motherboard):
        return_address = motherboard.pop_from_stack()
        motherboard.program_counter = return_address
        motherboard.IME_flag = True
        return 16


@dataclass
class POP(Instruction):
    """ Pop from stack """

    register_pair: str

    def execute(self, motherboard: Motherboard):
        popped = motherboard.pop_from_stack()
        if popped >= 256 ** 2:
            raise ValueError(f"Popped {popped} from stack. [{self}]")
        motherboard.reg.set(self.register_pair, popped)

        return 12


@dataclass
class PUSH(Instruction):
    """ Push to stack """

    register_pair: str

    def execute(self, motherboard: Motherboard):
        value = motherboard.reg.get(self.register_pair)
        if value >= 256 ** 2:
            raise ValueError(f"Tried to push {value} from {self.register_pair}")
        motherboard.push_to_stack(value)
        return 16


@dataclass
class CPL(Instruction):
    """ Complement A register (flip bits)"""

    def execute(self, motherboard: Motherboard):
        motherboard.reg.set("A", ~motherboard.reg.get("A"))

        motherboard.reg.set_bit("F", 6, True)
        motherboard.reg.set_bit("F", 5, True)

        return 4


@dataclass
class RLC(Instruction):
    """ Rotate n left. Old bit 7 to carry flag """

    operand: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        value = self.operand.read(motherboard)
        rotated = value << 1
        old_bit_7 = rotated > 0xFF
        if old_bit_7:
            rotated += 1
        self.operand.write(motherboard, rotated)

        motherboard.reg.set_bit("F", 7, rotated & 0xFF == 0)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, False)
        motherboard.reg.set_bit("F", 4, old_bit_7)

        return self.cycles


@dataclass
class RRC(Instruction):
    """ Rotate n right. Old bit 0 to Carry Flag """

    operand: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        value = self.operand.read(motherboard)
        rotated = value >> 1
        old_bit_0 = value & 0b1 == 0b1
        if old_bit_0:
            rotated += 0b1000_0000
        self.operand.write(motherboard, rotated)

        motherboard.reg.set_bit("F", 7, rotated == 0)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, False)
        motherboard.reg.set_bit("F", 4, old_bit_0)

        return self.cycles


@dataclass
class RL(Instruction):
    """ Rotate n left through carry """

    operand: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        value = self.operand.read(motherboard)

        rotated = value << 1
        if motherboard.reg.get_flag_condition("C"):
            rotated += 1

        self.operand.write(motherboard, rotated)

        motherboard.reg.set_bit("F", 7, rotated & 0xFF == 0)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, False)
        motherboard.reg.set_bit("F", 4, rotated > 0xFF)
        return self.cycles


@dataclass
class RLA(Instruction):
    """ Rotate A left through carry """

    def execute(self, motherboard: Motherboard):
        rotated = motherboard.reg.get("A") << 1
        if motherboard.reg.get_flag_condition("C"):
            rotated = rotated + 1

        motherboard.reg.set("A", rotated)

        motherboard.reg.set_bit("F", 7, False)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, False)
        motherboard.reg.set_bit("F", 4, rotated > 0xFF)
        return 4


@dataclass
class ADC(Instruction):
    """ Add n + carry flag into A """

    n: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        value = self.n.read(motherboard)
        target = motherboard.reg.get("A")
        carry_flag = motherboard.reg.get_flag_condition("C")
        result = target + value
        lower_result = ((target & 0xF) + (value & 0xF))
        if carry_flag:
            result += 1
            lower_result += 1

        motherboard.reg.set("A", result)

        motherboard.reg.set_bit("F", 7, result & 0xFF == 0)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, lower_result > 0xF)
        motherboard.reg.set_bit("F", 4, result > 0xFF)

        return self.cycles


@dataclass
class SWAP(Instruction):
    """ Swap upper & lower nibbles """

    operand: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        value = self.operand.read(motherboard)

        swapped = ((value & 0b0000_1111) << 4) | ((value & 0b1111_0000) >> 4)

        self.operand.write(motherboard, swapped)

        motherboard.reg.set_bit("F", 7, swapped == 0)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, False)
        motherboard.reg.set_bit("F", 4, False)

        return self.cycles


@dataclass
class RST(Instruction):
    """ Restart """

    address: int

    def execute(self, motherboard: Motherboard):
        motherboard.push_to_stack(motherboard.program_counter)
        motherboard.program_counter = self.address
        return 16


@dataclass
class ADD(Instruction):
    """ Add n to destination"""

    destination: Any
    n: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        target = self.destination.read(motherboard)
        value = self.n.read(motherboard)
        result = target + value
        self.destination.write(motherboard, result)

        motherboard.reg.set_bit("F", 7, result & 0xFF == 0)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, ((target & 0xF) + (value & 0xF)) >= 16)
        motherboard.reg.set_bit("F", 4, result > 0xFF)

        return self.cycles


@dataclass
class ADD_HL(Instruction):
    """ Add n (16b) to HL """

    n: Any

    def execute(self, motherboard: Motherboard):
        target = motherboard.reg.get("HL")
        value = self.n.read(motherboard)
        result = target + value
        motherboard.reg.set("HL", result)

        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, (target & 0xFFF) + (value & 0xFFF) > 0xFFF)
        motherboard.reg.set_bit("F", 4, result > 0xFFFF)

        return 8


@dataclass
class ADD_SP(Instruction):
    """ Add n (8b signed) to SP """

    n: int

    def execute(self, motherboard: Motherboard):
        sp = motherboard.reg.stack_pointer
        value = self.n
        result = sp + value
        motherboard.reg.stack_pointer = result

        motherboard.reg.set_bit("F", 7, False)
        motherboard.reg.set_bit("F", 6, False)
        # motherboard.reg.set_bit("F", 5, (sp & 0xFFF) + (value & 0xFFF) > 0xFFF)
        # motherboard.reg.set_bit("F", 4, result > 0xFFFF)

        if self.n >= 0:
            motherboard.reg.set_bit("F", 5, (sp & 0xF) + (self.n & 0xF) > 0xF)
            motherboard.reg.set_bit("F", 4, (sp & 0xFF) + self.n > 0xFF)
        else:
            motherboard.reg.set_bit("F", 5, (result & 0xF) <= (sp & 0xF))
            motherboard.reg.set_bit("F", 4, (result & 0xFF) <= (sp & 0xFF))

        return 16


@dataclass
class BIT(Instruction):
    """ Test bit in register"""

    bit: int
    target: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        is_set = get_bit(self.target.read(motherboard), self.bit)
        motherboard.reg.set_bit("F", 7, not is_set)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, True)

        return self.cycles


@dataclass
class SRL(Instruction):
    """ Shift n right into carry """

    n: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        before = self.n.read(motherboard)
        result = before >> 1
        self.n.write(motherboard, result)

        motherboard.reg.set_bit("F", 7, result == 0)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, False)
        motherboard.reg.set_bit("F", 4, before % 2 == 1)

        return self.cycles


@dataclass
class RR(Instruction):
    """ Rotate n right through carry """

    n: Any
    cycles: int

    def execute(self, motherboard: Motherboard):
        _rotate_right_through_carry(motherboard, self.n)
        return self.cycles


@dataclass
class RRA(Instruction):
    """ Rotate A right through carry """

    def execute(self, motherboard: Motherboard):
        before = motherboard.reg.get("A")
        result = before >> 1
        if motherboard.reg.get_bit("F", 4):
            result += 0b1000_0000
        motherboard.reg.set("A", result)

        motherboard.reg.set_bit("F", 7, False)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, False)
        motherboard.reg.set_bit("F", 4, before & 1)

        return 4


@dataclass
class RLCA(Instruction):
    """ Rotate A left. Old bit 7 to carry flag """

    def execute(self, motherboard: Motherboard):
        result = motherboard.reg.get("A") << 1
        if result > 0xFF:
            result += 1
        motherboard.reg.set("A", result)
        motherboard.reg.set_bit("F", 7, False)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, False)
        motherboard.reg.set_bit("F", 4, result > 0xFF)

        return 4


def _rotate_right_through_carry(motherboard: Motherboard, n: Any):
    before = n.read(motherboard)
    result = before >> 1
    if motherboard.reg.get_bit("F", 4):
        result += 0b1000_0000
    n.write(motherboard, result)
    motherboard.reg.set_bit("F", 7, result == 0)
    motherboard.reg.set_bit("F", 6, False)
    motherboard.reg.set_bit("F", 5, False)
    motherboard.reg.set_bit("F", 4, before % 2 == 1)


@dataclass
class LD_HL(Instruction):
    """ Put SP + n into HL """

    n: int

    def execute(self, motherboard: Motherboard):
        sp = motherboard.reg.stack_pointer
        value = self.n
        result = sp + value
        motherboard.reg.set("HL", result)

        motherboard.reg.set_bit("F", 7, False)
        motherboard.reg.set_bit("F", 6, False)

        if self.n >= 0:
            motherboard.reg.set_bit("F", 5, (sp & 0xF) + (value & 0xF) > 0xF)
            motherboard.reg.set_bit("F", 4, (sp & 0xFF) + self.n > 0xFF)
        else:
            motherboard.reg.set_bit("F", 5, (result & 0xF) <= (sp & 0xF))
            motherboard.reg.set_bit("F", 4, (result & 0xFF) <= (sp & 0xFF))

        return 12


@dataclass
class STOP(Instruction):
    """ Stop CPU and LCD until button is pressed """

    def execute(self, motherboard: Motherboard):
        motherboard.stopped = True
        motherboard.memory.write(0xFF04, 0) # Write to DIV
        # TODO Timer should stop running here (https://gbdev.io/pandocs/#ff04-div-divider-register-r-w)
        logger.info("Stopping CPU and LCD")

        return 4


@dataclass
class SCF(Instruction):
    """ Set Carry flag """

    def execute(self, motherboard: Motherboard):
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, False)
        motherboard.reg.set_bit("F", 4, True)
        return 4


@dataclass
class CCF(Instruction):
    """ Complement Carry flag """

    def execute(self, motherboard: Motherboard):
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, False)
        carry = motherboard.reg.get_bit("F", 4)
        motherboard.reg.set_bit("F", 4, not carry)
        return 4


@dataclass
class RRCA(Instruction):
    """ Rotate A right. Old bit 0 to Carry flag """

    def execute(self, motherboard: Motherboard):
        before = motherboard.reg.get("A")
        rotated = before >> 1
        if before & 1:
            rotated = rotated | 0b1000_0000
        motherboard.reg.set("A", rotated)

        motherboard.reg.set_bit("F", 7, False)
        motherboard.reg.set_bit("F", 6, False)
        motherboard.reg.set_bit("F", 5, False)
        motherboard.reg.set_bit("F", 4, before & 1)
        return 4


@dataclass
class DAA(Instruction):
    """ Decimal adjust register A """

    def execute(self, motherboard: Motherboard):

        # Algorithm copied from https://forums.nesdev.com/viewtopic.php?t=15944

        a = motherboard.reg.get("A")
        n = motherboard.reg.get_flag_condition("N")
        c = motherboard.reg.get_flag_condition("C")
        h = motherboard.reg.get_flag_condition("H")

        if not n:
            # after an addition, adjust if (half-)carry occurred or if result is out of bounds
            if c or a > 0x99:
                a += 0x60
                motherboard.reg.set_bit("F", 4, True)
            if h or (a & 0x0f) > 0x09:
                a += 0x6
        else:
            # after a subtraction, only adjust if (half-)carry occurred
            if c:
                a -= 0x60
            if h:
                a -= 0x6

        motherboard.reg.set("A", a)

        motherboard.reg.set_bit("F", 7, motherboard.reg.get("A") == 0)
        motherboard.reg.set_bit("F", 5, False)
        return 4


def get_bit(value: int, bit: int) -> bool:
    bitmask = 1 << bit
    return bool(value & bitmask)
