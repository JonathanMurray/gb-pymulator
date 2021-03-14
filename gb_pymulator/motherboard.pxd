# cython: profile=True
import cython
from gb_pymulator.timer cimport Timer
from gb_pymulator.display cimport Display

cdef class Memory:

    cdef public int IF_flag
    cdef public int IE_flag

    cdef int[0x2000] _internal_ram
    cdef int[127] _high_internal_ram
    cdef Timer _timer
    cdef Display _display
    cdef _cartridge
    cdef _joypad

    cpdef write(self, int address, int value)
    cpdef int read(self, int address)

cdef class Registers:

    cdef public int stack_pointer

    cdef dict _registers
    cdef list _register_pairs

    cpdef set(self, str register_name, int value)
    cpdef int get(self, str register_name)
    cpdef decrement(self, str register_name)
    cpdef increment(self, str register_name)
    cpdef set_bit(self, str register_name, int bit, bint value)
    cpdef bint get_bit(self, str register_name, int bit)
    cpdef bint get_flag_condition(self, str key)



cdef class Motherboard:

    cdef public Registers reg
    cdef public int IME_flag
    cdef public Memory memory
    cdef public int program_counter
    cdef public int halted
    cdef public int stopped
    cdef _ei_countdown
    cdef _di_countdown

    cpdef enable_interrupts_after_next_instruction(self)
    cpdef disable_interrupts_after_next_instruction(self)
    cpdef handle_ime_flag(self)
    cpdef push_to_stack(self, int value)
    cpdef int pop_from_stack(self)

    @cython.locals(value=int)
    cdef int load_u8(self)

    @cython.locals(value=int)
    cdef int load_i8(self)

    cdef int load_u16(self)
