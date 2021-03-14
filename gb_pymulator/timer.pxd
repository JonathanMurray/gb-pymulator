# cython: profile=True
import cython

cdef list BITMASKS

cdef class Timer:

    cdef int div
    cdef int tima
    cdef int tma
    cdef int tac
    cdef unsigned int _previous_and_result
    cdef int _interrupt_countdown

    @cython.locals(bitmask=int, timer_enable=bint, should_interrupt=bint, div_bit=bint, and_result=bint)
    cdef bint update(self, int cycle_delta)
    cdef write(self, int address, int value)
    cdef int read(self, int address)