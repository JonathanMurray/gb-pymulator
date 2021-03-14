#!/usr/bin/env python3

import pyximport;

pyximport.install()

import sys

from gb_pymulator import emulator

import os.path

GAMES_DIR = "games"
TESTS_DIR = "test_roms"


def main():
    args = sys.argv
    if len(args) < 2:
        filename_arg = f"{GAMES_DIR}/dr_mario.gb"
    elif len(args) == 2:
        filename_arg = args[1]
    else:
        print(f"Usage: {args[0]} [ ROM_FILE_NAME ]")
        return

    if os.path.isfile(filename_arg):
        rom_filename = filename_arg
    elif os.path.isfile(f"{GAMES_DIR}/{filename_arg}"):
        rom_filename = f"{GAMES_DIR}/{filename_arg}"
    elif os.path.isfile(f"{TESTS_DIR}/{filename_arg}"):
        rom_filename = f"{TESTS_DIR}/{filename_arg}"
    else:
        print(f"File not found: '{filename_arg}'")
        return

    print(f"Running emulator on ROM file: {rom_filename}")

    emulator.run_game_from_file(rom_filename)


if __name__ == "__main__":
    main()
