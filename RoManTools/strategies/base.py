"""
The shared shape every romanization method's parsing rules must follow.

Pinyin and Wade-Giles both break a syllable into an initial and a final,
but the specific rules for doing so differ (Wade-Giles keeps apostrophes as
part of the initial, e.g. "ch'i"; Pinyin doesn't use apostrophes inside a
syllable at all). Rather than writing one big function full of
"if method is Pinyin do this, if method is Wade-Giles do that" checks,
RoManTools gives each method its own small object - called a strategy -
that implements the same set of methods, each in whatever way is correct
for that particular method. Code elsewhere (see SyllableProcessor and
Syllable in syllable.py) just calls `self.strategy.find_final(...)` and
gets the right behavior automatically for whichever method is active. This
approach is a common one in software design, usually called the "Strategy
pattern" - naming it is less important than the idea itself: swap out the
one part that's genuinely different, and share everything else.

This module defines the common shape (an "abstract base class") every
strategy must follow. "Abstract" means this class is never used directly -
it exists only to be built on top of by PinyinStrategy and WadeGilesStrategy
(see pinyin.py and wade_giles.py), each of which fills in the method-specific
details. Some methods below are marked `@abstractmethod`: every strategy
*must* provide its own version of these, or Python will refuse to create
the strategy at all. Others have a default implementation here that a
strategy can use as-is, or override if it needs to behave differently.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from ..syllable import SyllableProcessor, Syllable


class RomanizationStrategy(ABC):
    """
    The common shape shared by every romanization method's parsing rules.
    See the module docstring above for the full explanation.
    """

    def __init__(self, processor: "SyllableProcessor"):
        """
        Args:
            processor: The SyllableProcessor this strategy works with - it
                holds the shared data (the syllable-validity table, lists of
                valid initials/finals) the strategy needs to consult.
        """
        self.processor = processor

    def handle_apostrophe_in_initial(self, text: str, index: int) -> str:
        """
        Decide what to do when an apostrophe is found while reading a
        syllable's initial. The default (used by Pinyin, where apostrophes
        never belong inside a syllable) is to treat everything before the
        apostrophe as the initial and stop there; Wade-Giles overrides this,
        since it keeps the apostrophe as a meaningful part of the initial
        (e.g. "ch'i").

        Args:
            text: The text being parsed.
            index: Where the apostrophe was found in `text`.

        Returns:
            The initial, as this method's rules define it.
        """
        return text[:index]

    def handle_dash_in_initial(self, text: str, index: int) -> str:
        """
        Decide what to do when a dash is found while reading a syllable's
        initial. Default: treat everything before the dash as the initial.

        Args:
            text: The text being parsed.
            index: Where the dash was found in `text`.

        Returns:
            The initial, as this method's rules define it.
        """
        return text[:index]

    @abstractmethod
    def find_final(self, text: str, initial: str, syllable: "Syllable") -> str:
        """
        Work out a syllable's final, given its already-known initial. Every
        strategy must implement this - see PinyinStrategy.find_final and
        WadeGilesStrategy.find_final for the two very different approaches
        (Pinyin scans character-by-character; Wade-Giles tries progressively
        shorter candidate finals until one validates).

        Args:
            text: The remaining text to extract the final from.
            initial: The syllable's already-known initial.
            syllable: The Syllable being built, for access to its helper
                methods (handle_vowel_case, handle_consonant_case, etc. -
                see syllable.py).

        Returns:
            The final.
        """
        pass

    def get_illegal_characters(self) -> List[Tuple[str, str]]:
        """
        List the characters that should never appear in this romanization
        method's text at all, each paired with a short explanation. The
        default list below (digits, brackets, and other punctuation that
        has no place in romanized Mandarin) applies to every method;
        PinyinStrategy adds apostrophes to this list, since Pinyin only uses
        them as word separators, never inside a syllable.

        Returns:
            A list of (character, reason) pairs.
        """
        return [
            ('(', 'parentheses not allowed in romanized text'),
            (')', 'parentheses not allowed in romanized text'),
            ('[', 'brackets not allowed in romanized text'),
            (']', 'brackets not allowed in romanized text'),
            ('{', 'braces not allowed in romanized text'),
            ('}', 'braces not allowed in romanized text'),
            ('<', 'angle brackets not allowed in romanized text'),
            ('>', 'angle brackets not allowed in romanized text'),
            ('0', 'digits not allowed in romanized text'),
            ('1', 'digits not allowed in romanized text'),
            ('2', 'digits not allowed in romanized text'),
            ('3', 'digits not allowed in romanized text'),
            ('4', 'digits not allowed in romanized text'),
            ('5', 'digits not allowed in romanized text'),
            ('6', 'digits not allowed in romanized text'),
            ('7', 'digits not allowed in romanized text'),
            ('8', 'digits not allowed in romanized text'),
            ('9', 'digits not allowed in romanized text'),
            ('!', 'punctuation not allowed in romanized syllables'),
            ('?', 'punctuation not allowed in romanized syllables'),
            ('@', 'special character not allowed in romanized text'),
            ('#', 'special character not allowed in romanized text'),
            ('$', 'special character not allowed in romanized text'),
            ('%', 'special character not allowed in romanized text'),
            ('^', 'special character not allowed in romanized text'),
            ('&', 'special character not allowed in romanized text'),
            ('*', 'special character not allowed in romanized text'),
            ('=', 'special character not allowed in romanized text'),
            ('+', 'special character not allowed in romanized text'),
            ('_', 'underscore not allowed in romanized text'),
            ('|', 'special character not allowed in romanized text'),
            ('\\', 'special character not allowed in romanized text'),
            ('/', 'special character not allowed in romanized text'),
            (':', 'colon not allowed in romanized syllables'),
            (';', 'semicolon not allowed in romanized syllables'),
            (',', 'comma not allowed in romanized syllables'),
            ('.', 'period not allowed in romanized syllables'),
        ]

    def check_illegal_characters(self, text: str, syllable: "Syllable") -> List[Tuple[str, str]]:
        """
        Check `text` against this method's list of disallowed characters
        (from get_illegal_characters above) and report which ones, if any,
        were actually found.

        Args:
            text: The text to check.
            syllable: The Syllable this check is being run for (kept for a
                consistent method signature across strategies; this default
                implementation doesn't need anything from it).

        Returns:
            A list of (character, reason) pairs, one for each disallowed
            character actually found in `text`.
        """
        illegal_chars = self.get_illegal_characters()
        found_illegal: List[Tuple[str, str]] = []

        for char, reason in illegal_chars:
            if char in text:
                found_illegal.append((char, reason))

        return found_illegal
