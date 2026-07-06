"""
Text chunking utilities for romanized Mandarin text.

This module provides the `TextChunkProcessor` class, which is used to process text into chunks
based on the specified romanization method (e.g., Pinyin, Wade-Giles). It includes functionality for:
- Splitting text into segments (words and non-text).
- Processing each segment into syllables or leaving it as is.
- Handling different romanization methods.

Classes:
    TextChunkProcessor: Processes text into chunks for further processing based on the specified romanization method.
"""

from typing import List, Union, Dict, Tuple
import re
import unicodedata
from .config import Config
from .syllable import SyllableProcessor, Syllable
from .constants import supported_methods, method_shorthand_to_full, nontext_chars


class TextChunkProcessor:
    """
    Processes text into chunks for further processing based on the specified romanization method (e.g., Pinyin, Wade-Giles).

    Attributes:
        text (str): The input text to be processed.
        config (Config): Configuration object that manages processing options like crumbs, error skipping, and error reporting.
        method (str): The romanization method being used ("py" for Pinyin or "wg" for Wade-Giles).
        syllable_processor (SyllableProcessor): The processor used to handle syllable creation and validation.
        chunks (List[Union[List[Syllable], str]]): The processed chunks of text, where each chunk is either a list of syllables or a string.
    """

    def __init__(self, text: str, config: Config, method_params: Dict[str, Union[Tuple[Tuple[bool, ...], ...], List[str], str]]):
        """
        Initialize a TextChunkProcessor with the provided text, configuration, and method parameters.

        Args:
            text (str): The input text to be processed.
            config (Config): Configuration object that manages processing options like crumbs, error skipping, and error reporting.
            method_params (dict): Parameters for the romanization method (e.g., syllable rules, method name).
        """
        self.text = text
        self.config = config
        self.method = str(method_params['method'])
        # Syllable processor is initialized with the configuration and romanization method parameters
        self.syllable_processor = SyllableProcessor(config, method_params)
        self.chunks: List[Union[List[Syllable], str]] = []
        self._syllable_cache: Dict[str, Syllable] = {}
        self._process_text()

    def _split_text_into_segments(self, text: str) -> List[str]:
        """
        Splits text into segments (words and non-text) based on the specified regex pattern.

        Args:
            text (str): The text to be split.

        Returns:
            List[str]: A list of split segments.
        """

        # Normalize the text to NFC form
        text = unicodedata.normalize('NFC', text)

        if self.config.error_skip:
            # Regular expression splits text into groups of words (including apostrophes and dashes) with
            # non-text elements separated
            pattern = r"[a-zA-ZüÜ]+(?:['’ʼ`\-–—][a-zA-ZüÜ]+)*|[^a-zA-ZüÜ]+"
        else:
            # Default pattern for word splitting, including apostrophes and dashes and excluding non-text elements
            # **FUTURE: Add error messages for non-text elements
            pattern = r"[a-zA-ZüÜ]+(?:['’ʼ`\-–—][a-zA-ZüÜ]+)*"
        return re.findall(pattern, text)

    def _split_word(self, word: str) -> List[str]:
        """
        Splits a word into smaller components based on the specified romanization method.

        Args:
            word (str): The word to be split.

        Returns:
            List[str]: A list of split components of the word.
        """

        if self.method == 'wg':
            # Splits string with respect to Wade-Giles's use of apostrophes in syllable initials and dashes
            # between syllables (dashes strongly recommended for reliable parsing)
            pattern = r"[a-zA-ZüÜ'’ʼ`]+|[\-–—][a-zA-ZüÜ'’ʼ`]+"
        else:
            # Splits string with respect to Pinyin's use of apostrophes for multi-syllable words
            pattern = r"[a-zA-ZüÜ]+|['’ʼ`\-–—][a-zA-ZüÜ]+"
        split_words = re.findall(pattern, word)
        return split_words if len(split_words) > 1 else [word]

    def _process_text(self):
        """
        Splits text into segments (words and non-text) and processes each segment into syllables or leaves it as is.

        Depending on the configuration, it can use different regex patterns for splitting the text.
        """

        # Collect segments using regular expressions
        segments = self._split_text_into_segments(self.text)
        for segment in segments:
            # Text elements are processed into syllables
            if re.match(r"[a-zA-ZüÜ]+", segment):
                # Print crumb for syllable analysis
                pretty_method = supported_methods[method_shorthand_to_full[self.method]]["pretty"]
                self.config.print_crumb(1, f'Analyzing text as {pretty_method}', segment)
                # Regular expressions are used again to split words into smaller components
                split_words = self._split_word(segment)
                # Process each split word into Syllable objects
                self._process_split_words(split_words)
                self.config.print_crumb(footer=True)
            else:
                # Non-text elements are directly appended as strings
                self.chunks.append(segment)
                # Print crumb for non-text segment
                if segment in nontext_chars:
                    segment = nontext_chars[segment]['pretty']
                self.config.print_crumb(1, 'Non-text segment', segment)
                self.config.print_crumb(footer=True)

    def _send_to_syllable_processor(self, remaining_text: str) -> Syllable:
        # Cache is scoped to this instance so it doesn't outlive the processor
        # (a class-level lru_cache would pin every instance in memory forever).
        if remaining_text in self._syllable_cache:
            result = self._syllable_cache[remaining_text]
            self.config.print_crumb(2, "Cached", f'"{result.text_attr.full_syllable}" | valid: {result.valid}')
            return result
        result = self.syllable_processor.create_syllable(remaining_text)
        self._syllable_cache[remaining_text] = result
        return result

    def _process_split_words(self, split_words: List[str]):
        """
        Processes a list of split words into syllables, handling case detection and syllable creation.

        Args:
            split_words (List[str]): The split words to process.

        Side Effects:
            Appends a list of Syllable objects to self.chunks for each word processed.
        """

        syllables: List[Syllable] = []
        for syllable in split_words:
            remaining_text = syllable
            while remaining_text:
                # Send remaining text to syllable processor to create a syllable object
                syllable_obj = self._send_to_syllable_processor(remaining_text)
                syllables.append(syllable_obj)
                remaining_text = syllable_obj.text_attr.remainder
        # Add crumb summarizing the validity of the word
        if self.config.crumbs and syllables:
            validity = "valid" if all(syl.valid for syl in syllables) else "invalid"
            if self.method == 'wg':
                word_str = "-".join(syl.text_attr.full_syllable for syl in syllables)
            else:
                word_str = "".join(syl.text_attr.full_syllable for syl in syllables)
            self.config.print_crumb(level=1, stage="Word Validation", message=f'"{word_str}" is {validity}')
        self.chunks.append(syllables)

    def get_chunks(self) -> List[Union[List[Syllable], str]]:
        """
        Returns the processed chunks of text.

        Returns:
            List[Union[List[Syllable], str]]: A list where each element is either a list of Syllable objects (for text segments) or a string (for non-text segments).
        """

        return self.chunks
