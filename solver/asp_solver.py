"""Bridge Python-Clingo: traduce lo stato del gioco in fatti ASP, esegue il solver
e restituisce la mossa ottimale tramite Monte Carlo rollout ibrido Python+ASP.

Algoritmo di get_best_move:
  1. Clingo estrae le top _N_CANDIDATES mosse candidate tramite esclusione iterativa:
     trova la mossa ottimale, la esclude con un vincolo duro, trova la seconda, ecc.
     (L'approccio --opt-mode=optN non funziona perché P0 rende ogni cella unica.)
  2. Per ognuna, Python esegue _N_SIMULATIONS simulazioni casuali complete:
     applica la mossa su una copia della board, poi usa _get_single_best per le
     mosse simulate e RuneGenerator con seed diverso per ogni simulazione.
  3. Il punteggio finale di ogni candidata è:
       score_mc * 0.7 + compatibility_score_normalizzato * 0.3
     dove compatibility_score conta quante delle possibili rune future del livello
     di difficoltà potrebbero essere piazzate in almeno una cella adiacente libera
     alla posizione scelta (dopo il piazzamento).
  4. Ogni simulazione ha un timeout di _SIM_TIMEOUT_S secondi; se scatta, viene
     usato il risultato parziale (celle_oro accumulate fino a quel momento).
  5. Le simulazioni girano in parallelo su _MC_WORKERS thread per candidata.
"""

from __future__ import annotations
import copy
import sys
import time
from concurrent.futures import ThreadPoolExecutor, Future
from pathlib import Path
from typing import Optional
import clingo

from game.board import Board, GRID_SIZE
from game.forge import Forge
from game.generator import RuneGenerator
from game.rune import Rune, RuneType, SYMBOLS_BY_DIFFICULTY, COLORS_BY_DIFFICULTY

_LP_DIR = Path(__file__).parent

# Tipo di ritorno del solver
type Move = dict  # {"action": "place"|"use_skull"|"discard", "row"?: int, "col"?: int}

_N_CANDIDATES         = 3      # mosse candidate estratte per il rollout MC
_LOOKAHEAD_DIFFICULTY = "hard" # difficoltà usata per generare le rune nelle simulazioni
_N_SIMULATIONS        = 15     # simulazioni MC per candidata
_MC_DEPTH             = 15     # turni simulati per ogni rollout (profondità fissa)
_SIM_TIMEOUT_S        = 2.0    # timeout di sicurezza per singola simulazione (secondi)
_MC_WORKERS           = 8      # thread paralleli per le simulazioni


# ============================================================
# Conversione stato → fatti ASP
# ============================================================

def _board_to_asp(board: Board, current_rune: Rune, forge_level: int) -> str:
    """Genera i fatti ASP dinamici che descrivono lo stato corrente del gioco."""
    lines: list[str] = []

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            rune = board.get_rune(r, c)
            if rune is not None:
                if rune.rune_type == RuneType.WILDCARD:
                    lines.append(f"wildcard_cell({r},{c}).")
                else:
                    sym = rune.symbol.name.lower()  # type: ignore[union-attr]
                    col = rune.color.name.lower()   # type: ignore[union-attr]
                    lines.append(f"cell({r},{c},{sym},{col}).")
            if board.is_gold(r, c):
                lines.append(f"gold({r},{c}).")

    match current_rune.rune_type:
        case RuneType.WILDCARD:
            lines.append("current_type(wildcard).")
            lines.append("current_rune(none,none).")
        case RuneType.SKULL:
            lines.append("current_type(skull).")
            lines.append("current_rune(none,none).")
        case _:
            sym = current_rune.symbol.name.lower()  # type: ignore[union-attr]
            col = current_rune.color.name.lower()   # type: ignore[union-attr]
            lines.append("current_type(normal).")
            lines.append(f"current_rune({sym},{col}).")

    lines.append(f"forge_level({forge_level}).")
    return "\n".join(lines)


# ============================================================
# Parsing del modello ASP
# ============================================================

def _parse_model(model: clingo.Model) -> Optional[Move]:
    """Estrae la mossa dall'answer set."""
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


# ============================================================
# Chiamate ASP
# ============================================================

