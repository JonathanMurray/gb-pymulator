# cython: profile=True
import os.path

from gb_pymulator import instruction_decoding
from gb_pymulator import logger
from gb_pymulator.cartridge import Cartridge
from gb_pymulator.cartridge_header import CartridgeHeader, CartridgeType, RAM_Size
from gb_pymulator.display import Display
from gb_pymulator.joypad import JoyPad
from gb_pymulator.motherboard import Motherboard, Memory
from gb_pymulator.timer import Timer


# DR_MARIO_DEBUG_POINTS = {
#     40: "JumpTableBelow",
#     339: "Unk_0153",
#     422: "VBlankHandler",
#     442: "Unk_01BA",
#     451: "dontTransferSprites",
#     488: "Init",
#     # 496: "clearWRAM1",
#     505: "di_InClearWRAM1",
#     679: "MainLoop",
#     1311: "unk_051F",
#     7744: "ClearOAMBuffer",
#     8393: "PrintTileMap",
#     1076: "Unk_SerialRelated",
#     1109: "GameStatus_Dispatch",
#     1245: "__from__JumpTableBelow_when_hGameStatus=1",
#     8285: "TimerHandler",
#     8355: "Clear9800Map",
#     8370: "Copy",
#     8379: "CopyTiles",
#     8784: "__from__JumpTableBelow_when_hGameStatus=0or11",
#     8988: "PollJoypad",
#     15774: "Tiles",
#     32752: "JumpTo",
#     32755: "JumpToInitMusic",
#     65462: "hDMARoutine",
# }


def run_game_from_file(filename: str):
    with open(filename, "rb") as file:
        cartridge_data = list(file.read())
        logger.info(f"Loaded game ROM ({len(cartridge_data)} bytes)")

    with open("DMG_ROM.bin", "rb") as boot_file:
        boot_rom_buffer = list(boot_file.read())
        logger.info(f"Loaded boot ROM ({len(boot_rom_buffer)} bytes)")

    joypad = JoyPad()
    timer = Timer()
    display = Display(joypad)

    ram_size_enum = RAM_Size(cartridge_data[0x149])
    if ram_size_enum == RAM_Size.NONE:
        ram_size = 0
    elif ram_size_enum == RAM_Size.RAM_32KB:
        ram_size = 32 * 1024
    elif ram_size_enum == RAM_Size.RAM_8KB:
        ram_size = 8 * 1024
    else:
        raise ValueError(f"TODO Handle RAM size: {ram_size_enum}")

    escaped_title = bytes(cartridge_data[0x134:0x134 + 11]).decode("utf-8").replace("\x00", "")
    save_file_name = f"savefiles/__{escaped_title.replace(' ', '_')}__"
    if os.path.exists(save_file_name):
        logger.info(f"Savefile found: {save_file_name}")
        with open(save_file_name, "rb") as save_file:
            ram_data = list(save_file.read())
            logger.debug(f"Loaded RAM data ({len(ram_data)} bytes)")
            if len(ram_data) != ram_size:
                raise ValueError(f"Expected RAM size {ram_size} but savefile has size {len(ram_data)}")
    else:
        ram_data = [0] * ram_size
        logger.info(f"Savefile not found: {save_file_name}. Created new RAM data with size {ram_size}")

    cartridge = Cartridge(cartridge_data, ram_data)
    memory = Memory(cartridge, joypad, timer, display)
    motherboard = Motherboard(memory, 0)

    cartridge_header = _handle_header_and_entrypoint(motherboard)

    display.set_title(cartridge_header.title)

    _run_game(motherboard, display, timer, cartridge, save_file_name)
    logger.info("Exiting emulator")


