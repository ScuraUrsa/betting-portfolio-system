# Betting Portfolio System

> **Game-agnostic betting portfolio optimization engine**
>
> Z-score · Extremum Index · Mean Reversion · Kelly Criterion · Monte Carlo · Risk Management

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-130%20passed-green)]()

---

## What is this?

A **game-agnostic** system that doesn't try to predict which bet will win. Instead, it answers:

> *"How should I distribute my capital across all available bets, considering local extremes, mean reversion, correlations, and the expected profit/risk profile of the entire portfolio?"*

The same engine works for roulette, poker, dice, lottery — any game with finite outcomes.

## Quick Start

```bash
git clone https://github.com/ScuraUrsa/betting-portfolio-system.git
cd betting-portfolio-system
pip install -e ".[dev]"
pytest                                    # 130 tests
streamlit run ui/app.py                   # Dashboard at http://localhost:8501
```

## Features

| Module | What it does |
|--------|-------------|
| **Game Engine** | Abstract Bet/Game model — add any game in 30 lines |
| **Roulette Wheel** | Wheel geometry, French bets, neighbors, opposite numbers, interactive visualization |
| **History Engine** | SQLite storage, rolling windows (50–5000) |
| **Session Manager** | Multi-table support — independent sessions with separate histories |
| **Extremum Engine** | Z-score, Extremum Index, learned Mean Reversion Factor |
| **Value Engine** | EV, Kelly Criterion (full, 1/2, 1/4), risk scoring |
| **Correlation Engine** | Structural (win-set overlap) and empirical (Pearson) |
| **Portfolio Engine** | Constrained optimization across ALL bets simultaneously |
| **Monte Carlo** | VaR, CVaR, ruin probability, profit distribution |
| **Risk Manager** | Exposure limits, drawdown controls, loss distribution |
| **i18n** | English/Polish translations (150+ keys) |

## UI Dashboard

6 interactive pages + 15-step tutorial:

| Page | Description |
|------|-------------|
| 🎓 **Tutorial** | Step-by-step walkthrough of every feature |
| 🎰 **Roulette** | Interactive wheel with highlighting, French bets, number lookup, recommendations |
| 🃏 **Poker** | Hand ranking analysis, probability distribution |
| 📊 **Portfolio** | Cross-game optimization, loss distribution |
| 📈 **History** | Session-aware draw recording, Z-score heatmap, history browser |
| ⚙️ **Settings** | Language (EN/PL), bankroll, risk limits, data management |

### Key UI Features

- **Interactive roulette wheel** — Plotly donut chart with white glow (selected), gold border (neighbors), cyan border (opposite zone). Sliders control neighbor count (1-5) and opposite zone spread (0-3).
- **Multi-table sessions** — Create independent sessions (e.g. "Table 1", "Casino Warsaw"), each with its own draw history and recommendations. Switch between them in the sidebar.
- **Bilingual** — Full English and Polish support. Switch language in Settings.
- **French announced bets** — Jeu 0, Voisins du Zéro, Tiers du Cylindre, Orphelins with wheel coverage visualization.

## Architecture

```
GAME DEFINITION
      ↓
HISTORY (SQLite + rolling windows) ← SESSION MANAGER (multi-table)
      ↓
EXTREMUM ENGINE ←────────── VALUE ENGINE
(Z-score, EI, MRF)         (EV, Kelly)
      ↓                          ↓
CORRELATION ENGINE ←─────────────┘
      ↓
PORTFOLIO ENGINE (constrained optimization)
      ↓
MONTE CARLO ←────────── RISK MANAGER
(VaR, CVaR)             (limits, loss dist)
      ↓
FINAL STAKES
```

## Documentation

- **[Full Architecture & API Docs](docs/ARCHITECTURE.md)** — complete module reference, mathematical background, extension guide
- **[Manual Test Plan](docs/MANUAL_TESTS.md)** — 41 manual test scenarios covering every UI feature
- **[Automated Tests](tests/test_ui_automated.py)** — 25 automated UI + pipeline tests

## Supported Games

- 🎰 **European Roulette** — 37 fields, 55 bet types, wheel geometry, French announced bets
- 🃏 **Texas Hold'em Poker** — 10 hand rankings
- 🎲 Extensible: add any game by implementing the `Game` interface

## Testing

```bash
pytest                                          # All 130 tests
pytest tests/test_ui_automated.py -v            # Automated UI tests
pytest --cov=core --cov=games --cov-report=html # Coverage report
```

## License

MIT — see [LICENSE](LICENSE) file.
