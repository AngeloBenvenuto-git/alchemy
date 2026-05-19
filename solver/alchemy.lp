% ============================================================
% ALCHEMY.LP — Fatti e regole di validità del gioco Alchemy
%
% Fatti dinamici aggiunti da Python a ogni turno:
%   cell(R,C,Sym,Col)    – runa normale in (R,C)
%   wildcard_cell(R,C)   – wildcard in (R,C)
%   gold(R,C)            – cella permanentemente oro
%   current_type(T)      – tipo runa corrente: normal | wildcard | skull
%   current_rune(Sym,Col)– simbolo e colore runa corrente (none,none per speciali)
%   forge_level(N)       – livello forge corrente (0-3)
% ============================================================

% Fatti forniti dinamicamente da Python: nessuna regola li definisce qui.
#defined cell/4.
#defined wildcard_cell/2.
#defined gold/2.
#defined current_type/1.
#defined current_rune/2.
#defined forge_level/1.

% --- Dominio ---
row(0..8). col(0..8).

% --- Adiacenza ortogonale entro i bordi ---
adj(R,C, R-1,C) :- row(R), R > 0,  col(C).
adj(R,C, R+1,C) :- row(R), R < 8,  col(C).
adj(R,C, R,C-1) :- row(R), col(C), C > 0.
adj(R,C, R,C+1) :- row(R), col(C), C < 8.

% --- Stato delle celle ---
occupied(R,C) :- cell(R,C,_,_).
occupied(R,C) :- wildcard_cell(R,C).

empty(R,C) :- row(R), col(C), not occupied(R,C), not gold(R,C).

% La board è vuota se non ci sono rune (prima mossa: placement libero)
board_empty :- #count{ R,C : occupied(R,C) } = 0.

% --- Compatibilità della runa corrente con i vicini già piazzati ---

% La runa corrente è wildcard: compatibile con qualsiasi vicino
neighbor_compat(R1,C1) :- current_type(wildcard), occupied(R1,C1).

% Il vicino è una wildcard sulla board: compatibile con qualsiasi runa corrente
neighbor_compat(R1,C1) :- wildcard_cell(R1,C1).

% Runa normale: stesso simbolo del vicino
neighbor_compat(R1,C1) :- current_type(normal), current_rune(S,_), cell(R1,C1,S,_).

% Runa normale: stesso colore del vicino
neighbor_compat(R1,C1) :- current_type(normal), current_rune(_,Col), cell(R1,C1,_,Col).

% Un vicino occupato che non soddisfa nessuna delle regole sopra è incompatibile
bad_neighbor(R,C) :-
    adj(R,C,R1,C1),
    occupied(R1,C1),
    not neighbor_compat(R1,C1).

% --- Posizioni di piazzamento valide ---

% Prima mossa: la griglia è vuota, qualsiasi cella libera va bene
valid_placement(R,C) :-
    empty(R,C),
    board_empty,
    not current_type(skull).

% Mosse successive: deve esserci almeno un vicino occupato
%                   e tutti i vicini occupati devono essere compatibili
valid_placement(R,C) :-
    empty(R,C),
    not board_empty,
    not current_type(skull),
    adj(R,C,R1,C1), occupied(R1,C1),   % almeno un vicino (condizione esistenziale)
    not bad_neighbor(R,C).              % tutti i vicini compatibili (universale via negazione)

% --- Posizioni di rimozione valide (azione skull) ---
% Lo skull può rimuovere qualsiasi runa dalla griglia, non solo quelle adiacenti
valid_removal(R,C) :- occupied(R,C), current_type(skull).

% --- Statistiche righe e colonne (usate dalla strategia) ---
row_fill(R,N) :- row(R), N = #count{ C : occupied(R,C) }.
col_fill(C,N) :- col(C), N = #count{ R : occupied(R,C) }.

% Piazzare in (R,C) completerebbe la riga R (porta le rune a 9/9)
would_complete_row(R,C) :- valid_placement(R,C), row_fill(R,8).

% Piazzare in (R,C) completerebbe la colonna C
would_complete_col(R,C) :- valid_placement(R,C), col_fill(C,8).
