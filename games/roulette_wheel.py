"""European Roulette wheel layout, properties, and French announced bets.

The European roulette wheel has 37 slots (0-36) in a specific order.
This module provides:
- Wheel order and number properties (color, parity, half, dozen, column)
- French announced bets (Jeu 0, Voisins du Zéro, Tiers du Cylindre, Orphelins)
- Neighbors and opposite number lookup
- Interactive wheel visualization (Plotly donut chart)
"""

from typing import Optional

# European roulette wheel order (clockwise, starting from 0 at top)
WHEEL_ORDER: list[int] = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23,
    10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26,
]

RED_NUMBERS: set[int] = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS: set[int] = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}

# ── French announced bets (les annonces) ──────────────────────────────

# Jeu 0 (Zero Game / Zero Spiel): 7 numbers around zero
JEU_0: set[int] = {12, 35, 3, 26, 0, 32, 15}

# Voisins du Zéro (Neighbors of Zero): 17 numbers — almost half the wheel
VOISINS_DU_ZERO: set[int] = {
    22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15, 19, 4, 21, 2, 25,
}

# Tiers du Cylindre (Thirds of the Wheel): 12 numbers opposite zero
TIERS_DU_CYLINDRE: set[int] = {
    27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33,
}

# Orphelins (Orphans): 8 numbers not in Voisins or Tiers
ORPHELINS: set[int] = {1, 20, 14, 31, 9, 17, 34, 6}


# ── Number properties ─────────────────────────────────────────────────

def get_color(n: int) -> str:
    """Return 'green', 'red', or 'black' for a roulette number."""
    if n == 0:
        return "green"
    return "red" if n in RED_NUMBERS else "black"


def get_parity(n: int) -> str:
    """Return 'even', 'odd', or '—' for zero."""
    if n == 0:
        return "—"
    return "even" if n % 2 == 0 else "odd"


def get_half(n: int) -> str:
    """Return 'low (1-18)', 'high (19-36)', or '—' for zero."""
    if n == 0:
        return "—"
    return "low (1-18)" if n <= 18 else "high (19-36)"


def get_dozen(n: int) -> str:
    """Return '1st 12', '2nd 12', '3rd 12', or '—' for zero."""
    if n == 0:
        return "—"
    d = (n - 1) // 12 + 1
    labels = {1: "1st 12", 2: "2nd 12", 3: "3rd 12"}
    return labels[d]


def get_column(n: int) -> str:
    """Return 'Column 1', 'Column 2', 'Column 3', or '—' for zero."""
    if n == 0:
        return "—"
    return f"Column {(n - 1) % 3 + 1}"


def get_section(n: int) -> str:
    """Return which French announced bet section the number belongs to."""
    if n in JEU_0:
        return "Jeu 0"
    if n in VOISINS_DU_ZERO:
        return "Voisins du Zéro"
    if n in TIERS_DU_CYLINDRE:
        return "Tiers du Cylindre"
    if n in ORPHELINS:
        return "Orphelins"
    return "—"


# ── Wheel geometry ───────────────────────────────────────────────────

def get_neighbors(n: int, count: int = 2) -> list[int]:
    """Return `count` neighbors on each side of `n` on the wheel.

    Returns [left_count, ..., left_1, right_1, ..., right_count]
    in wheel order (clockwise).
    """
    if n not in WHEEL_ORDER:
        return []
    idx = WHEEL_ORDER.index(n)
    result: list[int] = []
    for i in range(count, 0, -1):
        result.append(WHEEL_ORDER[(idx - i) % 37])
    for i in range(1, count + 1):
        result.append(WHEEL_ORDER[(idx + i) % 37])
    return result


def get_opposite(n: int) -> tuple[int, int]:
    """Return the two numbers roughly opposite `n` on the wheel.

    With 37 slots there is no exact opposite — returns the two
    numbers at positions +18 and +19 from `n`.
    """
    if n not in WHEEL_ORDER:
        return (0, 0)
    idx = WHEEL_ORDER.index(n)
    return (
        WHEEL_ORDER[(idx + 18) % 37],
        WHEEL_ORDER[(idx + 19) % 37],
    )


# ── Wheel visualization ──────────────────────────────────────────────

def build_wheel_figure(height: int = 500) -> "go.Figure":
    """Build an interactive European roulette wheel as a Plotly donut chart.

    Hover over any number to see all properties: color, parity, half,
    dozen, column, section, neighbors, and opposite numbers.
    """
    import plotly.graph_objects as go

    colors: list[str] = []
    hover_texts: list[str] = []

    for n in WHEEL_ORDER:
        c = get_color(n)
        if c == "green":
            colors.append("#1a6b1a")
        elif c == "red":
            colors.append("#c41e3a")
        else:
            colors.append("#1a1a2e")

        neighbors = get_neighbors(n, 2)
        opp = get_opposite(n)

        hover = (
            f"<b style='font-size:16px'>{n}</b><br>"
            f"<span style='color:{'#1a6b1a' if c == 'green' else '#c41e3a' if c == 'red' else '#888'}'>"
            f"{'🟢' if c == 'green' else '🔴' if c == 'red' else '⚫'} {c.title()}</span><br>"
            f"Parity: <b>{get_parity(n).title()}</b><br>"
            f"Half: <b>{get_half(n)}</b><br>"
            f"Dozen: <b>{get_dozen(n)}</b><br>"
            f"Column: <b>{get_column(n)}</b><br>"
            f"Section: <b>{get_section(n)}</b><br>"
            f"<br>← Neighbors →<br>"
            f"<b>{neighbors[0]}, {neighbors[1]}</b> ← <b>{n}</b> → <b>{neighbors[2]}, {neighbors[3]}</b><br>"
            f"<br>Opposite: <b>{opp[0]}, {opp[1]}</b>"
        )
        hover_texts.append(hover)

    fig = go.Figure(
        go.Pie(
            labels=[str(n) for n in WHEEL_ORDER],
            values=[1] * 37,
            hole=0.48,
            marker=dict(colors=colors, line=dict(color="white", width=1.5)),
            textinfo="label",
            textfont=dict(size=11, color="white", family="Arial Black"),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_texts,
            sort=False,
            direction="clockwise",
            rotation=90,
            showlegend=False,
        )
    )

    fig.add_annotation(
        text="🎰",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=36),
        xref="paper",
        yref="paper",
    )

    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig
