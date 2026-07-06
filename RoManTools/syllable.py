"""
Building and validating individual syllables.

This is the heart of RoManTools: taking one piece of romanized text and
figuring out whether it's a real syllable, and if so, what its parts are.
Every Mandarin syllable (in the romanization methods RoManTools supports)
breaks down into an initial and a final - for example, in "zhong", the
initial is "zh" (the consonant sound at the start) and the final is "ong"
(the vowel sound and anything after it). Some syllables have no initial at
all (e.g. "an"); RoManTools represents that case internally with the
placeholder symbol "ø" rather than an empty string, so it's never confused
with "we haven't looked yet."

Classes:
    SyllableProcessor: Shared setup for one romanization method - loads its
        syllable-validity data once, then builds and validates Syllable
        objects with it.
    Syllable: One syllable, with its initial/final worked out and validated.
"""

import re
import logging
from typing import Tuple, Optional, Dict, Union, List, Set
from .config import Config
from .constants import vowels, apostrophes, dashes
from .strategies import RomanizationStrategyFactory
from .errors import ErrorTracker
from .data_loader import load_rare_syllables


# Type alias for method_params for clarity and maintainability
MethodParams = Dict[str, Union[Tuple[Tuple[bool, ...], ...], List[str], str]]


class SyllableProcessor:
    """
    Holds everything needed to build and validate syllables for one
    romanization method, so that work only has to happen once per method
    rather than once per syllable.

    Pinyin and Wade-Giles each parse syllables slightly differently (for
    example, Wade-Giles keeps apostrophes as part of the initial; Pinyin
    doesn't use them at all). Rather than scattering `if method == 'wg'`
    checks throughout this file, each method's specific rules live in their
    own small object, called a strategy (see strategies/base.py for the
    full explanation) - this class picks the right one and hands it to
    every Syllable it builds.
    """

    def __init__(self, config: Config, method_params: MethodParams):
        """
        Args:
            config (Config): The settings for this run (see config.py).
            method_params (MethodParams): The syllable-validity data for one
                romanization method (see data_loader.load_method_params).
        """

        self.config = config
        self.ar = method_params['ar']
        self.init_list = method_params['init_list']
        self.fin_list = method_params['fin_list']
        self.method = method_params['method']

        # Initialize the appropriate strategy for this romanization method
        self.strategy = RomanizationStrategyFactory.create_strategy(str(self.method), self)

        # Load rare syllables data
        self.rare_syllables: Dict[str, Set[str]] = load_rare_syllables()

        # Initialize error tracker
        self.error_tracker = ErrorTracker()

    def create_syllable(self, text: str, remainder: str = "") -> "Syllable":
        """
        Build a Syllable object from a piece of text.

        Args:
            text (str): The text to parse into a syllable.
            remainder (str): Any leftover text already known to come after
                this syllable (usually left as the default; see
                Syllable._find_initial_final for where this is used).

        Returns:
            Syllable: The resulting syllable, with its initial, final, and
                validity already worked out.
        """
        return Syllable(text, self, remainder)

    def validate_final_using_array(self, initial: str, final: str, silent: bool = False, error_tracker: Optional[ErrorTracker] = None) -> bool:
        """
        Check whether a specific initial+final combination is a real
        syllable, by looking it up in the method's validity table (loaded
        from a CSV file - see data_loader.load_romanization_data). The
        table is a grid, one row per initial and one column per final, so
        this comes down to finding the right row and column and reading the
        True/False value stored there.

        Args:
            initial (str): The initial to look up (or 'ø' for "no initial").
            final (str): The final to look up.
            silent (bool): If True, don't print a breadcrumb or record an
                error for an invalid result - used when this is just a
                trial check (e.g. "could this be the final?") rather than a
                final decision.
            error_tracker (Optional[ErrorTracker]): Where to record the
                problem if the combination turns out to be invalid.

        Returns:
            bool: True if this initial+final combination is a real syllable.
        """
        # Indexes for both initial and final are both determined
        initial_index = self.init_list.index(initial) if initial in self.init_list else -1
        final_index = self.fin_list.index(final) if final in self.fin_list else -1

        # If no valid indexes are found, return False
        if initial_index == -1 or final_index == -1:
            if not silent:
                error_parts: List[str] = []
                if initial_index == -1:
                    error_parts.append(f"invalid initial: '{initial}'")
                    # Track error in the error tracker if provided
                    if error_tracker:
                        error_tracker.add_invalid_initial(
                            initial if initial != 'ø' else '',
                            initial + final
                        )
                if final_index == -1:
                    error_parts.append(f"invalid final: '{final}'")
                    # Track error in the error tracker if provided
                    if error_tracker:
                        error_tracker.add_invalid_final(
                            final,
                            initial + final,
                            initial if initial != 'ø' else ''
                        )
                error_message = ", ".join(error_parts)
                self.config.print_crumb(3, "Validation", error_message, log_level=logging.ERROR)
            return False

        # Check the validity of the initial-final combination using the syllable array
        is_valid = bool(self.ar[initial_index][final_index])

        # If the combination is invalid, track it
        if not is_valid and not silent and error_tracker:
            error_tracker.add_invalid_syllable(
                initial + final,
                initial if initial != 'ø' else '',
                final
            )
            self.config.print_crumb(
                3,
                "Validation",
                f"invalid syllable combination: '{initial}' + '{final}'",
                log_level=logging.ERROR
            )

        return is_valid


