"""Tests for the i18n (internationalization) module."""

import pytest
from core.i18n import Translator, LANG_EN, LANG_PL


class TestTranslatorBasics:
    """Basic translator functionality."""

    def test_default_language_is_english(self):
        t = Translator()
        assert t.lang == "en"

    def test_set_language_to_polish(self):
        t = Translator()
        t.set_lang("pl")
        assert t.lang == "pl"

    def test_set_invalid_language_raises(self):
        t = Translator()
        with pytest.raises(ValueError, match="Unsupported language"):
            t.set_lang("de")

    def test_available_languages(self):
        t = Translator()
        langs = t.available_languages()
        assert "en" in langs
        assert "pl" in langs
        assert len(langs) == 2

    def test_language_names(self):
        t = Translator()
        assert t.lang_name("en") == "English"
        assert t.lang_name("pl") == "Polski"


class TestTranslatorSimpleKeys:
    """Translating simple key-value pairs."""

    def test_translate_english_returns_key_value(self):
        t = Translator()
        assert t.t("app_title") == "Betting Portfolio System"

    def test_translate_polish_returns_polish_value(self):
        t = Translator()
        t.set_lang("pl")
        assert t.t("app_title") == "System Portfela Zakładów"

    def test_translate_unknown_key_returns_key_name(self):
        t = Translator()
        assert t.t("nonexistent_key") == "[nonexistent_key]"

    def test_translate_unknown_key_polish(self):
        t = Translator()
        t.set_lang("pl")
        assert t.t("nonexistent_key") == "[nonexistent_key]"


class TestTranslatorFormatting:
    """Translating with format placeholders."""

    def test_format_single_placeholder(self):
        t = Translator()
        result = t.t("bankroll_value", bankroll="1,000 zł")
        assert "1,000 zł" in result

    def test_format_multiple_placeholders(self):
        t = Translator()
        result = t.t("active_signals_count", count=5)
        assert "5" in result

    def test_format_missing_placeholder_uses_raw(self):
        t = Translator()
        result = t.t("bankroll_value")
        assert "{bankroll}" in result  # Falls back to raw template

    def test_format_polish_with_placeholders(self):
        t = Translator()
        t.set_lang("pl")
        result = t.t("active_signals_count", count=3)
        assert "3" in result


class TestTranslatorCoverage:
    """Ensure all required keys exist in both languages."""

    def test_all_keys_present_in_both_languages(self):
        t = Translator()
        en_keys = set(LANG_EN.keys())
        pl_keys = set(LANG_PL.keys())
        missing_in_pl = en_keys - pl_keys
        missing_in_en = pl_keys - en_keys
        assert not missing_in_pl, f"Keys missing in PL: {missing_in_pl}"
        assert not missing_in_en, f"Keys missing in EN: {missing_in_en}"

    def test_no_empty_translations(self):
        for key, val in LANG_EN.items():
            assert val.strip(), f"Empty EN translation for '{key}'"
        for key, val in LANG_PL.items():
            assert val.strip(), f"Empty PL translation for '{key}'"
