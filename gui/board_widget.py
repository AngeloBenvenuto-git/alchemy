# gui/board_widget.py

from __future__ import annotations
from PyQt6.QtWidgets import QGridLayout, QPushButton, QWidget
from PyQt6.QtCore import Qt
from game.board import Board, GRID_SIZE
from game.rune import RuneType
from gui.rune_maps import SYMBOL_MAP, COLOR_MAP


class BoardWidget(QWidget):
    """Widget grafico avanzato per la griglia 9x9 con stile lucido e moderno."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._buttons: list[list[QPushButton]] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QGridLayout(self)
        layout.setSpacing(4)  # Spazio elegante tra le celle
        layout.setContentsMargins(5, 5, 5, 5)

        for r in range(GRID_SIZE):
            row_buttons = []
            for c in range(GRID_SIZE):
                btn = QPushButton()
                btn.setFixedSize(48, 48)  # Dimensione ottimale e simmetrica
                btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                layout.addWidget(btn, r, c)
                row_buttons.append(btn)
            self._buttons.append(row_buttons)

        self.update_styles_from_logic(Board())

    def update_styles_from_logic(self, board: Board) -> None:
        """Aggiorna la grafica della scacchiera applicando uno stile moderno."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                btn = self._buttons[r][c]
                rune = board.get_rune(r, c)
                is_gold = board.is_gold(r, c)

                # 1. Gestione del Testo/Icona all'interno del pulsante
                if rune is not None:
                    if rune.rune_type == RuneType.WILDCARD:
                        btn.setText("★")
                    elif rune.rune_type == RuneType.SKULL:
                        btn.setText("☠")
                    else:
                        sym_val = rune.symbol.value if rune.symbol else ""
                        btn.setText(SYMBOL_MAP.get(sym_val, "•"))
                else:
                    btn.setText("")

                # 2. Configurazione dello stile CSS avanzato (QSS)
                style = "font-size: 18px; font-weight: bold; border-radius: 6px;"

                if is_gold:
                    # Oro metallico premium con bordo scuro sottile
                    style += """
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFD700, stop:1 #FFA500);
                        border: 1px solid #B7950B;
                        color: #1E272C;
                    """
                elif rune is not None:
                    if rune.rune_type == RuneType.WILDCARD:
                        style += """
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4E54C8, stop:1 #8F94FB);
                            border: 2px dashed #FFFF00;
                            color: #FFFF00;
                        """
                    elif rune.rune_type == RuneType.SKULL:
                        style += """
                            background: #111111;
                            border: 2px solid #FF4B5C;
                            color: #FF4B5C;
                        """
                    else:
                        col_val = rune.color.value if rune.color else ""
                        bg_color = COLOR_MAP.get(col_val, "#7F8C8D")
                        style += f"""
                            background-color: {bg_color};
                            border: 1px solid rgba(0, 0, 0, 0.2);
                            color: #FFFFFF;
                        """
                else:
                    # Piombo: Grigio scuro con effetto incavato soft
                    style += """
                        background-color: #2F3640;
                        border: 1px solid #1E222B;
                    """

                btn.setStyleSheet(style)