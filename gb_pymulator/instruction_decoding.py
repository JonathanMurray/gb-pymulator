# cython: profile=True

from typing import Optional

from gb_pymulator.instructions import (
    Reg,
    Addr,
    AddrReg,
    HighPageAddrReg,
    Val,
    NOP,
    JP,
    XOR,
    LD,
    LDD,
    DEC,
    JR,
    INC,
    DI,
    LDH,
    CP,
    LDI,
    CALL,
    OR,
    RET,
    EI,
    AND,
    CPL,
    RLC,
    SWAP,
    RST,
    ADD,
    POP,
    PUSH,
    RETI,
    BIT,
    RL,
    RLA,
    ADC,
    RES,
    HighPageAddr,
    SUB,
    HALT,
    SRL,
    RR,
    RRA,
    LD_HL,
    RLCA,
    STOP,
    SLA,
    SET,
    SBC,
    ADD_HL, SCF, CCF, RRCA, RRC, SRA, DAA, Instruction, LD_16bit, ADD_SP,
)

A = Reg("A")
B = Reg("B")
C = Reg("C")
D = Reg("D")
E = Reg("E")
H = Reg("H")
L = Reg("L")
DE = Reg("DE")
HL = Reg("HL")
SP = Reg("SP")
BC = Reg("BC")
ADDR_BC = AddrReg("BC")
ADDR_DE = AddrReg("DE")
ADDR_HL = AddrReg("HL")

