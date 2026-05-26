# gui/rune_widget.py

from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from game.rune import Rune, RuneType
from gui.rune_maps import SYMBOL_MAP, COLOR_MAP


class RuneWidget(QWidget):
    """Widget grafico avanzato per l'anteprima della runa del turno con simboli reali."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._preview_box = QLabel()
        self._info_label = QLabel()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 15, 12, 15)

        # Titolo della sezione (Card Style)
        title = QLabel("RUNA CORRENTE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold; color: #3498DB; font-size: 10px; letter-spacing: 1.5px;")
        layout.addWidget(title)

        # Box grafico della runa ad alto contrasto
        self._preview_box.setFixedSize(110, 110)
        self._preview_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._preview_box, alignment=Qt.AlignmentFlag.AlignCenter)

        # Testo descrittivo (Simbolo + Colore esteso)
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_label.setStyleSheet("color: #ECF0F1; font-size: 13px; font-weight: bold; line-height: 18px;")
        layout.addWidget(self._info_label)

        self.clear_preview()

    def set_rune(self, rune: Rune) -> None:
        """Aggiorna l'anteprima mostrando i dettagli e i glifi reali della runa."""
        if rune.rune_type == RuneType.WILDCARD:
            self._preview_box.setText("★")
            self._preview_box.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4E54C8, stop:1 #8F94FB); "
                "border: 3px dashed #FFFF00; color: #FFFF00; font-size: 42px; font-weight: bold; border-radius: 12px;"
            )
            self._info_label.setText("WILDCARD\n(Universale)")

        elif rune.rune_type == RuneType.SKULL:
            self._preview_box.setText("☠")
            self._preview_box.setStyleSheet(
                "background-color: #111111; border: 2px solid #FF4B5C; "
                "color: #FF4B5C; font-size: 42px; font-weight: bold; border-radius: 12px;"
            )
            self._info_label.setText("TESCHIO\n(Rimuovi Runa)")

        else:
            # Runa normale: estrae il nome in italiano e mappa il glifo corretto
            sym_text = rune.symbol.value if rune.symbol else "?"
            col_text = rune.color.value if rune.color else "?"
            bg_color = COLOR_MAP.get(col_text, "#34495E")
            glyph = SYMBOL_MAP.get(sym_text, "•")

            self._preview_box.setText(glyph)
            self._preview_box.setStyleSheet(
                f"background-color: {bg_color}; border: 1px solid rgba(255,255,255,0.2); "
                f"color: #FFFFFF; font-size: 46px; font-weight: bold; border-radius: 12px;"
            )
            # Pulito e senza tag HTML instabili: usa il newline standard nativo
            self._info_label.setText(f"{sym_text}\n{col_text}")

    def clear_preview(self) -> None:
        """Stato di standby della card."""
        self._preview_box.setText("-")
        self._preview_box.setStyleSheet(
            "background-color: #1A1E24; border: 2px dashed #2C3540; "
            "color: #566573; font-size: 24px; border-radius: 12px;"
        )
        self._info_label.setText("In attesa...")