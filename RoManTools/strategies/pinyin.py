"""
Pinyin's specific parsing rules.

See base.py for what a "strategy" is and why this exists as its own class
rather than a set of if/else checks scattered through syllable.py.
"""

from typing import TYPE_CHECKING, List, Tuple
from .base import RomanizationStrategy
from ..constants import vowels, apostrophes

if TYPE_CHECKING:
    from ..syllable import Syllable


class PinyinStrategy(RomanizationStrategy):
    """
    Pinyin-specific parsing rules.

    Compared to Wade-Giles, Pinyin has simpler syllable boundaries (no
    apostrophes as part of an initial) and doesn't use apostrophes inside a
    syllable at all - they only ever separate two syllables in the same
    word (e.g. "Xi'an").
    """

    def find_final(self, text: str, initial: str, syllable: "Syllable") -> str:
        """
        Work out the final by reading characters one at a time: as soon as
        a vowel or consonant is found, hand off to whichever of
        Syllable.handle_vowel_case / handle_consonant_case (see syllable.py)
        matches, since the rules differ depending on which one it is.

        Args:
            text: The remaining text to extract the final from.
            initial: The syllable's already-known initial.
            syllable: The Syllable being built, for its handle_vowel_case/
                handle_consonant_case helper methods.

        Returns:
            The final.
        """
        for i, c in enumerate(text):
            # Handle cases where the final starts with a vowel or consonant
            if c in vowels:
                final = syllable.handle_vowel_case(text, i, initial)
                if final is not None:
                    return final
            else:
                return syllable.handle_consonant_case(text, i, initial)
        return text

    def get_illegal_characters(self) -> List[Tuple[str, str]]:
        """
        Same disallowed characters as every method (see
        RomanizationStrategy.get_illegal_characters in base.py), plus
        apostrophes - in Pinyin, an apostrophe only ever separates two
        syllables, so one appearing inside what's supposed to be a single
        syllable is always a mistake.

        Returns:
            A list of (character, reason) pairs.
        """
        illegal_chars = super().get_illegal_characters()

        # Add apostrophes as illegal in Pinyin (they are only word separators, not part of syllables)
        for apos in apostrophes:
            illegal_chars.append((apos, 'apostrophes not used in Pinyin syllables'))

        return illegal_chars