def _get_top_candidates(board: Board, rune: Rune, forge_level: int) -> list[Move]:
    """Estrae le top _N_CANDIDATES mosse in ordine di preferenza ASP.

    Usa esclusione iterativa: trova la mossa ottimale, aggiunge un vincolo duro
    che la esclude, trova la seconda migliore, ecc.

    Nota: --opt-mode=optN non funziona perché il vincolo P0 (R*9+C@0) rende ogni
    cella unica → Clingo trova sempre un solo modello al costo ottimale globale.
    L'esclusione iterativa contorna il problema e restituisce mosse davvero distinte.

    Nella fase iniziale (rune_count < 8) con 1-2 piazzamenti validi, inietta il fatto
    allow_early_discard affinché discard sia un candidato valutabile dal MC.
    _get_single_best non inietta questo fatto, così le simulazioni MC restano
    conservative (non sovra-scartano nelle fasi simulate).
    """
    candidates: list[Move] = []
    exclusions: list[str] = []

    # Calcola una volta sola se abilitare lo scarto anticipato come candidato MC
    extra_facts = ""
    if (board.rune_count() < 8
            and rune.rune_type == RuneType.NORMAL):
        n_valid = len(board.get_valid_placements(rune))
        if 0 < n_valid < 3:
            extra_facts = "allow_early_discard."

    for _ in range(_N_CANDIDATES):
        ctl = clingo.Control(["--opt-mode=opt"])
        ctl.load(str(_LP_DIR / "alchemy.lp"))
        ctl.load(str(_LP_DIR / "strategy.lp"))
        ctl.add("base", [], _board_to_asp(board, rune, forge_level))
        if extra_facts:
            ctl.add("base", [], extra_facts)
        for exc in exclusions:
            ctl.add("base", [], exc)
        ctl.ground([("base", [])])

        found: Move | None = None
        with ctl.solve(yield_=True) as handle:
            for model in handle:
                parsed = _parse_model(model)
                if parsed is not None:
                    found = parsed

        if found is None:
            break  # UNSAT: tutte le alternative sono state escluse

        if found in candidates:
            break  # nessuna nuova alternativa disponibile

        candidates.append(found)

        # Esclude questa mossa nel prossimo round
        if found["action"] == "place":
            exclusions.append(f":- place({found['row']},{found['col']}).")
        elif found["action"] == "use_skull":
            exclusions.append(f":- use_skull({found['row']},{found['col']}).")
        else:
            # discard trovato: escludilo per cercare i piazzamenti alternativi.
            # Se non esistono piazzamenti (forzato), il prossimo round sarà
            # UNSAT e uscirà per il check found is None.
            exclusions.append(":- discard.")

    return candidates or [{"action": "discard"}]


def _get_single_best(board: Board, rune: Rune, forge_level: int) -> Move:
    """Singola chiamata ASP con --opt-mode=opt — usata per le mosse simulate nelle rollout."""
    ctl = clingo.Control(["--opt-mode=opt"])
    ctl.load(str(_LP_DIR / "alchemy.lp"))
    ctl.load(str(_LP_DIR / "strategy.lp"))
    ctl.add("base", [], _board_to_asp(board, rune, forge_level))
    ctl.ground([("base", [])])

    best: Move = {"action": "discard"}
    with ctl.solve(yield_=True) as handle:
        for model in handle:
            parsed = _parse_model(model)
            if parsed is not None:
                best = parsed
    return best


# ============================================================
# Applicazione mossa
# ============================================================

def _apply_move(board: Board, forge: Forge, rune: Rune, move: Move) -> None:
    """Applica una mossa su board e forge in-place."""
    action = move["action"]
    if action == "place":
        r, c = move["row"], move["col"]
        completions = board.place_rune(rune, r, c)
        if completions:
            forge.on_row_col_complete()
            if board.is_board_complete():
                forge.on_board_complete()
        else:
            forge.on_place()
    elif action == "use_skull":
        board.remove_rune(move["row"], move["col"])
        forge.on_place()
    elif action == "discard":
        forge.on_discard()


# ============================================================
# Compatibility score
# ============================================================

def _compatibility_score(board: Board, row: int, col: int, difficulty: str) -> int:
    """Conta quante rune normali del livello potrebbero essere piazzate in almeno
    una cella adiacente libera a (row, col) — chiamata dopo il piazzamento,
    quindi (row, col) è già occupata.

    Itera tutte le combinazioni simbolo/colore del livello e verifica se ognuna
    risulterebbe valida in almeno un vicino libero di (row, col).
    """
    free_neighbors: list[tuple[int, int]] = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        r, c = row + dr, col + dc
        if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
            if not board.is_gold(r, c) and not board.is_occupied(r, c):
                free_neighbors.append((r, c))

    if not free_neighbors:
        return 0

    symbols = SYMBOLS_BY_DIFFICULTY[difficulty]
    colors  = COLORS_BY_DIFFICULTY[difficulty]
    count = 0
    for sym in symbols:
        for clr in colors:
            future_rune = Rune(symbol=sym, color=clr)
            if any(board.can_place(future_rune, r, c) for r, c in free_neighbors):
                count += 1
    return count


# ============================================================
# Monte Carlo rollout
# ============================================================

