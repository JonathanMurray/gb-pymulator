# GB Pymulator

_A gameboy emulator written in Python_

## Installation

This project uses Python3, Pygame for graphics, and Cython for performance optimizations.

Install dependencies with `pip`:

```bash
pip3 install -r requirements.txt
```

Compile the emulator with Cython:
```bash
./compile_cython.sh
```

## Usage

Start a game:
```bash
./run.py games/super_mario.gb
```

![super_mario](screenshots/screenshot_2021_03_14_super_mario.png)

