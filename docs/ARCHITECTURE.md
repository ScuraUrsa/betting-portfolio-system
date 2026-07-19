# Betting Portfolio System — Full Documentation

> **Version**: 0.2.0 | **License**: MIT | **Python**: 3.10+
> **Repository**: https://github.com/ScuraUrsa/betting-portfolio-system

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Installation & Quick Start](#3-installation--quick-start)
4. [Core Modules API](#4-core-modules-api)
5. [Game Implementations](#5-game-implementations)
6. [Streamlit UI](#6-streamlit-ui)
7. [Testing](#7-testing)
8. [Extending the System](#8-extending-the-system)
9. [Mathematical Background](#9-mathematical-background)
10. [Configuration Reference](#10-configuration-reference)

---

## 1. Overview

The Betting Portfolio System is a **game-agnostic betting portfolio optimization engine**. It does not try to predict which individual bet will win. Instead, it answers:

> *"How should I distribute my capital across all available bets, considering local extremes, mean reversion, correlations between bets, and the expected profit/risk profile of the entire portfolio?"*

### Key Features

| Feature | Description |
|---------|-------------|
| **Game-agnostic** | Works for roulette, poker, dice, lottery — any game with finite outcomes |
| **Multi-table sessions** | Independent sessions with separate histories, like observing multiple tables |
| **Interactive wheel** | Plotly donut chart with highlighting — selected number, neighbors, opposite zone |
| **French announced bets** | Jeu 0, Voisins du Zéro, Tiers du Cylindre, Orphelins with wheel coverage |
| **Z-Score detection** | Rolling window statistics across 6 time horizons |
| **Extremum Index** | Weighted multi-window signal aggregation |
| **Mean Reversion Factor** | Learned parameter (0-1) from historical data |
| **Kelly Criterion** | Optimal bet sizing with fractional Kelly (1/4, 1/2) |
| **Correlation Engine** | Structural and empirical bet dependencies |
| **Portfolio Optimization** | Constrained optimization across ALL bets simultaneously |
| **Monte Carlo** | VaR, CVaR, ruin probability, risk scoring |
| **Risk Management** | Exposure limits, drawdown controls, loss distribution |
| **Bilingual UI** | Full English and Polish support (150+ translation keys) |
| **Interactive UI** | Streamlit dashboard with 6 pages + 15-step tutorial |

### Design Philosophy

The system treats betting as a **portfolio management problem**, not a prediction problem. The same engine works for any game because it only needs:
- A list of available bets
- Theoretical probabilities for each bet
- Payout odds for each bet
- Historical draw outcomes

---

## 2. Architecture

### Data Flow

```
┌─────────────────┐
│   Game Definition│  (core/game.py)
│   (bets, probs,  │
│    odds)         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  History Engine  │ ←── │ Session Manager │  (core/session.py)
│  (SQLite,        │     │ (multi-table,    │
│   rolling windows)│     │  per-session DB) │
└────────┬────────┘     └─────────────────┘
         │
         ├──────────────────────┐
         ▼                      ▼
┌─────────────────┐   ┌─────────────────┐
│ Extremum Engine  │   │  Value Engine   │
│ (Z-score, EI,    │   │  (EV, Kelly,    │
│  MRF)            │   │   risk score)   │
└────────┬────────┘   └────────┬────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
         ┌─────────────────┐
         │Correlation Engine│  (core/correlation.py)
         │(structural &     │
         │ empirical)       │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │Portfolio Engine  │  (core/portfolio.py)
         │(constrained      │
         │ optimization)    │
         └────────┬────────┘
                  │
         ┌────────┴────────┐
         ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│Monte Carlo Engine│  │ Risk Manager    │
│(simulations,     │  │(limits, loss    │
│ VaR, CVaR)      │  │ distribution)   │
└────────┬────────┘  └────────┬────────┘
         │                    │
         └──────────┬─────────┘
                    ▼
         ┌─────────────────┐
         │ Stake Optimizer  │
         │ (final stakes)   │
         └─────────────────┘
```

### Module Dependency Graph

```
game.py                  (no dependencies)
roulette_wheel.py        (no dependencies)
history.py               → game.py
session.py               → (standalone, wraps history)
session_history_adapter.py → session.py, history.py
i18n.py                  (no dependencies)
extremum.py              → history.py, game.py
value.py                 → game.py, extremum.py
correlation.py           → game.py, history.py
portfolio.py             → game.py, value.py
monte_carlo.py           → game.py, portfolio.py
risk.py                  → game.py, portfolio.py
```

### Directory Structure

```
betting-portfolio-system/
├── core/                         # Abstract engine (game-agnostic)
│   ├── game.py                   # Bet and Game dataclasses
│   ├── history.py                # SQLite history + rolling windows
│   ├── session.py                # SessionManager — multi-table support
│   ├── session_history_adapter.py # Bridges SessionManager ↔ HistoryEngine
│   ├── i18n.py                   # Translator — EN/PL (150+ keys)
│   ├── extremum.py               # Z-score, EI, MRF
│   ├── value.py                  # EV, Kelly criterion
│   ├── correlation.py            # Bet correlation matrix
│   ├── portfolio.py              # Constrained optimization
│   ├── monte_carlo.py            # Monte Carlo simulations
│   └── risk.py                   # Risk limits, loss distribution
├── games/                        # Concrete game implementations
│   ├── roulette.py               # European roulette (37 fields, 55 bets)
│   ├── roulette_wheel.py         # Wheel geometry, French bets, visualization
│   └── poker.py                  # Texas Hold'em hand rankings
├── ui/                           # Streamlit dashboard
│   ├── app.py                    # Main app with navigation + session selector
│   └── views/
│       ├── tutorial.py           # 15-step interactive tutorial
│       ├── roulette.py           # Wheel + numbers + French bets + signals + MC
│       ├── poker.py              # Poker recommendations
│       ├── portfolio.py          # Cross-game portfolio view
│       ├── history.py            # Session-aware draw recording + Z-score dashboard
│       └── settings.py           # Language, bankroll, risk limits
├── tests/                        # Test suite (130 tests)
│   ├── test_game.py              # Game/Bet unit tests
│   ├── test_games.py             # Roulette + poker tests
│   ├── test_history.py           # History engine tests
│   ├── test_session.py           # SessionManager tests (17 tests)
│   ├── test_i18n.py              # Translator tests (15 tests)
│   ├── test_extremum.py          # Extremum engine tests
│   ├── test_value.py             # Value engine tests
│   ├── test_correlation.py       # Correlation engine tests
│   ├── test_portfolio.py         # Portfolio engine tests
│   ├── test_monte_carlo.py       # Monte Carlo tests
│   ├── test_risk.py              # Risk manager tests
│   └── test_ui_automated.py      # Automated UI + pipeline tests (25 tests)
├── docs/                         # Documentation
│   ├── MANUAL_TESTS.md           # Manual test plan (41 scenarios)
│   └── ARCHITECTURE.md           # This file
├── data/                         # SQLite databases (gitignored)
│   ├── sessions.db               # Session metadata
│   └── session_*.db              # Per-session draw histories
├── pyproject.toml                # Project configuration
└── README.md
```

---

## 3. Installation & Quick Start

### Prerequisites

- Python 3.10 or later
- pip

### Install

```bash
git clone https://github.com/ScuraUrsa/betting-portfolio-system.git
cd betting-portfolio-system
pip install -e ".[dev]"
```

### Run Tests

```bash
# All 130 tests
pytest

# Unit tests only
pytest tests/ --ignore=tests/test_ui_automated.py

# Automated UI tests only
pytest tests/test_ui_automated.py -v

# With coverage
pytest --cov=core --cov=games --cov-report=term-missing
```

### Start UI

```bash
streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0
```

Open http://localhost:8501 in your browser.

### Quick Python Example

```python
from games.roulette import european_roulette
from core.history import HistoryEngine
from core.extremum import ExtremumEngine
from core.value import ValueEngine
from core.portfolio import PortfolioEngine

# Create game
game = european_roulette()

# Record some draws
history = HistoryEngine("data/example.db")
red_numbers = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
for num in [17, 32, 5, 0, 14, 23, 8, 31, 19, 2]:
    won = [f"num_{num}"]
    if num != 0:
        won.append("red" if num in red_numbers else "black")
        won.append("even" if num % 2 == 0 else "odd")
        won.append("low" if num <= 18 else "high")
        won.append(f"dozen_{(num-1)//12+1}")
        won.append(f"col_{(num-1)%3+1}")
    history.record_draw(game, str(num), won)

# Analyze
extremum = ExtremumEngine(history)
results = extremum.analyze_all(game)

ve = ValueEngine()
value_results = ve.analyze_all(game, {r.bet_id: r for r in results})

portfolio = PortfolioEngine(bankroll=1000.0)
allocation = portfolio.optimize(game, value_results)

print(f"Total exposure: {allocation.total_exposure:.2%}")
print(f"Expected return: {allocation.expected_return:+.2f} zł")
```

---

## 4. Core Modules API

### 4.1 Game Engine (`core/game.py`)

```python
@dataclass(frozen=True)
class Bet:
    id: str           # Unique identifier (e.g. "red", "num_17")
    name: str         # Human-readable name
    probability: float  # Theoretical P(win), 0 < p < 1
    odds: float       # Payout multiplier (36.0 = "pays 36:1")

@dataclass
class Game:
    name: str
    bets: list[Bet]

    # Properties
    n_bets: int       # Number of available bets

    # Methods
    validate()        # Check all probabilities and odds are valid
    get_bet(id)       # Get a bet by ID
    expected_value(id)  # EV = p * odds - 1
```

### 4.2 Roulette Wheel (`games/roulette_wheel.py`)

```python
# Wheel geometry
WHEEL_ORDER: list[int]  # 37 numbers in clockwise order
RED_NUMBERS: set[int]
BLACK_NUMBERS: set[int]

# French announced bets
JEU_0: set[int]           # 7 numbers around zero
VOISINS_DU_ZERO: set[int] # 17 numbers
TIERS_DU_CYLINDRE: set[int]  # 12 numbers
ORPHELINS: set[int]       # 8 numbers

# Number properties
get_color(n) -> str       # "green" | "red" | "black"
get_parity(n) -> str      # "even" | "odd" | "—"
get_half(n) -> str        # "low (1-18)" | "high (19-36)" | "—"
get_dozen(n) -> str       # "1st 12" | "2nd 12" | "3rd 12" | "—"
get_column(n) -> str      # "Column 1" | "Column 2" | "Column 3" | "—"
get_section(n) -> str     # French bet section name

# Wheel geometry
get_neighbors(n, count=2) -> list[int]  # count neighbors each side
get_opposite(n) -> tuple[int, int]     # 2 numbers ~180° away
get_opposite_zone(n, spread=1) -> set[int]  # opposite + neighbors

# Visualization
build_wheel_figure(height=500) -> go.Figure
build_wheel_figure_highlighted(
    selected_number=None,  # Number to highlight (white glow)
    neighbor_count=2,      # Neighbors each side (gold border)
    opposite_spread=1,     # Opposite zone spread (cyan border)
    height=550,
) -> go.Figure
```

### 4.3 History Engine (`core/history.py`)

```python
class HistoryEngine:
    def __init__(self, db_path: str = "data/history.db")
    def record_draw(game, raw_outcome, won_bet_ids, timestamp=None) -> int
    def get_draws(game_name, limit=None) -> list[DrawRecord]
    def count_draws(game_name) -> int
    def compute_window_stats(game, bet_id, window_size) -> WindowStats
    def compute_all_windows(game, bet_id, windows=None) -> list[WindowStats]
    def clear_history(game_name)

@dataclass
class WindowStats:
    bet_id: str
    window_size: int
    n_draws: int
    hits: int
    expected: float    # E = n * p
    std: float         # σ = sqrt(n * p * (1-p))
    z_score: float     # Z = (hits - expected) / std
```

**Default windows**: 50, 100, 250, 500, 1000, 5000

### 4.4 Session Manager (`core/session.py`)

```python
@dataclass
class Session:
    session_id: int
    name: str           # e.g. "Table 1", "Casino Warsaw"
    game_type: str      # "roulette" | "poker"
    created_at: str     # ISO timestamp
    draw_count: int

class SessionManager:
    def __init__(self, db_path: str = "data/sessions.db")
    def create(name, game_type) -> Session
    def get(session_id) -> Optional[Session]
    def list_all() -> list[Session]
    def delete(session_id)
    def record_draw(session_id, raw_outcome, won_bet_ids) -> int
    def get_draws(session_id, limit=None) -> list[DrawRecord]
    def count_draws(session_id) -> int
    def clear_history(session_id)
```

### 4.5 Session History Adapter (`core/session_history_adapter.py`)

Bridges `SessionManager` to the `HistoryEngine` interface so the pipeline (ExtremumEngine, ValueEngine, etc.) works unchanged with session-scoped data.

```python
class SessionHistoryAdapter:
    def __init__(self, session_mgr: SessionManager, session_id: int)
    # Exposes same API as HistoryEngine:
    #   record_draw(), get_draws(), count_draws(), compute_window_stats()
```

### 4.6 i18n Translator (`core/i18n.py`)

```python
class Translator:
    def __init__(self, lang: str = "en")
    def set_lang(lang: str)       # "en" | "pl"
    def t(key: str, **kwargs) -> str  # Translate with format placeholders

# Usage:
t = Translator()
t.set_lang("pl")
t.t("nav_roulette")           # → "🎰 Ruletka"
t.t("active_signals_count", count=5)  # → "5 aktywnych sygnałów"
```

**150+ translation keys** covering all UI elements: navigation, metrics, properties, signals, buttons, messages.

### 4.7 Extremum Engine (`core/extremum.py`)

```python
class ExtremumEngine:
    def __init__(self, history, ei_weights=None, mrf=0.35)
    def analyze(game, bet_id, windows=None) -> ExtremumResult
    def analyze_all(game, windows=None) -> list[ExtremumResult]
    def learn_mrf(game, bet_id, lookback=1000) -> float

@dataclass
class ExtremumResult:
    bet_id: str
    window_stats: list[WindowStats]
    extremum_index: float    # Weighted sum of Z-scores
    mrf: float               # Mean Reversion Factor
    signal_level: str        # none/observation/entry_small/medium/maximum
    max_z_score: float
    direction: str           # over/under/neutral
```

**Default EI weights**: 50→0.10, 100→0.20, 250→0.30, 500→0.40

**Signal thresholds**:
| EI | Signal |
|----|--------|
| < 1.0 | none |
| < 2.0 | observation |
| < 2.5 | entry_small |
| < 3.0 | medium |
| ≥ 3.0 | maximum |

### 4.8 Value Engine (`core/value.py`)

```python
class ValueEngine:
    def __init__(self, max_stake_pct=0.10)
    def analyze(bet, extremum=None) -> ValueResult
    def analyze_all(game, extremum_results=None) -> list[ValueResult]

@dataclass
class ValueResult:
    bet_id: str
    bet_name: str
    probability: float
    odds: float
    ev: float              # Expected Value
    kelly_full: float       # Full Kelly fraction
    kelly_half: float       # 1/2 Kelly
    kelly_quarter: float    # 1/4 Kelly
    risk_score: float       # 0-1
    exposure_score: float   # Recommended allocation
    has_value: bool         # EV > 0
    recommended_stake_pct: float  # min(kelly_quarter, max_stake_pct)
```

### 4.9 Correlation Engine (`core/correlation.py`)

```python
class CorrelationEngine:
    def compute_structural(game, win_sets) -> CorrelationMatrix
    def compute_empirical(game, history, lookback=1000) -> CorrelationMatrix

@dataclass
class CorrelationMatrix:
    bet_ids: list[str]
    matrix: np.ndarray       # shape (n, n), values in [-1, 1]
    def get_correlation(bet_a, bet_b) -> float
    def get_correlated_bets(bet_id, threshold=0.3) -> list[tuple[str, float]]
```

### 4.10 Portfolio Engine (`core/portfolio.py`)

```python
class PortfolioEngine:
    def __init__(self, bankroll=1000.0, max_per_bet=0.10,
                 max_per_draw=0.30, max_total=0.50)
    def optimize(game, value_results, correlation_matrix=None) -> PortfolioAllocation
    def analyze_scenarios(game, allocation, win_sets, outcomes, probs) -> list[ScenarioResult]

@dataclass
class PortfolioAllocation:
    bet_ids: list[str]
    stakes: np.ndarray       # Absolute amounts
    stake_pcts: np.ndarray   # As fraction of bankroll
    total_exposure: float
    expected_return: float
    max_loss: float
    max_profit: float
    sharpe_like: float
```

**Optimization method**: SLSQP (Sequential Least Squares Programming) via `scipy.optimize.minimize`.

### 4.11 Monte Carlo Engine (`core/monte_carlo.py`)

```python
class MonteCarloEngine:
    def __init__(self, seed=None)
    def simulate_independent(game, allocation, n_simulations=10000) -> MonteCarloResult
    def simulate_game_outcomes(game, allocation, outcome_probs, win_sets,
                                n_simulations=10000) -> MonteCarloResult

@dataclass
class MonteCarloResult:
    n_simulations: int
    expected_return: float
    expected_return_pct: float
    std_return: float
    max_drawdown: float
    max_profit: float
    var_95: float            # Value at Risk (95%)
    var_99: float            # Value at Risk (99%)
    cvar_95: float           # Conditional VaR
    profit_distribution: np.ndarray
    risk_score: float        # 0-1
    ruin_probability: float  # P(profit < 0)
```

### 4.12 Risk Manager (`core/risk.py`)

```python
class RiskManager:
    def __init__(self, limits=None)
    def validate(allocation, bankroll) -> list[str]  # Returns violations
    def compute_loss_distribution(scenarios) -> LossDistribution
    def assess(allocation, bankroll, scenarios=None) -> RiskReport

@dataclass
class RiskLimits:
    max_per_bet: float = 0.10
    max_per_hand: float = 0.20
    max_per_draw: float = 0.30
    max_total: float = 0.50
    max_drawdown: float = 0.25
    min_bankroll: float = 100.0

@dataclass
class LossDistribution:
    best_case: float
    worst_case: float
    expected_case: float
    median_case: float
    std_dev: float
    profit_probability: float
    loss_scenarios: list[ScenarioResult]
    profit_scenarios: list[ScenarioResult]
```

---

## 5. Game Implementations

### 5.1 European Roulette (`games/roulette.py` + `games/roulette_wheel.py`)

```python
from games.roulette import european_roulette
game = european_roulette()
```

**55 bets total**:
- 37 straight-up numbers (0-36): p=1/37, odds=36:1
- Red/Black: p=18/37, odds=2:1
- Even/Odd: p=18/37, odds=2:1
- Low(1-18)/High(19-36): p=18/37, odds=2:1
- 3 Dozens: p=12/37, odds=3:1
- 3 Columns: p=12/37, odds=3:1

**Wheel geometry** (`roulette_wheel.py`):
- 37 slots in European wheel order
- Color, parity, half, dozen, column, section for every number
- French announced bets: Jeu 0 (7), Voisins du Zéro (17), Tiers du Cylindre (12), Orphelins (8)
- Neighbors: configurable count (1-5) on each side
- Opposite numbers: 2 numbers ~180° away + configurable neighbor spread (0-3)
- Interactive Plotly donut chart with highlighting

**House edge**: -1/37 ≈ -2.70% on every bet.

### 5.2 Texas Hold'em Poker (`games/poker.py`)

```python
from games.poker import texas_holdem_hand_rankings
game = texas_holdem_hand_rankings()
```

**10 hand rankings** (7-card probabilities):
| Hand | Probability | Default Odds |
|------|------------|-------------|
| Royal Flush | 0.000032 | 800:1 |
| Straight Flush | 0.000279 | 500:1 |
| Four of a Kind | 0.001680 | 100:1 |
| Full House | 0.025961 | 25:1 |
| Flush | 0.030255 | 20:1 |
| Straight | 0.046194 | 15:1 |
| Three of a Kind | 0.048299 | 10:1 |
| Two Pair | 0.234955 | 3:1 |
| One Pair | 0.438225 | 1.5:1 |
| High Card | 0.174119 | 1:1 |

### 5.3 Adding a New Game

Create a file in `games/` that returns a `Game` instance:

```python
# games/dice.py
from core.game import Bet, Game

def two_dice():
    """Sum of two six-sided dice."""
    bets = []
    probabilities = {
        2: 1/36, 3: 2/36, 4: 3/36, 5: 4/36, 6: 5/36,
        7: 6/36, 8: 5/36, 9: 4/36, 10: 3/36, 11: 2/36, 12: 1/36,
    }
    for total, p in probabilities.items():
        bets.append(Bet(
            id=f"sum_{total}",
            name=f"Sum {total}",
            probability=p,
            odds=1.0 / p,  # fair odds
        ))
    game = Game(name="Two Dice", bets=bets)
    game.validate()
    return game
```

The entire pipeline (history → extremum → value → portfolio → MC → risk) works automatically for any game that implements the `Game` interface.

---

## 6. Streamlit UI

### Pages

| Page | File | Description |
|------|------|-------------|
| 🎓 Tutorial | `ui/views/tutorial.py` | 15-step interactive walkthrough |
| 🎰 Roulette | `ui/views/roulette.py` | Interactive wheel, numbers, French bets, signals, Monte Carlo |
| 🃏 Poker | `ui/views/poker.py` | Hand rankings, probability distribution |
| 📊 Portfolio | `ui/views/portfolio.py` | Cross-game optimization, loss distribution |
| 📈 History | `ui/views/history.py` | Session-aware draw recording, Z-score heatmap, history browser |
| ⚙️ Settings | `ui/views/settings.py` | Language (EN/PL), bankroll, risk limits |

### Roulette Page Tabs

The roulette page has 6 sub-tabs:
1. **🎡 Wheel** — Interactive wheel with highlighting + number lookup
2. **🔢 Numbers** — Straight-up number recommendations
3. **🎯 Other Bets** — Red/black, even/odd, low/high, dozens, columns
4. **🇫🇷 French Bets** — Jeu 0, Voisins, Tiers, Orphelins with wheel coverage
5. **📈 Signals** — Z-score per window
6. **🎲 Monte Carlo** — Simulations

### Wheel Highlighting

- **White glow + pull-out** — selected number
- **Gold border** — neighbors (configurable 1-5 each side)
- **Cyan border** — opposite zone (configurable spread 0-3)
- **Legend** — annotations on the chart itself
- **Hover** — full info: color, parity, half, dozen, column, section, neighbors, opposite

### Session Management

- **Sidebar selector** — switch between active sessions
- **Create** — new session with name + game type
- **Delete** — remove session and its history
- **Per-session data** — each session has independent draw history and recommendations

### Tutorial Steps

1. Welcome & Concepts
2. Game Model (Roulette)
3. Game Model (Poker)
4. Recording Draws
5. Rolling Windows & Z-Score
6. Extremum Index (EI)
7. Mean Reversion Factor (MRF)
8. Value Engine (EV & Kelly)
9. Correlation Engine
10. Portfolio Optimization
11. Monte Carlo Simulation
12. Risk Management
13. Loss Distribution
14. Combined Portfolio
15. Summary & Next Steps

### Running the UI

```bash
# Default port 8501
streamlit run ui/app.py

# Custom port, accessible from network
streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0

# Headless (no browser auto-open)
streamlit run ui/app.py --server.headless true
```

---

## 7. Testing

### Test Suite Overview

| File | Tests | Coverage |
|------|-------|----------|
| `test_game.py` | 12 | Game/Bet dataclasses, validation, EV |
| `test_games.py` | 13 | Roulette and poker implementations |
| `test_history.py` | 9 | SQLite storage, rolling windows, Z-score |
| `test_session.py` | 17 | SessionManager CRUD, draw recording, multi-table |
| `test_i18n.py` | 15 | Translator, EN/PL, format placeholders, edge cases |
| `test_extremum.py` | 8 | EI, MRF learning, signal classification |
| `test_value.py` | 7 | EV, Kelly fractions, risk scoring |
| `test_correlation.py` | 4 | Structural and empirical correlation |
| `test_portfolio.py` | 6 | Constrained optimization, scenarios |
| `test_monte_carlo.py` | 5 | Independent and game-outcome simulation |
| `test_risk.py` | 9 | Risk limits, loss distribution, assessment |
| `test_ui_automated.py` | 25 | Module structure, full pipeline, HTTP, edge cases, regression |
| **Total** | **130** | |

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_game.py -v

# Specific test
pytest tests/test_game.py::TestGame::test_expected_value_fair_coin -v

# With coverage report
pytest --cov=core --cov=games --cov-report=html
```

### Automated UI Tests (`test_ui_automated.py`)

Six test classes covering:

1. **TestUIModuleStructure** (4 tests) — all pages have `show()`, NAV_KEYS complete, files exist
2. **TestFullPipeline** (3 tests) — end-to-end: game → history → extremum → value → portfolio → MC → risk
3. **TestStreamlitAppHTTP** (3 tests) — app starts, returns 200, serves static resources
4. **TestStateManagement** (3 tests) — bankroll default/update, tutorial step state
5. **TestEdgeCases** (8 tests) — zero/negative bankroll, single/many bets, extreme probabilities, MC convergence, correlation symmetry, risk limit consistency
6. **TestRegression** (4 tests) — specific bugs: overlapping probabilities, Kelly=0 for negative EV, Z-score=0 with no data, MRF default

### Manual Test Plan

See `docs/MANUAL_TESTS.md` for 41 manual test scenarios across 9 test suites covering every UI feature, button, and edge case.

---

## 8. Extending the System

### Adding a New Game

1. Create `games/yourgame.py`
2. Implement a factory function returning `Game` with `Bet` objects
3. Call `game.validate()` before returning
4. Add tests in `tests/test_games.py`
5. Add a UI page in `ui/views/yourgame.py` with a `show()` function
6. Register the page in `ui/app.py` → `NAV_KEYS` and routing

### Adding a New Analysis Module

1. Create `core/yourmodule.py`
2. Import only from `core/game.py` (or other core modules as needed)
3. Use dataclasses for results
4. Add tests in `tests/test_yourmodule.py`
5. Integrate into the pipeline in UI pages

### Adding a New Language

1. Add language code to `core/i18n.py` → `TRANSLATIONS` dict
2. Copy the `en` block and translate all 150+ keys
3. Add the language to `LANGUAGES` list
4. The Settings page auto-detects new languages

### Customizing Risk Limits

Edit `core/risk.py` → `RiskLimits` dataclass defaults:

```python
@dataclass
class RiskLimits:
    max_per_bet: float = 0.10    # Change to 0.05 for more conservative
    max_per_hand: float = 0.20
    max_per_draw: float = 0.30
    max_total: float = 0.50
    max_drawdown: float = 0.25
    min_bankroll: float = 100.0
```

### Customizing EI Weights

Edit `core/extremum.py` → `DEFAULT_EI_WEIGHTS`:

```python
DEFAULT_EI_WEIGHTS = {
    50: 0.10,
    100: 0.20,
    250: 0.30,
    500: 0.40,
}
```

### Customizing Signal Thresholds

Edit `core/extremum.py` → `ExtremumEngine._classify_signal()`.

### Using a Different Database

The `HistoryEngine` accepts any path. For production, use a persistent path:

```python
history = HistoryEngine("/var/lib/betting/history.db")
```

For testing, use `:memory:` (in-memory SQLite) or `tmp_path`.

---

## 9. Mathematical Background

### Z-Score

For a bet with probability $p$, over $n$ draws:

$$E = n \cdot p$$
$$\sigma = \sqrt{n \cdot p \cdot (1-p)}$$
$$Z = \frac{X - E}{\sigma}$$

Where $X$ is the actual number of wins.

### Extremum Index

Weighted sum of Z-scores across multiple time windows:

$$EI = \sum_{w} w_i \cdot Z_{w_i}$$

Default weights: 50→0.10, 100→0.20, 250→0.30, 500→0.40.

### Mean Reversion Factor

$$MRF = P(\text{correction} \mid \text{extremum})$$

Learned from historical data: for each extremum (|Z| > 2), check whether the next period shows regression toward the mean. MRF is the fraction of extremes followed by correction.

### Kelly Criterion

For a bet with win probability $p$ and odds $b$:

$$f^* = \frac{p \cdot b - 1}{b - 1}$$

Where $f^*$ is the optimal fraction of bankroll to bet. In practice, we use fractional Kelly:
- $f_{1/2} = f^* / 2$ (half Kelly)
- $f_{1/4} = f^* / 4$ (quarter Kelly)

### Portfolio Optimization

The objective is to maximize expected return:

$$\max_{x_i} \sum_i x_i \cdot EV_i$$

Subject to:
- $0 \leq x_i \leq 0.10$ (max 10% per bet)
- $\sum_i x_i \leq 0.50$ (max 50% total exposure)

Solved via SLSQP (Sequential Least Squares Programming).

### Monte Carlo Metrics

- **VaR₉₅**: 5th percentile of profit distribution
- **CVaR₉₅**: Mean of profits below VaR₉₅
- **Ruin Probability**: P(profit < 0)
- **Risk Score**: $\min(1, \sigma / (|\mu| + \sigma))$

---

## 10. Configuration Reference

### pyproject.toml

```toml
[project]
name = "betting-portfolio-system"
version = "0.2.0"
requires-python = ">=3.10"

dependencies = [
    "numpy>=1.24",
    "scipy>=1.10",
    "pandas>=2.0",
    "streamlit>=1.30",
    "plotly>=5.18",
    "pytest>=7.0",
]

[project.optional-dependencies]
dev = [
    "pytest-cov>=4.0",
    "hypothesis>=6.90",
    "ruff>=0.3",
]
```

### Environment Variables

None required. All configuration is in-code.

### Database

SQLite databases are stored in `data/` directory (gitignored):
- `sessions.db` — session metadata (names, game types, timestamps)
- `session_<id>.db` — per-session draw histories

---

## References

- Kelly, J.L. (1956). "A New Interpretation of Information Rate"
- Thorp, E.O. (1997). "The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market"
- Poundstone, W. (2005). "Fortune's Formula"
- Markowitz, H. (1952). "Portfolio Selection"
