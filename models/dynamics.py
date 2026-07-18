"""
dynamics.py — Epidemic-style ideological spread simulation.

Each generation (40 years) proceeds in two phases:
  1. Biological reproduction   — each group grows by its fertility multiplier.
  2. Ideological infection      — mass-action spread between groups.

The core infection term is the classic SIR mass-action contact rate:

    converted = β · compat(src, tgt) · immunity(tgt) · P_src · P_tgt / N

where:
  β          = base transmission rate (global tuning knob)
  compat     = 1 / (1 + |feminism_src − feminism_tgt|)   ∈ (0, 1]
  immunity   = 1 / generational_immunity                  ∈ (0, 1]
  P_src      = population of source group at time t
  P_tgt      = population of target group at time t
  N          = total population at time t
"""

from __future__ import annotations

import numpy as np

REPLACEMENT_RATE: float = 2.1  # children per woman for stable population


# ── Helper functions ──────────────────────────────────────────────────────────

def feminism_compatibility(f_src: float, f_tgt: float) -> float:
    """
    Cross-group conversion compatibility based on feminism-score proximity.

    Groups with similar cultural positions convert each other more easily.
    Returns a value in (0, 1]; maximum 1.0 when scores are identical.
    """
    return 1.0 / (1.0 + abs(f_src - f_tgt))


def _to_shares(pops: dict[str, float]) -> dict[str, float]:
    total = sum(pops.values()) or 1.0
    return {k: v / total for k, v in pops.items()}


# ── Main simulation ───────────────────────────────────────────────────────────

def simulate(
    groups: dict,           # dict[str, IdeologicalGroup]
    initial_pops: dict,     # dict[str, float]  — fractional or absolute
    n_generations: int,
    base_rate: float = 0.15,
) -> list[dict[str, float]]:
    """
    Run the ideological spread model for *n_generations* time steps.

    Parameters
    ----------
    groups : dict[str, IdeologicalGroup]
        All groups to simulate (including the "Others" reservoir).
    initial_pops : dict[str, float]
        Starting population (fractional shares that need not sum to 1).
    n_generations : int
        Number of 40-year generations to simulate.
    base_rate : float
        Global transmission rate β.  Typical range 0.05–0.5.

    Returns
    -------
    list of dicts, length n_generations + 1.
    Each dict maps group name → population SHARE at that time step (generation 0
    is the initial state).
    """
    pops = {k: float(v) for k, v in initial_pops.items()}
    history: list[dict[str, float]] = [_to_shares(pops)]

    for _ in range(n_generations):
        # ── Phase 1: Biological reproduction ─────────────────────────────────
        new_pops: dict[str, float] = {}
        for name, group in groups.items():
            repro_factor = group.reproduction / REPLACEMENT_RATE
            new_pops[name] = pops[name] * repro_factor

        total = sum(pops.values()) or 1.0

        # ── Phase 2: Ideological infection (mass-action) ──────────────────────
        for src_name, src in groups.items():
            if not src.desire_to_infect:
                continue

            for tgt_name, tgt in groups.items():
                if src_name == tgt_name:
                    continue
                if pops[tgt_name] <= 0.0:
                    continue

                compat = feminism_compatibility(src.feminism, tgt.feminism)
                immunity = 1.0 / tgt.generational_immunity

                converted = (
                    base_rate
                    * compat
                    * immunity
                    * pops[src_name]
                    * pops[tgt_name]
                    / total
                )
                # Hard caps: never convert more than is present or available
                converted = min(converted, new_pops.get(tgt_name, 0.0))
                converted = max(converted, 0.0)

                if src.infection_outcome == "convert":
                    new_pops[src_name] = new_pops.get(src_name, 0.0) + converted
                    new_pops[tgt_name] = new_pops.get(tgt_name, 0.0) - converted
                else:  # "eliminate"
                    new_pops[tgt_name] = new_pops.get(tgt_name, 0.0) - converted

        # Clamp negatives (numerical safety)
        pops = {k: max(0.0, v) for k, v in new_pops.items()}
        history.append(_to_shares(pops))

    return history


def find_dominance_year(
    sim_df,             # pd.DataFrame — index=years, columns=group names
    group_name: str,
    threshold: float = 0.50,
) -> int | None:
    """Return the first year in sim_df where group_name reaches *threshold* share."""
    col = sim_df[group_name]
    dominant = col[col >= threshold]
    return int(dominant.index[0]) if not dominant.empty else None
