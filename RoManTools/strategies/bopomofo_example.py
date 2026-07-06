"""
Example: Bopomofo (Zhuyin) romanization strategy implementation.

This is a template/example showing how to add Bopomofo support to the modular system.
Bopomofo is fundamentally different from Latin-script romanization systems as it uses
Chinese phonetic symbols, but this example shows how it could be integrated if needed
for transliteration or mixed-script processing.
"""

from typing import TYPE_CHECKING, Optional
from .base import RomanizationStrategy
from ..constants import vowels

if TYPE_CHECKING:
    from ..syllable import Syllable


class BopomofoStrategy(RomanizationStrategy):
    """
    Strategy for processing Bopomofo (Zhuyin) romanization syllables.
    
    Bopomofo characteristics:
    - Uses Chinese phonetic symbols (ㄅㄆㄇㄈ etc.)
    - Different initials: ㄅ(b), ㄆ(p), ㄇ(m), ㄈ(f), etc.
    - Different finals: ㄚ(a), ㄛ(o), ㄜ(e), ㄞ(ai), etc.
    - Tone marks: ˊˇˋ˙ (2nd, 3rd, 4th, light tone)
    - No apostrophes
    - Compact syllable representation
    
    Note: This example assumes transliterated Bopomofo input (romanized representations
    of the symbols) rather than actual Unicode Bopomofo characters.
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
        Handles the initial part extraction for Bopomofo method.
        
        Args:
            text: The text from which to extract the initial.
            syllable: The Syllable instance for accessing helper methods.
            
        Returns:
            The initial part of the syllable, or 'ø' if no initial exists.
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
        Bopomofo doesn't use apostrophes in initials.
        
        Args:
            text: The text being processed.
            index: The index where the apostrophe was found.
            
        Returns:
            The initial part without the apostrophe.
        """
        # Bopomofo doesn't use apostrophes, so remove them
        return text[:index]
    
    def find_final(self, text: str, initial: str, syllable: "Syllable") -> str:
        """
        Handles the final part extraction for Bopomofo method.
        
        Bopomofo has a more compact representation and different phonetic boundaries
        compared to other romanization systems.
        
        Args:
            text: The text from which to extract the final.
            initial: The initial part of the syllable.
            syllable: The Syllable instance for accessing helper methods.
            
        Returns:
            The final part of the syllable.
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
        Validate a complete syllable for Bopomofo method.
        
        Args:
            initial: The initial part of the syllable.
            final: The final part of the syllable.
            syllable: The Syllable instance for accessing helper methods.
            
        Returns:
            True if the syllable is valid, False otherwise.
        """
        # Use the processor's validation method with Bopomofo-specific considerations
        if initial == '':
            return self.processor.validate_final_using_array('ø', final)
        return self.processor.validate_final_using_array(initial, final)
    
    def _remove_tone_marks(self, text: str) -> str:
        """
        Remove Bopomofo tone marks from the text.
        
        Bopomofo uses: ˊ(2nd tone), ˇ(3rd tone), ˋ(4th tone), ˙(light tone)
        1st tone has no mark.
        
        Args:
            text: The text possibly containing tone marks.
            
        Returns:
            Text with tone marks removed.
        """
        tone_marks = ['ˊ', 'ˇ', 'ˋ', '˙']
        for mark in tone_marks:
            text = text.replace(mark, '')
        return text
    
    def _handle_bopomofo_vowel_case(self, text: str, i: int, initial: str, syllable: "Syllable") -> Optional[str]:
        """
        Handle Bopomofo-specific vowel patterns.
        
        Args:
            text: The syllable text to be processed.
            i: The index of the vowel in the text.
            initial: The initial part of the syllable.
            syllable: The Syllable instance for accessing helper methods.
            
        Returns:
            The final part of the syllable or None to continue processing.
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
        Handle Bopomofo-specific consonant endings.
        
        Bopomofo has limited consonant endings: n, ng, r
        
        Args:
            text: The syllable text to be processed.
            i: The index of the consonant in the text.
            initial: The initial part of the syllable.
            syllable: The Syllable instance for accessing helper methods.
            
        Returns:
            The final part of the syllable.
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
        Convert romanized initial and final to Bopomofo symbols.
        
        This is a utility method that could be used for display or conversion purposes.
        
        Args:
            initial: The romanized initial.
            final: The romanized final.
            
        Returns:
            The Bopomofo representation.
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
