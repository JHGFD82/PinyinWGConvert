"""
Base romanization strategy abstract class.

This module defines the abstract base class that all romanization strategies must implement.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from ..syllable import SyllableProcessor, Syllable


class RomanizationStrategy(ABC):
    """
    Abstract base class for romanization-specific syllable processing strategies.
    """
    
    def __init__(self, processor: "SyllableProcessor"):
        """
        Initialize the strategy with a processor reference.
        
        Args:
            processor: The SyllableProcessor instance containing shared data and methods.
        """
        self.processor = processor
    
    def handle_apostrophe_in_initial(self, text: str, index: int) -> str:
        """
        Handle apostrophes found within initial detection for this romanization method.
        Default implementation returns the text up to the apostrophe.
        
        Args:
            text: The text being processed.
            index: The index where the apostrophe was found.
            
        Returns:
            The initial part including apostrophe handling.
        """
        return text[:index]

    
    def handle_dash_in_initial(self, text: str, index: int) -> str:
        """
        Handle dashes found within initial detection for this romanization method.
        Default implementation returns the text up to the dash.
        
        Args:
            text: The text being processed.
            index: The index where the dash was found.
            
        Returns:
            The initial part including dash handling.
        """
        return text[:index]
    
    @abstractmethod
    def find_final(self, text: str, initial: str, syllable: "Syllable") -> str:
        """
        Find the final part of a syllable for this romanization method.
        
        Args:
            text: The text from which to extract the final.
            initial: The initial part of the syllable.
            syllable: The Syllable instance for accessing helper methods.
            
        Returns:
            The final part of the syllable.
        """
        pass

    def get_illegal_characters(self) -> List[Tuple[str, str]]:
        """
        Get a list of illegal characters and reasons for this romanization method.
        
        Returns:
            List of tuples containing (character, reason) pairs.
            Default implementation returns common illegal characters.
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
        Check text for illegal characters specific to this romanization method.
        
        Args:
            text: The text to check.
            syllable: The Syllable instance for error reporting.
            
        Returns:
            List of tuples containing (character, reason) for each illegal character found.
        """
        illegal_chars = self.get_illegal_characters()
        found_illegal: List[Tuple[str, str]] = []
        
        for char, reason in illegal_chars:
            if char in text:
                found_illegal.append((char, reason))
        
        return found_illegal
