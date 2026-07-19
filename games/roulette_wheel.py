"""European Roulette wheel layout, properties, and French announced bets.

The European roulette wheel has 37 slots (0-36) in a specific order.
This module provides:
- Wheel order and number properties (color, parity, half, dozen, column)
- French announced bets (Jeu 0, Voisins du Zéro, Tiers du Cylindre, Orphelins)
- Neighbors and opposite number lookup
- Interactive wheel visualization (Plotly donut chart) with highlighting
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

JEU_0: set[int] = {12, 35, 3, 26, 0, 32, 15}
VOISINS_DU_ZERO: set[int] = {
    22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15, 19, 4, 21, 2, 25,
}
TIERS_DU_CYLINDRE: set[int] = {
    27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33,
}
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


def get_opposite_zone(n: int, spread: int = 1) -> set[int]:
    """Return the opposite zone: the two opposite numbers plus their neighbors.

    With spread=1: returns the 2 opposite numbers + 1 neighbor on each side = 6 numbers.
    With spread=2: returns 2 opposite + 2 neighbors each side = 10 numbers.
    """
    if n not in WHEEL_ORDER:
        return set()
    opp_a, opp_b = get_opposite(n)
    zone: set[int] = {opp_a, opp_b}
    for count in range(1, spread + 1):
        for opp in (opp_a, opp_b):
            for nb in get_neighbors(opp, count):
                zone.add(nb)
    return zone


# ── Wheel visualization ──────────────────────────────────────────────

def build_wheel_figure(height: int = 500) -> "go.Figure":
    """Build a basic interactive European roulette wheel (no highlighting)."""
    return build_wheel_figure_highlighted(height=height)


def build_wheel_figure_highlighted(
    selected_number: Optional[int] = None,
    neighbor_count: int = 2,
    opposite_spread: int = 1,
    height: int = 550,
) -> "go.Figure":
    """Build an interactive roulette wheel with highlighted zones.

    Args:
        selected_number: The number to highlight (None = no highlight).
        neighbor_count: How many neighbors on each side to highlight.
        opposite_spread: How many neighbors around opposite numbers to highlight.
        height: Chart height in pixels.

    Highlights:
        - Selected number: thick white glow border + slight pull-out
        - Neighbors: gold/amber border
        - Opposite zone: cyan/blue border
    """
    import plotly.graph_objects as go

    # ── Compute highlight sets ────────────────────────────────────────
    highlight_pull: list[float] = [0.0] * 37
    line_colors: list[str] = ["white"] * 37
    line_widths: list[float] = [1.5] * 37
    hover_texts: list[str] = []
    slice_colors: list[str] = []

    neighbor_set: set[int] = set()
    opposite_set: set[int] = set()

    if selected_number is not None and selected_number in WHEEL_ORDER:
        neighbors = get_neighbors(selected_number, neighbor_count)
        neighbor_set = set(neighbors)
        opposite_set = get_opposite_zone(selected_number, opposite_spread)

    for i, n in enumerate(WHEEL_ORDER):
        c = get_color(n)
        if c == "green":
            slice_colors.append("#1a6b1a")
        elif c == "red":
            slice_colors.append("#c41e3a")
        else:
            slice_colors.append("#1a1a2e")

        # ── Highlighting ──────────────────────────────────────────────
        if selected_number is not None and n == selected_number:
            # Selected number: white glow, thick border, slight pull
            line_colors[i] = "#ffffff"
            line_widths[i] = 4.5
            highlight_pull[i] = 0.08
        elif n in neighbor_set:
            # Neighbors: gold border
            line_colors[i] = "#ffd700"
            line_widths[i] = 3.0
            highlight_pull[i] = 0.03
        elif n in opposite_set:
            # Opposite zone: cyan border
            line_colors[i] = "#00bcd4"
            line_widths[i] = 3.0
            highlight_pull[i] = 0.03

        # ── Hover text ────────────────────────────────────────────────
        nbs = get_neighbors(n, 2)
        opp = get_opposite(n)

        # Build role label
        roles: list[str] = []
        if selected_number is not None and n == selected_number:
            roles.append("🎯 SELECTED")
        if n in neighbor_set:
            roles.append("👥 Neighbor")
        if n in opposite_set:
            roles.append("🔄 Opposite zone")

        role_html = ""
        if roles:
            role_html = "<br>" + " | ".join(f"<b>{r}</b>" for r in roles)

        hover = (
            f"<b style='font-size:16px'>{n}</b>{role_html}<br>"
            f"<span style='color:{'#1a6b1a' if c == 'green' else '#c41e3a' if c == 'red' else '#888'}'>"
            f"{'🟢' if c == 'green' else '🔴' if c == 'red' else '⚫'} {c.title()}</span><br>"
            f"Parity: <b>{get_parity(n).title()}</b><br>"
            f"Half: <b>{get_half(n)}</b><br>"
            f"Dozen: <b>{get_dozen(n)}</b><br>"
            f"Column: <b>{get_column(n)}</b><br>"
            f"Section: <b>{get_section(n)}</b><br>"
            f"<br>← Neighbors →<br>"
            f"<b>{nbs[0]}, {nbs[1]}</b> ← <b>{n}</b> → <b>{nbs[2]}, {nbs[3]}</b><br>"
            f"<br>Opposite: <b>{opp[0]}, {opp[1]}</b>"
        )
        hover_texts.append(hover)

    # ── Build figure ──────────────────────────────────────────────────
    fig = go.Figure(
        go.Pie(
            labels=[str(n) for n in WHEEL_ORDER],
            values=[1] * 37,
            hole=0.48,
            marker=dict(
                colors=slice_colors,
                line=dict(color=line_colors, width=line_widths),
            ),
            pull=highlight_pull,
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

    # ── Legend annotations ───────────────────────────────────────────
    if selected_number is not None:
        legend_y = 0.02
        fig.add_annotation(
            text="<span style='color:#fff;background:#333;padding:2px 8px;border-radius:4px;"
                 "border:2px solid #fff'>⬜ Selected</span>",
            x=0.02, y=legend_y, xref="paper", yref="paper",
            showarrow=False, font=dict(size=11), align="left",
        )
        fig.add_annotation(
            text="<span style='color:#ffd700;background:#333;padding:2px 8px;border-radius:4px;"
                 "border:2px solid #ffd700'>🟡 Neighbors</span>",
            x=0.02, y=legend_y + 0.04, xref="paper", yref="paper",
            showarrow=False, font=dict(size=11), align="left",
        )
        fig.add_annotation(
            text="<span style='color:#00bcd4;background:#333;padding:2px 8px;border-radius:4px;"
                 "border:2px solid #00bcd4'>🔵 Opposite zone</span>",
            x=0.02, y=legend_y + 0.08, xref="paper", yref="paper",
            showarrow=False, font=dict(size=11), align="left",
        )

    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig
