"""
Pinyin romanization strategy implementation.

This module contains the strategy for processing Pinyin syllables.
"""

from typing import TYPE_CHECKING, List, Tuple
from .base import RomanizationStrategy
from ..constants import vowels, apostrophes

if TYPE_CHECKING:
    from ..syllable import Syllable


class PinyinStrategy(RomanizationStrategy):
    """
    Strategy for processing Pinyin syllables.
    
    Pinyin characteristics:
    - Standard vowel/consonant case handling
    - No apostrophes in initials
    - Clear syllable boundaries
    """
    
    def find_final(self, text: str, initial: str, syllable: "Syllable") -> str:
        """
        Handles the final part extraction for Pinyin method.
        
        Args:
            text: The text from which to extract the final.
            initial: The initial part of the syllable.
            syllable: The Syllable instance for accessing helper methods.
            
        Returns:
            The final part of the syllable.
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
        Get illegal characters specific to Pinyin romanization.
        
        Pinyin does not use apostrophes within syllables (they are word separators).
        
        Returns:
            List of tuples containing (character, reason) pairs.
        """
        illegal_chars = super().get_illegal_characters()
        
        # Add apostrophes as illegal in Pinyin (they are only word separators, not part of syllables)
        for apos in apostrophes:
            illegal_chars.append((apos, 'apostrophes not used in Pinyin syllables'))
        
        return illegal_chars
