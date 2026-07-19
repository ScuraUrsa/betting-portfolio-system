# Manual Test Plan — Betting Portfolio System

> **Goal**: Verify every UI feature, button, and scenario works correctly through manual interaction.
> **Prerequisites**: System running at http://192.168.56.101:8501
> **Start command**: `streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0`

---

## Test Suite 1: Navigation & Layout

### T1.1 — All pages accessible
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open http://192.168.56.101:8501 | App loads, sidebar visible |
| 2 | Click "🎓 Tutorial" | Tutorial page loads with step 1 |
| 3 | Click "🎰 Roulette" | Roulette page loads with 3 tabs |
| 4 | Click "🃏 Poker" | Poker page loads with 2 tabs |
| 5 | Click "📊 Portfolio" | Portfolio page loads |
| 6 | Click "📈 History & Signals" | History page loads with 3 tabs |
| 7 | Click "⚙️ Settings" | Settings page loads with 2 tabs |

### T1.2 — Bankroll display
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Check sidebar | Shows "Bankroll: 1,000 zł" |
| 2 | Go to Settings → change bankroll to 2000 | Sidebar updates to "2,000 zł" |
| 3 | Refresh page | Bankroll resets to 1000 (default) |

### T1.3 — Sidebar footer
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Check sidebar bottom | Shows "Game-agnostic portfolio optimization..." |

---

## Test Suite 2: Tutorial (15 steps)

### T2.1 — Step navigation
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Go to Tutorial | Step 1 "Welcome & Concepts" shown |
| 2 | Click "Next →" | Step 2 "Game Model (Roulette)" shown |
| 3 | Click "Next →" 13 more times | Reach step 15 "Summary & Next Steps" |
| 4 | Click "Next →" on step 15 | Button disabled (last step) |
| 5 | Click "← Previous" | Goes back to step 14 |
| 6 | Click "← Previous" on step 1 | Button disabled (first step) |
| 7 | Click "🔄 Restart Tutorial" on step 15 | Returns to step 1, balloons shown |

### T2.2 — Step 2: Roulette model
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to step 2 | Shows "Total Bets", "Straight-up Numbers", "House Edge" metrics |
| 2 | Select "num_17" from dropdown | Shows probability=0.0270, odds=36.0, EV=-0.0270 |
| 3 | Select "red" from dropdown | Shows probability=0.4865, odds=2.0, EV=-0.0270 |

### T2.3 — Step 4: Recording draws
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to step 4 | Shows number input and "Record This Draw" button |
| 2 | Enter 17, click "Record This Draw" | Success message: "Draw #1 recorded!" |
| 3 | Enter 0, click "Record This Draw" | Success: only num_0 wins (no color/even-odd/dozen/col) |
| 4 | Set slider to 100, click "Generate Random Draws" | "Generated 100 random draws!" |
| 5 | Check counter | Shows 102 total draws |

### T2.4 — Step 5: Z-Score
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to step 5 (need ≥10 draws first) | Z-score bar chart shown |
| 2 | Select "red" from dropdown | Chart updates with Z-scores per window |
| 3 | Check raw statistics table | Shows Window, Draws, Hits, Expected, Std, Z-Score |
| 4 | Verify Z=2 and Z=3 lines visible | Orange dashed at ±2, red dashed at ±3 |

### T2.5 — Step 6: Extremum Index
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to step 6 | Top 10 signals table shown |
| 2 | Check for active signals | Either "🔔 N bets with active signals" or "No significant signals" |

### T2.6 — Step 7: MRF
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to step 7 (need ≥100 draws) | MRF explanation shown |
| 2 | Select "red", click "Learn MRF from Data" | Shows learned MRF value (0-1) |
| 3 | If <100 draws | Warning: "Need at least 100 draws", shows default 0.35 |

### T2.7 — Step 8: Value Engine
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to step 8 | Table with EV, Kelly Full, Kelly 1/4, Risk Score, Exposure, Signal |
| 2 | Verify all roulette EVs are negative | All EV values show "-0.0270" |

### T2.8 — Step 9: Correlation
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to step 9 | Correlation explanation shown |
| 2 | Select "num_17" | Shows correlated bets (e.g. red, odd, low, dozen_2, col_2) |
| 3 | Select "red" | Shows many correlated straight-up numbers |

