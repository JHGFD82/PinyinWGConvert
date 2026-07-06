"""
Example: what a Bopomofo (Zhuyin) strategy could look like.

This file is not wired into RoManTools - it's not registered in factory.py
or listed in constants.supported_methods, so nothing in the package ever
actually runs this code. It exists purely as a worked example for anyone
who wants to add a new romanization method later (see base.py for what a
"strategy" is, and CLAUDE.md's "Adding New Romanization Methods" section
for the full checklist of steps - registering this file's class is one of
them).

Bopomofo (also called Zhuyin) doesn't use the Latin alphabet at all - it has
its own set of phonetic symbols (ㄅㄆㄇㄈ, etc.). This example assumes
someone has already spelled those symbols out using Latin letters (e.g.
typing "b" instead of "ㄅ"), and shows how that transliterated input could
be parsed the same way Pinyin and Wade-Giles are.
"""

from typing import TYPE_CHECKING, Optional
from .base import RomanizationStrategy
from ..constants import vowels

if TYPE_CHECKING:
    from ..syllable import Syllable


class BopomofoStrategy(RomanizationStrategy):
    """
    A worked example of Bopomofo-specific parsing rules (see the module
    docstring above - this class is not registered anywhere and never runs).

    Bopomofo characteristics this example accounts for:
    - Its own initials and finals, mapped from Latin-letter stand-ins to the
      actual Bopomofo symbols below (e.g. "b" -> "ㄅ").
    - Tone marks (ˊˇˋ˙) that need to be stripped out before parsing, rather
      than the numbered tones or bare vowels other methods use.
    - No apostrophes.
    - A more limited set of consonant endings than Pinyin or Wade-Giles.
    """

    # Bopomofo initials mapping (transliterated forms)
    BOPOMOFO_INITIALS = {
        'b': 'ㄅ', 'p': 'ㄆ', 'm': 'ㄇ', 'f': 'ㄈ',
        'd': 'ㄉ', 't': 'ㄊ', 'n': 'ㄋ', 'l': 'ㄌ',
        'g': 'ㄍ', 'k': 'ㄎ', 'h': 'ㄏ',
        'j': 'ㄐ', 'q': 'ㄑ', 'x': 'ㄒ',
        'zh': 'ㄓ', 'ch': 'ㄔ', 'sh': 'ㄕ', 'r': 'ㄖ',
        'z': 'ㄗ', 'c': 'ㄘ', 's': 'ㄙ'
    }

    # Bopomofo finals mapping (transliterated forms)
    BOPOMOFO_FINALS = {
        'a': 'ㄚ', 'o': 'ㄛ', 'e': 'ㄜ', 'i': 'ㄧ', 'u': 'ㄨ', 'v': 'ㄩ',
        'ai': 'ㄞ', 'ei': 'ㄟ', 'ao': 'ㄠ', 'ou': 'ㄡ',
        'an': 'ㄢ', 'en': 'ㄣ', 'ang': 'ㄤ', 'eng': 'ㄥ',
        'er': 'ㄦ'
    }

    def find_initial(self, text: str, syllable: "Syllable") -> str:
        """
        Extract the initial, after first stripping tone marks out of the
        way (see _remove_tone_marks below).

        Args:
            text: The text to extract the initial from.
            syllable: The Syllable being built, for error reporting.

        Returns:
            The initial, or 'ø' if there isn't one.
        """
        # Bopomofo initial detection with tone mark handling
        from ..constants import vowels, apostrophes, dashes

        # Remove tone marks first
        text_clean = self._remove_tone_marks(text)

        for i, c in enumerate(text_clean):
            if c in vowels:
                if i == 0:  # If a vowel is found at the beginning, return 'ø'
                    return 'ø'
                # Check if the initial is valid for Bopomofo
                if (initial := text_clean[:i]) not in self.processor.init_list:
                    syllable.error_tracker.add_invalid_initial(initial, text_clean)
                    return text_clean[:i]
                return initial
            if c in apostrophes:  # Bopomofo doesn't use apostrophes
                return self.handle_apostrophe_in_initial(text_clean, i)
            if c in dashes:  # Handle dashes
                return self.handle_dash_in_initial(text_clean, i)

        return text_clean

    def handle_apostrophe_in_initial(self, text: str, index: int) -> str:
        """
        Bopomofo doesn't use apostrophes at all, so one appearing here is
        just discarded rather than kept as part of the initial.

        Args:
            text: The text being processed.
            index: Where the apostrophe was found in `text`.

        Returns:
            The initial, without the apostrophe.
        """
        # Bopomofo doesn't use apostrophes, so remove them
        return text[:index]

    def find_final(self, text: str, initial: str, syllable: "Syllable") -> str:
        """
        Extract the final, after stripping tone marks, by first checking a
        list of known multi-letter finals and falling back to the same
        vowel/consonant handling Pinyin uses (see syllable.py's
        handle_vowel_case/handle_consonant_case) for anything not on that list.

        Args:
            text: The remaining text to extract the final from.
            initial: The syllable's already-known initial.
            syllable: The Syllable being built, for its shared helper methods.

        Returns:
            The final.
        """
        # Handle tone markers first (Bopomofo uses specific tone marks)
        text_without_tones = self._remove_tone_marks(text)

        # Bopomofo has specific final patterns
        for i, c in enumerate(text_without_tones):
            if c in vowels:
                # Bopomofo vowel combinations follow different rules
                final = self._handle_bopomofo_vowel_case(text_without_tones, i, initial, syllable)
                if final is not None:
                    return final
            else:
                # Bopomofo consonant endings are more limited
                return self._handle_bopomofo_consonant_case(text_without_tones, i, initial, syllable)

        return text_without_tones

    def validate_syllable(self, initial: str, final: str, syllable: "Syllable") -> bool:
        """
        Check whether this initial+final combination is a valid Bopomofo
        syllable, using the same validity-table lookup every method uses
        (see SyllableProcessor.validate_final_using_array in syllable.py).

        Args:
            initial: The initial to check.
            final: The final to check.
            syllable: The Syllable being built (kept for a consistent method
                signature; not needed by this implementation).

        Returns:
            True if the combination is valid.
        """
        # Use the processor's validation method with Bopomofo-specific considerations
        if initial == '':
            return self.processor.validate_final_using_array('ø', final)
        return self.processor.validate_final_using_array(initial, final)

    def _remove_tone_marks(self, text: str) -> str:
        """
        Strip Bopomofo's tone marks out of `text` before parsing: ˊ (2nd
        tone), ˇ (3rd tone), ˋ (4th tone), ˙ (light tone). The 1st tone has
        no mark at all, so there's nothing to remove for it.

        Args:
            text: The text possibly containing tone marks.

        Returns:
            `text` with any tone marks removed.
        """
        tone_marks = ['ˊ', 'ˇ', 'ˋ', '˙']
        for mark in tone_marks:
            text = text.replace(mark, '')
        return text

    def _handle_bopomofo_vowel_case(self, text: str, i: int, initial: str, syllable: "Syllable") -> Optional[str]:
        """
        Try Bopomofo's known multi-letter final patterns (longest first)
        before falling back to Pinyin's general-purpose vowel handling for
        anything not on that list.

        Args:
            text: The text being processed.
            i: Where the vowel was found in `text`.
            initial: The syllable's already-known initial.
            syllable: The Syllable being built, for its handle_vowel_case
                fallback method.

        Returns:
            The final, or None to signal "keep scanning".
        """
        # Check for common Bopomofo vowel combinations
        remaining_text = text[i:]

        # Try longer combinations first (greedy matching)
        bopomofo_finals = ['ang', 'eng', 'ong', 'ai', 'ei', 'ao', 'ou', 'an', 'en', 'er']
        for final_pattern in bopomofo_finals:
            if remaining_text.startswith(final_pattern):
                # Check if this is a valid Bopomofo combination
                if self.processor.validate_final_using_array(initial, final_pattern, silent=True):
                    return final_pattern

        # Fall back to single vowel
        if i + 1 == len(text):
            return text[i:]  # Single vowel at end

        # Use standard vowel case handling for complex cases
        vowel_result = syllable.handle_vowel_case(text, i, initial)
        return vowel_result if vowel_result is not None else text[i:]

    def _handle_bopomofo_consonant_case(self, text: str, i: int, initial: str, syllable: "Syllable") -> str:
        """
        Handle Bopomofo's small set of valid consonant endings ("n", "ng",
        and "r" - as in the "r" ending that colors the preceding vowel,
        called erhua/儿化音), falling back to Pinyin's general-purpose
        consonant handling for anything else.

        Args:
            text: The text being processed.
            i: Where the consonant was found in `text`.
            initial: The syllable's already-known initial.
            syllable: The Syllable being built, for its handle_consonant_case
                fallback method.

        Returns:
            The final.
        """
        remainder = len(text) - i - 1

        # Handle "ng" ending (common in Bopomofo)
        if text[i] == 'n' and remainder > 0 and text[i + 1] == 'g':
            if self.processor.validate_final_using_array(initial, text[:i + 2], silent=True):
                return text[:i + 2]  # Return "ng"

        # Handle "n" ending
        if text[i] == 'n':
            if remainder == 0 or self.processor.validate_final_using_array(initial, text[:i + 1], silent=True):
                return text[:i + 1]  # Return "n"

        # Handle "r" ending (like 儿化音)
        if text[i] == 'r':
            if remainder == 0 or self.processor.validate_final_using_array(initial, text[:i + 1], silent=True):
                return text[:i + 1]  # Return "r"

        # Fall back to standard consonant handling
        return syllable.handle_consonant_case(text, i, initial)

    def get_bopomofo_representation(self, initial: str, final: str) -> str:
        """
        Convert a romanized (Latin-letter) initial and final into their
        actual Bopomofo symbols, using the two lookup dictionaries above.
        Not used anywhere in parsing - this would only matter if someone
        wanted to display real Bopomofo symbols rather than the
        transliterated form.

        Args:
            initial: The romanized initial.
            final: The romanized final.

        Returns:
            The Bopomofo symbol representation.
        """
        bopomofo_initial = self.BOPOMOFO_INITIALS.get(initial, '')
        bopomofo_final = self.BOPOMOFO_FINALS.get(final, final)

        return bopomofo_initial + bopomofo_final


# To register this strategy, add it to the factory in factory.py:
#
# strategies: Dict[str, Type[RomanizationStrategy]] = {
#     'py': PinyinStrategy,
#     'wg': WadeGilesStrategy,
#     'yale': YaleStrategy,
#     'bopomofo': BopomofoStrategy,  # Add this line
# }
#
# And add the import to __init__.py:
#
# from .bopomofo import BopomofoStrategy
#
# __all__ = [
#     'RomanizationStrategy',
#     'PinyinStrategy',
#     'WadeGilesStrategy',
#     'YaleStrategy',
#     'BopomofoStrategy',  # Add this line
#     'RomanizationStrategyFactory'
# ]
#
# Usage example:
# processor = SyllableProcessor(config, bopomofo_method_params)
# syllable = processor.create_syllable("jiang")  # Would process as Bopomofo
# bopomofo_repr = processor.strategy.get_bopomofo_representation("j", "iang")  # "ㄐㄧㄤ"
