"""Definisce la classe Rune e le costanti per simboli zodiacali e colori per livello di difficoltà."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class RuneType(Enum):
    NORMAL = auto()
    WILDCARD = auto()
    SKULL = auto()


class Symbol(Enum):
    ARIES = "Ariete"
    TAURUS = "Toro"
    GEMINI = "Gemelli"
    CANCER = "Cancro"
    LEO = "Leone"
    VIRGO = "Vergine"
    LIBRA = "Bilancia"
    SCORPIO = "Scorpione"
    SAGITTARIUS = "Sagittario"
    CAPRICORN = "Capricorno"
    AQUARIUS = "Acquario"
    PISCES = "Pesci"


class Color(Enum):
    RED = "Rosso"
    BLUE = "Blu"
    GREEN = "Verde"
    YELLOW = "Giallo"


_ALL_SYMBOLS: list[Symbol] = list(Symbol)
_ALL_COLORS: list[Color] = list(Color)

SYMBOLS_BY_DIFFICULTY: dict[str, list[Symbol]] = {
    "easy":   _ALL_SYMBOLS[:4],
    "medium": _ALL_SYMBOLS[:8],
    "hard":   _ALL_SYMBOLS[:12],
}

COLORS_BY_DIFFICULTY: dict[str, list[Color]] = {
    "easy":   _ALL_COLORS[:2],
    "medium": _ALL_COLORS[:3],
    "hard":   _ALL_COLORS[:4],
}


@dataclass(frozen=True)
class Rune:
    """Immutable rune value: symbol + color + type (normal / wildcard / skull)."""

    symbol: Optional[Symbol]
    color: Optional[Color]
    rune_type: RuneType = RuneType.NORMAL

    @staticmethod
    def make_wildcard() -> Rune:
        return Rune(symbol=None, color=None, rune_type=RuneType.WILDCARD)

    @staticmethod
    def make_skull() -> Rune:
        return Rune(symbol=None, color=None, rune_type=RuneType.SKULL)

    def is_compatible_with(self, other: Rune) -> bool:
        """Returns True if self and other can legally be adjacent on the board.

        Wildcards are compatible with everything.
        Normal runes are compatible when they share color OR symbol.
        """
        if self.rune_type == RuneType.WILDCARD or other.rune_type == RuneType.WILDCARD:
            return True
        return self.symbol == other.symbol or self.color == other.color

    def __repr__(self) -> str:
        if self.rune_type == RuneType.WILDCARD:
            return "Rune(WILDCARD)"
        if self.rune_type == RuneType.SKULL:
            return "Rune(SKULL)"
        sym = self.symbol.value if self.symbol else "?"
        col = self.color.value if self.color else "?"
        return f"Rune({sym}, {col})"