OPCODE_TABLE = {
    0x00: NOP(),
    0xE9: JP(None, ADDR_HL),
    0xAF: XOR(A, 4),
    0xA8: XOR(B, 4),
    0xA9: XOR(C, 4),
    0xAA: XOR(D, 4),
    0xAB: XOR(E, 4),
    0xAC: XOR(H, 4),
    0xAD: XOR(L, 4),
    0xAE: XOR(ADDR_HL, 8),
    0xB7: OR(A, 4),
    0xB0: OR(B, 4),
    0xB1: OR(C, 4),
    0xB2: OR(D, 4),
    0xB3: OR(E, 4),
    0xB4: OR(H, 4),
    0xB5: OR(L, 4),
    0xB6: OR(ADDR_HL, 8),
    0xA7: AND(A, 4),
    0xA0: AND(B, 4),
    0xA1: AND(C, 4),
    0xA2: AND(D, 4),
    0xA3: AND(E, 4),
    0xA4: AND(H, 4),
    0xA5: AND(L, 4),
    0xA6: AND(ADDR_HL, 8),
    0x87: ADD(A, A, 4),
    0x80: ADD(A, B, 4),
    0x81: ADD(A, C, 4),
    0x82: ADD(A, D, 4),
    0x83: ADD(A, E, 4),
    0x84: ADD(A, H, 4),
    0x85: ADD(A, L, 4),
    0x86: ADD(A, ADDR_HL, 8),
    0x09: ADD_HL(BC),
    0x19: ADD_HL(DE),
    0x29: ADD_HL(HL),
    0x39: ADD_HL(SP),
    0x7F: LD(A, A, 4),
    0x78: LD(A, B, 4),
    0x79: LD(A, C, 4),
    0x7A: LD(A, D, 4),
    0x7B: LD(A, E, 4),
    0x7C: LD(A, H, 4),
    0x7D: LD(A, L, 4),
    0x0A: LD(A, ADDR_BC, 8),
    0x1A: LD(A, ADDR_DE, 8),
    0x7E: LD(A, ADDR_HL, 8),
    0xF2: LD(A, HighPageAddrReg("C"), 8),
    0x47: LD(B, A, 4),
    0x4F: LD(C, A, 4),
    0x57: LD(D, A, 4),
    0x5F: LD(E, A, 4),
    0x67: LD(H, A, 4),
    0x6F: LD(L, A, 4),
    0x02: LD(ADDR_BC, A, 8),
    0x12: LD(ADDR_DE, A, 8),
    0x77: LD(ADDR_HL, A, 8),
    0x40: LD(B, B, 4),
    0x41: LD(B, C, 4),
    0x42: LD(B, D, 4),
    0x43: LD(B, E, 4),
    0x44: LD(B, H, 4),
    0x45: LD(B, L, 4),
    0x46: LD(B, ADDR_HL, 8),
    0x48: LD(C, B, 4),
    0x49: LD(C, C, 4),
    0x4A: LD(C, D, 4),
    0x4B: LD(C, E, 4),
    0x4C: LD(C, H, 4),
    0x4D: LD(C, L, 4),
    0x4E: LD(C, ADDR_HL, 8),
    0x50: LD(D, B, 4),
    0x51: LD(D, C, 4),
    0x52: LD(D, D, 4),
    0x53: LD(D, E, 4),
    0x54: LD(D, H, 4),
    0x55: LD(D, L, 4),
    0x56: LD(D, ADDR_HL, 8),
    0x60: LD(H, B, 4),
    0x61: LD(H, C, 4),
    0x62: LD(H, D, 4),
    0x63: LD(H, E, 4),
    0x64: LD(H, H, 4),
    0x65: LD(H, L, 4),
    0x66: LD(H, ADDR_HL, 8),
    0x68: LD(L, B, 4),
    0x69: LD(L, C, 4),
    0x6A: LD(L, D, 4),
    0x6B: LD(L, E, 4),
    0x6C: LD(L, H, 4),
    0x6D: LD(L, L, 4),
    0x6E: LD(L, ADDR_HL, 8),
    0x58: LD(E, B, 4),
    0x59: LD(E, C, 4),
    0x5A: LD(E, D, 4),
    0x5B: LD(E, E, 4),
    0x5C: LD(E, H, 4),
    0x5D: LD(E, L, 4),
    0x5E: LD(E, ADDR_HL, 8),
    0x70: LD(ADDR_HL, B, 8),
    0x71: LD(ADDR_HL, C, 8),
    0x72: LD(ADDR_HL, D, 8),
    0x73: LD(ADDR_HL, E, 8),
    0x74: LD(ADDR_HL, H, 8),
    0x75: LD(ADDR_HL, L, 8),
    0xE2: LD(HighPageAddrReg("C"), A, 8),
    0xF9: LD(SP, HL, 8),
    0xF5: PUSH("AF"),
    0xC5: PUSH("BC"),
    0xD5: PUSH("DE"),
    0xE5: PUSH("HL"),
    0xF1: POP("AF"),
    0xC1: POP("BC"),
    0xD1: POP("DE"),
    0xE1: POP("HL"),
    0x32: LDD(ADDR_HL, A),
    0x3A: LDD(A, ADDR_HL),
    0x3D: DEC(A, True, 4),
    0x05: DEC(B, True, 4),
    0x0D: DEC(C, True, 4),
    0x15: DEC(D, True, 4),
    0x1D: DEC(E, True, 4),
    0x25: DEC(H, True, 4),
    0x2D: DEC(L, True, 4),
    0x35: DEC(ADDR_HL, True, 12),
    0x0B: DEC(BC, False, 8),
    0x1B: DEC(DE, False, 8),
    0x2B: DEC(HL, False, 8),
    0x3B: DEC(SP, False, 8),
    0x97: SUB(A, 4),
    0x90: SUB(B, 4),
    0x91: SUB(C, 4),
    0x92: SUB(D, 4),
    0x93: SUB(E, 4),
    0x94: SUB(H, 4),
    0x95: SUB(L, 4),
    0x96: SUB(ADDR_HL, 8),
    0x3C: INC(A, True, 4),
    0x04: INC(B, True, 4),
    0x0C: INC(C, True, 4),
    0x14: INC(D, True, 4),
    0x1C: INC(E, True, 4),
    0x24: INC(H, True, 4),
    0x2C: INC(L, True, 4),
    0x34: INC(ADDR_HL, True, 12),
    0x03: INC(BC, False, 8),
    0x13: INC(DE, False, 8),
    0x23: INC(HL, False, 8),
    0x33: INC(SP, False, 8),
    0xF3: DI(),
    0xFB: EI(),
    0xD9: RETI(),
    0x22: LDI(ADDR_HL, A),
    0x2A: LDI(A, ADDR_HL),
    0xC9: RET(None),
    0xC0: RET("NZ"),
    0xC8: RET("Z"),
    0xD0: RET("NC"),
    0xD8: RET("C"),
    0x2F: CPL(),
    0xC7: RST(0x00),
    0xCF: RST(0x08),
    0xD7: RST(0x10),
    0xDF: RST(0x18),
    0xE7: RST(0x20),
    0xEF: RST(0x28),
    0xF7: RST(0x30),
    0xFF: RST(0x38),
    0x17: RLA(),
    0x8F: ADC(A, 4),
    0x88: ADC(B, 4),
    0x89: ADC(C, 4),
    0x8A: ADC(D, 4),
    0x8B: ADC(E, 4),
    0x8C: ADC(H, 4),
    0x8D: ADC(L, 4),
    0x8E: ADC(ADDR_HL, 8),
    0x1F: RRA(),
    0x07: RLCA(),
    0x76: HALT(),
    0x9F: SBC(A, 4),
    0x98: SBC(B, 4),
    0x99: SBC(C, 4),
    0x9A: SBC(D, 4),
    0x9B: SBC(E, 4),
    0x9C: SBC(H, 4),
    0x9D: SBC(L, 4),
    0x9E: SBC(ADDR_HL, 8),
    0x37: SCF(),
    0x3F: CCF(),
    0x0F: RRCA(),
    0x27: DAA(),
    0xBF: CP("A", A, 4),
    0xB8: CP("A", B, 4),
    0xB9: CP("A", C, 4),
    0xBA: CP("A", D, 4),
    0xBB: CP("A", E, 4),
    0xBC: CP("A", H, 4),
    0xBD: CP("A", L, 4),
    0xBE: CP("A", ADDR_HL, 8),
}

