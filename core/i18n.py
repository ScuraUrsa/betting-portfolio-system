"""Internationalization (i18n) module for the Betting Portfolio System.

Supports English (en) and Polish (pl) with a simple key-value translation
system. Format placeholders use Python's str.format() syntax.

Usage:
    from core.i18n import Translator

    t = Translator()
    t.set_lang("pl")
    print(t.t("app_title"))  # "System Portfela Zakładów"
    print(t.t("bankroll_value", bankroll="1,000 zł"))
"""

from __future__ import annotations

from typing import Any

# ── English translations ─────────────────────────────────────────────

LANG_EN: dict[str, str] = {
    # App shell
    "app_title": "Betting Portfolio System",
    "app_subtitle": "Game-agnostic portfolio optimization",
    "app_tagline": "Z-score · Extremum Index · Kelly · Monte Carlo",
    "bankroll_label": "Bankroll",
    "bankroll_value": "Bankroll: {bankroll}",
    "navigation_label": "Navigation",

    # Navigation items
    "nav_tutorial": "🎓 Tutorial",
    "nav_roulette": "🎰 Roulette",
    "nav_poker": "🃏 Poker",
    "nav_portfolio": "📊 Portfolio",
    "nav_history": "📈 History & Signals",
    "nav_settings": "⚙️ Settings",

    # Tutorial
    "tutorial_title": "🎓 Interactive Tutorial",
    "tutorial_subtitle": "Step-by-step walkthrough of every feature in the Betting Portfolio System",
    "tutorial_steps_title": "Tutorial Steps",
    "tutorial_prev": "← Previous",
    "tutorial_next": "Next →",
    "tutorial_welcome": "Welcome to the Betting Portfolio System",
    "tutorial_what_is": "What is this system?",
    "tutorial_description": "This is a game-agnostic betting portfolio optimization engine. It doesn't try to predict which bet will win. Instead, it answers a much harder question:",
    "tutorial_quote": "\"How should I distribute my capital across all available bets, considering local extremes, mean reversion, correlations between bets, and the expected profit/risk profile of the entire portfolio?\"",
    "tutorial_concepts_title": "Key concepts you'll learn:",
    "tutorial_supported_games": "Supported games:",
    "tutorial_cta": "Click \"Next →\" to start exploring!",

    # Roulette
    "roulette_title": "🎰 Roulette — European (37 fields)",
    "roulette_tab_wheel": "🎡 Wheel",
    "roulette_tab_numbers": "🔢 Numbers",
    "roulette_tab_other": "🎯 Other Bets",
    "roulette_tab_french": "🇫🇷 French Bets",
    "roulette_tab_signals": "📈 Signals",
    "roulette_tab_monte_carlo": "🎲 Monte Carlo",
    "roulette_wheel_title": "🎡 European Roulette Wheel",
    "roulette_wheel_hint": "Hover over any number to see all properties, neighbors, and opposite numbers",
    "roulette_lookup_title": "🔍 Number Lookup",
    "roulette_lookup_label": "Enter a number (0-36)",
    "roulette_numbers_title": "🔢 Straight-Up Numbers (0-36)",
    "roulette_numbers_hint": "Bet on individual numbers — each pays 36:1",
    "roulette_other_title": "🎯 Outside & Group Bets",
    "roulette_other_hint": "Red/Black, Even/Odd, Low/High, Dozens, Columns",
    "roulette_french_title": "🇫🇷 French Announced Bets (Les Annonces)",
    "roulette_french_hint": "Traditional French roulette call bets covering specific wheel sectors",
    "roulette_french_jeu0": "🎯 Jeu 0 (Zero Game)",
    "roulette_french_voisins": "🟢 Voisins du Zéro (Neighbors of Zero)",
    "roulette_french_tiers": "🔵 Tiers du Cylindre (Thirds of the Wheel)",
    "roulette_french_orphelins": "🟠 Orphelins (Orphans)",
    "roulette_french_coverage": "These numbers are adjacent on the wheel. Bet covers {covered}/{total} = {pct:.1f}% of the wheel.",
    "roulette_signal_title": "Extremum Index by Bet",
    "roulette_signal_select": "Select bet",
    "roulette_monte_carlo_title": "Monte Carlo Simulation",
    "roulette_monte_carlo_slider": "Simulations",
    "roulette_monte_carlo_button": "Run Monte Carlo",
    "roulette_monte_carlo_running": "Running {n:,} simulations...",

    # Recommendations table
    "rec_bet": "Bet",
    "rec_id": "ID",
    "rec_probability": "Probability",
    "rec_odds": "Odds",
    "rec_ev": "EV",
    "rec_kelly": "Kelly 1/4",
    "rec_signal": "Signal",
    "rec_direction": "Direction",
    "rec_stake_pct": "Rec. Stake %",
    "rec_stake_pln": "Rec. Stake zł",
    "active_signals_count": "🔔 {count} bets with active signals",
    "no_signals": "No significant signals detected",

    # Metrics
    "metric_ei": "EI",
    "metric_max_z": "Max Z",
    "metric_direction": "Direction",
    "metric_signal": "Signal",
    "metric_expected_return": "Expected Return",
    "metric_std_dev": "Std Dev",
    "metric_max_drawdown": "Max Drawdown",
    "metric_ruin_prob": "Ruin Prob",
    "metric_var_95": "VaR 95%",
    "metric_cvar_95": "CVaR 95%",
    "metric_color": "Color",
    "metric_parity": "Parity",
    "metric_half": "Half",
    "metric_dozen": "Dozen",
    "metric_column": "Column",
    "metric_section": "Section",
    "metric_wheel_pos": "Wheel Position",

    # Number properties
    "prop_green": "Green",
    "prop_red": "Red",
    "prop_black": "Black",
    "prop_even": "Even",
    "prop_odd": "Odd",
    "prop_low": "Low (1-18)",
    "prop_high": "High (19-36)",
    "prop_na": "—",
    "prop_dozen_1": "1st 12",
    "prop_dozen_2": "2nd 12",
    "prop_dozen_3": "3rd 12",
    "prop_col_1": "Column 1",
    "prop_col_2": "Column 2",
    "prop_col_3": "Column 3",
    "prop_jeu0": "Jeu 0",
    "prop_voisins": "Voisins du Zéro",
    "prop_tiers": "Tiers du Cylindre",
    "prop_orphelins": "Orphelins",

    # Neighbors / opposite
    "neighbors_label": "← Neighbors (2 each side) →",
    "opposite_label": "Opposite (positions +18/+19)",

    # Poker
    "poker_title": "🃏 Poker — Texas Hold'em Hand Rankings",
    "poker_tab_rankings": "🏆 Rankings",
    "poker_tab_distribution": "📊 Distribution",
    "poker_tab_monte_carlo": "🎲 Monte Carlo",
    "poker_rankings_title": "Hand Rankings",
    "poker_rankings_hint": "Standard Texas Hold'em hand rankings with probabilities",
    "poker_distribution_title": "Probability Distribution",
    "poker_monte_carlo_title": "Monte Carlo Simulation",

    # Portfolio
    "portfolio_title": "📊 Portfolio — Cross-Game Optimization",
    "portfolio_tab_overview": "📋 Overview",
    "portfolio_tab_allocation": "💰 Allocation",
    "portfolio_tab_loss": "📉 Loss Distribution",
    "portfolio_overview_title": "Portfolio Overview",
    "portfolio_allocation_title": "Capital Allocation",
    "portfolio_loss_title": "Loss Distribution Analysis",

    # History
    "history_title": "📈 History & Signals",
    "history_tab_draws": "📝 Draw History",
    "history_tab_heatmap": "🔥 Z-Score Heatmap",
    "history_tab_record": "➕ Record Draw",
    "history_draws_title": "Draw History",
    "history_heatmap_title": "Z-Score Heatmap",
    "history_record_title": "Record New Draw",

    # Settings
    "settings_title": "⚙️ Settings",
    "settings_language": "🌐 Language",
    "settings_language_hint": "Select interface language",
    "settings_bankroll": "💰 Bankroll",
    "settings_bankroll_hint": "Starting capital for portfolio optimization",
    "settings_risk": "🛡️ Risk Limits",
    "settings_risk_hint": "Maximum exposure per bet, hand, draw, and total",
    "settings_signals": "📶 Signal Thresholds",
    "settings_signals_hint": "EI thresholds for signal levels",
    "settings_mrf": "📐 Mean Reversion Factor",
    "settings_mrf_hint": "Learned parameter: how often extremes regress to the mean",

    # Page crash
    "page_crashed": "Page crashed: {error}",

    # Z-score chart
    "zscore_chart_title": "Z-Score by Window — {bet_id}",

    # Monte Carlo results
    "mc_profit_distribution": "Profit Distribution ({n:,} simulations)",
    "mc_break_even": "Break-even",
    "mc_mean": "Mean: {value:+.1f}",

    # French bets sections
    "french_numbers_count": "{count} numbers",
}

