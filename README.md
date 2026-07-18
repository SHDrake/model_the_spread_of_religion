# Modeling the Spread of Religion

A generational epidemic-style simulation of the ideological spread of **Christianity**, **Islam**, **Secularism**, and **Pridianism** (LGBTQ+ identity and culture), modeled as competing "strains" of belief across a shared population.

---

## Overview

This project applies a modified viral-disease model to ideological and religious demographic change. Each ideological group is characterized by a set of epidemiological-style parameters that govern how it spreads, competes, and reproduces across generations.

The model is validated against approximately 120 years of historical data (roughly 4 generations, ~1906–2026) and then projected forward to estimate at what point — if ever — each ideological group achieves demographic dominance.

---

## The Model

### Analogy

| Epidemiology     | This Model                              |
|------------------|-----------------------------------------|
| Pathogen strain  | Ideological / religious group           |
| Host population  | Individuals in a shared society         |
| Infection        | Conversion or adoption of an ideology   |
| Immunity         | Resistance to conversion (generational) |
| Reproduction     | Biological population growth            |
| Time step        | One generation (40 years)               |

### Parameters

Each ideological group is assigned the following parameters:

| Parameter             | Type       | Description |
|-----------------------|------------|-------------|
| `feminism`            | `float`    | Position on the patriarchy–feminism spectrum. **1** = fully patriarchal, **4** = fully feminist. Affects both internal reproduction rates and cross-group conversion susceptibility. |
| `desire_to_infect`    | `bool`     | Whether the group actively proselytizes or recruits (True/False). |
| `infection_outcome`   | `str`      | What happens on successful "infection": `"convert"` (target adopts the group's ideology) or `"eliminate"` (target is suppressed/removed from competition). |
| `reproduction`        | `float`    | Expected biological population growth multiplier per generation (e.g., 2.1 children per woman ≈ replacement). |
| `generational_immunity` | `int`   | At which generation conversion is expected. **1** = current generation is susceptible; **2** = children's generation; **3** = grandchildren's, etc. Higher values indicate strong within-group identity retention. |
| `time`                | `int`      | Time step unit. Each generation = **40 years**. |

### Groups & Default Parameter Estimates

| Group          | `feminism` | `desire_to_infect` | `infection_outcome` | `reproduction` | `generational_immunity` |
|----------------|------------|--------------------|---------------------|----------------|--------------------------|
| Christianity   | 2.5        | True               | convert             | 2.0            | 2                        |
| Islam          | 1.5        | True               | convert             | 3.0            | 1                        |
| Secularism     | 3.2        | False              | convert             | 1.5            | 2                        |
| Pridianism     | 4.0        | True               | convert             | 0.8            | 3                        |

> **Note:** These are initial estimates subject to calibration during the validation phase. All parameters are tunable.

### Dynamics

At each time step (generation):

1. **Reproduction** — each group grows its base population by its `reproduction` multiplier.
2. **Proselytization** — groups with `desire_to_infect = True` attempt to convert susceptible individuals from other groups. Susceptibility is modulated by the interaction between the source group's `feminism` score and the target group's `feminism` score (alignment increases conversion rate).
3. **Generational immunity** — individuals within a group with `generational_immunity > 1` are resistant to conversion for the indicated number of generations; conversion begins to occur in later generations.
4. **Infection outcome** — a successful "infection" either converts the target (population transfers to source group) or eliminates the target (population is removed from all groups).
5. **Normalization** — total population fractions are recalculated.

---

## Validation

The model is calibrated and validated against the **past 4 generations (~1906–2026)**:

| Generation | Approximate Year |
|------------|-----------------|
| G-4        | ~1906            |
| G-3        | ~1946            |
| G-2        | ~1986            |
| G-1        | ~2026 (present)  |

Validation targets include global or regional share-of-population data for each group at each generation. The model parameters are tuned until simulated trajectories match observed demographic trends within an acceptable error threshold.

**Data sources** (to be integrated):
- Pew Research Center global religious composition data
- UN World Population Prospects fertility rates
- LGBTQ+ demographic surveys (Gallup, Williams Institute)

---

## Projection

After validation, parameters can be varied to answer questions such as:

- What happens if Islam's reproduction rate declines to replacement level?
- At what point does Secularism's lack of proselytization cause long-term decline despite low fertility?
- Under what feminism-score configuration does Pridianism achieve sustained growth despite low biological reproduction?
- **At what point does each group take over?** (i.e., reach >50% of the modeled population)

---

## Repository Structure

```
model_the_spread_of_religion/
├── README.md
├── LICENSE
├── .gitignore
├── data/
│   ├── raw/                  # Historical demographic data
│   └── processed/            # Cleaned, generation-binned data
├── models/
│   ├── base_model.py         # Core epidemic model class
│   ├── groups.py             # Parameter definitions for each group
│   └── dynamics.py           # Time-step simulation logic
├── validation/
│   ├── calibrate.py          # Parameter fitting against historical data
│   └── validate.py           # Error metrics and validation plots
├── projection/
│   ├── scenarios.py          # Scenario definitions (variable sweeps)
│   └── project.py            # Forward projection runner
├── notebooks/
│   ├── 01_model_overview.ipynb
│   ├── 02_validation.ipynb
│   └── 03_projections.ipynb
├── results/
│   └── figures/
└── requirements.txt
```

---

## Getting Started

### Requirements

- Python 3.10+
- See `requirements.txt` for dependencies (numpy, pandas, matplotlib, scipy)

### Installation

```bash
git clone https://github.com/your-username/model_the_spread_of_religion.git
cd model_the_spread_of_religion
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the Model

```bash
# Validate model against historical data
python validation/validate.py

# Run forward projections
python projection/project.py

# Launch interactive notebooks
jupyter lab notebooks/
```

---

## License

MIT — see [LICENSE](LICENSE).

---

## Disclaimer

This project is a **quantitative demographic modeling exercise**. The epidemic metaphor is a mathematical abstraction and does not reflect any normative judgment about the groups modeled. All parameter values are empirically motivated and subject to revision.
