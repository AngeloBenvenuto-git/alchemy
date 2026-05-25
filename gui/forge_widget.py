# Widget PyQt6 che visualizza lo stato corrente della forge (0–3 livelli),
# con aggiornamento visivo ad ogni piazzamento, scarto o completamento riga/colonna.


# gui/forge_widget.py

from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from game.forge import Forge


class ForgeWidget(QWidget):
    """Widget grafico che mostra visivamente l'indicatore a 3 livelli della forge."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._labels: list[QLabel] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        # Etichetta descrittiva
        title_label = QLabel("FORGE:")
        title_label.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 13px;")
        layout.addWidget(title_label)

        # Crea i 3 blocchi indicatori
        for _ in range(Forge.MAX_LEVEL):
            lbl = QLabel()
            lbl.setFixedSize(30, 20)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl)
            self._labels.append(lbl)

        # Aggiunge uno stretch per allineare tutto a sinistra
        layout.addStretch()
        self.update_state(0, False)

    def update_state(self, level: int, is_game_over: bool) -> None:
        """Aggiorna i fogli di stile dei blocchi in base al livello della forge."""
        for i, lbl in enumerate(self._labels):
            if is_game_over:
                # Stato di Game Over: tutti i blocchi lampeggiano/rimangono rossi scuri
                lbl.setStyleSheet("background-color: #8B0000; border: 1px solid #FF0000;")
            elif i < level:
                # Blocco attivo: se siamo al livello 3 usiamo il rosso, altrimenti arancione/giallo
                if level == Forge.MAX_LEVEL:
                    color = "#FF4B4B"  # Rosso pericolo
                elif level == 2:
                    color = "#FFA500"  # Arancione avviso
                else:
                    color = "#FFD700"  # Giallo normale
                lbl.setStyleSheet(f"background-color: {color}; border: 1px solid #FFFFFF; border-radius: 2px;")
            else:
                # Blocco spento (vuoto)
                lbl.setStyleSheet("background-color: #2C3E50; border: 1px solid #555555; border-radius: 2px;")