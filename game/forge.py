"""Gestisce i livelli della forge (0–3): incremento allo scarto, decremento al piazzamento,
svuotamento al completamento riga/colonna, e rilevamento del game over."""

from __future__ import annotations


class Forge:
    """Tiene traccia del livello della forge e rileva il game over.

    Livelli: 0 (vuota) → 3 (piena).
    Scartare quando il livello è già 3 causa il game over.
    """

    MAX_LEVEL: int = 3

    def __init__(self) -> None:
        self._level: int = 0
        self._game_over: bool = False

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def level(self) -> int:
        return self._level

    @property
    def is_game_over(self) -> bool:
        return self._game_over

    def can_discard(self) -> bool:
        """True se è ancora possibile scartare senza causare il game over."""
        return not self._game_over and self._level < self.MAX_LEVEL

    # ------------------------------------------------------------------
    # Mutazioni — il game loop chiama il metodo appropriato dopo ogni evento
    # ------------------------------------------------------------------

    def on_discard(self) -> None:
        """Runa scartata: +1 livello, oppure game over se la forge era già piena."""
        if self._game_over:
            return
        if self._level >= self.MAX_LEVEL:
            self._game_over = True
        else:
            self._level += 1

    def on_place(self) -> None:
        """Piazzamento valido senza completamenti: -1 livello (minimo 0)."""
        self._level = max(0, self._level - 1)

    def on_row_col_complete(self) -> None:
        """Una o più righe/colonne completate: forge svuotata completamente."""
        self._level = 0

    def on_board_complete(self) -> None:
        """Board completata (tutti i quadrati oro): -1 livello, non svuota del tutto."""
        self._level = max(0, self._level - 1)

    def reset(self) -> None:
        """Reimposta la forge per una nuova partita."""
        self._level = 0
        self._game_over = False

    def __repr__(self) -> str:
        if self._game_over:
            return "Forge(GAME OVER)"
        bars = "█" * self._level + "░" * (self.MAX_LEVEL - self._level)
        return f"Forge([{bars}] {self._level}/{self.MAX_LEVEL})"
