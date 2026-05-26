# gui/main_window.py

from __future__ import annotations
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QComboBox, QGroupBox
)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from game.board import Board
from game.forge import Forge
from game.generator import RuneGenerator
from game.rune import Rune
from solver.asp_solver import get_best_move


class MoveWorker(QThread):
    """Thread background che calcola la mossa ottimale senza bloccare la GUI.

    Emette move_ready(dict) con la mossa scelta al termine del calcolo.
    La GUI rimane responsiva durante l'elaborazione del Monte Carlo rollout.
    """
    move_ready: pyqtSignal = pyqtSignal(dict)

    def __init__(self, board: Board, rune: Rune, forge_level: int) -> None:
        super().__init__()
        self._board = board
        self._rune = rune
        self._forge_level = forge_level

    def run(self) -> None:
        move = get_best_move(self._board, self._rune, self._forge_level)
        self.move_ready.emit(move)


class MainWindow(QMainWindow):
    """Finestra principale con interfaccia Dark Premium e layout Card-Based."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Alchemy — AI Solver (ASP)")
        self.setMinimumSize(820, 600)

        # Logica di gioco
        self._board = Board()
        self._forge = Forge()
        self._generator: RuneGenerator | None = None
        self._turn_count = 0

        # Runa del turno corrente — condivisa tra _game_tick e _on_move_ready
        self._current_rune: Rune | None = None

        # Worker per il calcolo asincrono della mossa
        self._worker: MoveWorker | None = None

        # Timer single-shot: pausa visibile tra un turno e il successivo.
        # Non si riarma automaticamente; viene riavviato da _on_move_ready
        # dopo che la mossa è stata applicata e la UI aggiornata.
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._game_tick)
        self._tick_interval_ms = 800

        # Widget grafici
        from gui.board_widget import BoardWidget
        from gui.forge_widget import ForgeWidget
        from gui.rune_widget import RuneWidget

        self._board_widget = BoardWidget()
        self._forge_widget = ForgeWidget()
        self._rune_widget = RuneWidget()

        # Etichette statistiche
        self._lbl_status = QLabel("Pronto per una nuova partita")
        self._lbl_turns = QLabel("Turno: 0")
        self._lbl_gold = QLabel("Oro completato: 0/81 (0%)")

        self._init_ui()
        self._apply_premium_theme()

    def _init_ui(self) -> None:
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- SEZIONE SINISTRA: Plancia di Gioco ---
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)

        forge_container = QWidget()
        forge_layout = QHBoxLayout(forge_container)
        forge_layout.setContentsMargins(5, 0, 0, 0)
        forge_layout.addWidget(self._forge_widget)
        left_layout.addWidget(forge_container)

        left_layout.addWidget(self._board_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(left_layout, stretch=3)

        # --- SEZIONE DESTRA: Pannello di Controllo (Card-Based) ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)

        # Card 1: Configurazione
        ctrl_group = QGroupBox("CONFIGURAZIONE")
        ctrl_layout = QVBoxLayout(ctrl_group)
        ctrl_layout.setSpacing(10)
        ctrl_layout.setContentsMargins(12, 18, 12, 12)

        self._combo_diff = QComboBox()
        self._combo_diff.addItems(["easy", "medium", "hard"])
        self._combo_diff.setCurrentText("medium")

        lbl_diff = QLabel("Livello di Difficoltà:")
        lbl_diff.setStyleSheet("color: #95A5A6; font-size: 11px; font-weight: bold;")
        ctrl_layout.addWidget(lbl_diff)
        ctrl_layout.addWidget(self._combo_diff)

        self._btn_start = QPushButton("AVVIA AGENTE")
        self._btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_start.clicked.connect(self._start_game)
        ctrl_layout.addWidget(self._btn_start)
        right_panel.addWidget(ctrl_group)

        # Card 2: Visualizzatore Runa
        right_panel.addWidget(self._rune_widget)

        # Card 3: Statistiche
        stats_group = QGroupBox("STATISTICHE AGENTE")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(8)
        stats_layout.setContentsMargins(12, 18, 12, 12)

        self._lbl_turns.setStyleSheet("font-size: 13px; color: #ECF0F1;")
        self._lbl_gold.setStyleSheet("font-size: 13px; color: #ECF0F1;")
        stats_layout.addWidget(self._lbl_turns)
        stats_layout.addWidget(self._lbl_gold)
        right_panel.addWidget(stats_group)

        # Log mosse
        self._lbl_status.setWordWrap(True)
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_panel.addWidget(self._lbl_status)
        right_panel.addStretch()

        main_layout.addLayout(right_panel, stretch=1)

    def _apply_premium_theme(self) -> None:
        """Applica un foglio di stile QSS professionale scuro ad alto contrasto."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1A1E24;
            }
            QGroupBox {
                border: 1px solid #2C3540;
                border-radius: 8px;
                margin-top: 12px;
                font-size: 11px;
                font-weight: bold;
                color: #3498DB;
                background-color: #212730;
                letter-spacing: 0.5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
                background-color: #1A1E24;
            }
            QLabel {
                color: #E2E8F0;
                font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
            }
            QComboBox {
                background-color: #1A1E24;
                color: #ECF0F1;
                border: 1px solid #3A4454;
                border-radius: 5px;
                padding: 6px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QPushButton {
                background-color: #2980B9;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #3498DB;
            }
            QPushButton:pressed {
                background-color: #21618C;
            }
            QPushButton:disabled {
                background-color: #2C3E50;
                color: #7F8C8D;
            }
        """)
        self._lbl_status.setStyleSheet(
            "color: #E67E22; font-weight: bold; font-size: 12px; padding: 5px;"
        )

    def _start_game(self) -> None:
        # Disconnette un eventuale worker rimasto da una partita precedente
        if self._worker is not None:
            self._worker.move_ready.disconnect()
            self._worker = None

        self._btn_start.setEnabled(False)
        self._combo_diff.setEnabled(False)

        self._board = Board()
        self._forge = Forge()
        self._generator = RuneGenerator(difficulty=self._combo_diff.currentText())
        self._turn_count = 0
        self._current_rune = None

        self._board_widget.update_styles_from_logic(self._board)
        self._forge_widget.update_state(0, False)
        self._rune_widget.clear_preview()

        self._lbl_status.setStyleSheet(
            "color: #E67E22; font-weight: bold; font-size: 12px; padding: 5px;"
        )
        self._lbl_status.setText("IA in esecuzione...")
        self._timer.start(self._tick_interval_ms)

    def _game_tick(self) -> None:
        """Genera la runa del turno e avvia il worker per il calcolo asincrono della mossa."""
        self._turn_count += 1

        assert self._generator is not None
        self._current_rune = self._generator.next_rune()
        self._rune_widget.set_rune(self._current_rune)

        # Indicatore visivo: la GUI rimane responsiva mentre il worker calcola
        self._lbl_status.setStyleSheet(
            "color: #3498DB; font-weight: bold; font-size: 12px; padding: 5px;"
        )
        self._lbl_status.setText("Agente sta pensando...")

        self._worker = MoveWorker(self._board, self._current_rune, self._forge.level)
        self._worker.move_ready.connect(self._on_move_ready)
        self._worker.start()

    def _on_move_ready(self, move: dict) -> None:
        """Riceve la mossa dal worker, la applica e aggiorna tutta la GUI."""
        assert self._current_rune is not None
        current_rune = self._current_rune
        action = move["action"]

        # Ripristina il colore normale del log mosse
        self._lbl_status.setStyleSheet(
            "color: #E67E22; font-weight: bold; font-size: 12px; padding: 5px;"
        )

        if action == "place":
            r, c = move["row"], move["col"]
            completions = self._board.place_rune(current_rune, r, c)
            if completions:
                self._forge.on_row_col_complete()
                if self._board.is_board_complete():
                    self._forge.on_board_complete()
            else:
                self._forge.on_place()
            self._lbl_status.setText(f"Piazzata runa in ({r}, {c})")

        elif action == "use_skull":
            r, c = move["row"], move["col"]
            self._board.remove_rune(r, c)
            self._forge.on_place()
            self._lbl_status.setText(f"☠️ Skull usato in ({r}, {c})")

        elif action == "discard":
            self._forge.on_discard()
            self._lbl_status.setText("Nessun incastro. Runa scartata.")

        self._board_widget.update_styles_from_logic(self._board)
        self._forge_widget.update_state(self._forge.level, self._forge.is_game_over)
        self._update_statistics_labels()

        if self._board.is_board_complete():
            self._lbl_status.setStyleSheet(
                "color: #2ECC71; font-weight: bold; font-size: 13px;"
            )
            self._lbl_status.setText("🏆 VITTORIA! Board completata con successo!")
            self._finalize_game()
        elif self._forge.is_game_over:
            self._lbl_status.setStyleSheet(
                "color: #E74C3C; font-weight: bold; font-size: 13px;"
            )
            self._lbl_status.setText("💥 GAME OVER! La forge è esplosa.")
            self._finalize_game()
        else:
            # Pausa visibile, poi turno successivo
            self._timer.start(self._tick_interval_ms)

    def _update_statistics_labels(self) -> None:
        self._lbl_turns.setText(f"Turno Corrente: {self._turn_count}")
        gold_cells = self._board.gold_count()
        percentage = (gold_cells / 81) * 100
        self._lbl_gold.setText(f"Celle Oro: {gold_cells}/81 ({percentage:.1f}%)")

    def _finalize_game(self) -> None:
        self._btn_start.setEnabled(True)
        self._combo_diff.setEnabled(True)
        self._btn_start.setText("AVVIA AGENTE")
