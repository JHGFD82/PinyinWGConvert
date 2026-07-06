"""
Wade-Giles's specific parsing rules.

See base.py for what a "strategy" is and why this exists as its own class.
Wade-Giles is the trickier of the two supported methods to parse: Pinyin
signals a syllable boundary clearly (an apostrophe, or a shift from
consonant to vowel), but Wade-Giles text without hyphens between syllables
can be genuinely ambiguous about where one syllable ends and the next
begins. The methods below handle that by trying a guess, checking whether
it leads somewhere valid, and trying a shorter guess if it doesn't - a
technique generally called backtracking: attempt the most promising option
first, and fall back to the next-best option if it turns out to be a dead
end, rather than giving up.
"""

from typing import TYPE_CHECKING, List, Tuple
from .base import RomanizationStrategy
from ..constants import vowels, apostrophes

if TYPE_CHECKING:
    from ..syllable import Syllable


class WadeGilesStrategy(RomanizationStrategy):
    """
    Wade-Giles-specific parsing rules.

    Compared to Pinyin, Wade-Giles keeps apostrophes as part of the initial
    (e.g. "ch'i", "ts'ai") rather than using them only as separators, and -
    when the input doesn't use hyphens between syllables - needs the
    backtracking approach described in the module docstring above to work
    out where syllable boundaries fall.
    """

    def handle_apostrophe_in_initial(self, text: str, index: int) -> str:
        """
        Unlike the default (see RomanizationStrategy.handle_apostrophe_in_initial
        in base.py), Wade-Giles keeps the apostrophe as part of the initial
        rather than stopping just before it, since it's a meaningful part of
        the spelling (e.g. the apostrophe in "ch'i" distinguishes it from "chi").

        Args:
            text: The text being processed.
            index: Where the apostrophe was found in `text`.

        Returns:
            The initial, including the apostrophe.
        """
        return text[:index] + "'"

    def find_final(self, text: str, initial: str, syllable: "Syllable") -> str:
        """
        Work out the final. If an apostrophe appears in the remaining text,
        it must mark the start of the *next* syllable's initial (Wade-Giles
        apostrophes only ever appear at the start of an initial), so
        everything before it is this syllable's final. Otherwise, hand off
        to whichever backtracking method applies depending on whether an
        initial was already found.

        Args:
            text: The remaining text to extract the final from.
            initial: The syllable's already-known initial (or 'ø').
            syllable: The Syllable being built (unused here, but part of the
                shared method signature every strategy implements - see
                base.py's RomanizationStrategy.find_final).

        Returns:
            The final.
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
        Given a known initial, find its final by trying the longest
        possible candidate first (all the remaining text), and progressively
        shorter candidates, stopping at the first one that's both a valid
        final for this initial *and* leaves the rest of the text able to
        form valid syllables of its own.

        Args:
            text: The text to search for a final in.
            initial: The syllable's already-known initial.

        Returns:
            The final.
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

    def get_illegal_characters(self) -> List[Tuple[str, str]]:
        """
        Same disallowed characters as every method (see
        RomanizationStrategy.get_illegal_characters in base.py) - unlike
        Pinyin, Wade-Giles doesn't add apostrophes to this list, since
        they're a legitimate part of Wade-Giles spelling (e.g. "ch'i").

        Returns:
            A list of (character, reason) pairs.
        """
        # Get base illegal characters, but exclude apostrophes since they're used in Wade-Giles
        illegal_chars = super().get_illegal_characters()

        # Wade-Giles allows apostrophes in initials, so we don't add them to illegal list
        # (apostrophes are a valid part of Wade-Giles romanization)

        return illegal_chars

    def _find_wg_syllable_boundaries(self, text: str) -> str:
        """
        Used when there's no initial to anchor the search (the text starts
        with a vowel, or this is the very first syllable in a run of text
        with no separators at all). Tries progressively longer candidate
        syllables - starting from the shortest possible - and returns the
        first one that's both a real syllable and leaves the rest of the
        text able to form valid syllables of its own.

        Args:
            text: The text to search for a syllable boundary in.

        Returns:
            The first valid syllable found.
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
        Check whether `syllable_text`, taken as a whole, is a valid Wade-
        Giles syllable - by trying every known initial that it starts with
        (longest first, so e.g. "ch'" is tried before "c") and checking
        whether what's left over is a valid final for that initial.

        Args:
            syllable_text: The complete candidate syllable to check.

        Returns:
            True if some initial+final split of this text is valid.
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
        A quick, approximate check on whether `text` could plausibly be
        parsed into more valid syllables - used to decide whether a
        candidate final/syllable is worth accepting, without fully parsing
        the rest of the text (a real recursive parse of the remainder isn't
        needed here; just confirming it *could* start a valid syllable is
        enough to rule out an obviously-wrong split).

        Args:
            text: The remaining text to check.

        Returns:
            True if this text could plausibly form valid syllables.
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
