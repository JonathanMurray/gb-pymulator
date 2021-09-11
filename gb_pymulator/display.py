# cython: profile=True

import pygame
from pygame.surface import Surface

from gb_pymulator.joypad import JoyPad
from gb_pymulator import logger

MARGIN = 10

COLOR_MAPS = \
    [
        # GRAYSCALE
        [
            (255, 255, 255),
            (170, 170, 170),
            (85, 85, 85),
            (0, 0, 0),
        ],
        # RETRO GREEN
        [
            (155, 188, 15),
            (139, 172, 15),
            (48, 98, 48),
            (15, 56, 15),
        ]
    ]


def _tile_offset_8800_method(tile_byte_size, tile_number):
    # The "8800 method" uses $9000 as its base pointer and uses a signed addressing,
    # meaning that tiles 0-127 are in block 2, and tiles -128 to -1 are in block 1,
    # or to put it differently, "8800 addressing" takes tiles 0-127 from block 2
    # and tiles 128-255 from block 1.
    signed_offset = tile_number if tile_number < 128 else tile_number - 256
    tile_offset = 0x9000 + signed_offset * tile_byte_size - 0x8000  # offset within VRAM
    return tile_offset


def _tile_offset_8000_method(tile_byte_size, tile_number):
    # The "8000 method" uses $8000 as its base pointer and uses an unsigned addressing,
    # meaning that tiles 0-127 are in block 0, and tiles 128-255 are in block 1.
    tile_offset = 0x8000 + tile_number * tile_byte_size - 0x8000  # offset within VRAM
    return tile_offset


