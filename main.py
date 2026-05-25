# Entry point dell'applicazione: inizializza PyQt6, mostra la schermata di selezione
# difficoltà e avvia il loop principale della GUI.

# main.py

from __future__ import annotations
import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

def main() -> None:
    """Entry point principale dell'applicazione Alchemy."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