# ── Polish translations ──────────────────────────────────────────────

LANG_PL: dict[str, str] = {
    # App shell
    "app_title": "System Portfela Zakładów",
    "app_subtitle": "Optymalizacja portfela niezależna od gry",
    "app_tagline": "Z-score · Extremum Index · Kelly · Monte Carlo",
    "bankroll_label": "Kapitał",
    "bankroll_value": "Kapitał: {bankroll}",
    "navigation_label": "Nawigacja",

    # Navigation items
    "nav_tutorial": "🎓 Samouczek",
    "nav_roulette": "🎰 Ruletka",
    "nav_poker": "🃏 Poker",
    "nav_portfolio": "📊 Portfel",
    "nav_history": "📈 Historia i Sygnały",
    "nav_settings": "⚙️ Ustawienia",

    # Tutorial
    "tutorial_title": "🎓 Interaktywny Samouczek",
    "tutorial_subtitle": "Przewodnik krok po kroku po wszystkich funkcjach Systemu Portfela Zakładów",
    "tutorial_steps_title": "Kroki Samouczka",
    "tutorial_prev": "← Poprzedni",
    "tutorial_next": "Następny →",
    "tutorial_welcome": "Witaj w Systemie Portfela Zakładów",
    "tutorial_what_is": "Czym jest ten system?",
    "tutorial_description": "To silnik optymalizacji portfela zakładów niezależny od gry. Nie próbuje przewidzieć, który zakład wygra. Zamiast tego odpowiada na znacznie trudniejsze pytanie:",
    "tutorial_quote": "\"Jak rozdzielić kapitał pomiędzy wszystkie dostępne zakłady, uwzględniając lokalne ekstrema, regresję do średniej, korelacje między zakładami oraz oczekiwany profil zysku/ryzyka całego portfela?\"",
    "tutorial_concepts_title": "Kluczowe pojęcia, których się nauczysz:",
    "tutorial_supported_games": "Obsługiwane gry:",
    "tutorial_cta": "Kliknij \"Następny →\" aby rozpocząć!",

    # Roulette
    "roulette_title": "🎰 Ruletka — Europejska (37 pól)",
    "roulette_tab_wheel": "🎡 Koło",
    "roulette_tab_numbers": "🔢 Numery",
    "roulette_tab_other": "🎯 Pozostałe Zakłady",
    "roulette_tab_french": "🇫🇷 Zakłady Francuskie",
    "roulette_tab_signals": "📈 Sygnały",
    "roulette_tab_monte_carlo": "🎲 Monte Carlo",
    "roulette_wheel_title": "🎡 Koło Ruletki Europejskiej",
    "roulette_wheel_hint": "Najedź na numer, aby zobaczyć wszystkie właściwości, sąsiadów i przeciwne numery",
    "roulette_lookup_title": "🔍 Wyszukiwarka Numerów",
    "roulette_lookup_label": "Wprowadź numer (0-36)",
    "roulette_numbers_title": "🔢 Zakłady Proste (0-36)",
    "roulette_numbers_hint": "Zakład na pojedynczy numer — wypłaca 36:1",
    "roulette_other_title": "🎯 Zakłady Zewnętrzne i Grupowe",
    "roulette_other_hint": "Czerwone/Czarne, Parzyste/Nieparzyste, Niskie/Wysokie, Tuziny, Kolumny",
    "roulette_french_title": "🇫🇷 Francuskie Zakłady Ogłaszane (Les Annonces)",
    "roulette_french_hint": "Tradycyjne francuskie zakłady ruletkowe obejmujące określone sektory koła",
    "roulette_french_jeu0": "🎯 Jeu 0 (Gra Zero)",
    "roulette_french_voisins": "🟢 Voisins du Zéro (Sąsiedzi Zera)",
    "roulette_french_tiers": "🔵 Tiers du Cylindre (Trzecie Koła)",
    "roulette_french_orphelins": "🟠 Orphelins (Sieroty)",
    "roulette_french_coverage": "Te numery sąsiadują ze sobą na kole. Zakład obejmuje {covered}/{total} = {pct:.1f}% koła.",
    "roulette_signal_title": "Extremum Index według Zakładu",
    "roulette_signal_select": "Wybierz zakład",
    "roulette_monte_carlo_title": "Symulacja Monte Carlo",
    "roulette_monte_carlo_slider": "Liczba symulacji",
    "roulette_monte_carlo_button": "Uruchom Monte Carlo",
    "roulette_monte_carlo_running": "Uruchamiam {n:,} symulacji...",

    # Recommendations table
    "rec_bet": "Zakład",
    "rec_id": "ID",
    "rec_probability": "Prawdopodobieństwo",
    "rec_odds": "Kurs",
    "rec_ev": "EV",
    "rec_kelly": "Kelly 1/4",
    "rec_signal": "Sygnał",
    "rec_direction": "Kierunek",
    "rec_stake_pct": "Stawka %",
    "rec_stake_pln": "Stawka zł",
    "active_signals_count": "🔔 {count} zakładów z aktywnymi sygnałami",
    "no_signals": "Brak istotnych sygnałów",

    # Metrics
    "metric_ei": "EI",
    "metric_max_z": "Max Z",
    "metric_direction": "Kierunek",
    "metric_signal": "Sygnał",
    "metric_expected_return": "Oczekiwany Zwrot",
    "metric_std_dev": "Odch. Std.",
    "metric_max_drawdown": "Max Drawdown",
    "metric_ruin_prob": "Prawd. Ruiny",
    "metric_var_95": "VaR 95%",
    "metric_cvar_95": "CVaR 95%",
    "metric_color": "Kolor",
    "metric_parity": "Parzystość",
    "metric_half": "Połowa",
    "metric_dozen": "Tuzin",
    "metric_column": "Kolumna",
    "metric_section": "Sekcja",
    "metric_wheel_pos": "Pozycja na Kole",

    # Number properties
    "prop_green": "Zielony",
    "prop_red": "Czerwony",
    "prop_black": "Czarny",
    "prop_even": "Parzyste",
    "prop_odd": "Nieparzyste",
    "prop_low": "Niskie (1-18)",
    "prop_high": "Wysokie (19-36)",
    "prop_na": "—",
    "prop_dozen_1": "1. tuzin",
    "prop_dozen_2": "2. tuzin",
    "prop_dozen_3": "3. tuzin",
    "prop_col_1": "Kolumna 1",
    "prop_col_2": "Kolumna 2",
    "prop_col_3": "Kolumna 3",
    "prop_jeu0": "Jeu 0",
    "prop_voisins": "Voisins du Zéro",
    "prop_tiers": "Tiers du Cylindre",
    "prop_orphelins": "Orphelins",

    # Neighbors / opposite
    "neighbors_label": "← Sąsiedzi (po 2 z każdej strony) →",
    "opposite_label": "Przeciwne (pozycje +18/+19)",

    # Poker
    "poker_title": "🃏 Poker — Rankingi Rąk Texas Hold'em",
    "poker_tab_rankings": "🏆 Rankingi",
    "poker_tab_distribution": "📊 Rozkład",
    "poker_tab_monte_carlo": "🎲 Monte Carlo",
    "poker_rankings_title": "Rankingi Rąk",
    "poker_rankings_hint": "Standardowe rankingi rąk Texas Hold'em z prawdopodobieństwami",
    "poker_distribution_title": "Rozkład Prawdopodobieństwa",
    "poker_monte_carlo_title": "Symulacja Monte Carlo",

    # Portfolio
    "portfolio_title": "📊 Portfel — Optymalizacja Międzygrami",
    "portfolio_tab_overview": "📋 Przegląd",
    "portfolio_tab_allocation": "💰 Alokacja",
    "portfolio_tab_loss": "📉 Rozkład Strat",
    "portfolio_overview_title": "Przegląd Portfela",
    "portfolio_allocation_title": "Alokacja Kapitału",
    "portfolio_loss_title": "Analiza Rozkładu Strat",

    # History
    "history_title": "📈 Historia i Sygnały",
    "history_tab_draws": "📝 Historia Losowań",
    "history_tab_heatmap": "🔥 Mapa Z-Score",
    "history_tab_record": "➕ Zapisz Losowanie",
    "history_draws_title": "Historia Losowań",
    "history_heatmap_title": "Mapa Cieplna Z-Score",
    "history_record_title": "Zapisz Nowe Losowanie",

    # Settings
    "settings_title": "⚙️ Ustawienia",
    "settings_language": "🌐 Język",
    "settings_language_hint": "Wybierz język interfejsu",
    "settings_bankroll": "💰 Kapitał",
    "settings_bankroll_hint": "Kapitał początkowy do optymalizacji portfela",
    "settings_risk": "🛡️ Limity Ryzyka",
    "settings_risk_hint": "Maksymalna ekspozycja na zakład, rozdanie, losowanie i łącznie",
    "settings_signals": "📶 Progi Sygnałów",
    "settings_signals_hint": "Progi EI dla poziomów sygnałów",
    "settings_mrf": "📐 Mean Reversion Factor",
    "settings_mrf_hint": "Parametr uczony: jak często ekstrema wracają do średniej",

    # Page crash
    "page_crashed": "Błąd strony: {error}",

    # Z-score chart
    "zscore_chart_title": "Z-Score według Okna — {bet_id}",

    # Monte Carlo results
    "mc_profit_distribution": "Rozkład Zysku ({n:,} symulacji)",
    "mc_break_even": "Próg rentowności",
    "mc_mean": "Średnia: {value:+.1f}",

    # French bets sections
    "french_numbers_count": "{count} liczb",
}

