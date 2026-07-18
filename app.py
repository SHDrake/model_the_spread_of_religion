"""
app.py — Streamlit webapp for the Ideological Spread Model.

Run with:
    streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from models.dynamics import REPLACEMENT_RATE, find_dominance_year, simulate
from models.groups import DEFAULT_GROUPS, OTHERS_GROUP, IdeologicalGroup

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ideological Spread Model",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────
START_YEAR = 1906
GEN_YEARS = 40
N_HIST = 3  # historical generations: 1906 → 1946 → 1986 → 2026

GROUP_COLORS = {
    "Christianity": "#3B82F6",
    "Islam":        "#10B981",
    "Secularism":   "#F59E0B",
    "Pridianism":   "#EC4899",
    "Others":       "#9CA3AF",
}

# Approximate global share data from Pew Research, UN, Gallup.
# Used for validation only — not directly fitted.
HISTORICAL: dict[str, list[float]] = {
    "Christianity": [0.340, 0.335, 0.330, 0.310],
    "Islam":        [0.121, 0.135, 0.190, 0.250],
    "Secularism":   [0.005, 0.020, 0.100, 0.160],
    "Pridianism":   [0.001, 0.002, 0.010, 0.055],
}
HIST_YEARS = [1906, 1946, 1986, 2026]

DEFAULT_INIT_SHARES = {
    "Christianity": 0.340,
    "Islam":        0.121,
    "Secularism":   0.005,
    "Pridianism":   0.001,
}


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("Model Controls")

st.sidebar.header("Global Parameters")
base_rate = st.sidebar.slider(
    "Base transmission rate (β)",
    min_value=0.01, max_value=1.0, value=0.15, step=0.01,
    help=(
        "Controls how aggressively ideologies spread per generation. "
        "Higher β = faster spread. Typical range: 0.05–0.40."
    ),
)
n_future = st.sidebar.slider(
    "Future generations to project",
    min_value=1, max_value=20, value=8,
    help="Each generation = 40 years.  8 generations → year 2346.",
)

st.sidebar.divider()
st.sidebar.header("Group Parameters")
st.sidebar.caption(
    "Adjust each group's parameters. Initial share sets their fraction of the "
    "global population in 1906. The remainder goes to 'Others' (non-modelled groups)."
)


def group_sidebar(name: str, defaults: IdeologicalGroup, default_share: float):
    """Render sidebar controls for one ideological group. Returns (group, init_share)."""
    color = GROUP_COLORS[name]
    header_html = (
        f"<span style='color:{color}; font-weight:700; font-size:1.05rem;'>{name}</span>"
    )
    with st.sidebar.expander(name, expanded=False):
        st.markdown(header_html, unsafe_allow_html=True)
        feminism = st.slider(
            "Feminism score  (1 = patriarchal → 4 = feminist)",
            1.0, 4.0, float(defaults.feminism), 0.1, key=f"{name}_fem",
        )
        desire = st.checkbox(
            "Proselytises / actively spreads",
            value=defaults.desire_to_infect, key=f"{name}_des",
        )
        outcome = st.selectbox(
            "Infection outcome",
            ["convert", "eliminate"],
            index=0 if defaults.infection_outcome == "convert" else 1,
            key=f"{name}_out",
            help='"convert" moves people into this group; "eliminate" removes them entirely.',
        )
        repro = st.slider(
            "Total fertility rate",
            0.3, 6.0, float(defaults.reproduction), 0.1, key=f"{name}_rep",
            help="Children per woman. 2.1 = replacement level.",
        )
        gen_imm = st.slider(
            "Generational immunity",
            1, 6, defaults.generational_immunity, key=f"{name}_gi",
            help=(
                "How resistant members are to conversion. "
                "1 = current generation fully susceptible; "
                "higher values mean identity is strongly inherited."
            ),
        )
        init_share = st.slider(
            "Initial share (1906)",
            0.001, 0.60, default_share, 0.001,
            key=f"{name}_share", format="%.3f",
        )

    group = IdeologicalGroup(
        name=name,
        feminism=feminism,
        desire_to_infect=desire,
        infection_outcome=outcome,
        reproduction=repro,
        generational_immunity=gen_imm,
    )
    return group, init_share


groups: dict[str, IdeologicalGroup] = {}
init_shares: dict[str, float] = {}

for g_name, g_defaults in DEFAULT_GROUPS.items():
    g, s = group_sidebar(g_name, g_defaults, DEFAULT_INIT_SHARES[g_name])
    groups[g_name] = g
    init_shares[g_name] = s

# "Others" fills the remainder — not exposed in UI
others_share = max(0.001, 1.0 - sum(init_shares.values()))
groups["Others"] = OTHERS_GROUP
init_shares["Others"] = others_share

# ── Run simulation ────────────────────────────────────────────────────────────
total_gens = N_HIST + n_future
all_years = [START_YEAR + i * GEN_YEARS for i in range(total_gens + 1)]
hist_years = all_years[: N_HIST + 1]          # 1906 … 2026
proj_years = all_years[N_HIST:]               # 2026 … future

results = simulate(groups, init_shares, total_gens, base_rate)
sim_df = pd.DataFrame(results, index=all_years)

# ── Page header ───────────────────────────────────────────────────────────────
st.title("Modeling the Spread of Ideology")
st.markdown(
    "An epidemic-style generational model of how **Christianity**, **Islam**, "
    "**Secularism**, and **Pridianism** compete for global share across time.  "
    "Each time step = one generation (40 years).  Adjust parameters in the sidebar."
)

# Summary metrics row
col_c, col_i, col_s, col_p, col_o = st.columns(5)
for col, name in zip([col_c, col_i, col_s, col_p, col_o], [*DEFAULT_GROUPS.keys(), "Others"]):
    current = sim_df.loc[all_years[N_HIST], name] * 100
    initial = sim_df.loc[all_years[0], name] * 100
    col.metric(
        label=name,
        value=f"{current:.1f}%",
        delta=f"{current - initial:+.1f}pp since 1906",
    )

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_val, tab_proj, tab_params, tab_data = st.tabs(
    ["📊 Validation (1906–2026)", "🔭 Projections", "⚙️ Parameter Explorer", "📋 Data"]
)

# ────────────────────────────────────────────────────────────────────────────
# TAB 1 — Validation
# ────────────────────────────────────────────────────────────────────────────
with tab_val:
    st.subheader("Model vs. Historical Data  (1906 – 2026)")
    st.caption(
        "Solid lines = model output.  Open circle markers = approximate observed data "
        "(Pew Research, Gallup, UN estimates).  Tune parameters in the sidebar to improve fit."
    )

    fig_val = go.Figure()
    for name in DEFAULT_GROUPS:
        color = GROUP_COLORS[name]
        # Model line
        fig_val.add_trace(go.Scatter(
            x=hist_years,
            y=(sim_df.loc[hist_years, name] * 100).tolist(),
            mode="lines",
            name=f"{name} (model)",
            line=dict(color=color, width=2.5),
        ))
        # Historical markers
        fig_val.add_trace(go.Scatter(
            x=HIST_YEARS,
            y=[v * 100 for v in HISTORICAL[name]],
            mode="markers",
            name=f"{name} (observed)",
            marker=dict(color=color, size=11, symbol="circle-open",
                        line=dict(width=2.5, color=color)),
            showlegend=True,
        ))

    fig_val.update_layout(
        yaxis_title="Global Share (%)",
        xaxis_title="Year",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        height=460,
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig_val, use_container_width=True)

    # RMSE per group
    st.subheader("Validation Error (RMSE)")
    err_cols = st.columns(len(DEFAULT_GROUPS))
    for col, name in zip(err_cols, DEFAULT_GROUPS):
        sim_vals = np.array([sim_df.loc[yr, name] for yr in HIST_YEARS])
        hist_vals = np.array(HISTORICAL[name])
        rmse = float(np.sqrt(np.mean((sim_vals - hist_vals) ** 2)))
        col.metric(name, f"{rmse:.4f}", help="Lower = better fit to historical data.")

    st.info(
        "**Note:** Historical shares for Pridianism (LGBTQ+ identity) are estimates "
        "from survey data and carry significant uncertainty, especially pre-1986.",
        icon="ℹ️",
    )


# ────────────────────────────────────────────────────────────────────────────
# TAB 2 — Projections
# ────────────────────────────────────────────────────────────────────────────
with tab_proj:
    end_year = 2026 + n_future * GEN_YEARS
    st.subheader(f"Forward Projection  (2026 → {end_year})")

    fig_proj = go.Figure()
    for name in DEFAULT_GROUPS:
        color = GROUP_COLORS[name]
        y_vals = (sim_df.loc[proj_years, name] * 100).tolist()
        fig_proj.add_trace(go.Scatter(
            x=proj_years,
            y=y_vals,
            mode="lines+markers",
            name=name,
            line=dict(color=color, width=2.5),
            marker=dict(size=7),
        ))

    fig_proj.add_hline(
        y=50, line_dash="dash", line_color="#6B7280",
        annotation_text="50 % — majority", annotation_position="bottom right",
    )
    fig_proj.update_layout(
        yaxis_title="Global Share (%)",
        xaxis_title="Year",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        height=460,
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig_proj, use_container_width=True)

    # Dominance summary
    st.subheader("Dominance Analysis")
    dom_cols = st.columns(len(DEFAULT_GROUPS))
    for col, name in zip(dom_cols, DEFAULT_GROUPS):
        yr = find_dominance_year(sim_df.loc[proj_years], name, threshold=0.50)
        if yr is not None:
            col.metric(name, f"Dominant by {yr}",
                       delta=f"+{yr - 2026} yrs from now", delta_color="normal")
        else:
            peak = float(sim_df.loc[proj_years, name].max() * 100)
            final = float(sim_df.loc[proj_years[-1], name] * 100)
            delta_val = final - float(sim_df.loc[proj_years[0], name] * 100)
            col.metric(
                name,
                f"Peak {peak:.1f}%",
                delta=f"{delta_val:+.1f}pp over window",
                delta_color="normal",
            )

    # Stacked area chart showing full picture including Others
    st.subheader("Population Share — Stacked View (all groups)")
    fig_stack = go.Figure()
    all_names = [*DEFAULT_GROUPS.keys(), "Others"]
    for name in reversed(all_names):
        color = GROUP_COLORS[name]
        fig_stack.add_trace(go.Scatter(
            x=all_years,
            y=(sim_df[name] * 100).tolist(),
            mode="lines",
            name=name,
            stackgroup="one",
            line=dict(width=0.5, color=color),
            fillcolor=color,
        ))
    fig_stack.add_vline(
        x=2026, line_dash="dot", line_color="white",
        annotation_text="2026 (present)", annotation_position="top left",
    )
    fig_stack.update_layout(
        yaxis_title="Population Share (%)",
        xaxis_title="Year",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        height=400,
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig_stack, use_container_width=True)


# ────────────────────────────────────────────────────────────────────────────
# TAB 3 — Parameter Explorer
# ────────────────────────────────────────────────────────────────────────────
with tab_params:
    st.subheader("Current Parameter Summary")
    st.caption("Values reflect what you have set in the sidebar.")

    param_rows = []
    for name, g in groups.items():
        if name == "Others":
            continue
        param_rows.append({
            "Group": name,
            "Feminism (1–4)": g.feminism,
            "Proselytises": "Yes" if g.desire_to_infect else "No",
            "Infection Outcome": g.infection_outcome,
            "Fertility Rate": g.reproduction,
            "Gen. Immunity": g.generational_immunity,
            "Initial Share (1906)": f"{init_shares[name]:.3f}",
        })
    param_df = pd.DataFrame(param_rows).set_index("Group")
    st.dataframe(param_df, use_container_width=True)

    st.divider()
    st.subheader("Feminism Compatibility Matrix")
    st.caption(
        "How easily can each group's ideology spread to another?  "
        "Computed as 1 / (1 + |f_src − f_tgt|).  Diagonal = self (N/A)."
    )

    group_names_main = list(DEFAULT_GROUPS.keys())
    compat_data = {}
    for src in group_names_main:
        row = {}
        for tgt in group_names_main:
            if src == tgt:
                row[tgt] = "—"
            else:
                f_src = groups[src].feminism
                f_tgt = groups[tgt].feminism
                val = 1.0 / (1.0 + abs(f_src - f_tgt))
                row[tgt] = f"{val:.3f}"
        compat_data[src] = row
    compat_df = pd.DataFrame(compat_data).T
    compat_df.index.name = "Source →"
    st.dataframe(compat_df, use_container_width=True)

    st.divider()
    st.subheader("Generation Timeline")
    gen_rows = [
        {"Generation": f"G{i}", "Year": START_YEAR + i * GEN_YEARS,
         "Phase": "Historical" if i <= N_HIST else "Projected"}
        for i in range(total_gens + 1)
    ]
    st.dataframe(pd.DataFrame(gen_rows).set_index("Generation"), use_container_width=True)


# ────────────────────────────────────────────────────────────────────────────
# TAB 4 — Raw Data
# ────────────────────────────────────────────────────────────────────────────
with tab_data:
    st.subheader("Full Simulation Output")
    display_df = (sim_df * 100).round(3).copy()
    display_df.index.name = "Year"
    display_df.columns = [f"{c} (%)" for c in display_df.columns]
    st.dataframe(display_df, use_container_width=True)

    csv = display_df.to_csv()
    st.download_button(
        label="⬇️ Download as CSV",
        data=csv,
        file_name="ideological_spread_simulation.csv",
        mime="text/csv",
    )

    st.divider()
    st.subheader("Historical Reference Data")
    hist_display = pd.DataFrame(HISTORICAL, index=HIST_YEARS)
    hist_display.index.name = "Year"
    hist_display = (hist_display * 100).round(2)
    hist_display.columns = [f"{c} (%)" for c in hist_display.columns]
    st.dataframe(hist_display, use_container_width=True)
    st.caption(
        "Sources: Pew Research Center Global Religious Landscape, "
        "Gallup LGBTQ+ identification surveys, UN World Population Prospects. "
        "All figures are estimates and subject to uncertainty."
    )
