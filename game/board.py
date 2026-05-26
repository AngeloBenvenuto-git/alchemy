"""Gestisce la griglia 9x9: stato delle celle, piazzamento rune, regole di adiacenza,
completamento righe/colonne e transizione da piombo a oro."""

from __future__ import annotations
from typing import Optional
from game.rune import Rune

GRID_SIZE = 9


class Board:
    """Griglia 9x9 che traccia rune piazzate e celle oro (completate)."""

    def __init__(self) -> None:
        # None = cella vuota (piombo); Rune = cella occupata
        self._grid: list[list[Optional[Rune]]] = [
            [None] * GRID_SIZE for _ in range(GRID_SIZE)
        ]
        # True = cella oro permanente (riga/colonna completata e rimossa)
        self._gold: list[list[bool]] = [
            [False] * GRID_SIZE for _ in range(GRID_SIZE)
        ]
        self._rune_count: int = 0

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_rune(self, row: int, col: int) -> Optional[Rune]:
        return self._grid[row][col]

    def is_gold(self, row: int, col: int) -> bool:
        return self._gold[row][col]

    def is_occupied(self, row: int, col: int) -> bool:
        return self._grid[row][col] is not None

    def is_empty(self) -> bool:
        """True se non è ancora stata piazzata nessuna runa."""
        return self._rune_count == 0

    def rune_count(self) -> int:
        """Numero di rune attualmente sulla griglia."""
        return self._rune_count

    def gold_count(self) -> int:
        """Numero di celle permanentemente oro."""
        return sum(
            1
            for r in range(GRID_SIZE)
            for c in range(GRID_SIZE)
            if self._gold[r][c]
        )

    def is_board_complete(self) -> bool:
        """True quando tutti gli 81 quadrati sono oro."""
        return all(
            self._gold[r][c]
            for r in range(GRID_SIZE)
            for c in range(GRID_SIZE)
        )

    def get_neighbors(self, row: int, col: int) -> list[tuple[int, int, Rune]]:
        """Restituisce (r, c, runa) per ogni cella ortogonalmente adiacente occupata."""
        result: list[tuple[int, int, Rune]] = []
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            r, c = row + dr, col + dc
            if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                rune = self._grid[r][c]
                if rune is not None:
                    result.append((r, c, rune))
        return result

    def can_place(self, rune: Rune, row: int, col: int) -> bool:
        """Verifica se la runa può essere piazzata legalmente in (row, col).

        Regole:
        - La cella deve essere vuota e non oro.
        - Se la griglia è vuota, qualsiasi cella va bene (prima mossa).
        - Altrimenti deve esserci almeno un vicino con una runa.
        - Tutti i vicini devono essere compatibili con la runa (colore O simbolo,
          o wildcard da entrambi i lati).
        """
        if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
            return False
        if self._grid[row][col] is not None or self._gold[row][col]:
            return False
        if self.is_empty():
            return True
        neighbors = self.get_neighbors(row, col)
        if not neighbors:
            return False
        return all(rune.is_compatible_with(nb_rune) for _, _, nb_rune in neighbors)

    def get_valid_placements(self, rune: Rune) -> list[tuple[int, int]]:
        """Restituisce tutte le posizioni (row, col) valide per questa runa."""
        return [
            (r, c)
            for r in range(GRID_SIZE)
            for c in range(GRID_SIZE)
            if self.can_place(rune, r, c)
        ]

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def place_rune(self, rune: Rune, row: int, col: int) -> list[tuple[int, int]]:
        """Piazza la runa in (row, col) e gestisce i completamenti.

        Restituisce la lista di [(axis, index)] completati:
          axis=0 → riga completata, axis=1 → colonna completata.
        Lancia ValueError se il piazzamento non è valido.
        """
        if not self.can_place(rune, row, col):
            raise ValueError(f"Piazzamento non valido in ({row}, {col})")
        self._grid[row][col] = rune
        self._rune_count += 1
        return self._resolve_completions(row, col)

    def remove_rune(self, row: int, col: int) -> Optional[Rune]:
        """Rimuove e restituisce la runa in (row, col) — azione skull.

        Restituisce None se la cella era già vuota.
        """
        rune = self._grid[row][col]
        if rune is not None:
            self._grid[row][col] = None
            self._rune_count -= 1
        return rune

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _resolve_completions(self, row: int, col: int) -> list[tuple[int, int]]:
        """Controlla riga e colonna dell'ultima mossa; se complete, le azzera e le dora.

        Usa una work-queue BFS per rilevare completamenti indiretti: quando una colonna
        viene completata e le sue rune rimosse, una riga che aveva già 8 rune + quella
        cella ora oro può diventare anch'essa completa senza che vi sia stata piazzata
        una runa nuova. La condizione di completamento include sia rune (grid != None)
        che celle già oro (gold == True).
        """
        def is_line_complete(axis: int, idx: int) -> bool:
            if axis == 0:
                return all(self._grid[idx][c] is not None or self._gold[idx][c]
                           for c in range(GRID_SIZE))
            return all(self._grid[r][idx] is not None or self._gold[r][idx]
                       for r in range(GRID_SIZE))

        completed: list[tuple[int, int]] = []
        done: set[tuple[int, int]] = set()
        queue: list[tuple[int, int]] = []

        if is_line_complete(0, row):
            queue.append((0, row))
        if is_line_complete(1, col):
            queue.append((1, col))

        while queue:
            item = queue.pop(0)
            if item in done:
                continue
            done.add(item)
            completed.append(item)
            axis, idx = item

            line_cells = (
                [(idx, c) for c in range(GRID_SIZE)] if axis == 0
                else [(r, idx) for r in range(GRID_SIZE)]
            )
            perp_axis = 1 - axis
            for r, c in line_cells:
                if self._grid[r][c] is not None:
                    self._grid[r][c] = None
                    self._rune_count -= 1
                self._gold[r][c] = True
                perp_idx = c if axis == 0 else r
                candidate = (perp_axis, perp_idx)
                if candidate not in done and is_line_complete(perp_axis, perp_idx):
                    queue.append(candidate)

        return completed

    def __repr__(self) -> str:
        lines = []
        for r in range(GRID_SIZE):
            row_str = ""
            for c in range(GRID_SIZE):
                if self._gold[r][c]:
                    row_str += "G "
                elif self._grid[r][c] is not None:
                    row_str += "R "
                else:
                    row_str += ". "
            lines.append(row_str.rstrip())
        return "\n".join(lines)