def _run_mc_simulation(board: Board, candidate: Move, rune: Rune,
                       forge_level: int, seed: int) -> float:
    """Singola simulazione MC con seed fisso e profondità limitata a _MC_DEPTH turni.

    Applica candidate sulla copia della board, poi simula fino a _MC_DEPTH turni
    con _get_single_best, fermandosi prima in caso di game_over, board completa,
    o timeout di sicurezza.

    Restituisce (celle_oro / 81) * 100 - 20 se game_over, senza penalità altrimenti.
    """
    sim_board = copy.deepcopy(board)
    sim_forge = Forge()
    # Ripristina il livello forge: on_discard da 0 incrementa senza mai triggerare
    # game_over finché il livello target è <= MAX_LEVEL (invariante del chiamante).
    for _ in range(forge_level):
        sim_forge.on_discard()

    _apply_move(sim_board, sim_forge, rune, candidate)

    gen = RuneGenerator(difficulty=_LOOKAHEAD_DIFFICULTY, seed=seed)
    deadline = time.monotonic() + _SIM_TIMEOUT_S

    for _ in range(_MC_DEPTH):
        if sim_forge.is_game_over or sim_board.is_board_complete():
            break
        if time.monotonic() >= deadline:
            break
        next_rune = gen.next_rune()
        move = _get_single_best(sim_board, next_rune, sim_forge.level)
        _apply_move(sim_board, sim_forge, next_rune, move)

    gold = sim_board.gold_count()
    penalty = 20.0 if sim_forge.is_game_over else 0.0
    return (gold / 81.0) * 100.0 - penalty


def _mc_candidate_score(board: Board, candidate: Move, rune: Rune,
                        forge_level: int) -> float:
    """Media dei punteggi di _N_SIMULATIONS rollout per una mossa candidata.

    Le simulazioni girano in parallelo su _MC_WORKERS thread. Se una simulazione
    supera il timeout del future (timeout interno + 1s di buffer), contribuisce
    con 0.0 alla media — penalizzando candidati che portano a stati lenti/bloccanti.
    """
    pool = ThreadPoolExecutor(max_workers=_MC_WORKERS)
    futures: list[Future[float]] = [
        pool.submit(_run_mc_simulation, board, candidate, rune, forge_level, seed)
        for seed in range(_N_SIMULATIONS)
    ]

    scores: list[float] = []
    for fut in futures:
        try:
            scores.append(fut.result(timeout=_SIM_TIMEOUT_S + 1.0))
        except Exception:
            scores.append(0.0)

    # shutdown non bloccante: i thread residui terminano in background
    pool.shutdown(wait=False)
    return sum(scores) / len(scores)


# ============================================================
# API pubblica
# ============================================================

def get_best_move(board: Board, current_rune: Rune, forge_level: int,
                  difficulty: str = "hard") -> Move:
    """Calcola la mossa ottimale tramite Monte Carlo rollout ibrido Python+ASP.

    Il punteggio finale di ogni candidata è:
      score_mc * 0.7 + compatibility_score_normalizzato * 0.3
    Il compatibility score misura quante rune future potrebbero essere piazzate
    adiacenti alla posizione scelta dopo il piazzamento (solo per azioni place).

    Ritorna uno tra:
      {"action": "place",     "row": R, "col": C}
      {"action": "use_skull", "row": R, "col": C}
      {"action": "discard"}
    """
    candidates = _get_top_candidates(board, current_rune, forge_level)

    # --- DEBUG TEMPORANEO: attivo solo quando ci sono ≤3 rune sulla board ---
    if board.rune_count() <= 3:
        valid_py = board.get_valid_placements(current_rune)
        asp_facts = _board_to_asp(board, current_rune, forge_level)
        print("\n" + "="*60, file=sys.stderr)
        print(f"[DEBUG] rune_count={board.rune_count()}  forge={forge_level}", file=sys.stderr)
        print(f"[DEBUG] current_rune: {current_rune!r}", file=sys.stderr)
        print(f"[DEBUG] valid_placements (Python): {valid_py}", file=sys.stderr)
        print(f"[DEBUG] ASP facts:\n{asp_facts}", file=sys.stderr)
        print(f"[DEBUG] candidates (ASP): {candidates}", file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)
    # --- FINE DEBUG ---

    # Fast path: unica candidata, il rollout non cambierebbe nulla
    if len(candidates) == 1:
        return candidates[0]

    # Fast path: board quasi vuota — le candidati sono equivalenti e il MC
    # non ha abbastanza contesto per distinguerle in modo significativo
    if board.rune_count() < 5:
        return candidates[0]

    n_syms = len(SYMBOLS_BY_DIFFICULTY[difficulty])
    n_clrs = len(COLORS_BY_DIFFICULTY[difficulty])
    max_possible_runes = n_syms * n_clrs

    best_move  = candidates[0]
    best_score = float("-inf")
    for candidate in candidates:
        score_mc = _mc_candidate_score(board, candidate, current_rune, forge_level)

        if candidate["action"] == "place":
            temp_board = copy.deepcopy(board)
            temp_forge = Forge()
            for _ in range(forge_level):
                temp_forge.on_discard()
            _apply_move(temp_board, temp_forge, current_rune, candidate)
            compat_norm = _compatibility_score(
                temp_board, candidate["row"], candidate["col"], difficulty
            ) / max_possible_runes
        else:
            compat_norm = 0.0

        score_finale = score_mc * 0.7 + compat_norm * 0.3
        if score_finale > best_score:
            best_score = score_finale
            best_move  = candidate

    return best_move


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