# ── Translator class ─────────────────────────────────────────────────

SUPPORTED_LANGS: dict[str, str] = {
    "en": "English",
    "pl": "Polski",
}


class Translator:
    """Simple key-value translator with format placeholder support.

    Usage:
        t = Translator()
        t.set_lang("pl")
        print(t.t("app_title"))  # "System Portfela Zakładów"
    """

    def __init__(self, lang: str = "en") -> None:
        self._lang: str = lang
        self._dicts: dict[str, dict[str, str]] = {
            "en": LANG_EN,
            "pl": LANG_PL,
        }

    @property
    def lang(self) -> str:
        """Current language code."""
        return self._lang

    def set_lang(self, lang: str) -> None:
        """Set the active language.

        Args:
            lang: Language code ('en' or 'pl').

        Raises:
            ValueError: If the language is not supported.
        """
        if lang not in SUPPORTED_LANGS:
            raise ValueError(
                f"Unsupported language: '{lang}'. "
                f"Available: {', '.join(SUPPORTED_LANGS)}"
            )
        self._lang = lang

    def available_languages(self) -> list[str]:
        """Return list of available language codes."""
        return list(SUPPORTED_LANGS.keys())

    def lang_name(self, code: str) -> str:
        """Return the display name for a language code."""
        return SUPPORTED_LANGS.get(code, code)

    def t(self, key: str, **kwargs: Any) -> str:
        """Translate a key to the current language.

        Args:
            key: Translation key.
            **kwargs: Format placeholders (e.g., count=5).

        Returns:
            Translated string with placeholders filled, or [key] if not found.
        """
        d = self._dicts.get(self._lang, LANG_EN)
        template = d.get(key)
        if template is None:
            return f"[{key}]"
        if kwargs:
            try:
                return template.format(**kwargs)
            except (KeyError, ValueError):
                return template
        return template
