# Alchemy — AI Solver

Implementazione del gioco **Alchemy di PopCap Games** con un agente autonomo basato su **Answer Set Programming (ASP)** che gioca in modo completamente automatico.

Il progetto è stato sviluppato per il corso di **Intelligenza Artificiale** ed esplora l'uso di ASP come tecnica di ragionamento per la pianificazione di mosse in un gioco a turni.

---

## Come funziona

Ad ogni turno viene generata casualmente una runa (simbolo zodiacale + colore). Il solver analizza lo stato della griglia e decide autonomamente la mossa ottimale: dove piazzare la runa, oppure se scartarla. L'obiettivo è trasformare tutti i quadrati della griglia da piombo a oro completando righe e colonne.

Il solver non usa euristiche cablate a mano, ma ragiona tramite regole dichiarative scritte in ASP e ottimizzazione tramite vincoli deboli, scegliendo sempre la mossa che massimizza le possibilità future e minimizza il rischio di game over.

---

## Regole del gioco

### Griglia
La partita si svolge su una griglia **9×9** (81 quadrati). Ogni quadrato inizia come "piombo" e diventa "oro" quando fa parte di una riga o colonna completamente riempita.

### Rune
Ogni turno viene generata una runa con un simbolo zodiacale e un colore. Per piazzarla sulla griglia deve essere adiacente (su, giù, sinistra, destra — no diagonale) ad almeno un'altra runa già presente, e tutte le rune vicine devono condividere il **colore oppure il simbolo** con quella da piazzare.

### Forge
La forge è un indicatore a 3 livelli. Ogni volta che una runa viene scartata la forge sale di un livello; ogni piazzamento valido la abbassa di uno. Completare una riga o colonna la svuota completamente. Se la forge è piena e si scarta ancora, la partita termina con un **game over**.

### Rune speciali
- **Wildcard** — può essere piazzata adiacente a qualsiasi runa, ignorando colore e simbolo
- **Skull & Crossbones** — rimuove una runa a scelta dalla griglia

### Completamento
Riempire una riga o colonna intera fa sparire tutte le rune presenti, converte quei quadrati in oro e svuota la forge. Quando tutti gli 81 quadrati sono oro la board è completata.

---

## Livelli di difficoltà

| Livello   | Simboli zodiacali | Colori |
|-----------|-------------------|--------|
| Facile    | 4                 | 2      |
| Medio     | 8                 | 3      |
| Difficile | 12                | 4      |

La difficoltà si sceglie all'inizio di ogni partita e rimane fissa per tutta la durata.

---

## Il solver ASP

Il cuore del progetto è il solver scritto in **Answer Set Programming**, eseguito tramite [Clingo](https://potassco.org/clingo/).

Ad ogni turno il solver riceve lo stato completo della griglia, la runa corrente e il livello della forge, e calcola la mossa ottimale tramite una gerarchia di vincoli deboli:

| Priorità | Obiettivo |
|----------|-----------|
| P4 — massima | Completare una riga o colonna (svuota la forge) |
| P3 | Preferire righe/colonne già dense (avvicinarsi al completamento) |
| P2 | Evitare scarti con forge a livello 2 o 3 |
| P1 | Evitare scarti in generale |
| P0 | Tie-break deterministico per mosse riproducibili |

Il solver è **deterministico**: a parità di stato produce sempre la stessa mossa.

---

## Struttura del progetto

```
alchemy/
├── main.py                    # entry point
├── game/
│   ├── board.py               # griglia 9x9, logica piombo/oro
│   ├── rune.py                # definizione runa (simbolo, colore, speciali)
│   ├── forge.py               # gestione forge
│   └── generator.py           # generatore rune casuali
├── solver/
│   ├── asp_solver.py          # bridge Python-Clingo
│   ├── alchemy.lp             # regole ASP del gioco
│   └── strategy.lp            # strategia e ottimizzazione
└── gui/
    ├── main_window.py         # finestra principale PyQt6
    ├── board_widget.py        # widget griglia
    ├── forge_widget.py        # widget forge
    └── rune_widget.py         # widget runa corrente
```

---

## Requisiti e installazione

**Python 3.8+** — verifica la versione con `python --version`

Installa le dipendenze:
```bash
pip install clingo
pip install PyQt6
```

Avvia l'applicazione:
```bash
python main.py
```

---

## Tecnologie utilizzate

- **Python** — linguaggio principale
- **Clingo / ASP** — motore di ragionamento per il solver
- **PyQt6** — interfaccia grafica desktop
