"""
Wade-Giles romanization strategy implementation.

This module contains the strategy for processing Wade-Giles syllables with 
systematic ambiguity resolution.
"""

from typing import TYPE_CHECKING, List, Tuple
from .base import RomanizationStrategy
from ..constants import vowels, apostrophes

if TYPE_CHECKING:
    from ..syllable import Syllable


class WadeGilesStrategy(RomanizationStrategy):
    """
    Strategy for processing Wade-Giles syllables with systematic ambiguity resolution.
    
    Wade-Giles characteristics:
    - Uses apostrophes in initials (ch', ts', etc.)
    - Ambiguous syllable boundaries in continuous text
    - Requires backtracking for optimal parsing
    - Different final patterns compared to Pinyin
    """
    
    def find_initial(self, text: str, syllable: "Syllable") -> str:
        """
        Handles the initial part extraction for Wade-Giles method.
        
        Args:
            text: The text from which to extract the initial.
            syllable: The Syllable instance for accessing helper methods.
            
        Returns:
            The initial part of the syllable, or 'ø' if no initial exists.
        """
        # Use the standard initial detection logic but with Wade-Giles specific handling
        from ..constants import vowels, apostrophes, dashes
        
        for i, c in enumerate(text):
            if c in vowels:
                if i == 0:  # If a vowel is found at the beginning of the syllable, return 'ø' to indicate no initial
                    return 'ø'
                # Otherwise, all text up to this point is the initial
                if (initial := text[:i]) not in self.processor.init_list:  # Check if the initial is valid
                    syllable.errors.append(f"invalid initial: '{initial}'")
                    return text[:i]  # Return text up to this point if not valid
                return initial
            if c in apostrophes:  # Handle apostrophes using strategy (Wade-Giles keeps them)
                return self.handle_apostrophe_in_initial(text, i)
            if c in dashes:  # Handle dashes using strategy  
                return self.handle_dash_in_initial(text, i)

        return text
    
    def handle_apostrophe_in_initial(self, text: str, index: int) -> str:
        """
        Handle apostrophes in Wade-Giles initials by including the apostrophe.
        
        Args:
            text: The text being processed.
            index: The index where the apostrophe was found.
            
        Returns:
            The initial part including the apostrophe.
        """
        return text[:index] + "'"
    
    def find_final(self, text: str, initial: str, syllable: "Syllable") -> str:
        """
        Handles the final part extraction for Wade-Giles method with systematic ambiguity resolution.
        
        Args:
            text: The text from which to extract the final.
            initial: The initial part of the syllable.
            syllable: The Syllable instance for accessing helper methods.
            
        Returns:
            The final part of the syllable.
        """
        # Handle apostrophes first (existing Wade-Giles functionality)
        for i, c in enumerate(text):
            if c in apostrophes:
                return text[:i]
        
        # If we have an initial, we're looking for just the final part
        if initial and initial != 'ø':
            return self._find_wg_final_with_backtrack(text, initial)
        
        # If no initial, use systematic boundary detection
        return self._find_wg_syllable_boundaries(text)
    
    def _find_wg_final_with_backtrack(self, text: str, initial: str) -> str:
        """
        Find the final part when we already have an initial, using Wade-Giles specific logic.
        
        Args:
            text: The text to analyze for final extraction.
            initial: The initial part of the syllable.
            
        Returns:
            The final part of the syllable.
        """
        valid_finals: list[tuple[str, str]] = []

        # Try different final lengths, from longest to shortest
        for final_end in range(len(text), 0, -1):
            potential_final = text[:final_end]
            remaining_text = text[final_end:]
            
            # Check if this initial + final combination is valid
            if self.processor.validate_final_using_array(initial, potential_final, silent=True):
                # If no remaining text, this is the complete final
                if not remaining_text:
                    return potential_final
                # If there is remaining text, check if it can form valid syllables
                elif self._can_form_valid_wg_syllables(remaining_text):
                    valid_finals.append((potential_final, remaining_text))
        
        # If we found valid combinations, return the one with the longest final
        if valid_finals:
            return valid_finals[0][0]  # Return the longest valid final
        
        # Fallback: return the full text
        return text
    
    def validate_syllable(self, initial: str, final: str, syllable: "Syllable") -> bool:
        """
        Validate a complete syllable for Wade-Giles method.
        
        Args:
            initial: The initial part of the syllable.
            final: The final part of the syllable.
            syllable: The Syllable instance for accessing helper methods.
            
        Returns:
            True if the syllable is valid, False otherwise.
        """
        # Use the processor's validation method with error tracking
        if initial == '':
            return self.processor.validate_final_using_array('ø', final, error_tracker=syllable.error_tracker)
        return self.processor.validate_final_using_array(initial, final, error_tracker=syllable.error_tracker)
    
    def get_illegal_characters(self) -> List[Tuple[str, str]]:
        """
        Get illegal characters specific to Wade-Giles romanization.
        
        Wade-Giles uses apostrophes in initials (e.g., ch', ts'), so they are not illegal.
        
        Returns:
            List of tuples containing (character, reason) pairs.
        """
        # Get base illegal characters, but exclude apostrophes since they're used in Wade-Giles
        illegal_chars = super().get_illegal_characters()
        
        # Wade-Giles allows apostrophes in initials, so we don't add them to illegal list
        # (apostrophes are a valid part of Wade-Giles romanization)
        
        return illegal_chars
        
    def _find_wg_syllable_boundaries(self, text: str) -> str:
        """
        Systematic approach to find syllable boundaries in Wade-Giles text without explicit separators.
        
        Args:
            text: The text to analyze for syllable boundaries.
            
        Returns:
            The first valid syllable found in the text.
        """
        # Try to find the best syllable boundary by testing complete syllables
        for syllable_end in range(2, len(text) + 1):  # Start from 2 to ensure we have at least a minimal syllable
            potential_syllable = text[:syllable_end]
            remaining_text = text[syllable_end:]
            
            # Check if this potential syllable is valid
            if self._is_complete_wg_syllable_valid(potential_syllable):
                # If there's remaining text, check if it can form valid syllables
                if not remaining_text:
                    return potential_syllable  # This completes the entire text as one syllable
                elif self._can_form_valid_wg_syllables(remaining_text):
                    return potential_syllable  # This syllable is valid and remainder can be parsed
        
        # Default: return full text (original behavior)
        return text
    
    def _is_complete_wg_syllable_valid(self, syllable_text: str) -> bool:
        """
        Check if a complete syllable text forms a valid Wade-Giles syllable by trying different initial/final splits.
        
        Args:
            syllable_text: The complete syllable text to validate.
            
        Returns:
            True if the syllable is valid, False otherwise.
        """
        # Get all initials from the processor, excluding 'ø' and sort by length (longest first for greedy matching)
        all_initials = [init for init in self.processor.init_list if isinstance(init, str) and init != 'ø']
        all_initials.sort(key=len, reverse=True)
        
        # Try each possible initial
        for initial in all_initials:
            if syllable_text.startswith(initial):
                final = syllable_text[len(initial):]
                if self.processor.validate_final_using_array(initial, final, silent=True):
                    return True
        
        # Try no initial (starts with vowel)
        if syllable_text and syllable_text[0] in vowels:
            if self.processor.validate_final_using_array('ø', syllable_text, silent=True):
                return True
                
        return False
    
    def _can_form_valid_wg_syllables(self, text: str) -> bool:
        """
        Check if remaining text can be broken down into valid Wade-Giles syllables.
        
        This is a simplified check - in a full implementation, this would recursively
        try to parse the remaining text.
        
        Args:
            text: The remaining text to check.
            
        Returns:
            True if the text can potentially form valid syllables, False otherwise.
        """
        if len(text) <= 1:
            return False
            
        # Check if it starts with a valid initial (using data from processor)
        # Sort by length (longest first) for proper greedy matching
        all_initials = [init for init in self.processor.init_list if isinstance(init, str) and init != 'ø']
        all_initials.sort(key=len, reverse=True)
        
        for init in all_initials:
            if text.startswith(init):
                return True
                
        # Check if it starts with a vowel (no initial)
        if text[0] in vowels:
            return True
            
        return False
