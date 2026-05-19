"""Genera rune casuali in base al livello di difficoltà, con probabilità bassa di speciali."""

from __future__ import annotations
import random
from typing import Optional
from game.rune import Rune, SYMBOLS_BY_DIFFICULTY, COLORS_BY_DIFFICULTY

# Probabilità di generare una runa speciale invece di una normale
_WILDCARD_PROB: float = 0.05
_SKULL_PROB: float = 0.05


class RuneGenerator:
    """Genera rune casuali (normali, wildcard, skull) per il livello di difficoltà dato.

    Distribuzione: 5% wildcard, 5% skull, 90% normale.
    Le rune normali usano i subset di simboli e colori del livello scelto.
    """

    VALID_DIFFICULTIES = frozenset(SYMBOLS_BY_DIFFICULTY.keys())

    def __init__(self, difficulty: str, seed: Optional[int] = None) -> None:
        if difficulty not in self.VALID_DIFFICULTIES:
            raise ValueError(
                f"Difficoltà non valida: {difficulty!r}. "
                f"Valori accettati: {sorted(self.VALID_DIFFICULTIES)}"
            )
        self._symbols = SYMBOLS_BY_DIFFICULTY[difficulty]
        self._colors = COLORS_BY_DIFFICULTY[difficulty]
        self._rng = random.Random(seed)

    def next_rune(self) -> Rune:
        """Genera e restituisce la prossima runa casuale."""
        roll = self._rng.random()
        if roll < _WILDCARD_PROB:
            return Rune.make_wildcard()
        if roll < _WILDCARD_PROB + _SKULL_PROB:
            return Rune.make_skull()
        symbol = self._rng.choice(self._symbols)
        color = self._rng.choice(self._colors)
        return Rune(symbol=symbol, color=color)

    def reseed(self, seed: int) -> None:
        """Reimposta il seme per partite riproducibili o testing."""
        self._rng.seed(seed)