### T2.9 — Step 10: Portfolio Optimization
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to step 10 | "Run Portfolio Optimization" button shown |
| 2 | Click button | Allocation table appears (or "No positive-EV bets") |
| 3 | Check metrics | Total Exposure, Expected Return, Sharpe-like shown |

### T2.10 — Step 11: Monte Carlo
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to step 11 | Slider (1000-50000) and "Run Monte Carlo" button |
| 2 | Set to 5000, click button | Spinner, then metrics + histogram appear |
| 3 | Check all 6 metrics | Expected Return, Std Dev, Max Drawdown, Ruin Prob, VaR, CVaR |
| 4 | Verify histogram | Shows distribution with break-even and mean lines |

### T2.11 — Step 12: Risk Management
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to step 12 | Risk limits table and assessment shown |
| 2 | Check status | Either "✅ All risk limits satisfied" or "⚠️ Risk limits exceeded" |

### T2.12 — Step 13: Loss Distribution
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to step 13 | 4 metrics: Best Case, Worst Case, Expected, P(Profit) |
| 2 | Check scenario chart | Bar chart with green (profit) and red (loss) bars |

### T2.13 — Step 14: Combined Portfolio
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to step 14 | "Optimize Combined Portfolio" button |
| 2 | Click button | Cross-game allocation table (Roulette + Poker) |

### T2.14 — Step 15: Summary
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to step 15 | Summary text, balloons animation |
| 2 | Click "🔄 Restart Tutorial" | Returns to step 1 |

---

## Test Suite 3: Roulette Page

### T3.1 — Recommendations tab
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Go to Roulette → Recommendations | Table with all 55 bets |
| 2 | Check columns | Bet, ID, Probability, Odds, EV, Kelly 1/4, Signal, Direction, Rec. Stake |
| 3 | Verify sorting | Bets with signals appear first |
| 4 | Check signal banner | "🔔 N bets with active signals" or "No significant signals" |

### T3.2 — Signals tab
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Go to Roulette → Signals | Bet selector dropdown |
| 2 | Select "red" | EI, Max Z, Direction, Signal metrics shown |
| 3 | Check Z-score chart | Bar chart with Z=±2 and Z=±3 reference lines |
| 4 | Select "num_0" | Chart updates for num_0 |

### T3.3 — Monte Carlo tab
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Go to Roulette → Monte Carlo | Slider + "Run Monte Carlo" button |
| 2 | Set 5000, click button | Spinner → 6 metrics + histogram |
| 3 | Set 20000, click button | More simulations, tighter distribution |
| 4 | Verify histogram has reference lines | Break-even (red) and mean (green) |

---

## Test Suite 4: Poker Page

### T4.1 — Recommendations tab
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Go to Poker → Recommendations | Table with 10 hand rankings |
| 2 | Check probability chart | Bar chart showing hand distribution |
| 3 | Verify Royal Flush is rarest | Smallest bar |

### T4.2 — Monte Carlo tab
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Go to Poker → Monte Carlo | Slider + button |
| 2 | Set 5000, click button | Metrics + histogram appear |
| 3 | Verify independent simulation | Different from roulette (game-outcome simulation) |

---

## Test Suite 5: Portfolio Page

### T5.1 — Overview metrics
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Go to Portfolio | 3 metrics: Bankroll, Max Exposure, Max Per Bet |
| 2 | Verify values | Bankroll=1000, Max Exposure=500, Max Per Bet=100 |

### T5.2 — Active signals
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Check signals section | Shows signals from both Roulette and Poker |
| 2 | If no data | "No active signals. Add some history data..." |

### T5.3 — Combined optimization
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click "Optimize Combined Portfolio" | Allocation table with Game column |
| 2 | Check risk status | Green "✅ Risk limits OK" or warning |
| 3 | Check Total Exposure and Expected Return | Both metrics shown |

### T5.4 — Loss distribution
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Scroll to Loss Distribution | 4 metrics: Best/Worst/Expected/P(Profit) |
| 2 | Check scenario chart | 37 bars (one per roulette number) |

---

## Test Suite 6: History & Signals Page

### T6.1 — Record Draw tab
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Go to History → Record Draw | Number input (0-36) |
| 2 | Enter 17 | Shows winning bets: num_17, black, odd, low, dozen_2, col_2 |
| 3 | Click "Record Draw" | Success message with draw ID |
| 4 | Enter 0 | Shows only num_0 (no color/even-odd/dozen/col) |
| 5 | Click "Record Draw" | Success |
| 6 | Generate 50 random draws | Counter updates |

