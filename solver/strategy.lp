% ============================================================
% STRATEGY.LP — Selezione e ottimizzazione della mossa
%
% Il solver sceglie UNA tra le azioni disponibili e la ottimizza
% usando vincoli deboli a priorità decrescente.
%
% Azioni possibili:
%   place(R,C)      – piazza la runa corrente in (R,C)
%   use_skull(R,C)  – usa lo skull per rimuovere la runa in (R,C)
%   discard         – scarta la runa corrente (+1 livello forge)
% ============================================================

% --- Scelta dell'azione ---

% Per rune normali e wildcard: piazza oppure scarta
1 { place(R,C) : valid_placement(R,C) ; discard } 1 :- not current_type(skull).

% Per skull: rimuovi una runa oppure scarta
1 { use_skull(R,C) : valid_removal(R,C) ; discard } 1 :- current_type(skull).

% --- Gestione del discard: contestuale nella fase iniziale ---
%
% Nei primissimi turni (rune_count < 8) con solo 1-2 piazzamenti validi,
% il solver può scartare per "aspettare" una runa più compatibile invece di
% costruire un cluster difficile da espandere.
%
% allow_early_discard è un fatto opzionale iniettato da Python solo in
% _get_top_candidates (selezione candidati). _get_single_best non lo inietta,
% così le simulazioni MC interne restano conservative e non sovra-scartano.

#defined allow_early_discard/0.

% Numero di piazzamenti validi disponibili questo turno
valid_count(N) :- N = #count{ R,C : valid_placement(R,C) }.

% Fase iniziale: meno di 8 rune sulla board E nessuna riga/colonna ancora completata.
% Se gold_count >= 9 il board ha già avuto almeno un completamento: il rune_count
% basso è dovuto alla pulizia della riga/colonna, non a una board davvero vuota.
early_game :- rune_count(N), N < 8, gold_count(G), G < 9.

% HARD — Skull: non scartare mai se si può rimuovere una runa
:- discard, valid_removal(_,_), current_type(skull).

% HARD — Fase avanzata (≥8 rune): comportamento originale
:- discard, valid_placement(_,_), not current_type(skull), not early_game.

% HARD — Fase iniziale con ≥3 piazzamenti: abbondanza di scelte, vietato scartare
:- discard, valid_placement(_,_), not current_type(skull), early_game, valid_count(N), N >= 3.

% HARD — Fase iniziale con 1-2 piazzamenti, senza allow_early_discard (simulazioni MC):
%         le simulazioni restano conservative per stimare correttamente il rischio forge
:- discard, valid_placement(_,_), not current_type(skull), early_game, valid_count(N), N < 3, not allow_early_discard.

% ============================================================
% Calcolo del cluster principale (connettività della board)
%
% Le rune sulla board formano idealmente un unico gruppo connesso.
% Dopo azioni skull la board può frammentarsi: i vincoli P3a
% garantiscono che si espanda sempre il cluster principale.
% ============================================================

% Radice deterministica: cella occupata con indice R*9+C minore
main_anchor(R,C) :-
    occupied(R,C),
    #min{ R1*9+C1 : occupied(R1,C1) } = R*9+C.

% BFS: celle raggiungibili dall'ancora via adiacenza tra celle occupate
in_main_cluster(R,C) :- main_anchor(R,C).
in_main_cluster(R,C) :- in_main_cluster(R1,C1), adj(R1,C1,R,C), occupied(R,C).

% Il piazzamento proposto tocca almeno un vicino del cluster principale
has_main_cluster_neighbor(R,C) :-
    valid_placement(R,C),
    adj(R,C,R1,C1),
    in_main_cluster(R1,C1).

% ============================================================
% Celle libere adiacenti dopo il piazzamento (opzioni future)
%
% Misura quante celle vuote resterebbero raggiungibili dalla
% nuova posizione, proxy per le opzioni disponibili al turno dopo.
% ============================================================

free_neighbors_after(R,C,N) :-
    valid_placement(R,C),
    N = #count{ R1,C1 : adj(R,C,R1,C1), empty(R1,C1) }.

% ============================================================
% Espansione bidirezionale (asse orizzontale e verticale)
%
% Il solver deve espandersi in entrambe le dimensioni per costruire
% cluster compatti. Piazzare su una cella senza libertà su un asse
% costringe il cluster a crescere solo in linea, riducendo le opzioni.
% ============================================================

