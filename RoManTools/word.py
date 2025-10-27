"""
Word processing utilities for romanized Mandarin text.

This module provides the `WordProcessor` and `Word` classes, which are used to process words and their syllables
based on the specified romanization method (e.g., Pinyin, Wade-Giles). It includes functionality for:
- Creating words from syllables (as a list of Syllable objects).
- Validating and converting syllables.
- Handling contractions and stopwords.
- Collecting and reporting validation errors.

Classes:
    WordProcessor: Processes words and their syllables based on the specified romanization method.
    Word: Represents a word and its syllables, providing methods for validation and conversion.
"""

import logging
from typing import List, Set, Tuple
from .config import Config
from .syllable import Syllable
from .constants import supported_contractions, vowels
from .conversion import RomanizationConverter
from .errors import ErrorTracker


class WordProcessor:
    """
    Processes words and their syllables based on the specified romanization method.

    Attributes:
        config (Config): Configuration object that manages processing options like crumbs, error skipping, and error reporting.
        convert_from (str): The romanization method to convert from (e.g., 'py' for Pinyin).
        convert_to (str): The romanization method to convert to (e.g., 'wg' for Wade-Giles).
        stopwords (Set[str]): A set of stopwords to be excluded from processing.
        converter (RomanizationConverter): The converter object used for romanization conversion.
    """

    def __init__(self, config: Config, convert_from: str, convert_to: str, stopwords: Set[str]):
        """
        Initialize a WordProcessor with the provided configuration and romanization method parameters.

        Args:
            config (Config): Configuration object that manages processing options like crumbs, error skipping, and error reporting.
            convert_from (str): The romanization method to convert from (e.g., 'py' for Pinyin).
            convert_to (str): The romanization method to convert to (e.g., 'wg' for Wade-Giles).
            stopwords (Set[str]): A set of stopwords to be excluded from processing.
        """

        self.config = config
        self.convert_from = convert_from
        self.convert_to = convert_to
        self.stopwords = stopwords
        self.converter = RomanizationConverter(convert_from, convert_to, self.config)

    def create_word(self, syllables: List[Syllable]) -> "Word":
        """
        Create a Word object from a list of Syllable objects.

        Args:
            syllables (List[Syllable]): A list of Syllable objects to be processed.

        Returns:
            Word: A Word object created from the given syllables.
        """

        return Word(syllables, self)