EXTENDED_OPCODE_TABLE = {
    0x00: RLC(B, 8),
    0x01: RLC(C, 8),
    0x02: RLC(D, 8),
    0x03: RLC(E, 8),
    0x04: RLC(H, 8),
    0x05: RLC(L, 8),
    0x06: RLC(ADDR_HL, 16),
    0x07: RLC(A, 8),
    0x08: RRC(B, 8),
    0x09: RRC(C, 8),
    0x0A: RRC(D, 8),
    0x0B: RRC(E, 8),
    0x0C: RRC(H, 8),
    0x0D: RRC(L, 8),
    0x0E: RRC(ADDR_HL, 16),
    0x0F: RRC(A, 8),
    0x10: RL(B, 8),
    0x11: RL(C, 8),
    0x12: RL(D, 8),
    0x13: RL(E, 8),
    0x14: RL(H, 8),
    0x15: RL(L, 8),
    0x16: RL(ADDR_HL, 16),
    0x17: RL(A, 8),
    0x18: RR(B, 8),
    0x19: RR(C, 8),
    0x1A: RR(D, 8),
    0x1B: RR(E, 8),
    0x1C: RR(H, 8),
    0x1D: RR(L, 8),
    0x1E: RR(ADDR_HL, 16),
    0x1F: RR(A, 8),
    0x20: SLA(B, 8),
    0x21: SLA(C, 8),
    0x22: SLA(D, 8),
    0x23: SLA(E, 8),
    0x24: SLA(H, 8),
    0x25: SLA(L, 8),
    0x26: SLA(ADDR_HL, 16),
    0x27: SLA(A, 8),
    0x28: SRA(B, 8),
    0x29: SRA(C, 8),
    0x2A: SRA(D, 8),
    0x2B: SRA(E, 8),
    0x2C: SRA(H, 8),
    0x2D: SRA(L, 8),
    0x2E: SRA(ADDR_HL, 16),
    0x2F: SRA(A, 8),
    0x30: SWAP(B, 8),
    0x31: SWAP(C, 8),
    0x32: SWAP(D, 8),
    0x33: SWAP(E, 8),
    0x34: SWAP(H, 8),
    0x35: SWAP(L, 8),
    0x36: SWAP(ADDR_HL, 16),
    0x37: SWAP(A, 8),
    0x38: SRL(B, 8),
    0x39: SRL(C, 8),
    0x3A: SRL(D, 8),
    0x3B: SRL(E, 8),
    0x3C: SRL(H, 8),
    0x3D: SRL(L, 8),
    0x3E: SRL(ADDR_HL, 16),
    0x3F: SRL(A, 8),
    0x40: BIT(0, B, 8),
    0x41: BIT(0, C, 8),
    0x42: BIT(0, D, 8),
    0x43: BIT(0, E, 8),
    0x44: BIT(0, H, 8),
    0x45: BIT(0, L, 8),
    0x46: BIT(0, ADDR_HL, 12),
    0x47: BIT(0, A, 8),
    0x48: BIT(1, B, 8),
    0x49: BIT(1, C, 8),
    0x4A: BIT(1, D, 8),
    0x4B: BIT(1, E, 8),
    0x4C: BIT(1, H, 8),
    0x4D: BIT(1, L, 8),
    0x4E: BIT(1, ADDR_HL, 12),
    0x4F: BIT(1, A, 8),
    0x50: BIT(2, B, 8),
    0x51: BIT(2, C, 8),
    0x52: BIT(2, D, 8),
    0x53: BIT(2, E, 8),
    0x54: BIT(2, H, 8),
    0x55: BIT(2, L, 8),
    0x56: BIT(2, ADDR_HL, 12),
    0x57: BIT(2, A, 8),
    0x58: BIT(3, B, 8),
    0x59: BIT(3, C, 8),
    0x5A: BIT(3, D, 8),
    0x5B: BIT(3, E, 8),
    0x5C: BIT(3, H, 8),
    0x5D: BIT(3, L, 8),
    0x5E: BIT(3, ADDR_HL, 12),
    0x5F: BIT(3, A, 8),
    0x60: BIT(4, B, 8),
    0x61: BIT(4, C, 8),
    0x62: BIT(4, D, 8),
    0x63: BIT(4, E, 8),
    0x64: BIT(4, H, 8),
    0x65: BIT(4, L, 8),
    0x66: BIT(4, ADDR_HL, 12),
    0x67: BIT(4, A, 8),
    0x68: BIT(5, B, 8),
    0x69: BIT(5, C, 8),
    0x6A: BIT(5, D, 8),
    0x6B: BIT(5, E, 8),
    0x6C: BIT(5, H, 8),
    0x6D: BIT(5, L, 8),
    0x6E: BIT(5, ADDR_HL, 12),
    0x6F: BIT(5, A, 8),
    0x70: BIT(6, B, 8),
    0x71: BIT(6, C, 8),
    0x72: BIT(6, D, 8),
    0x73: BIT(6, E, 8),
    0x74: BIT(6, H, 8),
    0x75: BIT(6, L, 8),
    0x76: BIT(6, ADDR_HL, 12),
    0x77: BIT(6, A, 8),
    0x78: BIT(7, B, 8),
    0x79: BIT(7, C, 8),
    0x7A: BIT(7, D, 8),
    0x7B: BIT(7, E, 8),
    0x7C: BIT(7, H, 8),
    0x7D: BIT(7, L, 8),
    0x7E: BIT(7, ADDR_HL, 12),
    0x7F: BIT(7, A, 8),
    0x80: RES(0, B, 8),
    0x81: RES(0, C, 8),
    0x82: RES(0, D, 8),
    0x83: RES(0, E, 8),
    0x84: RES(0, H, 8),
    0x85: RES(0, L, 8),
    0x86: RES(0, ADDR_HL, 16),
    0x87: RES(0, A, 8),
    0x88: RES(1, B, 8),
    0x89: RES(1, C, 8),
    0x8A: RES(1, D, 8),
    0x8B: RES(1, E, 8),
    0x8C: RES(1, H, 8),
    0x8D: RES(1, L, 8),
    0x8E: RES(1, ADDR_HL, 16),
    0x8F: RES(1, A, 8),
    0x90: RES(2, B, 8),
    0x91: RES(2, C, 8),
    0x92: RES(2, D, 8),
    0x93: RES(2, E, 8),
    0x94: RES(2, H, 8),
    0x95: RES(2, L, 8),
    0x96: RES(2, ADDR_HL, 16),
    0x97: RES(2, A, 8),
    0x98: RES(3, B, 8),
    0x99: RES(3, C, 8),
    0x9A: RES(3, D, 8),
    0x9B: RES(3, E, 8),
    0x9C: RES(3, H, 8),
    0x9D: RES(3, L, 8),
    0x9E: RES(3, ADDR_HL, 16),
    0x9F: RES(3, A, 8),
    0xA0: RES(4, B, 8),
    0xA1: RES(4, C, 8),
    0xA2: RES(4, D, 8),
    0xA3: RES(4, E, 8),
    0xA4: RES(4, H, 8),
    0xA5: RES(4, L, 8),
    0xA6: RES(4, ADDR_HL, 16),
    0xA7: RES(4, A, 8),
    0xA8: RES(5, B, 8),
    0xA9: RES(5, C, 8),
    0xAA: RES(5, D, 8),
    0xAB: RES(5, E, 8),
    0xAC: RES(5, H, 8),
    0xAD: RES(5, L, 8),
    0xAE: RES(5, ADDR_HL, 16),
    0xAF: RES(5, A, 8),
    0xB0: RES(6, B, 8),
    0xB1: RES(6, C, 8),
    0xB2: RES(6, D, 8),
    0xB3: RES(6, E, 8),
    0xB4: RES(6, H, 8),
    0xB5: RES(6, L, 8),
    0xB6: RES(6, ADDR_HL, 16),
    0xB7: RES(6, A, 8),
    0xB8: RES(7, B, 8),
    0xB9: RES(7, C, 8),
    0xBA: RES(7, D, 8),
    0xBB: RES(7, E, 8),
    0xBC: RES(7, H, 8),
    0xBD: RES(7, L, 8),
    0xBE: RES(7, ADDR_HL, 16),
    0xBF: RES(7, A, 8),
    0xC0: SET(0, B, 8),
    0xC1: SET(0, C, 8),
    0xC2: SET(0, D, 8),
    0xC3: SET(0, E, 8),
    0xC4: SET(0, H, 8),
    0xC5: SET(0, L, 8),
    0xC6: SET(0, ADDR_HL, 16),
    0xC7: SET(0, A, 8),
    0xC8: SET(1, B, 8),
    0xC9: SET(1, C, 8),
    0xCA: SET(1, D, 8),
    0xCB: SET(1, E, 8),
    0xCC: SET(1, H, 8),
    0xCD: SET(1, L, 8),
    0xCE: SET(1, ADDR_HL, 16),
    0xCF: SET(1, A, 8),
    0xD0: SET(2, B, 8),
    0xD1: SET(2, C, 8),
    0xD2: SET(2, D, 8),
    0xD3: SET(2, E, 8),
    0xD4: SET(2, H, 8),
    0xD5: SET(2, L, 8),
    0xD6: SET(2, ADDR_HL, 16),
    0xD7: SET(2, A, 8),
    0xD8: SET(3, B, 8),
    0xD9: SET(3, C, 8),
    0xDA: SET(3, D, 8),
    0xDB: SET(3, E, 8),
    0xDC: SET(3, H, 8),
    0xDD: SET(3, L, 8),
    0xDE: SET(3, ADDR_HL, 16),
    0xDF: SET(3, A, 8),
    0xE0: SET(4, B, 8),
    0xE1: SET(4, C, 8),
    0xE2: SET(4, D, 8),
    0xE3: SET(4, E, 8),
    0xE4: SET(4, H, 8),
    0xE5: SET(4, L, 8),
    0xE6: SET(4, ADDR_HL, 16),
    0xE7: SET(4, A, 8),
    0xE8: SET(5, B, 8),
    0xE9: SET(5, C, 8),
    0xEA: SET(5, D, 8),
    0xEB: SET(5, E, 8),
    0xEC: SET(5, H, 8),
    0xED: SET(5, L, 8),
    0xEE: SET(5, ADDR_HL, 16),
    0xEF: SET(5, A, 8),
    0xF0: SET(6, B, 8),
    0xF1: SET(6, C, 8),
    0xF2: SET(6, D, 8),
    0xF3: SET(6, E, 8),
    0xF4: SET(6, H, 8),
    0xF5: SET(6, L, 8),
    0xF6: SET(6, ADDR_HL, 16),
    0xF7: SET(6, A, 8),
    0xF8: SET(7, B, 8),
    0xF9: SET(7, C, 8),
    0xFA: SET(7, D, 8),
    0xFB: SET(7, E, 8),
    0xFC: SET(7, H, 8),
    0xFD: SET(7, L, 8),
    0xFE: SET(7, ADDR_HL, 16),
    0xFF: SET(7, A, 8),
}


