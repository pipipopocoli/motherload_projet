#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LEC Versus odds calculator (exact enumeration).
- Interactive "what-if" constraints: e.g. "KC>FNC, LR<G2, LR>SK"
- Computes P(target finishes Top K) under:
  (A) fair model: every undecided match is 50/50
  (B) strength model: p(team A beats B) derived from current record (Laplace-smoothed)

Tie-breaking implemented:
1) Head-to-head within tied group (mini-league score)
2) Strength of Victory (SoV): sum of final wins of opponents you beat
3) If still tied after SoV: treated as unresolved tie and split uniformly for cutoff math
NOTE: Official rules may also include time-based criteria; we don't have those, so we stop at (3).

No external dependencies. Python 3.9+ recommended.
"""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Iterable, Set

# -----------------------------
# League state (DEFAULT DATA)
# -----------------------------

TEAMS = [
    "Fnatic",
    "G2 Esports",
    "GIANTX",
    "Karmine Corp",
    "Karmine Corp Blue",
    "Los Ratones",
    "Movistar KOI",
    "Natus Vincere",
    "Shifters",
    "SK Gaming",
    "Team Heretics",
    "Team Vitality",
]

# Aliases for quick typing
ALIASES = {
    "FNC": "Fnatic",
    "G2": "G2 Esports",
    "GX": "GIANTX",
    "KC": "Karmine Corp",
    "KCB": "Karmine Corp Blue",
    "LR": "Los Ratones",
    "KOI": "Movistar KOI",
    "MKOI": "Movistar KOI",
    "NAVI": "Natus Vincere",
    "SHFT": "Shifters",
    "SK": "SK Gaming",
    "TH": "Team Heretics",
    "VIT": "Team Vitality",
}

# Played matches: list of (winner, loser)
# Built from the match list lines that have explicit scores (Week1/2 + played Week3 games so far).
PLAYED = [
    # Week3 (played entries with scores)
    ("Movistar KOI", "SK Gaming"),
    ("Team Vitality", "GIANTX"),
    ("Team Heretics", "Karmine Corp Blue"),
    ("Natus Vincere", "Shifters"),
    ("Los Ratones", "Movistar KOI"),
    ("Team Vitality", "Karmine Corp"),
    ("G2 Esports", "Karmine Corp Blue"),
    ("Shifters", "Fnatic"),
    ("GIANTX", "Natus Vincere"),
    ("SK Gaming", "Team Heretics"),

    # Week2
    ("GIANTX", "Movistar KOI"),
    ("Karmine Corp", "Natus Vincere"),
    ("G2 Esports", "Team Heretics"),
    ("Fnatic", "Team Vitality"),
    ("Los Ratones", "Shifters"),
    ("SK Gaming", "Karmine Corp Blue"),
    ("Karmine Corp", "G2 Esports"),
    ("Fnatic", "GIANTX"),
    ("Movistar KOI", "Karmine Corp Blue"),
    ("Los Ratones", "Team Heretics"),
    ("Natus Vincere", "SK Gaming"),
    ("Team Vitality", "Shifters"),
    ("Movistar KOI", "Fnatic"),
    ("Karmine Corp", "SK Gaming"),
    ("G2 Esports", "Shifters"),
    ("Team Heretics", "Team Vitality"),
    ("Natus Vincere", "Karmine Corp Blue"),
    ("GIANTX", "Los Ratones"),

    # Week1
    ("G2 Esports", "SK Gaming"),
    ("Karmine Corp", "Los Ratones"),
    ("Shifters", "Movistar KOI"),
    ("Team Heretics", "GIANTX"),
    ("Team Vitality", "Karmine Corp Blue"),
    ("Fnatic", "Natus Vincere"),
    ("Movistar KOI", "Karmine Corp"),
    ("GIANTX", "G2 Esports"),
    ("SK Gaming", "Fnatic"),
    ("Natus Vincere", "Team Vitality"),
    ("Karmine Corp Blue", "Los Ratones"),
    ("Shifters", "Team Heretics"),
    ("Movistar KOI", "G2 Esports"),
    ("Karmine Corp", "Karmine Corp Blue"),
    ("Team Vitality", "SK Gaming"),
    ("Natus Vincere", "Team Heretics"),
    ("GIANTX", "Shifters"),
    ("Fnatic", "Los Ratones"),
]

# Remaining matches (20) to complete the single round robin.
# If some already got played, you can either move them into PLAYED or just "set" them in the CLI.
REMAINING = [
    # Week3 "not yet scored" items
    ("Los Ratones", "G2 Esports"),
    ("Karmine Corp", "Fnatic"),
    ("Karmine Corp Blue", "Fnatic"),
    ("SK Gaming", "GIANTX"),
    ("Natus Vincere", "Los Ratones"),
    ("Team Vitality", "G2 Esports"),
    ("Team Heretics", "Movistar KOI"),
    ("Shifters", "Karmine Corp"),

    # Week4 (Feb 7–8)
    ("Fnatic", "Team Heretics"),
    ("Shifters", "Karmine Corp Blue"),
    ("SK Gaming", "Los Ratones"),
    ("G2 Esports", "Natus Vincere"),
    ("Team Vitality", "Movistar KOI"),
    ("Karmine Corp", "GIANTX"),

    ("Team Vitality", "Los Ratones"),
    ("GIANTX", "Karmine Corp Blue"),
    ("SK Gaming", "Shifters"),
    ("Natus Vincere", "Movistar KOI"),
    ("Karmine Corp", "Team Heretics"),
    ("G2 Esports", "Fnatic"),
]

# -----------------------------
# Core structures
# -----------------------------

@dataclass(frozen=True)
class Match:
    a: str
    b: str

    def key(self) -> Tuple[str, str]:
        return tuple(sorted((self.a, self.b)))

def canonical_team(s: str) -> Optional[str]:
    s = s.strip()
    if not s:
        return None
    s_up = s.upper()
    if s_up in ALIASES:
        return ALIASES[s_up]
    # try exact match (case sensitive)
    if s in TEAMS:
        return s
    # try case-insensitive match
    for t in TEAMS:
        if t.lower() == s.lower():
            return t
    return None

def build_pair_to_match_index(matches: List[Match]) -> Dict[Tuple[str, str], int]:
    d = {}
    for i, m in enumerate(matches):
        k = m.key()
        if k in d:
            raise ValueError(f"Duplicate match found for pair {k}: {matches[d[k]]} and {m}")
        d[k] = i
    return d

def initial_state_from_played(played: List[Tuple[str, str]]) -> Tuple[Dict[str, int], Dict[Tuple[str, str], str]]:
    """Return (wins, winner_by_pair) from played results."""
    wins = {t: 0 for t in TEAMS}
    winner_by_pair: Dict[Tuple[str, str], str] = {}
    for w, l in played:
        if w not in wins or l not in wins:
            raise ValueError(f"Unknown team in played result: {w} vs {l}")
        wins[w] += 1
        k = tuple(sorted((w, l)))
        if k in winner_by_pair:
            raise ValueError(f"Duplicate played result for pair {k}")
        winner_by_pair[k] = w
    return wins, winner_by_pair

def compute_strength_probs(base_wins: Dict[str, int], base_games: Dict[str, int], alpha: float = 1.0) -> Dict[str, float]:
    """Team 'strength' = smoothed winrate."""
    strength = {}
    for t in TEAMS:
        g = base_games[t]
        w = base_wins[t]
        strength[t] = (w + alpha) / (g + 2 * alpha)  # Laplace smoothing
    return strength

def p_win(model: str, strength: Dict[str, float], a: str, b: str) -> float:
    if model == "fair":
        return 0.5
    # "strength" model
    sa, sb = strength[a], strength[b]
    return sa / (sa + sb)

# -----------------------------
# Tie-break logic
# -----------------------------

def head_to_head_score(group: List[str], winner_by_pair: Dict[Tuple[str, str], str]) -> Dict[str, int]:
    """Mini-league H2H wins within 'group'."""
    s = {t: 0 for t in group}
    gset = set(group)
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            a, b = group[i], group[j]
            k = tuple(sorted((a, b)))
            w = winner_by_pair.get(k)
            if w is None:
                # should not happen in complete season, but if it does, treat as unknown => no H2H advantage
                continue
            if w in gset:
                s[w] += 1
    return s

def strength_of_victory(team: str, winner_by_pair: Dict[Tuple[str, str], str], final_wins: Dict[str, int]) -> int:
    """SoV: sum(final wins of opponents you beat)."""
    total = 0
    for opp in TEAMS:
        if opp == team:
            continue
        k = tuple(sorted((team, opp)))
        w = winner_by_pair.get(k)
        if w == team:
            total += final_wins[opp]
    return total

def break_tie(group: List[str], winner_by_pair: Dict[Tuple[str, str], str], final_wins: Dict[str, int]) -> List[List[str]]:
    """
    Returns a list of 'buckets' (each bucket is a list of teams).
    Order of buckets is determined; inside a bucket, teams are still tied after our criteria.
    """
    if len(group) <= 1:
        return [group[:]]

    # 1) H2H mini-league score
    h2h = head_to_head_score(group, winner_by_pair)
    by_h2h: Dict[int, List[str]] = {}
    for t in group:
        by_h2h.setdefault(h2h[t], []).append(t)
    h2h_levels = sorted(by_h2h.keys(), reverse=True)

    buckets: List[List[str]] = []
    for lvl in h2h_levels:
        tied = by_h2h[lvl]
        if len(tied) == 1:
            buckets.append(tied)
            continue

        # 2) SoV
        sov = {t: strength_of_victory(t, winner_by_pair, final_wins) for t in tied}
        by_sov: Dict[int, List[str]] = {}
        for t in tied:
            by_sov.setdefault(sov[t], []).append(t)
        sov_levels = sorted(by_sov.keys(), reverse=True)

        for s_lvl in sov_levels:
            tied2 = by_sov[s_lvl]
            buckets.append(tied2)  # still possibly tied -> unresolved bucket

    return buckets

def ordered_buckets(final_wins: Dict[str, int], winner_by_pair: Dict[Tuple[str, str], str]) -> List[List[str]]:
    """Sort by wins, then break ties into ordered buckets."""
    by_wins: Dict[int, List[str]] = {}
    for t, w in final_wins.items():
        by_wins.setdefault(w, []).append(t)

    win_levels = sorted(by_wins.keys(), reverse=True)
    buckets: List[List[str]] = []
    for w in win_levels:
        group = by_wins[w]
        if len(group) == 1:
            buckets.append(group)
        else:
            buckets.extend(break_tie(group, winner_by_pair, final_wins))
    return buckets

def prob_target_in_topk_from_buckets(buckets: List[List[str]], target: str, k: int) -> float:
    """
    If a bucket (unresolved tie) crosses the cutoff, split uniformly.
    """
    slots_used = 0
    for bucket in buckets:
        size = len(bucket)
        if slots_used >= k:
            return 0.0
        if slots_used + size <= k:
            # whole bucket is inside top-k
            if target in bucket:
                return 1.0
            slots_used += size
            continue

        # Bucket crosses cutoff: allocate remaining slots uniformly
        remaining = k - slots_used
        if target in bucket:
            return remaining / size
        return 0.0
    return 0.0

# -----------------------------
# Exact enumeration engine
# -----------------------------

def exact_probability_topk(
    target: str,
    k: int,
    model: str,
    matches: List[Match],
    base_wins: Dict[str, int],
    base_games: Dict[str, int],
    base_winner_by_pair: Dict[Tuple[str, str], str],
    fixed_winners: Dict[Tuple[str, str], str],
    alpha: float = 1.0,
) -> float:
    """
    Enumerate all undecided matches exactly, consistent with fixed_winners.
    """
    strength = compute_strength_probs(base_wins, base_games, alpha=alpha)

    # Prepare recursion over matches, skipping fixed
    undecided: List[Match] = []
    fixed_local: Dict[Tuple[str, str], str] = {}

    for m in matches:
        kpair = m.key()
        if kpair in base_winner_by_pair:
            # already played; ignore
            continue
        if kpair in fixed_winners:
            fixed_local[kpair] = fixed_winners[kpair]
        else:
            undecided.append(m)

    # Start from base + fixed results applied
    wins0 = dict(base_wins)
    winner_by_pair0 = dict(base_winner_by_pair)

    for m in matches:
        kpair = m.key()
        if kpair in fixed_local and kpair not in winner_by_pair0:
            w = fixed_local[kpair]
            a, b = m.a, m.b
            l = b if w == a else a
            wins0[w] += 1
            winner_by_pair0[kpair] = w

    def rec(i: int, wins: Dict[str, int], winner_by_pair: Dict[Tuple[str, str], str], weight: float) -> float:
        if i == len(undecided):
            buckets = ordered_buckets(wins, winner_by_pair)
            pt = prob_target_in_topk_from_buckets(buckets, target, k)
            return weight * pt

        m = undecided[i]
        a, b = m.a, m.b
        kpair = m.key()

        p_a = p_win(model, strength, a, b)

        # Branch: a wins
        wins[a] += 1
        winner_by_pair[kpair] = a
        out_a = rec(i + 1, wins, winner_by_pair, weight * p_a)
        wins[a] -= 1
        del winner_by_pair[kpair]

        # Branch: b wins
        wins[b] += 1
        winner_by_pair[kpair] = b
        out_b = rec(i + 1, wins, winner_by_pair, weight * (1.0 - p_a))
        wins[b] -= 1
        del winner_by_pair[kpair]

        return out_a + out_b

    return rec(0, wins0, winner_by_pair0, 1.0)

# -----------------------------
# CLI
# -----------------------------

def compute_base_games(played: List[Tuple[str, str]]) -> Dict[str, int]:
    g = {t: 0 for t in TEAMS}
    for w, l in played:
        g[w] += 1
        g[l] += 1
    return g

def parse_constraints(s: str, pair_index: Dict[Tuple[str, str], int], matches: List[Match]) -> Dict[Tuple[str, str], str]:
    """
    Parse constraints like: "KC>FNC, LR<G2, VIT>KOI"
    Returns dict pair->winner
    """
    s = s.strip()
    if not s:
        return {}

    parts = re.split(r"[,\s]+", s)
    out: Dict[Tuple[str, str], str] = {}
    for token in parts:
        token = token.strip()
        if not token:
            continue
        if ">" in token:
            left, right = token.split(">", 1)
            A = canonical_team(left)
            B = canonical_team(right)
            if not A or not B:
                raise ValueError(f"Équipe inconnue dans: {token}")
            winner = A
        elif "<" in token:
            left, right = token.split("<", 1)
            A = canonical_team(left)
            B = canonical_team(right)
            if not A or not B:
                raise ValueError(f"Équipe inconnue dans: {token}")
            winner = B
        else:
            raise ValueError(f"Format invalide: {token} (utilise A>B ou A<B)")

        kpair = tuple(sorted((A, B)))
        if kpair not in pair_index:
            raise ValueError(f"Match introuvable dans la liste restante: {A} vs {B}")
        out[kpair] = winner
    return out

def pretty_match(m: Match) -> str:
    return f"{m.a} vs {m.b}"

def main():
    target = "Los Ratones"
    cutoff = 8
    model = "fair"        # "fair" or "strength"
    alpha = 1.0

    # Build matches list as Match objects
    matches = [Match(a, b) for a, b in REMAINING]
    pair_index = build_pair_to_match_index(matches)

    base_wins, base_winner_by_pair = initial_state_from_played(PLAYED)
    base_games = compute_base_games(PLAYED)

    fixed: Dict[Tuple[str, str], str] = {}

    print("\nLEC Versus odds CLI")
    print("------------------")
    print(f"Target: {target} | Cutoff: Top {cutoff} | Model: {model}")
    print("Tape 'help' pour l'aide.\n")

    def do_compute():
        p = exact_probability_topk(
            target=target,
            k=cutoff,
            model=model,
            matches=matches,
            base_wins=base_wins,
            base_games=base_games,
            base_winner_by_pair=base_winner_by_pair,
            fixed_winners=fixed,
            alpha=alpha,
        )
        print(f"→ P(Top {cutoff} | contraintes) = {100.0*p:.2f}%")

    def do_list():
        print("\nMatchs restants (numérotés) :")
        for i, m in enumerate(matches):
            kpair = m.key()
            tag = ""
            if kpair in fixed:
                tag = f"  [fixé: {fixed[kpair]} gagne]"
            print(f"{i:02d}. {pretty_match(m)}{tag}")
        print("")

    def do_impact(a: str, b: str):
        A = canonical_team(a)
        B = canonical_team(b)
        if not A or not B:
            print("Équipe inconnue.")
            return
        kpair = tuple(sorted((A, B)))
        if kpair not in pair_index:
            print(f"Match {A} vs {B} introuvable (pas dans REMAINING).")
            return

        # save/restore
        old = dict(fixed)

        fixed[kpair] = A
        pA = exact_probability_topk(target, cutoff, model, matches, base_wins, base_games, base_winner_by_pair, fixed, alpha)
        fixed[kpair] = B
        pB = exact_probability_topk(target, cutoff, model, matches, base_wins, base_games, base_winner_by_pair, fixed, alpha)

        fixed.clear()
        fixed.update(old)

        print(f"Impact {A} vs {B} (sur {target} Top {cutoff}):")
        print(f"- si {A} gagne: {100*pA:.2f}%")
        print(f"- si {B} gagne: {100*pB:.2f}%")
        print(f"- différence: {100*(pA - pB):+.2f} points")

    while True:
        try:
            cmd = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not cmd:
            continue

        low = cmd.lower()

        if low in ("q", "quit", "exit"):
            print("Bye.")
            break

        if low == "help":
            print("""