def _run_game(motherboard, display, timer, cartridge, save_file_name):
    logger.info(f"ENTERING INSTRUCTION LOOP... (address={motherboard.program_counter})")

    i = 0
    cycles_until_next_scanline = 0
    cycle = 0

    try:
        while True:

            cycle_delta = 0
            cycle_delta += _handle_interrupts(motherboard)

            if not motherboard.halted and not motherboard.stopped:

                cycle_delta += instruction_decoding.fetch_decode_execute(motherboard)

                motherboard.handle_ime_flag()

            else:
                # ? This is where we need to involve real-time to determine how many cycles should be emulated
                cycle_delta += 4

            # With cycle, we mean T-cycle, as defined here https://hacktix.github.io/GBEDG/cpu/
            # We don't mean M-cycle (which is 4 T-cycles long).

            timer_interrupt = timer.update(cycle_delta)
            if timer_interrupt:
                motherboard.memory.IF_flag |= 0b0000_0100  # Timer interrupt

            if cycles_until_next_scanline > 0:
                cycles_until_next_scanline -= cycle_delta
            else:
                interrupt_flag = display.advance_one_scanline()
                motherboard.memory.IF_flag |= interrupt_flag  # LCDC-STAT or V-Blank interrupts
                cycles_until_next_scanline += 456

            if i % 300 == 0:
                user_input_return_value = display.handle_user_input()
                if user_input_return_value == 1:
                    motherboard.memory.IF_flag |= 0b0001_0000  # Joypad interrupt
                    motherboard.stopped = False
                elif user_input_return_value == -1:
                    with open(save_file_name, "wb") as savefile:
                        savefile.write(bytes(cartridge._ram))
                    logger.info(f"Saved RAM to file {save_file_name} ({len(cartridge._ram)} bytes)")
                    return

            i += 1
            cycle += cycle_delta

            if i % 1_000_000 == 0:
                logger.info(f"[cycle {int(cycle / 1_000_000)}M]")

    except BaseException as e:
        logger.info(
            f"Quit after {i} iterations (at addr {motherboard.program_counter}): {repr(e)}"
        )
        raise e


def _handle_interrupts(motherboard):
    if motherboard.IME_flag:

        flag = motherboard.memory.IF_flag & motherboard.memory.IE_flag

        # optimization: don't bother to check for flags if none of the last 5 bits are set
        if flag & 0b0001_1111:

            if flag & 0b0000_0001:  # V-Blank
                motherboard.IME_flag = False
                motherboard.push_to_stack(motherboard.program_counter)
                motherboard.program_counter = 0x40
                motherboard.memory.IF_flag &= 0b1111_1110  # Acknowledge interrupt
                motherboard.halted = False
                return 5  # (https://gbdev.io/pandocs/#interrupt-service-routine)
            elif flag & 0b0000_0010:  # LCDC (see STAT)
                motherboard.IME_flag = False
                motherboard.push_to_stack(motherboard.program_counter)
                motherboard.program_counter = 0x48
                motherboard.memory.IF_flag &= 0b1111_1101  # Acknowledge interrupt
                motherboard.halted = False
                return 5  # (https://gbdev.io/pandocs/#interrupt-service-routine)
            elif flag & 0b0000_0100:  # Timer overflow
                motherboard.IME_flag = False
                motherboard.push_to_stack(motherboard.program_counter)
                motherboard.program_counter = 0x50
                motherboard.memory.IF_flag &= 0b1111_1011  # Acknowledge interrupt
                motherboard.halted = False
                return 5  # (https://gbdev.io/pandocs/#interrupt-service-routine)
            elif flag & 0b0000_1000:  # Serial I/O transfer complete
                logger.info("Got a Serial IO interrupt")
                motherboard.IME_flag = False
                motherboard.push_to_stack(motherboard.program_counter)
                motherboard.program_counter = 0x58
                motherboard.memory.IF_flag &= 0b1111_0111  # Acknowledge interrupt
                motherboard.halted = False
                return 5  # (https://gbdev.io/pandocs/#interrupt-service-routine)
            elif flag & 0b0001_0000:  # Transition from high to low on keypad
                logger.info("Got a Joypad interrupt")
                logger.warn("TODO: Implement interrupt: Transition from high to low (joypad)")
                raise ValueError("Implement interrupt high to low (joypad)")
    return 0


def _handle_header_and_entrypoint(motherboard: Motherboard) -> CartridgeHeader:
    motherboard.program_counter = 0x100
    b = b""
    for i in range(0x0100, 0x0150):
        b += bytes([motherboard.memory.read(i)])
    logger.debug("Cartridge bytes to parse:")
    logger.debug(str(b))
    logger.debug("")
    logger.debug(str(motherboard.memory._cartridge))

    header = CartridgeHeader.parse(b)
    logger.debug(str(header))

    if header.cartridge_type in [CartridgeType.ROM_ONLY, CartridgeType.MBC1]:
        # This should be handled correctly
        pass
    else:
        logger.warn(f"We may not handle cartridge correctly: {header.cartridge_type}")

    logger.debug("Will load instruction from " + str(motherboard.program_counter))
    instruction_decoding.fetch_decode_execute(motherboard)
    instruction_decoding.fetch_decode_execute(motherboard)
    return header