def fetch_decode_execute(motherboard) -> int:
    instruction = _fetch_and_decode_instruction(motherboard)
    return instruction.execute(motherboard)


def _fetch_and_decode_instruction(motherboard) -> Optional[Instruction]:
    opcode = motherboard.load_u8()

    if opcode in OPCODE_TABLE:
        return OPCODE_TABLE[opcode]

    # TODO Move the dynamic opcodes below into a table with function references

    # -------------------
    #        JP
    # -------------------

    elif opcode == 0xC3:
        address = motherboard.load_u16()
        return JP(None, Addr(address))

    elif opcode == 0xC2:
        address = motherboard.load_u16()
        return JP("NZ", Addr(address))
    elif opcode == 0xCA:
        address = motherboard.load_u16()
        return JP("Z", Addr(address))
    elif opcode == 0xD2:
        address = motherboard.load_u16()
        return JP("NC", Addr(address))
    elif opcode == 0xDA:
        address = motherboard.load_u16()
        return JP("C", Addr(address))

    # -------------------
    #        OR
    # -------------------

    elif opcode == 0xF6:
        value = motherboard.load_u8()
        return OR(Val(value), 8)

    # -------------------
    #        AND
    # -------------------

    elif opcode == 0xE6:
        value = motherboard.load_u8()
        return AND(Val(value), 8)

    # -------------------
    #        ADD
    # -------------------

    elif opcode == 0xC6:
        value = motherboard.load_u8()
        return ADD(A, Val(value), 8)

    # -------------------
    #        SUB
    # -------------------

    elif opcode == 0xD6:
        value = motherboard.load_u8()
        return SUB(Val(value), 8)

    # -------------------
    #        LD
    # -------------------

    elif opcode == 0x01:
        value = motherboard.load_u16()
        return LD(BC, Val(value), 12)
    elif opcode == 0x11:
        value = motherboard.load_u16()
        return LD(DE, Val(value), 12)
    elif opcode == 0x21:
        value = motherboard.load_u16()
        return LD(HL, Val(value), 12)
    elif opcode == 0x31:
        value = motherboard.load_u16()
        return LD(SP, Val(value), 12)

    elif opcode == 0x06:
        value = motherboard.load_u8()
        return LD(B, Val(value), 8)
    elif opcode == 0x0E:
        value = motherboard.load_u8()
        return LD(C, Val(value), 8)
    elif opcode == 0x16:
        value = motherboard.load_u8()
        return LD(D, Val(value), 8)
    elif opcode == 0x1E:
        value = motherboard.load_u8()
        return LD(E, Val(value), 8)
    elif opcode == 0x26:
        value = motherboard.load_u8()
        return LD(H, Val(value), 8)
    elif opcode == 0x2E:
        value = motherboard.load_u8()
        return LD(L, Val(value), 8)

    elif opcode == 0xFA:
        value = motherboard.load_u16()
        return LD(A, Addr(value), 16)
    elif opcode == 0x3E:
        value = motherboard.load_u8()
        return LD(A, Val(value), 8)

    elif opcode == 0xEA:
        address = motherboard.load_u16()
        return LD(Addr(address), A, 16)

    elif opcode == 0x36:
        value = motherboard.load_u8()
        return LD(ADDR_HL, Val(value), 12)

    elif opcode == 0x08:
        address = motherboard.load_u16()
        return LD_16bit(Addr(address), SP, 20)

    # -------------------
    #        JR
    # -------------------

    elif opcode == 0x18:
        relative_address = motherboard.load_i8()
        return JR(None, relative_address)
    elif opcode == 0x20:
        relative_address = motherboard.load_i8()
        return JR("NZ", relative_address)
    elif opcode == 0x28:
        relative_address = motherboard.load_i8()
        return JR("Z", relative_address)
    elif opcode == 0x30:
        relative_address = motherboard.load_i8()
        return JR("NC", relative_address)
    elif opcode == 0x38:
        relative_address = motherboard.load_i8()
        return JR("C", relative_address)

    # -------------------
    #        LDH
    # -------------------

    elif opcode == 0xE0:
        relative_address = motherboard.load_u8()
        return LDH(HighPageAddr(relative_address), A)
    elif opcode == 0xF0:
        relative_address = motherboard.load_u8()
        return LDH(A, HighPageAddr(relative_address))

    elif opcode == 0xFE:
        value = motherboard.load_u8()
        return CP("A", Val(value), 8)

    # -------------------
    #        CALL
    # -------------------

    elif opcode == 0xCD:
        address = motherboard.load_u16()
        return CALL(None, address)
    elif opcode == 0xC4:
        address = motherboard.load_u16()
        return CALL("NZ", address)
    elif opcode == 0xCC:
        address = motherboard.load_u16()
        return CALL("Z", address)
    elif opcode == 0xD4:
        address = motherboard.load_u16()
        return CALL("NC", address)
    elif opcode == 0xDC:
        address = motherboard.load_u16()
        return CALL("C", address)

    # -------------------
    #        ADC
    # -------------------

    elif opcode == 0xCE:
        value = motherboard.load_u8()
        return ADC(Val(value), 8)

    elif opcode == 0xEE:
        value = motherboard.load_u8()
        return XOR(Val(value), 8)

    elif opcode == 0xF8:
        relative_address = motherboard.load_i8()
        return LD_HL(relative_address)

    elif opcode == 0x10:
        next_byte = motherboard.load_u8()
        if next_byte != 0x00:
            raise ValueError(f"Invalid opcode! {hex(opcode)} {next_byte}. (Expected 0x00 after STOP)")
        return STOP()

    elif opcode == 0xDE:
        value = motherboard.load_u8()
        return SBC(Val(value), 8)

    elif opcode == 0xE8:
        relative_address = motherboard.load_i8()
        return ADD_SP(relative_address)

    # -------------------
    # Extended instruction set
    # -------------------

    elif opcode == 0xCB:

        opcode_2 = motherboard.load_u8()

        if opcode_2 in EXTENDED_OPCODE_TABLE:
            return EXTENDED_OPCODE_TABLE[opcode_2]
        else:
            raise ValueError(f"Unknown opcode: {hex(opcode)} {hex(opcode_2)}")

    else:
        raise ValueError(f"Unknown opcode: {hex(opcode)}")
