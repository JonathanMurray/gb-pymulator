import pygame
from dataclasses import dataclass
from typing import Dict


@dataclass
class UserInputKeyBindings:
    down: int
    up: int
    left: int
    right: int
    start: int
    select: int
    a: int
    b: int


def load_keybindings(config: Dict[str, str]) -> UserInputKeyBindings:
    return UserInputKeyBindings(
        down=load_keybinding(config, "DOWN"),
        up=load_keybinding(config, "UP"),
        left=load_keybinding(config, "LEFT"),
        right=load_keybinding(config, "RIGHT"),
        start=load_keybinding(config, "START"),
        select=load_keybinding(config, "SELECT"),
        a=load_keybinding(config, "A"),
        b=load_keybinding(config, "B"),
    )


def load_keybinding(config: Dict[str, str], gb_key: str) -> int:
    if gb_key not in config:
        raise ValueError(f"Missing key binding for GB key: {gb_key}")
    key_str = config[gb_key]
    try:
        return pygame.key.key_code(key_str)
    except ValueError as e:
        raise ValueError(f"Key string not recognized by Pygame: '{key_str}'") from e