Commandes:
  list
    -> affiche les matchs restants + tes contraintes fixées

  compute
    -> calcule P(target Top8) avec les contraintes actuelles

  clear
    -> enlève toutes les contraintes

  model fair
  model strength
    -> change le modèle (50/50 ou basé sur les records actuels)

  impact KC vs FNC
  impact LR vs G2
    -> compare les % si A gagne vs si B gagne

  (raccourci spammable)
    Tape une ligne d'hypothèses:  KC>FNC, LR<G2, LR>SK
    - '>' = l'équipe de gauche gagne
    - '<' = l'équipe de droite gagne
    - alias: LR, G2, KC, FNC, SK, VIT, KOI, NAVI, GX, KCB, TH, SHFT

Exemples:
  KC>FNC, LR<G2
  LR>SK, LR>VIT
  impact KC vs FNC
""")
            continue

        if low == "list":
            do_list()
            continue

        if low == "compute":
            do_compute()
            continue

        if low == "clear":
            fixed.clear()
            print("OK: contraintes effacées.")
            continue

        if low.startswith("model "):
            parts = cmd.split()
            if len(parts) != 2:
                print("Ex: model fair  |  model strength")
                continue
            m = parts[1].strip().lower()
            if m not in ("fair", "strength"):
                print("Modèle inconnu. Choisis: fair | strength")
                continue
            model = m
            print(f"OK: model = {model}")
            continue

        if low.startswith("impact "):
            # impact A vs B
            m = re.match(r"impact\s+(.+?)\s+vs\s+(.+)$", cmd, flags=re.IGNORECASE)
            if not m:
                print("Format: impact A vs B")
                continue
            do_impact(m.group(1), m.group(2))
            continue

        # Otherwise, treat as constraints line
        try:
            new = parse_constraints(cmd, pair_index, matches)
            # merge (latest overwrites)
            fixed.update(new)
            do_compute()
        except Exception as e:
            print(f"Erreur: {e}")
            print("Tape 'help' pour voir les formats acceptés.")

if __name__ == "__main__":
    main()
