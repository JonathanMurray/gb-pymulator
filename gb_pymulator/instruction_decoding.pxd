# cython: profile=True
import cython
from gb_pymulator.motherboard cimport Motherboard


cdef dict OPCODE_TABLE
cdef dict EXTENDED_OPCODE_TABLE

cpdef int fetch_decode_execute(Motherboard motherboard)

@cython.locals(opcode=int, opcode_2=int, value=int, address=int, relative_address=int)
cpdef _fetch_and_decode_instruction(Motherboard motherboard)