% Distanza Manhattan dal centro della griglia (riga 4, colonna 4)
% — usata per la preferenza centrale alla prima mossa
center_dist(R,C,D) :- valid_placement(R,C), D = |R-4| + |C-4|.

% Esiste almeno una cella libera a sinistra o a destra
has_free_horiz(R,C) :- valid_placement(R,C), C1 = C-1, col(C1), empty(R,C1).
has_free_horiz(R,C) :- valid_placement(R,C), C1 = C+1, col(C1), empty(R,C1).

% Esiste almeno una cella libera sopra o sotto
has_free_vert(R,C)  :- valid_placement(R,C), R1 = R-1, row(R1), empty(R1,C).
has_free_vert(R,C)  :- valid_placement(R,C), R1 = R+1, row(R1), empty(R1,C).

% ============================================================
% Vincoli deboli (weak constraints)
% Sintassi: :~ condizione. [peso@priorità, variabili...]
% Il solver minimizza la somma pesata; priorità più alta = criterio più importante.
% ============================================================

% P4 — MASSIMA PRIORITÀ: preferire mosse che completano righe/colonne.
%      Il completamento svuota completamente la forge e fa oro 9 celle.
:~ place(R,C), not would_complete_row(R,C), not would_complete_col(R,C). [1@4, R, C]

% P3a — Espandere il cluster principale, non un cluster secondario.
%      Peso 25 > Gap massimo (16): la connettività batte sempre il fill,
%      salvo completamenti di riga/colonna (gestiti da P4).
:~ place(R,C), not board_empty, not has_main_cluster_neighbor(R,C). [25@3, R, C]

% P3b — Preferire posizioni in righe/colonne già più riempite, penalizzando lo sbilanciamento.
%      Costo = Gap + |NR-NC| = 16 - 2*min(NR,NC): massimizza il minimo tra fill di riga e colonna,
%      evitando il feedback loop che concentra i piazzamenti su una sola dimensione.
:~ place(R,C), row_fill(R,NR), col_fill(C,NC), Gap = 16 - NR - NC, Imb = |NR - NC|. [Gap + Imb@3, R, C]

% P2a — Penalizzare piazzamenti che lasciano meno di 3 celle libere adiacenti.
%      Evita di incastrarsi in vicoli ciechi che forzano scarti consecutivi.
%      Penalità crescente: N=2 → 1, N=1 → 2, N=0 → 3.
:~ place(R,C), free_neighbors_after(R,C,N), N < 3. [3-N@2, R, C]

% P2b — Evitare il discard quando la forge è pericolosa (livello 2 o 3).
:~ discard, forge_level(N), N >= 2. [N@2]

% P2c — Penalizzare piazzamenti che bloccano l'espansione su almeno un asse.
%      Peso 3 per asse mancante: max +6 se entrambi gli assi sono bloccati.
:~ place(R,C), not has_free_horiz(R,C). [3@2, R, C]
:~ place(R,C), not has_free_vert(R,C).  [3@2, R, C]

% P1a — Prima mossa (board vuota): preferire il centro per massimizzare
%       le direzioni di espansione. Attivo SOLO al primo turno; si disattiva
%       automaticamente non appena una runa è piazzata.
:~ place(R,C), board_empty, center_dist(R,C,D). [D@1, R, C]

% P1b — Evitare il discard anche quando la forge è bassa (preferire sempre piazzare).
:~ discard. [1@1]

% P0 — Tie-breaking deterministico: a parità di tutto, scegliere la posizione
%      con (R,C) lessicograficamente minima per garantire mosse riproducibili.
:~ place(R,C). [R*9 + C@0, R, C]
:~ use_skull(R,C). [R*9 + C@0, R, C]

% ============================================================
% Strategia skull
% ============================================================
% Rimuovere la runa più "isolata" (minor numero di vicini occupati):
% perdere una runa con pochi vicini impatta meno la connettività della board.
skull_neighbor_count(R,C,N) :-
    valid_removal(R,C),
    N = #count{ R1,C1 : adj(R,C,R1,C1), occupied(R1,C1) }.

% Penalizza la rimozione di rune con molti vicini (centrale/connessa):
% minimizzare il costo = preferire rune isolate (pochi vicini).
:~ use_skull(R,C), skull_neighbor_count(R,C,N). [N@1, R, C]

% ============================================================
% Atomi visibili nell'answer set restituito a Python
% ============================================================
#show place/2.
#show use_skull/2.
#show discard/0.