class SyllableTextAttributes:
    """
    The text-related pieces of a syllable: its raw text, and (once worked
    out) its initial, final, and combined full form.
    """

    def __init__(self, text: str, remainder: str = ""):
        """
        Args:
            text: The syllable's text.
            remainder: Any leftover text known to follow this syllable.
        """

        self.text = text.lower()
        self.remainder = remainder
        self.initial = ""
        self.final = ""
        self.full_syllable = ""


class SyllableStatusAttributes:
    """
    How a syllable was originally written, so that formatting can be
    restored later: was it in ALL CAPS, Title Case, did it start with an
    apostrophe or a dash?
    """

    def __init__(self, text: str):
        """
        Args:
            text: The syllable's original text, before any of this
                information is stripped out for parsing.
        """

        self.has_apostrophe = False
        self.has_dash = False
        self.capitalize = False
        self.uppercase = text.isupper()
        self._is_titlecase(text)

    def _is_titlecase(self, text: str):
        """
        Work out whether `text` is capitalized like "Zhong" rather than
        "zhong" or "ZHONG", while ignoring apostrophes/dashes that would
        otherwise confuse Python's built-in `.istitle()` check.
        """

        # Remove all non-letter characters (.istitle() does not function properly with apostrophes and dashes)
        cleaned_text = re.sub(r'[^a-zA-Z]', '', text)
        self.capitalize = cleaned_text.istitle()


