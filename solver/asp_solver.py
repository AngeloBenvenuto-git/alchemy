"""Bridge Python-Clingo: traduce lo stato del gioco in fatti ASP, esegue il solver
e restituisce la mossa ottimale (piazzamento, skull, o scarto)."""

from __future__ import annotations
from pathlib import Path
from typing import Optional
import clingo

from game.board import Board, GRID_SIZE
from game.rune import Rune, RuneType

_LP_DIR = Path(__file__).parent

# Tipo di ritorno del solver
type Move = dict  # {"action": "place"|"use_skull"|"discard", "row"?: int, "col"?: int}


def _board_to_asp(board: Board, current_rune: Rune, forge_level: int) -> str:
    """Genera i fatti ASP dinamici che descrivono lo stato corrente del gioco."""
    lines: list[str] = []

    # Celle occupate e celle oro
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            rune = board.get_rune(r, c)
            if rune is not None:
                if rune.rune_type == RuneType.WILDCARD:
                    lines.append(f"wildcard_cell({r},{c}).")
                else:
                    sym = rune.symbol.name.lower()   # type: ignore[union-attr]
                    col = rune.color.name.lower()    # type: ignore[union-attr]
                    lines.append(f"cell({r},{c},{sym},{col}).")
            if board.is_gold(r, c):
                lines.append(f"gold({r},{c}).")

    # Runa corrente
    match current_rune.rune_type:
        case RuneType.WILDCARD:
            lines.append("current_type(wildcard).")
            lines.append("current_rune(none,none).")
        case RuneType.SKULL:
            lines.append("current_type(skull).")
            lines.append("current_rune(none,none).")
        case _:
            sym = current_rune.symbol.name.lower()   # type: ignore[union-attr]
            col = current_rune.color.name.lower()    # type: ignore[union-attr]
            lines.append("current_type(normal).")
            lines.append(f"current_rune({sym},{col}).")

    lines.append(f"forge_level({forge_level}).")
    return "\n".join(lines)


def _parse_model(model: clingo.Model) -> Optional[Move]:
    """Estrae la mossa dall'answer set ottimale."""
    for atom in model.symbols(shown=True):
        name = atom.name
        args = atom.arguments
        if name == "place" and len(args) == 2:
            return {"action": "place", "row": args[0].number, "col": args[1].number}
        if name == "use_skull" and len(args) == 2:
            return {"action": "use_skull", "row": args[0].number, "col": args[1].number}
        if name == "discard" and len(args) == 0:
            return {"action": "discard"}
    return None


def get_best_move(board: Board, current_rune: Rune, forge_level: int) -> Move:
    """Calcola la mossa ottimale per lo stato corrente del gioco.

    Ritorna uno tra:
      {"action": "place",     "row": R, "col": C}
      {"action": "use_skull", "row": R, "col": C}
      {"action": "discard"}

    Il solver è deterministico: a parità di stato produce sempre la stessa mossa.
    """
    ctl = clingo.Control(["--opt-mode=opt"])
    ctl.load(str(_LP_DIR / "alchemy.lp"))
    ctl.load(str(_LP_DIR / "strategy.lp"))

    facts = _board_to_asp(board, current_rune, forge_level)
    ctl.add("base", [], facts)
    ctl.ground([("base", [])])

    best: Move = {"action": "discard"}
    with ctl.solve(yield_=True) as handle:
        for model in handle:
            # Clingo con --opt-mode=opt produce modelli a costo decrescente;
            # l'ultimo è il globalmente ottimale.
            parsed = _parse_model(model)
            if parsed is not None:
                best = parsed
    return best


def get_valid_placements_asp(board: Board, current_rune: Rune) -> list[tuple[int, int]]:
    """Restituisce tutte le posizioni valide calcolate dall'ASP (utile per debug/test)."""
    ctl = clingo.Control()
    ctl.load(str(_LP_DIR / "alchemy.lp"))

    facts = _board_to_asp(board, current_rune, 0)
    ctl.add("base", [], facts)
    ctl.add("base", [], "#show valid_placement/2.")
    ctl.ground([("base", [])])

    placements: list[tuple[int, int]] = []
    with ctl.solve(yield_=True) as handle:
        for model in handle:
            placements = [
                (a.arguments[0].number, a.arguments[1].number)
                for a in model.symbols(shown=True)
                if a.name == "valid_placement"
            ]
            break
    return sorted(placements)
