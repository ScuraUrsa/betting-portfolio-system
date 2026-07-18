# Betting Portfolio System

Abstract, game-agnostic betting portfolio optimization engine.

## Architecture

```
HISTORY → ROLLING WINDOWS → VALUE ENGINE (EV, Kelly)
         → EXTREMUM ENGINE (Z-score, EI, MRF)
         → CORRELATION ENGINE
         → PORTFOLIO ENGINE (profit/loss distribution)
         → MONTE CARLO ENGINE (simulations)
         → LOSS DISTRIBUTION ENGINE
         → RISK MANAGEMENT (exposure limits)
         → STAKE OPTIMIZER → FINAL STAKES
```

## Supported Games

- Roulette (European, 37 fields)
- Poker (Texas Hold'em hand rankings)
- Dice
- Lottery

## Quick Start

```bash
pip install -e ".[dev]"
pytest
streamlit run ui/app.py
```

## License

MIT