class Syllable:
    """
    One syllable: its text, its initial/final breakdown, whether it's
    valid, and any problems found along the way (in `error_tracker` - see
    errors.py).
    """

    def __init__(self, text: str, processor: SyllableProcessor, remainder: str = ""):

        """
        Parses and validates `text` as a syllable immediately upon creation
        - by the time this constructor returns, every attribute described
        above is already filled in.

        Args:
            text (str): The syllable's text.
            remainder (str, optional): Any leftover text known to follow
                this syllable. Defaults to "".
            processor (SyllableProcessor): The processor to validate
                against (holds the method-specific rules and data).
        """

        self.processor = processor
        self.text_attr = SyllableTextAttributes(text, remainder)
        self.valid = False
        self.status_attr = SyllableStatusAttributes(text)
        self.error_tracker = ErrorTracker()

        # Check for illegal characters before processing
        self._check_illegal_characters(text)

        self._handle_first_char()
        self._process_syllable()

        # Check for rare syllables if valid
        if self.valid:
            self._check_rare_syllable()

    def apply_caps(self, text: str) -> str:
        """
        Re-apply this syllable's original capitalization to `text` (used
        after conversion, to restore the capitalization the input had).

        Args:
            text (str): The text to capitalize.

        Returns:
            str: The capitalized text.
        """

        if self.status_attr.uppercase:
            return text.upper()
        if self.status_attr.capitalize:
            return text.capitalize()
        return text

    def _handle_first_char(self):
        """
        If the syllable's text starts with an apostrophe or dash, note that
        (for `status_attr`) and, except for a Wade-Giles leading apostrophe
        (which is a meaningful part of the initial, not just a separator),
        strip it off before parsing continues.
        """

        if (first_char := self.text_attr.text[0]) in apostrophes:
            self.status_attr.has_apostrophe = True
        elif first_char in dashes:
            self.status_attr.has_dash = True

        if (first_char in apostrophes and self.processor.method != 'wg') or first_char in dashes:
            self.text_attr.text = self.text_attr.text[1:]

    def _process_syllable(self):
        """
        Work out this syllable's initial, final, and full form, then
        validate the result and print a breadcrumb describing what was
        found.
        """

        # Construct parts of syllable
        self.text_attr.initial, self.text_attr.final, self.text_attr.full_syllable, self.text_attr.remainder = (
            self._find_initial_final(self.text_attr.text))
        # Validate the syllable
        self.valid = self._validate_syllable()
        # Print the results of the syllable processing
        if self.valid:
            self.processor.config.print_crumb(3, "Syllable", f'"{self.text_attr.full_syllable}" valid: {self.valid}')
        else:
            error_msg = f'"{self.text_attr.full_syllable}" valid: {self.valid}'
            self.processor.config.print_crumb(3, "Syllable", error_msg, log_level=logging.ERROR)

    def _find_initial_final(self, text: str) -> Tuple[str, str, str, str]:
        """
        Work out where this syllable's initial ends and its final begins,
        and what (if anything) is left over as the start of the next
        syllable.

        Args:
            text (str): The text to parse.

        Returns:
            Tuple[str, str, str, str]: (initial, final, full syllable,
                leftover text for the next syllable).
        """

        initial = self._find_initial(text)
        self.processor.config.print_crumb(2, "initial found", initial)  # Print the initial found
        # If a "ø" is found, indicating no initial, find the final without the initial
        if initial == 'ø':
            final = self._find_final(text, initial)
            initial = ''
        else:
            final = self._find_final(text[len(initial):], initial)
        self.processor.config.print_crumb(2, "final found", final)  # Print the final found
        # After finding final, concatenate initial and final to get the full syllable
        full_syllable = initial + final
        remainder_start = len(full_syllable)
        remainder = text[remainder_start:]

        return initial, final, full_syllable, remainder

    def _find_initial(self, text: str) -> str:
        """
        Read characters from the start of `text` until a vowel (or
        apostrophe) is reached - everything read up to that point is the
        initial. If the very first character is a vowel, there's no
        initial at all, represented as 'ø'.

        Args:
            text (str): The text to extract the initial from.

        Returns:
            str: The initial, or 'ø' if there isn't one.
        """

        for i, c in enumerate(text):
            if c in vowels:
                if i == 0:  # If a vowel is found at the beginning of the syllable, return 'ø' to indicate no initial
                    return 'ø'
                # Otherwise, all text up to this point is the initial
                if (initial := text[:i]) not in self.processor.init_list:  # Check if the initial is valid
                    self.error_tracker.add_invalid_initial(initial, text)
                    return text[:i]  # Return text up to this point if not valid
                return initial
            if c in apostrophes:  # Handle apostrophes using strategy
                return self.processor.strategy.handle_apostrophe_in_initial(text, i)

        return text

    def _find_final(self, text: str, initial: str) -> str:
        """
        Work out the final, once the initial is already known. The actual
        rules differ by romanization method (see handle_vowel_case and
        handle_consonant_case below for Pinyin's rules, and
        strategies/wade_giles.py for Wade-Giles's), so this just asks the
        current method's strategy object to do it.

        Args:
            text (str): The remaining text to extract the final from.
            initial (str): This syllable's already-known initial.

        Returns:
            str: The final.
        """
        return self.processor.strategy.find_final(text, initial, self)

    def handle_vowel_case(self, text: str, i: int, initial: str) -> Optional[str]:
        """
        Work out the final when it starts with a vowel at position `i` in
        `text`. Because a run of vowels can belong to more than one
        possible final (e.g. "ao" vs. just "a"), this checks every final in
        the method's known list that starts with the text seen so far, and
        picks the longest one that's actually valid for this initial.

        Args:
            text (str): The text being parsed.
            i (int): Where the vowel was found in `text`.
            initial (str): This syllable's already-known initial.

        Returns:
            The final, or None to signal "keep scanning" (the caller,
            PinyinStrategy.find_final in strategies/pinyin.py, moves on to
            the next character in that case).
        """

        if i + 1 == len(text):
            return text  # This is a simple final with no further characters to process, usually in cases of no
            # consonants or multi-vowel finals
        # Iterate over the list of potential finals that start with the current vowel
        # Generate list of possible finals from this point in the text
        test_finals = [
            f_item for f_item in self.processor.fin_list
            if isinstance(f_item, str) and f_item.startswith(text[:i + 1]) and self._validate_final(initial, f_item, silent=True)
        ]
        # If no valid finals are found, return the text up to the vowel
        if not test_finals:
            self.error_tracker.add_invalid_final(text, self.text_attr.full_syllable or text, initial)
            if i == 0:
                return None
            up_to_vowel = text[:i]
            return up_to_vowel
        return None

    def handle_consonant_case(self, text: str, i: int, initial: str) -> str:
        """
        Work out the final when it starts with a consonant at position `i`
        in `text`, including the special cases "er"/"erh", "n", and "ng"
        that don't follow the simple "consonants can't be part of a final"
        rule.

        Args:
            text (str): The text being parsed.
            i (int): Where the consonant was found in `text`.
            initial (str): This syllable's already-known initial.

        Returns:
            str: The final.
        """

        remainder = len(text) - i - 1
        # Handle "er" and "erh"
        if text[i - 1:i + 1] == 'er':
            if self.processor.method == 'wg':
                # In Wade-Giles, 'er' is not valid, so if we see 'erh', it must be the 'erh' final
                if remainder > 0 and text[i + 1] == 'h':
                    return text[:i + 2]  # Return "erh"
                # If no 'h' follows, just return 'er' (which will be invalid and caught by validation)
                return text[:i + 1]
            else:
                # Pinyin logic
                if remainder == 0 or text[i + 1] not in vowels:
                    return text[:i + 1]
        # Handle "n" and "ng"
        if text[i] == 'n':
            # Determine whether we are dealing with "ng" or just "n"
            next_char_is_g = remainder > 0 and text[i + 1] == 'g'
            # For possible "ng" cases, check if "g" is the last letter, if the next character after "g"
            # is a consonant, or if the current "n" final is invalid
            # This allows for "changan" to be split into "chan" and "gan" instead of "chang" and "an"
            valid_ng = next_char_is_g and (
                remainder == 1 or text[i + 2] not in vowels or not self._validate_final(initial, text[:i + 1], silent=True))
            if valid_ng:
                return text[:i + 2]  # Return "ng"
            if next_char_is_g:
                return text[:i + 1]  # Return just "n" if the "ng" final isn't valid
            valid_n = remainder == 0 or text[i + 1] not in vowels or not self._validate_final(initial, text[:i], silent=True)
            return text[:i + 1] if valid_n else text[:i]  # Return "n" or fall back to last vowel
        # Default case: handle all other consonants
        return text[:i]

    def _validate_final(self, initial: str, final: str, silent: bool = False) -> bool:
        """
        Check whether this specific initial+final combination is a real
        syllable (delegates to SyllableProcessor.validate_final_using_array
        above, passing along this syllable's own error_tracker so any
        problem found gets recorded against this syllable specifically).
        Also used, via _validate_syllable below, to do the final check once
        the whole syllable has been parsed.

        Args:
            initial (str): The initial to check.
            final (str): The final to check.
            silent (bool): If True, don't print a breadcrumb or record an
                error - used while still testing candidate finals, before a
                final decision has been made.

        Returns:
            bool: True if the combination is valid.
        """
        return self.processor.validate_final_using_array(initial, final, silent, self.error_tracker)

    def _validate_syllable(self) -> bool:
        """
        Check whether this syllable's initial+final combination (now that
        both are known) is a real syllable.

        Returns:
            bool: True if valid.
        """

        # Syllable validation is performed by _validate_final, but is referenced here; "ø" supplied again for no initial
        if self.text_attr.initial == '':
            return self._validate_final('ø', self.text_attr.final)
        return self._validate_final(self.text_attr.initial, self.text_attr.final)

    def _check_illegal_characters(self, text: str) -> None:
        """
        Check `text` for characters that should never appear in this
        romanization method at all (digits, stray punctuation, etc. - the
        specific list depends on the method, e.g. Pinyin disallows
        apostrophes inside a syllable while Wade-Giles requires them), and
        record any found in this syllable's error_tracker.

        Args:
            text: The syllable's original text to check.
        """
        illegal_chars = self.processor.strategy.check_illegal_characters(text, self)
        for char, reason in illegal_chars:
            self.error_tracker.add_illegal_character(char, text, reason)

    def _check_rare_syllable(self) -> None:
        """
        If this (already-valid) syllable is flagged as rare/unusual for its
        method (see data_loader.load_rare_syllables), record that as a
        note in the error_tracker - not a failure, just something worth a
        second look.
        """
        method = str(self.processor.method)
        full_syllable_lower = self.text_attr.full_syllable.lower()

        if method in self.processor.rare_syllables:
            if full_syllable_lower in self.processor.rare_syllables[method]:
                self.error_tracker.add_rare_syllable(
                    self.text_attr.full_syllable,
                    method
                )
