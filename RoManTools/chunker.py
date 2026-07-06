"""
Breaking raw input text into pieces RoManTools can analyze.

Before RoManTools can validate or convert anything, it has to figure out
where one word ends and the next begins, and separate actual romanized text
from everything else in the input (spaces, punctuation, numbers). This
module does that first pass. The result is a list of "chunks" - the
package's term for either a word (represented as a list of its Syllable
objects, built by SyllableProcessor in syllable.py) or a stretch of
non-text content (represented as a plain string, left untouched).

Classes:
    TextChunkProcessor: Takes a string of input text and a romanization
        method, and produces the list of chunks described above.
"""

from typing import List, Union, Dict, Tuple
import re
import unicodedata
from .config import Config
from .syllable import SyllableProcessor, Syllable
from .constants import supported_methods, method_shorthand_to_full, nontext_chars


class TextChunkProcessor:
    """
    Splits input text into chunks and turns each word-chunk into syllables.

    Attributes:
        text (str): The input text being processed.
        config (Config): The settings for this run (see config.py).
        method (str): Which romanization method to use ("py" or "wg").
        syllable_processor (SyllableProcessor): Builds and validates
            individual syllables for the chosen method.
        chunks (List[Union[List[Syllable], str]]): The result: each entry is
            either a list of Syllable objects (one word) or a plain string
            (a stretch of non-text content, left as-is).
    """

    def __init__(self, text: str, config: Config, method_params: Dict[str, Union[Tuple[Tuple[bool, ...], ...], List[str], str]]):
        """
        Args:
            text (str): The input text to process.
            config (Config): The settings for this run.
            method_params (dict): The syllable-validity data for the chosen
                romanization method (see data_loader.load_method_params).
        """
        self.text = text
        self.config = config
        self.method = str(method_params['method'])
        # Syllable processor is initialized with the configuration and romanization method parameters
        self.syllable_processor = SyllableProcessor(config, method_params)
        self.chunks: List[Union[List[Syllable], str]] = []
        # Remembers syllables already built for this input, so a word that
        # repeats within the same text (e.g. "Beijing... Beijing again")
        # isn't parsed twice. Kept on the instance rather than shared across
        # every TextChunkProcessor ever created, so it doesn't grow forever.
        self._syllable_cache: Dict[str, Syllable] = {}
        self._process_text()

    def _split_text_into_segments(self, text: str) -> List[str]:
        """
        Split the raw input into alternating stretches of "romanized-looking
        text" and "everything else" (spaces, punctuation, digits).

        This uses a regular expression (often shortened to "regex") - a
        compact pattern language, built into Python, for describing what a
        piece of text should look like ("one or more letters, optionally
        followed by an apostrophe and more letters" in this case) so it can
        be found automatically instead of checked character by character.

        Args:
            text (str): The text to split.

        Returns:
            List[str]: The alternating list of text and non-text segments.
        """

        # Different keyboards/input methods can produce the same-looking
        # accented letter (e.g. "ü") as different sequences of underlying
        # characters. Normalizing to NFC ("Normalization Form C", a Unicode
        # standard) collapses those down to one consistent form, so the
        # patterns below match consistently no matter how the user typed it.
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
        Split one word-shaped segment into its syllable-sized pieces, using
        whichever punctuation marks the romanization method uses as syllable
        separators (Pinyin: apostrophes and dashes; Wade-Giles: dashes, with
        apostrophes kept attached to the syllable they belong to).

        Args:
            word (str): The word to split.

        Returns:
            List[str]: The word's pieces, or a single-item list containing
                the whole word unchanged if no separators were found (the
                remaining syllable boundaries get worked out later, in
                syllable.py, from the letters themselves).
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
        Do the full first pass over `self.text`: split it into segments,
        then either parse a text segment into syllables or keep a non-text
        segment as-is, appending each result to `self.chunks` in order.
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
        # If we've already built a Syllable for this exact piece of text earlier
        # in this same input, reuse it instead of parsing it again.
        if remaining_text in self._syllable_cache:
            result = self._syllable_cache[remaining_text]
            self.config.print_crumb(2, "Cached", f'"{result.text_attr.full_syllable}" | valid: {result.valid}')
            return result
        result = self.syllable_processor.create_syllable(remaining_text)
        self._syllable_cache[remaining_text] = result
        return result

    def _process_split_words(self, split_words: List[str]):
        """
        Turn a word's pieces (from `_split_word`) into a list of Syllable
        objects, one word-chunk at a time. A single piece can turn into more
        than one Syllable - e.g. "changan" has no separator, so it comes in
        as one piece, but is actually two syllables ("chan" + "gan"); the
        loop below keeps asking the syllable processor for "what's the next
        syllable, and what's left over after it?" until nothing is left.

        Args:
            split_words (List[str]): The word's pieces to process.

        Side Effects:
            Appends one list of Syllable objects to self.chunks, representing
            this whole word.
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
        Returns:
            List[Union[List[Syllable], str]]: The processed chunks - each
            entry is either a list of Syllable objects (one word) or a
            plain string (a non-text segment).
        """

        return self.chunks
