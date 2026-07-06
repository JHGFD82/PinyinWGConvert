"""
Example: Yale romanization strategy implementation.

This is a template/example showing how easy it is to add a new romanization
method to the modular system.
"""

from typing import TYPE_CHECKING
from .base import RomanizationStrategy
from ..constants import vowels

if TYPE_CHECKING:
    from ..syllable import Syllable


class YaleStrategy(RomanizationStrategy):
    """
    Strategy for processing Yale romanization syllables.
    
    Yale romanization characteristics:
    - Uses 'j' for what Pinyin represents as 'zh'
    - Uses 'ch' for what Pinyin represents as 'q'  
    - Different tone marking system
    - No apostrophes in initials
    - Unique vowel combinations
    """
    
    def find_initial(self, text: str, syllable: "Syllable") -> str:
        """
        Handles the initial part extraction for Yale method.
        
        Args:
            text: The text from which to extract the initial.
            syllable: The Syllable instance for accessing helper methods.
            
        Returns:
            The initial part of the syllable, or 'ø' if no initial exists.
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
        Yale typically doesn't use apostrophes in the same way as Wade-Giles.
        
        Args:
            text: The text being processed.
            index: The index where the apostrophe was found.
            
        Returns:
            The initial part without the apostrophe.
        """
        # Yale romanization typically doesn't use apostrophes in initials
        # So we use the default behavior (remove them)
        return text[:index]
    
    def find_final(self, text: str, initial: str, syllable: "Syllable") -> str:
        """
        Handles the final part extraction for Yale method.
        
        Yale has some unique characteristics in final detection that differ
        from both Pinyin and Wade-Giles.
        
        Args:
            text: The text from which to extract the final.
            initial: The initial part of the syllable.
            syllable: The Syllable instance for accessing helper methods.
            
        Returns:
            The final part of the syllable.
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
        Yale-specific consonant handling.
        
        Args:
            text: The syllable text to be processed.
            i: The index of the consonant in the text.
            initial: The initial part of the syllable.
            syllable: The Syllable instance for accessing helper methods.
            
        Returns:
            The final part of the syllable.
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
        Validate a complete syllable for Yale method.
        
        Args:
            initial: The initial part of the syllable.
            final: The final part of the syllable.
            syllable: The Syllable instance for accessing helper methods.
            
        Returns:
            True if the syllable is valid, False otherwise.
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
