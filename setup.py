from distutils.core import setup

from Cython.Build import cythonize

setup(
    ext_modules=cythonize(
        [
            "gb_pymulator/emulator.py",
            "gb_pymulator/motherboard.py",
            "gb_pymulator/timer.py",
            "gb_pymulator/display.py",
            "gb_pymulator/instruction_decoding.py",
            "gb_pymulator/logger.py",
        ],
        language_level="3",
        build_dir="build",
        annotate=True
    )
)
