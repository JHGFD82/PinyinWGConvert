"""
Example: what a Yale romanization strategy could look like.

Like bopomofo_example.py, this file is not wired into RoManTools - it's
not registered in factory.py or listed in constants.supported_methods, so
nothing ever runs this code. It's a worked example, meant to show how
little code a genuinely new (Latin-alphabet-based) romanization method
needs, since Yale is structurally close to Pinyin: mostly it's a case of
different letter choices for the same sounds (Yale spells with "j" what
Pinyin spells "zh", and "ch" what Pinyin spells "q", for example), rather
than fundamentally different parsing rules. See base.py for what a
"strategy" is, and CLAUDE.md's "Adding New Romanization Methods" section
for the full checklist for adding a real one.
"""

from typing import TYPE_CHECKING
from .base import RomanizationStrategy
from ..constants import vowels

if TYPE_CHECKING:
    from ..syllable import Syllable


class YaleStrategy(RomanizationStrategy):
    """
    A worked example of Yale-specific parsing rules (see the module
    docstring above - this class is not registered anywhere and never runs).

    Yale characteristics this example accounts for:
    - No apostrophes in initials (like Pinyin, unlike Wade-Giles).
    - A different tone-marking system than Pinyin or Wade-Giles use.
    - A couple of consonant endings ("r", "w") that would need Yale-specific
      handling if this were built out for real.
    """

    def find_initial(self, text: str, syllable: "Syllable") -> str:
        """
        Extract the initial - character by character, the same basic
        approach Pinyin and Wade-Giles use (see syllable.py's
        Syllable._find_initial), since Yale doesn't need anything
        method-specific for this part.

        Args:
            text: The text to extract the initial from.
            syllable: The Syllable being built, for error reporting.

        Returns:
            The initial, or 'ø' if there isn't one.
        """
        # Yale initial detection with method-specific characteristics
        from ..constants import vowels, apostrophes, dashes

        for i, c in enumerate(text):
            if c in vowels:
                if i == 0:  # If a vowel is found at the beginning, return 'ø'
                    return 'ø'
                # Check if the initial is valid for Yale
                if (initial := text[:i]) not in self.processor.init_list:
                    syllable.error_tracker.add_invalid_initial(initial, text)
                    return text[:i]
                return initial
            if c in apostrophes:  # Yale typically doesn't use apostrophes
                return self.handle_apostrophe_in_initial(text, i)
            if c in dashes:  # Handle dashes
                return self.handle_dash_in_initial(text, i)

        return text

    def handle_apostrophe_in_initial(self, text: str, index: int) -> str:
        """
        Yale doesn't give apostrophes any special meaning inside an
        initial (unlike Wade-Giles), so this just uses the same default
        behavior as the base class (see
        RomanizationStrategy.handle_apostrophe_in_initial in base.py).

        Args:
            text: The text being processed.
            index: Where the apostrophe was found in `text`.

        Returns:
            The initial, without the apostrophe.
        """
        # Yale romanization typically doesn't use apostrophes in initials
        # So we use the default behavior (remove them)
        return text[:index]

    def find_final(self, text: str, initial: str, syllable: "Syllable") -> str:
        """
        Extract the final using the same vowel/consonant approach Pinyin
        uses (see syllable.py's handle_vowel_case), except for consonant
        endings, which get Yale-specific handling below.

        Args:
            text: The remaining text to extract the final from.
            initial: The syllable's already-known initial.
            syllable: The Syllable being built, for its shared helper methods.

        Returns:
            The final.
        """
        for i, c in enumerate(text):
            if c in vowels:
                # Yale might have different vowel combination rules
                final = syllable.handle_vowel_case(text, i, initial)
                if final is not None:
                    return final
            else:
                # Yale consonant endings might be handled differently
                return self._handle_yale_consonant_case(text, i, initial, syllable)
        return text

    def _handle_yale_consonant_case(self, text: str, i: int, initial: str, syllable: "Syllable") -> str:
        """
        Handle the couple of consonant endings that would need Yale-
        specific rules (illustrative only - a real implementation would need
        to confirm the actual Yale rules here), falling back to Pinyin's
        general-purpose consonant handling for everything else.

        Args:
            text: The text being processed.
            i: Where the consonant was found in `text`.
            initial: The syllable's already-known initial.
            syllable: The Syllable being built, for its handle_consonant_case
                fallback method.

        Returns:
            The final.
        """
        # Example: Yale might handle 'r' endings differently than Pinyin
        if text[i] == 'r':
            # Yale-specific 'r' handling logic
            # Check if this is a valid Yale 'r' ending
            if self.processor.validate_final_using_array(initial, text[:i + 1], silent=True):
                return text[:i + 1]

        # Yale might handle 'w' endings uniquely
        if text[i] == 'w':
            # Yale-specific 'w' handling
            return text[:i + 1]

        # Fall back to standard consonant handling for other cases
        return syllable.handle_consonant_case(text, i, initial)

    def validate_syllable(self, initial: str, final: str, syllable: "Syllable") -> bool:
        """
        Check whether this initial+final combination is a valid Yale
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
        # Use the processor's validation method with Yale-specific considerations
        if initial == '':
            return self.processor.validate_final_using_array('ø', final)
        return self.processor.validate_final_using_array(initial, final)


# To register this strategy, simply add it to the factory in factory.py:
#
# strategies: Dict[str, Type[RomanizationStrategy]] = {
#     'py': PinyinStrategy,
#     'wg': WadeGilesStrategy,
#     'yale': YaleStrategy,  # Add this line
# }
#
# And add the import to __init__.py:
#
# from .yale import YaleStrategy
#
# __all__ = [
#     'RomanizationStrategy',
#     'PinyinStrategy',
#     'WadeGilesStrategy',
#     'YaleStrategy',  # Add this line
#     'RomanizationStrategyFactory'
# ]