class Word:
    """
    Represents a word and its syllables, providing methods for validation and conversion.

    Attributes:
        syllables (List[Syllable]): A list of Syllable objects that make up the word.
        processor (WordProcessor): The processor object used to handle syllable validation and conversion.
        processed_syllables (List[Tuple[str, Syllable]]): A list of tuples containing the converted syllable and the original Syllable object.
        preview_word (str): A preview of the word used to determine if it is a stopword.
        final_word (str): The final processed word.
        valid (bool): Indicates if all syllables in the word are valid.
        contraction (bool): Indicates if the word is a contraction.
    """

    def __init__(self, syllables: List[Syllable], processor: WordProcessor):
        """
        Initialize a Word object with the provided syllables and processor.

        Args:
            syllables (List[Syllable]): A list of Syllable objects that make up the word.
            processor (WordProcessor): The processor object used to handle syllable validation and conversion.
        """

        self.syllables = syllables
        self.processor = processor
        self.processed_syllables: List[Tuple[str, Syllable]] = []  # Will contain tuples with the converted syllable and the original syllable
        self.preview_word = self._create_preview_word()
        self.final_word = ""
        self.valid = self.all_valid()
        self.contraction = self.is_contraction()
        self._stopword_logged = False
        
        # Collect errors from all syllables
        self.error_tracker = ErrorTracker()
        for syl in self.syllables:
            self.error_tracker.merge(syl.error_tracker) 

    def _create_preview_word(self) -> str:
        """
        Creates a preview word by joining the full syllables of the word with apostrophes and dashes where necessary.
        The preview word is used to determine whether the word is a stopword, which includes contractions such as
        "we've" and "we're," which are potentially valid romanized syllables, even though they are not Mandarin terms.

        Returns:
            str: The preview word.
        """

        word_parts: List[str] = []
        for syl in self.syllables:
            if syl.status_attr.has_apostrophe and self.processor.convert_from != 'wg':
                word_parts.append("'" + syl.text_attr.full_syllable)
            elif syl.status_attr.has_dash:
                word_parts.append("-" + syl.text_attr.full_syllable)
            else:
                word_parts.append(syl.text_attr.full_syllable)
        return "".join(word_parts)

    def all_valid(self) -> bool:
        """
        Checks if all syllables in the word are valid.

        Returns:
            bool: True if all syllables are valid, False otherwise.
        """

        return all(syl.valid for syl in self.syllables)

    def is_contraction(self) -> bool:
        """
        Checks if the word is a contraction by verifying that all but the last syllable are valid,
        the last syllable has an apostrophe, and the last syllable matches a supported contraction.
        Only returns True if error_skip is enabled.

        Returns:
            bool: True if the word is a contraction, False otherwise.
        """

        valid_syllables = all(syl.valid for syl in self.syllables[:-1])
        last_apostrophe = self.syllables[-1].status_attr.has_apostrophe
        if self.processor.convert_from == 'wg':
            possible_contraction = self.syllables[-1].text_attr.full_syllable.replace("'", "")
            contraction = possible_contraction in supported_contractions
        else:
            contraction = self.syllables[-1].text_attr.full_syllable in supported_contractions
        error_skip = self.processor.config.error_skip
        return all([valid_syllables, last_apostrophe, contraction, error_skip])

    def is_convertable(self) -> bool:
        """
        Checks if the word is valid or a contraction and not a stopword.

        Returns:
            bool: True if the word is valid or a contraction and not a stopword, False otherwise.
        """

        if self.preview_word in self.processor.stopwords:
            if not self._stopword_logged:
                self.processor.config.print_crumb(
                    1, "Word Validation", f"'{self.preview_word}' is a stopword and cannot be processed", log_level=logging.ERROR
                )
                self._stopword_logged = True
            return False
        return self.valid or self.contraction

    def convert(self):
        """
        Converts the syllables of the word. If error_skip is False, all syllables are processed and errors are reported.
        If error_skip is True, only valid syllables or contractions are converted, and stopwords are not processed.
        """

        # For standard conversion requests, process syllables with error messages.
        if not self.processor.config.error_skip:
            self.processed_syllables = [(self.processor.converter.convert(syl.text_attr.full_syllable), syl) for syl in self.syllables]
        # Otherwise, process syllables without error messages, specifically for the cherry_pick action.
        # Convert the syllables if all are valid, or are part of a contraction, and the whole word is not a stopword.
        # The last syllable will fail conversion, but no error message will be produced and the self.contraction
        # attribute will be used later to allow proper processing of contractions.
        elif self.is_convertable():
            self.processed_syllables = [
                (self.processor.converter.convert(syl.text_attr.full_syllable), syl) if syl.valid else (syl.text_attr.full_syllable, syl)
                for syl in self.syllables
            ]
        # If this is for cherry_pick and there are an invalid number of valid syllables, and the word is not a
        # stopword, process syllables without conversion or error messages (allows English words to pass through).
        else:
            self.processed_syllables = [(syl.text_attr.full_syllable, syl) for syl in self.syllables]

    def apply_caps(self):
        """
        Applies capitalization to the converted syllables based on their capitalization attributes.
        """

        # The apply_caps method within the Syllable object is called on each syllable to apply capitalization based on
        # titlecase or uppercase attributes within each syllable.
        self.processed_syllables = [(syl[1].apply_caps(syl[0]), syl[1]) for syl in self.processed_syllables]

    def add_symbols(self):
        """
        Adds apostrophes and dashes to the converted syllables based on the conversion system and the presence of vowels.
        The result is stored in self.final_word.
        """

        # Syllables have to be processed individually if conversion took place. Otherwise, they are combined in a
        # different process. If the error_skip is False, then assume conversion took place.
        if not self.processor.config.error_skip or self.is_convertable():
            self.final_word = self.processed_syllables[0][0]
            for i in range(1, len(self.processed_syllables)):
                self._append_syllable(i)
        else:
            self._append_all_syllables()

    def _append_syllable(self, i: int):
        """
        Appends a syllable to the final word with an apostrophe or a dash based on the conversion system and the
        presence of vowels.

        Args:
            i (int): The index of the syllable to be appended.
        """

        # Specific rules for romanization are contained here.
        prev_syllable = self.processed_syllables[i - 1][0]
        curr_syllable = self.processed_syllables[i][0]
        is_last_syllable = i == len(self.processed_syllables) - 1
        # For romanization systems that don't use apostrophes in initials (aka not Wade-Giles), all contractions
        # require the apostrophe to be added.
        if self.contraction and is_last_syllable and self.processor.convert_from != 'wg':
            self.final_word += "'" + curr_syllable
        # For Pinyin, specific logic is applied to determine whether an apostrophe is needed between syllables.
        elif self.processor.convert_to == 'py':
            # self.final_word += "'" + curr_syllable
            if self.processed_syllables[i][1].valid and self._needs_apostrophe(prev_syllable, curr_syllable):
                self.final_word += "'" + curr_syllable
            else:
                self.final_word += curr_syllable
        # For Wade-Giles, dashes are used to separate syllables except if this happens to be a contraction.
        else:
            self.final_word += "-" + curr_syllable

    @staticmethod
    def _needs_apostrophe(prev_syllable: str, curr_syllable: str) -> bool:
        """
        Determines whether an apostrophe is needed between two syllables based on the last character of the previous
        syllable and the first character of the current syllable.

        Args:
            prev_syllable (str): The previous syllable.
            curr_syllable (str): The current syllable.

        Returns:
            bool: True if an apostrophe is needed, False otherwise.
        """

        # The logic for apostrophes in Pinyin is based on the following rules in which the start of the next syllable
        # is a vowel:
        # - If the last character of the previous syllable and the first character of the current syllable is a vowel
        # - If the previous syllable ends with 'er', 'n', or 'ng'
        conditions = {
            'vowel_vowel': prev_syllable[-1] in vowels and curr_syllable[0] in vowels,
            'er_vowel': prev_syllable.endswith('er') and curr_syllable[0] in vowels,
            'n_vowel': prev_syllable[-1] == 'n' and curr_syllable[0] in vowels,
            'ng_vowel': prev_syllable.endswith('ng') and curr_syllable[0] in vowels
        }
        return any(conditions.values())

    def _append_all_syllables(self):
        """
        Appends all syllables to the final word, adding any symbols if they were in the original text.
        """

        for syl in self.processed_syllables:
            if syl[1].status_attr.has_apostrophe:
                self.final_word += "'" + syl[0]
            elif syl[1].status_attr.has_dash:
                self.final_word += "-" + syl[0]
            else:
                self.final_word += syl[0]

    def process_syllables(self) -> str:
        """
        Processes the syllables of the word by converting them, applying capitalization, and adding symbols.
        Returns the final processed word as a string.

        Returns:
            str: The final word after processing the syllables.
        """

        self.convert()
        self.apply_caps()
        self.add_symbols()
        
        # Report errors if error_report is enabled
        if self.processor.config.error_report and self.error_tracker.has_errors():
            error_report = self.error_tracker.generate_report(
                verbose=self.processor.config.error_report_verbose,
                max_errors=self.processor.config.error_report_max,
                include_summary=False,
                include_details=True
            )
            
            # For verbose reports, include word context
            if self.processor.config.error_report_verbose:
                message = f"'{self.preview_word}':\n{error_report}"
            else:
                # For compact reports, just show the error
                message = f"'{self.preview_word}': {error_report}"
            
            self.processor.config.print_crumb(
                1,
                "Errors in word",
                message,
                log_level=logging.WARNING
            )
        
        return self.final_word
