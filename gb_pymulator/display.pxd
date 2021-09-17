# cython: profile=True
import cython

cdef list COLORS

cdef class Display:

    cdef public int[0x2000] VRAM
    cdef public int[0xA0] OAM

    cdef int LCDC
    cdef int STAT
    cdef int SCY
    cdef int SCX
    cdef int LY
    cdef int LYC
    cdef int BGP
    cdef int OBP0
    cdef int OBP1
    cdef int WY
    cdef int WX
    cdef int IE

    cdef _screen
    cdef int[160 * 144 * 3] _pixel_buffer
    cdef int[160 * 144] _bg_pixel_color_indices
    cdef _tiledata_surface
    cdef _joypad
    cdef int _last_draw
    cdef int _last_draw_debug
    cdef list _colors
    cdef int _color_map_index

    cdef int _key_down
    cdef int _key_up
    cdef int _key_left
    cdef int _key_right
    cdef int _key_start
    cdef int _key_select
    cdef int _key_a
    cdef int _key_b

    cpdef int advance_one_scanline(self)
    cdef int handle_user_input(self)

    @cython.locals(current_time=int)
    cdef _redraw_screen(self)
    # TODO optimize _draw_line with more static local vars
    @cython.locals(bg_window_tile_data_select=int, tile_byte_size=int, bg_colors=list, sprite_colors_0=list, sprite_colors_1=list, bg_tilemap_address=int, bg_tile_hor_index=int, bg_tile_ver_index=int, tile_index=int)
    cdef _draw_line(self)
    @cython.locals(byte_offset=int, line_lsb=int, line_msb=int, lsb=int, msb=int, color_index=int, screen_pixel_x=int, buffer_offset=int, x=int, color=tuple, screen_position=int[2])
    cdef _draw_tile_line(self, list colors, int offset_x, int y_inside_tile, int tile_offset, bint sprite, bint x_flip, bint sprite_covered_by_bg)