class Display:
    def __init__(self, joypad: JoyPad):
        # screen_resolution = (160 + MARGIN + 256 + 20, 256)
        screen_resolution = (160, 144)

        # In VRAM there are three "blocks" of 128 tiles each:
        # Block 0 is $8000-87FF
        # Block 1 is $8800-8FFF
        # Block 2 is $9000-97FF
        self.VRAM = [0] * 0x2000  # 8kB video ram

        self.OAM = [0] * 0xA0  # 160B sprite attribute table

        self.LCDC = 0  # LCD control register
        self.STAT = 0  # LCDC status
        self.SCY = 0  # BG scroll y
        self.SCX = 0  # BG scroll x
        self.LY = 0  # LCDC Y-coordinate
        self.LYC = 0  # LY Compare (if equal to LY, it causes STAT to set coincident flag)
        self.BGP = 0  # BG & Window Palette data
        self.OBP0 = 0  # Object (sprite) Palette 0 data
        self.OBP1 = 0  # Object (sprite) Palette 1 data
        self.WY = 0  # Window Y Position ($FF4A)
        self.WX = 0  # Window X Position ($FF4B)
        self.IE = 0  # Interrupt Enable ($FFFF)

        self._screen = pygame.display.set_mode((screen_resolution[0] * 2, screen_resolution[1] * 2))
        self._pixel_buffer = [0] * 160 * 144 * 3
        self._bg_pixel_color_indices = [0] * 160 * 144
        self._tiledata_surface = Surface((256, 256))
        self._joypad = joypad
        self._screen.fill((0, 0, 0))
        logger.debug("Initializing pygame")
        pygame.init()
        pygame.display.update()
        logger.debug("Pygame initialized")
        self._last_draw = pygame.time.get_ticks()
        self._last_draw_debug = pygame.time.get_ticks()

        # Dynamic color maps are features of the emulator and not properties of the gameboy console itself.
        self._color_map_index = 0
        self._colors = COLOR_MAPS[self._color_map_index]

    @staticmethod
    def set_title(title: str):
        pygame.display.set_caption(title)

    def write_reg(self, address: int, value: int):
        if address == 0xFF40:
            self.LCDC = value
        elif address == 0xFF41:
            self.STAT = value
        elif address == 0xFF42:
            self.SCY = value
        elif address == 0xFF43:
            self.SCX = value
        elif address == 0xFF44:
            self.LY = value
        elif address == 0xFF45:
            self.LYC = value
            # TODO can we do interrupts here? Messy to propagate interrupt result back form the write method
        elif address == 0xFF47:
            self.BGP = value
        elif address == 0xFF48:
            self.OBP0 = value
        elif address == 0xFF49:
            self.OBP1 = value
        elif address == 0xFF4A:
            self.WY = value
        elif address == 0xFF4B:
            self.WX = value
        else:
            raise ValueError(f"write {hex(address)}")

    def read_reg(self, address: int):
        if address == 0xFF40:
            return self.LCDC
        elif address == 0xFF41:
            return self.STAT
        elif address == 0xFF42:
            return self.SCY
        elif address == 0xFF43:
            return self.SCX
        elif address == 0xFF44:
            return self.LY
        elif address == 0xFF45:
            return self.LYC
        elif address == 0xFF47:
            return self.BGP
        elif address == 0xFF48:
            return self.OBP0
        elif address == 0xFF49:
            return self.OBP1
        elif address == 0xFF4A:
            return self.WY
        elif address == 0xFF4B:
            return self.WX
        else:
            raise ValueError(f"read {address}")

    def advance_one_scanline(self):

        self.LY = (self.LY + 1) % 154

        interrupt_flag = 0

        if self.LY == self.LYC:
            self.STAT |= 0b0000_0100
            if self.STAT & 0b0100_0000:
                interrupt_flag |= 0b0000_0010  # LCDC STAT interrupt
        else:
            self.STAT &= 0b1111_1011

        if self.LY < 144:
            self._redraw_screen()
            # PPU mode = 0 (H-Blank)
            self.STAT &= 0b1111_1100

            # STAT.3 (Mode 0 STAT Interrupt Enable)
            if self.STAT & 0b0000_1000:
                interrupt_flag |= 0b0000_0010  # LCDC STAT interrupt

        else:
            # PPU mode = 1 (V-Blank)
            self.STAT = self.STAT & 0b1111_1101 | 0b0000_0001

            if self.LY == 144:
                interrupt_flag |= 0b0000_0001  # V-Blank interrupt

                # STAT.4 (Mode 1 STAT Interrupt Enable)
                if self.STAT & 0b0001_0000:
                    interrupt_flag |= 0b0000_0010  # LCDC STAT interrupt

        return interrupt_flag

    def _redraw_screen(self):
        try:
            current_time = pygame.time.get_ticks()

            # Is LCD enabled
            if self.LCDC & 0b1000_0000:
                self._draw_line()
            else:
                return

            # Here we limit FPS to get better performance
            if current_time > self._last_draw + 50:
                self._last_draw = current_time
                main_surface = pygame.image.frombuffer(bytearray(self._pixel_buffer), (160, 144), "RGB")
                main_surface = pygame.transform.scale2x(main_surface)
                self._screen.blit(main_surface, (0, 0))
                pygame.display.update()

        except BaseException as e:
            raise Exception(f"Pygame frame error: {repr(e)}")

    def _draw_line(self):

        if self.LCDC & 0b0000_0100:  # sprite size mode
            raise ValueError("TODO: Support tall sprite mode")

        bg_window_tile_data_select = self.LCDC & 0b0001_0000
        tile_byte_size = 16

        if self.LCDC & 0b0000_0001:  # BG / window enabled

            bg_colors = [
                self._colors[(self.BGP & 0b0000_0011)],
                self._colors[(self.BGP & 0b0000_1100) >> 2],
                self._colors[(self.BGP & 0b0011_0000) >> 4],
                self._colors[(self.BGP & 0b1100_0000) >> 6],
            ]

            if self.LCDC & 0b0000_1000:
                bg_tilemap_address = 0x9C00 - 0x8000  # offset within VRAM
            else:
                bg_tilemap_address = 0x9800 - 0x8000  # offset within VRAM

            bg_tile_ver_index = ((self.SCY + self.LY) // 8) % 32
            y_inside_tile = (self.SCY + self.LY) % 8
            for bg_tile_hor_index in range(32):
                bg_tile_index = bg_tile_ver_index * 32 + bg_tile_hor_index
                tile_index = self.VRAM[bg_tilemap_address + bg_tile_index]
                if bg_window_tile_data_select == 0:
                    tile_offset = _tile_offset_8800_method(tile_byte_size, tile_index)
                else:
                    tile_offset = _tile_offset_8000_method(tile_byte_size, tile_index)

                offset_x = bg_tile_hor_index * 8 - self.SCX

                # Background tile wraps around
                if offset_x < -8:
                    offset_x += 256

                if offset_x < 160:
                    self._draw_tile_line(bg_colors, offset_x, y_inside_tile, tile_offset, False, False, False)

            if self.LCDC & 0b0010_0000:  # Window enabled

                if self.LCDC & 0b0100_0000:
                    window_tilemap_address = 0x9C00 - 0x8000  # offset within VRAM
                else:
                    window_tilemap_address = 0x9800 - 0x8000  # offset within VRAM

                window_tile_ver_index = ((self.LY - self.WY) // 8)
                y_inside_tile = (self.LY - self.WY) % 8
                if 0 <= window_tile_ver_index < 32:
                    for window_tile_hor_index in range(32):
                        window_tile_index = window_tile_ver_index * 32 + window_tile_hor_index
                        tile_index = self.VRAM[window_tilemap_address + window_tile_index]
                        if bg_window_tile_data_select == 0:
                            tile_offset = _tile_offset_8800_method(tile_byte_size, tile_index)
                        else:
                            tile_offset = _tile_offset_8000_method(tile_byte_size, tile_index)

                        offset_x = window_tile_hor_index * 8 + self.WX - 7

                        if -8 <= offset_x <= 160:
                            self._draw_tile_line(bg_colors, offset_x, y_inside_tile, tile_offset, False, False, False)

        if self.LCDC & 0b0000_0010:  # Sprites enabled

            sprite_colors_0 = [
                self._colors[(self.OBP0 & 0b0000_0011)],
                self._colors[(self.OBP0 & 0b0000_1100) >> 2],
                self._colors[(self.OBP0 & 0b0011_0000) >> 4],
                self._colors[(self.OBP0 & 0b1100_0000) >> 6],
            ]

            sprite_colors_1 = [
                self._colors[(self.OBP1 & 0b0000_0011)],
                self._colors[(self.OBP1 & 0b0000_1100) >> 2],
                self._colors[(self.OBP1 & 0b0011_0000) >> 4],
                self._colors[(self.OBP1 & 0b1100_0000) >> 6],
            ]

            sprites_drawn = 0

            for spr_index in range(40):

                if sprites_drawn == 10:
                    break

                spr_offset = spr_index * 4
                spr_screen_y = self.OAM[spr_offset] - 16

                # Check if the sprite has any pixels on the line we're drawing at the moment
                # (Support for tall sprites should be added here)
                if self.LY - 7 <= spr_screen_y <= self.LY:
                    spr_screen_x = self.OAM[spr_offset + 1] - 8

                    if -8 < spr_screen_x < 160:

                        sprites_drawn += 1

                        tile_index = self.OAM[spr_offset + 2]
                        sprite_flags = self.OAM[spr_offset + 3]

                        sprite_covered_by_bg = bool(sprite_flags & 0b1000_0000)
                        x_flip = bool(sprite_flags & 0b0010_0000)
                        colors = sprite_colors_1 if sprite_flags & 0b0001_0000 else sprite_colors_0

                        tile_offset = _tile_offset_8000_method(tile_byte_size, tile_index)

                        y_inside_tile = self.LY - spr_screen_y
                        if sprite_flags & 0b0100_0000:  # Y-flip
                            y_inside_tile = 7 - y_inside_tile

                        self._draw_tile_line(colors, spr_screen_x, y_inside_tile, tile_offset, True,
                                             x_flip, sprite_covered_by_bg)

    def _draw_tile_line(self, colors, offset_x, y_inside_tile, tile_offset, sprite: bool, x_flip: bool,
                        sprite_covered_by_bg: bool):

        byte_offset = tile_offset + y_inside_tile * 2
        line_lsb = self.VRAM[byte_offset]
        line_msb = self.VRAM[byte_offset + 1]
        for x in range(8):
            lsb = (line_lsb & (1 << (7 - x))) >> (7 - x)
            msb = (line_msb & (1 << (7 - x))) >> (7 - x)
            color_index = (msb << 1) + lsb
            if sprite and color_index == 0:
                # transparent pixel
                continue

            if x_flip:
                screen_pixel_x = offset_x + 7 - x
            else:
                screen_pixel_x = offset_x + x

            if 0 <= screen_pixel_x < 160:
                pixel_index = self.LY * 160 + screen_pixel_x
                buffer_offset = pixel_index * 3
                if not sprite:
                    self._bg_pixel_color_indices[pixel_index] = color_index
                elif sprite_covered_by_bg:
                    if self._bg_pixel_color_indices[pixel_index] != 0:
                        continue
                color = colors[color_index]
                self._pixel_buffer[buffer_offset] = color[0]
                self._pixel_buffer[buffer_offset + 1] = color[1]
                self._pixel_buffer[buffer_offset + 2] = color[2]

    def handle_user_input(self) -> int:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return -1
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return -1
                elif event.key == pygame.K_DOWN:
                    self._joypad.on_press_down()
                    return 1
                elif event.key == pygame.K_UP:
                    self._joypad.on_press_up()
                    return 1
                elif event.key == pygame.K_LEFT:
                    self._joypad.on_press_left()
                    return 1
                elif event.key == pygame.K_RIGHT:
                    self._joypad.on_press_right()
                    return 1
                elif event.key == pygame.K_RETURN:
                    self._joypad.on_press_start()
                    return 1
                elif event.key == pygame.K_BACKSPACE:
                    self._joypad.on_press_select()
                    return 1
                elif event.key == pygame.K_z:
                    self._joypad.on_press_a()
                    return 1
                elif event.key == pygame.K_x:
                    self._joypad.on_press_b()
                    return 1
                elif event.key == pygame.K_c:
                    self._color_map_index = (self._color_map_index + 1) % len(COLOR_MAPS)
                    self._colors = COLOR_MAPS[self._color_map_index]
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    self._joypad.on_release_down()
                    return 1
                elif event.key == pygame.K_UP:
                    self._joypad.on_release_up()
                    return 1
                elif event.key == pygame.K_LEFT:
                    self._joypad.on_release_left()
                    return 1
                elif event.key == pygame.K_RIGHT:
                    self._joypad.on_release_right()
                    return 1
                elif event.key == pygame.K_RETURN:
                    self._joypad.on_release_start()
                    return 1
                elif event.key == pygame.K_BACKSPACE:
                    self._joypad.on_release_select()
                    return 1
                elif event.key == pygame.K_z:
                    self._joypad.on_release_a()
                    return 1
                elif event.key == pygame.K_x:
                    self._joypad.on_release_b()
                    return 1
        return 0


class QuitException(BaseException):
    pass
