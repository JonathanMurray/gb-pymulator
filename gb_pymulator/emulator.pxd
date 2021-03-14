# cython: profile=True
import cython
from gb_pymulator.motherboard cimport Motherboard, Memory
from gb_pymulator.display cimport Display
from gb_pymulator.timer cimport Timer
from gb_pymulator cimport instruction_decoding
from gb_pymulator cimport logger

@cython.locals(i=cython.int, cycle=cython.int, cycles_until_next_scanline=cython.int, cycle_delta=cython.int, timer_interrupt=cython.int)
cdef _run_game(Motherboard motherboard, Display display, Timer timer, object cartridge, str save_file_name)

@cython.locals(flag=cython.int)
cdef int _handle_interrupts(Motherboard motherboard) except -1