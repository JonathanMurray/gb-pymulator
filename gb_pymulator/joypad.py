from gb_pymulator import logger


class JoyPad:
    def __init__(self):
        self._selected_keys = 0xFF
        self._button_keys = 0xFF
        self._direction_keys = 0xFF

    def on_press_down(self):
        self._direction_keys &= 0b0111

    def on_press_up(self):
        self._direction_keys &= 0b1011

    def on_press_left(self):
        self._direction_keys &= 0b1101

    def on_press_right(self):
        self._direction_keys &= 0b1110

    def on_press_start(self):
        self._button_keys &= 0b0111

    def on_press_select(self):
        self._button_keys &= 0b1011

    def on_press_b(self):
        self._button_keys &= 0b1101

    def on_press_a(self):
        self._button_keys &= 0b1110

    def on_release_down(self):
        self._direction_keys |= 0b1000

    def on_release_up(self):
        self._direction_keys |= 0b0100

    def on_release_left(self):
        self._direction_keys |= 0b0010

    def on_release_right(self):
        self._direction_keys |= 0b0001

    def on_release_start(self):
        self._button_keys |= 0b1000

    def on_release_select(self):
        self._button_keys |= 0b0100

    def on_release_b(self):
        self._button_keys |= 0b0010

    def on_release_a(self):
        self._button_keys |= 0b0001

    def register_write(self, value: int):
        if value & 0b0010_0000 == 0:
            logger.debug("Preparing to read button keys")
            self._selected_keys = self._button_keys
        elif value & 0b0001_0000 == 0:
            logger.debug("Preparing to read direction keys")
            self._selected_keys = self._direction_keys
        else:
            logger.debug("Won't read any keys")
            self._selected_keys = 0xFF

    def register_read(self) -> int:
        return self._selected_keys
