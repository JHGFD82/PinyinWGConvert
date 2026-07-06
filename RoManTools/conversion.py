"""
Romanization conversion utilities for romanized Mandarin text.

This module provides the `RomanizationConverter` class, which is used to convert romanized Chinese between different romanization systems (e.g., Pinyin, Wade-Giles).

Classes:
    RomanizationConverter: Converts romanized Chinese between different romanization systems.
"""

from functools import lru_cache
from .data_loader import load_conversion_data
from .config import Config


@lru_cache(maxsize=100000)
def _convert_syllable(convert_from: str, convert_to: str, text_to_convert: str) -> str:
    """
    Converts a single syllable between romanization methods.

    Module-level (not per-instance) so the cache is shared across every
    RomanizationConverter ever created with the same convert_from/convert_to
    pair — repeated syllables across separate convert_text()/cherry_pick()
    calls in a loop are only looked up once.

    Args:
        convert_from (str): The romanization system to convert from.
        convert_to (str): The romanization system to convert to.
        text_to_convert (str): The text to be converted.

    Returns:
        str: The converted text based on the selected romanization conversion mappings.
    """
    lowercased_text = text_to_convert.lower()
    for row in load_conversion_data():
        if row[convert_from].lower() == lowercased_text:
            if not row[convert_to] and row['meta'] == 'rare':
                return text_to_convert + '(!rare Pinyin!)'
            return row[convert_to]
    return text_to_convert + '(!)'


def clear_conversion_cache() -> None:
    """
    Clear the process-wide per-syllable conversion cache.

    Exposed mainly for tests that need a clean cache to make assertions
    about cache hits/misses independent of what ran earlier in the process.
    """
    _convert_syllable.cache_clear()


class RomanizationConverter:
    """
    Converts romanized Chinese between different romanization systems.

    Attributes:
        convert_from (str): The romanization system to convert from (e.g., 'py').
        convert_to (str): The romanization system to convert to (e.g., 'wg').
        config (Config): The configuration object for the conversion.
    """

    def __init__(self, convert_from: str, convert_to: str, config: Config):
        """
        Initialize a RomanizationConverter with the provided conversion systems and configuration.

        Args:
            convert_from (str): The romanization system to convert from.
            convert_to (str): The romanization system to convert to.
            config (Config): The configuration object for the conversion.
        """
        self.convert_from = convert_from
        self.convert_to = convert_to
        self.config = config

    def convert(self, text: str) -> str:
        """
        Converts a given text and prints a crumb if enabled in the config.
        Also prints a crumb if the result was loaded from the cache.

        Args:
            text (str): The text to be converted.

        Returns:
            str: The converted text based on the selected romanization conversion mappings.
        """
        before_hits = _convert_syllable.cache_info().hits
        result = _convert_syllable(self.convert_from, self.convert_to, text)
        after_hits = _convert_syllable.cache_info().hits

        if after_hits > before_hits and self.config.crumbs:
            self.config.print_crumb(2, "Cached", f'"{text}" -> "{result}"')
        else:
            self.config.print_crumb(2, "Converted text", f'"{text}" -> "{result}"')
        return result
