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

% --- Vincolo duro: non scartare se esistono piazzamenti validi ---
% Scartare aumenta la forge di 1; piazzare la diminuisce di 1.
% Non c'è mai motivo di scartare quando si può piazzare.
:- discard, valid_placement(_,_), not current_type(skull).

% --- Vincoli deboli (weak constraints) ---
% Sintassi: :~ condizione. [peso@priorità, variabili...]
% Il solver minimizza la somma pesata; priorità più alta = criterio più importante.

% P4 — MASSIMA PRIORITÀ: preferire mosse che completano righe/colonne.
%      Il completamento svuota completamente la forge e fa oro 9 celle.
:~ place(R,C), not would_complete_row(R,C), not would_complete_col(R,C). [1@4, R, C]

% P3 — Preferire posizioni in righe/colonne già più riempite.
%      Massimizzare NR+NC avvicina al completamento in entrambe le direzioni.
%      Gap = (8-NR) + (8-NC) = 16 - NR - NC; minimizzare Gap = massimizzare NR+NC.
:~ place(R,C), row_fill(R,NR), col_fill(C,NC), Gap = 16 - NR - NC. [Gap@3, R, C]

% P2 — Evitare il discard quando la forge è pericolosa (livello 2 o 3).
:~ discard, forge_level(N), N >= 2. [N@2]

% P1 — Evitare il discard anche quando la forge è bassa (preferire sempre piazzare).
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
