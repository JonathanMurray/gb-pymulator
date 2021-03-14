# cython: profile=True

BITMASKS = [
    0b0000_0010_0000_0000,  # TAC 0: bit 9
    0b0000_0000_0000_1000,  # TAC 1: bit 3
    0b0000_0000_0010_0000,  # TAC 2: bit 5
    0b0000_0000_1000_0000,  # TAC 4: bit 7
]


class Timer:
    def __init__(self):

        self.div = 0  # 16-bit hardware register. Upper 8 bits are mapped to memory 0xFF04
        self.tima = 0
        self.tma = 0
        self.tac = 0

        self._previous_and_result = 0
        self._interrupt_countdown = -1

    def write(self, address, value):
        if address == 0xFF04:
            self.div = 0
        elif address == 0xFF05:
            self.tima = value
        elif address == 0xFF06:
            self.tma = value
        elif address == 0xFF07:
            self.tac = value

    def read(self, address) -> int:
        if address == 0xFF04:
            return self.div
        elif address == 0xFF05:
            return self.tima
        elif address == 0xFF06:
            return self.tma
        elif address == 0xFF07:
            return self.tac

    def update(self, cycle_delta) -> bool:

        # Algorithm described here https://hacktix.github.io/GBEDG/timers/#timer-operation
        bitmask = BITMASKS[self.tac & 0b11]
        timer_enable = bool(self.tac & 0b100)

        should_interrupt = False

        for _ in range(cycle_delta):

            if self._interrupt_countdown != -1:
                if self._interrupt_countdown > 0:
                    self._interrupt_countdown -= 1
                else:
                    # TODO: the interrupt can be aborted by writing anything to TIMA
                    # But that will never happen for us because we don't run the timer in parallel with
                    # instructions (?)

                    self._interrupt_countdown = -1
                    should_interrupt = True

            self.div += 1

            div_bit = bool(self.div & bitmask)
            and_result = div_bit & timer_enable

            # If "falling edge"
            if self._previous_and_result and not and_result:
                self.tima += 1
                if self.tima > 0xFF:
                    self.tima = 0
                    self._interrupt_countdown = 4
            self._previous_and_result = and_result

        return should_interrupt
