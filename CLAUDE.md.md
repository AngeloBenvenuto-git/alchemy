# Alchemy — PopCap Games (AI Project)

## Panoramica del progetto
Implementazione del gioco **Alchemy di PopCap Games** (2001) con un solver basato su **Answer Set Programming (ASP)** che gioca in modo completamente autonomo. Il progetto è sviluppato per un corso universitario di Intelligenza Artificiale.

Il sistema riceve una runa alla volta (generata casualmente) e decide autonomamente dove piazzarla sulla griglia, usando Clingo come motore ASP per calcolare la mossa ottimale ad ogni turno.

---

## Stack tecnologico
- **Linguaggio**: Python 3.x
- **Motore ASP**: Clingo (installabile con `pip install clingo`)
- **Interfaccia grafica**: PyQt6 (installabile con `pip install PyQt6`)
- **Nessun framework web, nessun server esterno**

---

## Regole del gioco

### Griglia
- Dimensione: **9x9** (81 quadrati totali)
- Ogni quadrato inizia come "piombo" e diventa "oro" quando una runa viene piazzata su di esso
- Obiettivo: trasformare tutti i quadrati in oro

### Rune
- Ogni turno il sistema genera una runa casuale con un simbolo e un colore
- La runa deve essere piazzata adiacente (su/giù/sinistra/destra, NO diagonale) ad almeno un'altra runa già presente
- **Regola di adiacenza**: tutte le rune adiacenti alla posizione scelta devono condividere il colore OPPURE il simbolo con la runa da piazzare
- Eccezione: la prima runa può essere piazzata ovunque (griglia vuota)

### Forge
- Ha **3 livelli**
- Ogni scarto riempie la forge di 1 livello
- Ogni piazzamento valido svuota la forge di 1 livello
- Se la forge raggiunge il livello 3 e si scarta ancora → **game over**
- Completare una riga/colonna svuota completamente la forge

### Completamento riga/colonna
- Riempire una intera riga o colonna di rune le fa sparire tutte
- Quei quadrati diventano oro permanentemente
- La forge si svuota completamente

### Completamento board
- Quando tutti i 81 quadrati sono oro → board completata, si passa al livello successivo
- Il completamento della board abbassa la forge di 1 livello (non la svuota)

### Speciali
- **Wildcard** (jolly grigio): può essere piazzato adiacente a qualsiasi runa ignorando colore e simbolo. Qualsiasi runa può essere piazzata accanto ad una wildcard (purché le altre adiacenti siano compatibili)
- **Skull & Crossbones** (teschio): rimuove una runa a scelta dalla griglia
- Entrambi abbassano la forge di 1 livello se usati; se scartati la riempiono di 1

---

## Livelli di difficoltà

| Livello  | Simboli | Colori |
|----------|---------|--------|
| Facile   | 4       | 2      |
| Medio    | 8       | 3      |
| Difficile| 12      | 4      |

- La difficoltà è **fissa per tutta la partita**
- Può essere cambiata solo a inizio nuova partita
- I simboli sono simboli zodiacali: Ariete, Toro, Gemelli, Cancro, Leone, Vergine, Bilancia, Scorpione, Sagittario, Capricorno, Acquario, Pesci

---

## Flusso dell'applicazione

1. **Schermata iniziale**: l'utente sceglie il livello di difficoltà (Facile / Medio / Difficile)
2. **Partita**: il solver gioca in autonomia passo per passo, ogni mossa è visibile all'utente con una piccola animazione/pausa
3. **Fine partita**: viene mostrato il risultato (board completata o game over) con statistiche, poi si chiede se si vuole fare una nuova partita

---

## Architettura del progetto

```
alchemy/
├── CLAUDE.md                  # questo file
├── main.py                    # entry point, avvia la GUI
├── game/
│   ├── __init__.py
│   ├── board.py               # stato della griglia, logica piombo/oro
│   ├── rune.py                # definizione runa (simbolo, colore, speciali)
│   ├── forge.py               # gestione forge
│   └── generator.py           # generatore rune casuali
├── solver/
│   ├── __init__.py
│   ├── asp_solver.py          # bridge Python-Clingo
│   ├── alchemy.lp             # programma ASP principale (regole del gioco)
│   └── strategy.lp            # regole di strategia e ottimizzazione
└── gui/
    ├── __init__.py
    ├── main_window.py         # finestra principale PyQt6
    ├── board_widget.py        # widget griglia 9x9
    ├── forge_widget.py        # widget forge
    └── rune_widget.py         # rappresentazione visiva di una runa
```

---

## Il solver ASP

### Approccio
Ad ogni turno il solver riceve:
- Lo stato attuale della griglia (quali celle sono occupate, da quale runa)
- La runa corrente (simbolo + colore)
- Il livello della forge

Il solver ASP calcola la **mossa ottimale**: dove piazzare la runa (o se scartarla), con l'obiettivo di:
1. Massimizzare le possibilità di mosse future (non bloccarsi)
2. Favorire il completamento di righe/colonne
3. Minimizzare il rischio di riempire la forge

### File ASP
- `alchemy.lp`: contiene i fatti del gioco (stato griglia, runa corrente) e le regole di validità (vincoli di adiacenza, colore/simbolo)
- `strategy.lp`: contiene la funzione di ottimizzazione (`#minimize` / `#maximize`) per scegliere la mossa migliore

### Integrazione Python-Clingo
```python
import clingo

def get_best_move(board_state, current_rune, forge_level, difficulty):
    ctl = clingo.Control()
    ctl.load("solver/alchemy.lp")
    ctl.load("solver/strategy.lp")
    # aggiunge i fatti dinamici dello stato corrente
    ctl.add("base", [], board_state_to_asp(board_state, current_rune, forge_level))
    ctl.ground([("base", [])])
    result = None
    with ctl.solve(yield_=True) as handle:
        for model in handle:
            result = parse_move(model)
    return result
```

---

## Convenzioni di codice
- Usa **type hints** Python ovunque possibile
- Ogni modulo ha un docstring che spiega cosa fa
- I fatti ASP vengono generati dinamicamente da Python come stringhe
- La GUI non contiene logica di gioco — solo visualizzazione
- Il solver non conosce la GUI — comunica solo attraverso `asp_solver.py`

---

## Note importanti
- Questo è un progetto universitario per un corso di IA — la parte ASP è il cuore del progetto e deve essere ben documentata e commentata
- Il solver deve essere **deterministico**: a parità di stato, deve sempre scegliere la stessa mossa
- La GUI deve mostrare ogni mossa con una pausa visibile (es. 800ms) per permettere all'utente di seguire il ragionamento del solver
- Non implementare modalità multiplayer o punteggi online
