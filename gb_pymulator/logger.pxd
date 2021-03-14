# cython: profile=True
import cython

cdef int TRACE
cdef int DEBUG
cdef int INFO
cdef int WARN
cdef int LOG_LEVEL

cpdef warn(str msg)
cpdef info(str msg)
cpdef debug(str msg)
cpdef trace(str msg)

