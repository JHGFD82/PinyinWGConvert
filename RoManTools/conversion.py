"""
Converting one already-identified syllable into another romanization method.

By the time this module gets involved, RoManTools has already worked out
that a piece of text is a syllable (see syllable.py) - all that's left is
looking up its spelling in the other method. That lookup is just a row in
the conversion table loaded by data_loader.load_conversion_data: find the
row where this syllable's spelling matches, and read off its spelling in
the target method.

Classes:
    RomanizationConverter: Converts one syllable at a time between
        romanization methods, and prints a breadcrumb for each conversion.
"""

from functools import lru_cache
from .data_loader import load_conversion_data
from .config import Config


@lru_cache(maxsize=100000)
def _convert_syllable(convert_from: str, convert_to: str, text_to_convert: str) -> str:
    """
    Look up one syllable's spelling in another romanization method.

    This function remembers results it's already computed (a "cache"), and
    is defined at the module level - shared by every RomanizationConverter
    ever created with the same convert_from/convert_to pair - rather than
    each converter keeping its own private cache. That matters if you're
    calling convert_text() or cherry_pick() many times in a loop (e.g. over
    a column of a dataset): a syllable that comes up again, even in a
    completely separate call, is looked up once and reused after that,
    instead of re-scanning the conversion table every time.

    Args:
        convert_from (str): The romanization method to convert from.
        convert_to (str): The romanization method to convert to.
        text_to_convert (str): The syllable to convert.

    Returns:
        str: The syllable's spelling in `convert_to`.
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
    Empty the shared per-syllable conversion cache described above.

    Mainly useful in tests that need to check whether a particular
    conversion was a fresh lookup or a cache hit, independent of whatever
    else has already run earlier in the same process.
    """
    _convert_syllable.cache_clear()


class RomanizationConverter:
    """
    Converts syllables between romanization methods, one at a time, and
    prints a breadcrumb describing each conversion when `config.crumbs` is on.

    Attributes:
        convert_from (str): The romanization method to convert from (e.g. 'py').
        convert_to (str): The romanization method to convert to (e.g. 'wg').
        config (Config): The settings for this run (see config.py).
    """

    def __init__(self, convert_from: str, convert_to: str, config: Config):
        """
        Args:
            convert_from (str): The romanization method to convert from.
            convert_to (str): The romanization method to convert to.
            config (Config): The settings for this run.
        """
        self.convert_from = convert_from
        self.convert_to = convert_to
        self.config = config

    def convert(self, text: str) -> str:
        """
        Convert one syllable and print a breadcrumb describing what
        happened - noting specifically whether the result came from the
        cache (see _convert_syllable above) or was looked up fresh.

        Args:
            text (str): The syllable to convert.

        Returns:
            str: The converted syllable.
        """
        before_hits = _convert_syllable.cache_info().hits
        result = _convert_syllable(self.convert_from, self.convert_to, text)
        after_hits = _convert_syllable.cache_info().hits

        if after_hits > before_hits and self.config.crumbs:
            self.config.print_crumb(2, "Cached", f'"{text}" -> "{result}"')
        else:
            self.config.print_crumb(2, "Converted text", f'"{text}" -> "{result}"')
        return result
