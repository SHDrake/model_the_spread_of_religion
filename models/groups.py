from dataclasses import dataclass
from typing import Literal


@dataclass
class IdeologicalGroup:
    """
    Represents a single ideological / religious group in the spread model.

    Parameters
    ----------
    name : str
        Display name.
    feminism : float
        Position on the patriarchy–feminism spectrum.
        1 = fully patriarchal, 4 = fully feminist.
        Closer scores between groups → higher cross-group conversion compatibility.
    desire_to_infect : bool
        Whether the group actively proselytizes or recruits.
    infection_outcome : "convert" | "eliminate"
        On a successful "infection":
          - "convert"  → target individual joins this group.
          - "eliminate" → target individual is removed from the simulation pool.
    reproduction : float
        Total fertility rate (children per woman). 2.1 = replacement level.
    generational_immunity : int
        Resistance to conversion.  1 = current generation is fully susceptible.
        Higher values mean conversion is slower — identity is strongly transmitted
        across generations before outside ideologies take hold.
    """

    name: str
    feminism: float
    desire_to_infect: bool
    infection_outcome: Literal["convert", "eliminate"]
    reproduction: float
    generational_immunity: int


# ── Default parameter estimates (tunable via UI) ──────────────────────────────
DEFAULT_GROUPS: dict[str, IdeologicalGroup] = {
    "Christianity": IdeologicalGroup(
        name="Christianity",
        feminism=2.5,
        desire_to_infect=True,
        infection_outcome="convert",
        reproduction=2.3,
        generational_immunity=2,
    ),
    "Islam": IdeologicalGroup(
        name="Islam",
        feminism=1.5,
        desire_to_infect=True,
        infection_outcome="convert",
        reproduction=3.1,
        generational_immunity=1,
    ),
    "Secularism": IdeologicalGroup(
        name="Secularism",
        feminism=3.2,
        desire_to_infect=False,
        infection_outcome="convert",
        reproduction=1.6,
        generational_immunity=2,
    ),
    "Pridianism": IdeologicalGroup(
        name="Pridianism",
        feminism=4.0,
        desire_to_infect=True,
        infection_outcome="convert",
        reproduction=0.5,
        generational_immunity=3,
    ),
}

# ── Implicit "Others" reservoir (all remaining world population) ──────────────
# Not user-editable in the sidebar; acts as a susceptible pool for proselytising
# groups to draw from.  Feminism score is set to the midpoint (neutral).
OTHERS_GROUP = IdeologicalGroup(
    name="Others",
    feminism=2.5,
    desire_to_infect=False,
    infection_outcome="convert",
    reproduction=2.1,
    generational_immunity=1,
)
