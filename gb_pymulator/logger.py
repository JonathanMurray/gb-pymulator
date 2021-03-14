# cython: profile=True
TRACE = 1
DEBUG = 2
INFO = 3
WARN = 4

LOG_LEVEL = INFO


def warn(msg):
    print(f"[WARN] {msg}")


def info(msg):
    if LOG_LEVEL <= INFO:
        print(f"[INFO] {msg}")


def debug(msg):
    if LOG_LEVEL <= DEBUG:
        print(f"[DEBUG] {msg}")


def trace(msg):
    if LOG_LEVEL <= TRACE:
        print(f"[TRACE] {msg}")