### T6.2 — Z-Score Dashboard tab
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Go to History → Z-Score Dashboard | Top 20 signals table |
| 2 | Check heatmap | Z-Score by Bet × Window heatmap |
| 3 | Verify color scale | Red=negative Z, Blue=positive Z, White=0 |

### T6.3 — Draw History tab
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Go to History → Draw History | Table with ID, Time, Outcome, Won Bets |
| 2 | Adjust slider to 10 | Shows last 10 draws |
| 3 | Adjust slider to 100 | Shows last 100 draws |

---

## Test Suite 7: Settings Page

### T7.1 — Bankroll
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Go to Settings → Bankroll | Number input showing 1000 |
| 2 | Change to 5000 | "Bankroll updated to 5,000 zł" |
| 3 | Check sidebar | Shows 5,000 zł |

### T7.2 — Risk limits display
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Check risk limits section | 6 metrics: 10%, 20%, 30%, 50%, 25%, 100 zł |

### T7.3 — Model parameters
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Go to Settings → Model Parameters | EI weights, MRF, signal thresholds shown |
| 2 | Verify EI weights | 50:0.10, 100:0.20, 250:0.30, 500:0.40 |
| 3 | Verify MRF default | 0.35 |
| 4 | Verify signal thresholds | 5 levels from "No signal" to "Maximum exposure" |

### T7.4 — Data management
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click "Clear Roulette History" | "Roulette history cleared" |
| 2 | Go to History page | Draw count is 0 |
| 3 | Click "Clear Poker History" | "Poker history cleared" |

---

## Test Suite 8: Edge Cases & Stress

### T8.1 — Empty state
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Clear all history | All pages show "no data" messages, no crashes |
| 2 | Go to Roulette → Signals | "Need at least 10 draws" warning |
| 3 | Go to Portfolio → Optimize | "No positive-EV bets found" |

### T8.2 — Large data
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Generate 1000 random draws | No crash, pages still responsive |
| 2 | Run Monte Carlo with 50000 sims | Completes within 30 seconds |
| 3 | Check all pages | All charts render correctly |

### T8.3 — Rapid navigation
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click through all 6 pages rapidly | No errors, no white screens |
| 2 | Switch between tabs on each page | Content updates correctly |

### T8.4 — Browser refresh
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Record some draws | Data in DB |
| 2 | Refresh browser (F5) | Bankroll resets to 1000, DB data persists |
| 3 | Check history | Previously recorded draws still visible |

### T8.5 — Concurrent access
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open app in two browser tabs | Both work independently |
| 2 | Record draw in tab 1 | Tab 2 sees updated count after refresh |

---

## Test Suite 9: Data Integrity

### T9.1 — Roulette draw correctness
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Record draw for 1 (red, odd, low, dozen_1, col_1) | All 6 bets recorded |
| 2 | Record draw for 2 (black, even, low, dozen_1, col_2) | All 6 bets recorded |
| 3 | Record draw for 0 | Only num_0 recorded |

### T9.2 — Z-score direction
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Generate 200 draws with 70% red | Z-score for "red" is positive (over) |
| 2 | Z-score for "black" is negative (under) | Confirmed |

### T9.3 — Kelly correctness
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Check any roulette bet | Kelly = 0 (negative EV) |
| 2 | Check poker bets | Some may have positive Kelly if odds > 1/p |

---

## Pass/Fail Criteria

| Suite | Tests | Pass Condition |
|-------|-------|---------------|
| T1: Navigation | 3 | All pages load, bankroll updates |
| T2: Tutorial | 14 | All 15 steps navigable, all interactive elements work |
| T3: Roulette | 3 | All 3 tabs functional, charts render |
| T4: Poker | 2 | Both tabs functional |
| T5: Portfolio | 4 | Combined optimization works, loss distribution shows |
| T6: History | 3 | Draw recording, Z-score dashboard, history browser work |
| T7: Settings | 4 | Bankroll update, clear history, parameters display |
| T8: Edge Cases | 5 | No crashes on empty/large data, refresh works |
| T9: Data Integrity | 3 | Correct bet detection, Z-score direction, Kelly values |

**Total: 41 manual test scenarios**
