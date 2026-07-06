"""
Assembling syllables back into a converted word.

Once a word has been split into its Syllable objects (see chunker.py and
syllable.py) and each syllable's converted spelling looked up (see
conversion.py), there's still real work left before you get a finished,
readable word back: syllables need their capitalization restored, the
right apostrophes/dashes need to be added back in (Pinyin and Wade-Giles
each have their own rules for this), and a few special cases need
handling - contractions like "we've" that happen to look like valid
syllables, and words like "China" that shouldn't be "corrected" even
though they're not standard Pinyin/Wade-Giles spelling. This module is
where all of that comes together.

Classes:
    WordProcessor: Shared setup for converting words between two
        particular romanization methods (created once per convert_text()/
        cherry_pick() call, then used to build every Word in that call).
    Word: One word, from its syllables through to its final converted form.
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
    Holds everything needed to convert words from one romanization method
    to another, so that setup only happens once per convert_text()/
    cherry_pick() call rather than once per word.

    Attributes:
        config (Config): The settings for this run (see config.py).
        convert_from (str): The romanization method to convert from (e.g. 'py').
        convert_to (str): The romanization method to convert to (e.g. 'wg').
        stopwords (Set[str]): Words that should be left unconverted even if
            they look like valid syllables (e.g. "China").
        converter (RomanizationConverter): Looks up each syllable's
            converted spelling (see conversion.py).
    """

    def __init__(self, config: Config, convert_from: str, convert_to: str, stopwords: Set[str]):
        """
        Args:
            config (Config): The settings for this run.
            convert_from (str): The romanization method to convert from.
            convert_to (str): The romanization method to convert to.
            stopwords (Set[str]): Words to leave unconverted.
        """

        self.config = config
        self.convert_from = convert_from
        self.convert_to = convert_to
        self.stopwords = stopwords
        self.converter = RomanizationConverter(convert_from, convert_to, self.config)

    def create_word(self, syllables: List[Syllable]) -> "Word":
        """
        Build a Word from a list of already-parsed syllables.

        Args:
            syllables (List[Syllable]): The syllables making up this word,
                in order.

        Returns:
            Word: The resulting Word object.
        """

        return Word(syllables, self)


class Word:
    """
    One word, from its syllables through to its final converted form.

    Attributes:
        syllables (List[Syllable]): The syllables making up this word.
        processor (WordProcessor): Provides the conversion settings and
            method shared across every word in this run.
        processed_syllables (List[Tuple[str, Syllable]]): Each syllable
            paired with its converted spelling, filled in by convert() below.
        preview_word (str): A lowercase, unconverted rendering of the word,
            used only to check it against the stopword list.
        final_word (str): The finished, converted word - filled in by
            add_symbols() below.
        valid (bool): Whether every syllable in the word is valid.
        contraction (bool): Whether this word is an English contraction
            (like "we've") that happens to look like valid romanized
            syllables, rather than actual Mandarin.
    """

    def __init__(self, syllables: List[Syllable], processor: WordProcessor):
        """
        Args:
            syllables (List[Syllable]): The syllables making up this word.
            processor (WordProcessor): The shared conversion settings.
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
        Reassemble the word's syllables into one lowercase string, keeping
        any apostrophes/dashes the original text had. This "preview" isn't
        shown to the user - it exists purely so the word can be checked
        against the stopword list, which is what lets something like
        "we've" (a valid-looking but non-Mandarin sequence of syllables) be
        recognized as English rather than romanized Mandarin.

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
        Returns:
            bool: True if every syllable in this word is valid.
        """

        return all(syl.valid for syl in self.syllables)

    def is_contraction(self) -> bool:
        """
        Check whether this word is actually an English contraction (like
        "we've", "it'd", "we'll") that happens to parse as valid-looking
        syllables followed by an apostrophe and a recognized ending. Only
        relevant when `error_skip` is on (see config.py) - the setting
        needed for processing text that mixes English and Mandarin in the
        first place.

        Returns:
            bool: True if this word looks like a contraction.
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
        Check whether this word should actually be converted: it must not
        be a stopword (see WordProcessor.stopwords above), and it must be
        either fully valid or a recognized contraction.

        Returns:
            bool: True if this word should be converted.
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
        Fill in `processed_syllables` with each syllable's converted
        spelling.

        The two code paths below exist because `convert_text()` and
        `cherry_pick()` (see actions.py) need different behavior:
        `convert_text()` always converts every syllable and reports
        problems (error_skip is off); `cherry_pick()` needs to skip words
        that aren't valid Mandarin - including stopwords and contractions -
        and pass them through unchanged instead of "converting" them into
        nonsense (error_skip is on).
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
        Restore each converted syllable's original capitalization (ALL
        CAPS, Title Case, or unchanged) using the capitalization each
        Syllable already recorded about itself (see
        Syllable.apply_caps in syllable.py).
        """

        # The apply_caps method within the Syllable object is called on each syllable to apply capitalization based on
        # titlecase or uppercase attributes within each syllable.
        self.processed_syllables = [(syl[1].apply_caps(syl[0]), syl[1]) for syl in self.processed_syllables]

    def add_symbols(self):
        """
        Join the converted syllables into `self.final_word`, inserting
        whichever apostrophes/dashes the target romanization method needs
        between them (see _append_syllable below for the specific rules).
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
        Append one converted syllable to `self.final_word`, deciding
        whether it needs an apostrophe or dash before it:

        - A contraction's final syllable always gets an apostrophe (unless
          the target method is Wade-Giles, which already keeps apostrophes
          as part of its initials).
        - Converting to Pinyin: an apostrophe is added only where it's
          needed to keep the word unambiguous (see _needs_apostrophe below).
        - Converting to Wade-Giles: syllables are always separated by a dash.

        Args:
            i (int): Which syllable, by position, to append.
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
        Decide whether joining two Pinyin syllables without a separator
        would be ambiguous - specifically, whether it could be misread as
        a different syllable break. An apostrophe is needed whenever the
        next syllable starts with a vowel and the previous one ends in a
        way that could blend into it (another vowel, or "er"/"n"/"ng").

        Args:
            prev_syllable (str): The syllable just before this one.
            curr_syllable (str): The syllable being appended.

        Returns:
            bool: True if an apostrophe is needed between them.
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
        Used instead of _append_syllable/_needs_apostrophe when the word
        wasn't actually converted (e.g. an English word passing through
        cherry_pick unchanged) - just puts the syllables back together with
        whatever apostrophes/dashes they originally had, rather than
        applying romanization-specific separator rules that wouldn't make
        sense for non-Mandarin text.
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
        Run this word through the full pipeline - convert, restore
        capitalization, add separators - and, if `error_report` is on and
        anything went wrong, log a warning describing the problem.

        Returns:
            str: The finished word.
        """

        self.convert()
        self.apply_caps()
        self.add_symbols()

        # Report errors if error_report is enabled
        if self.processor.config.error_report and self.error_tracker.has_errors():
            error_report = self.error_tracker.generate_report(
                compact=self.processor.config.error_report_compact,
                max_errors=self.processor.config.error_report_max,
                include_summary=False,
                include_details=True
            )

            # For detailed reports, include word context
            if not self.processor.config.error_report_compact:
                message = f"'{self.preview_word}':\n{error_report}"
            else:
                # For compact reports, just show the error
                message = f"'{self.preview_word}': {error_report}"

            # Print error report directly (independent of crumbs setting)
            self.processor.config.logger.warning(f"# Errors in word: {message}")

        return self.final_word
