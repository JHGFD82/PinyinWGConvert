"""
Recording and reporting problems found while validating romanized text.

When RoManTools checks a syllable and finds something wrong with it - an
initial that doesn't exist in the romanization method, a combination that
isn't a real syllable, a stray character that shouldn't be there - it
doesn't just say "invalid". It records exactly what went wrong, so that
later on it can show you a useful report instead of a bare True/False.
This module defines what a single recorded problem looks like
(`ValidationError`), the fixed set of problem categories
(`ErrorType`), and the object that collects them all and turns them into a
report (`ErrorTracker`).

Classes:
    ErrorType: The fixed set of problem categories RoManTools can detect.
    ValidationError: One specific recorded problem.
    ErrorTracker: Collects ValidationErrors and builds reports from them.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


class ErrorType(Enum):
    """
    The fixed set of problem categories a syllable can be flagged with.

    This is an "enum" (short for enumeration) - Python's way of naming a
    small, fixed list of options instead of using plain strings everywhere.
    Writing `ErrorType.INVALID_INITIAL` instead of the string
    `"invalid_initial"` means a typo becomes an immediate error instead of
    a silently-wrong comparison somewhere else in the code.

    Each category also carries a message template - a string with a `{...}`
    placeholder that gets filled in with the specific detail (which initial
    was invalid, which character was illegal, etc.) via `format_message()`.

    Attributes:
        INVALID_INITIAL: The syllable's initial (the consonant sound before
            the vowel, e.g. the "zh" in "zhong") doesn't exist in this
            romanization method.
        INVALID_FINAL: The syllable's final (the vowel sound and anything
            after it, e.g. the "ong" in "zhong") doesn't exist in this
            romanization method.
        INVALID_SYLLABLE: The initial and final are each individually valid,
            but this particular combination of the two isn't a real syllable.
        ILLEGAL_CHARACTER: The text contains a character that romanized
            Mandarin text should never contain (a digit, punctuation, etc.).
        RARE_SYLLABLE: The syllable is valid, but unusual enough to be worth
            flagging as "check this by hand."
        UNKNOWN: A fallback category for anything that doesn't fit above.
    """
    # Format: (enum_value, message_template)
    INVALID_INITIAL = ("invalid_initial", "Invalid initial: '{initial}'")
    INVALID_FINAL = ("invalid_final", "Invalid final: '{final}'")
    INVALID_SYLLABLE = ("invalid_syllable", "Invalid syllable combination: '{initial}' + '{final}'")
    ILLEGAL_CHARACTER = ("illegal_character", "Illegal character: '{character}'")
    RARE_SYLLABLE = ("rare_syllable", "Rare syllable: '{syllable}'")
    UNKNOWN = ("unknown", "Unknown error")

    def __init__(self, value: str, message_template: str):
        """
        Args:
            value: The plain-string name for this category (e.g.
                "invalid_initial"), used when the category needs to be shown
                as text rather than as `ErrorType.INVALID_INITIAL`.
            message_template: The message for this category, with `{...}`
                placeholders to be filled in by `format_message()`.
        """
        self._value_ = value
        self.message_template = message_template

    def format_message(self, **kwargs: Any) -> str:
        """
        Fill in this category's message template with the specific details.

        Args:
            **kwargs: The values to substitute into the template's `{...}`
                placeholders (e.g. `initial="zh"` for INVALID_INITIAL).

        Returns:
            The finished, human-readable message string.
        """
        return self.message_template.format(**kwargs)


@dataclass
class ValidationError:
    """
    One specific problem found while validating a syllable.

    This is a "dataclass" - a class whose only job is to hold a handful of
    named values together (here: what kind of problem, a human-readable
    message, which syllable it came from, and so on), with the repetitive
    `__init__` code that would normally do that written for us automatically.

    Attributes:
        error_type: Which category of problem this is (see ErrorType above).
        message: The human-readable description of the problem.
        syllable: The syllable or text that caused the problem.
        position: Where in the original text this occurred, if known.
        details: Any extra category-specific information (e.g. which
            initial or final was involved).
    """
    error_type: ErrorType
    message: str
    syllable: str
    position: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=lambda: {})

    def __str__(self) -> str:
        """
        Format this error as a single readable line, e.g.
        "[invalid_initial] Invalid initial: 'xyz' (initial='xyz')".

        Returns:
            The formatted error message string.
        """
        parts = [f"[{self.error_type.value}]"]
        parts.append(self.message)

        if self.position is not None:
            parts.append(f"at position {self.position}")

        if self.details:
            detail_str = ", ".join(f"{k}='{v}'" for k, v in self.details.items())
            parts.append(f"({detail_str})")

        return " ".join(parts)


class ErrorTracker:
    """
    Collects every ValidationError found while checking one syllable (or
    one word, once the syllables' individual trackers are merged - see
    `merge()` below), and turns that collection into a report.

    Every `Syllable` object (see syllable.py) has its own ErrorTracker,
    created empty and filled in as that syllable is checked. If nothing
    goes wrong, it just stays empty.
    """

    def __init__(self):
        """Create an empty tracker - no errors recorded yet."""
        self.errors: List[ValidationError] = []
        self._error_counts: Dict[ErrorType, int] = {error_type: 0 for error_type in ErrorType}

    def add_error(
        self,
        error_type: ErrorType,
        message: str,
        syllable: str,
        position: Optional[int] = None,
        **details: Any
    ) -> None:
        """
        Record one problem. The category-specific methods below
        (`add_invalid_initial`, `add_illegal_character`, etc.) are
        convenience wrappers around this one - they build the right message
        and details for you, so you rarely need to call this directly.

        Args:
            error_type: The category of problem (see ErrorType).
            message: Human-readable description of the problem.
            syllable: The syllable or text that caused the problem.
            position: Where in the original text this occurred, if known.
            **details: Any extra category-specific information to record.
        """
        error = ValidationError(
            error_type=error_type,
            message=message,
            syllable=syllable,
            position=position,
            details=details
        )
        self.errors.append(error)
        self._error_counts[error_type] += 1

    def add_invalid_initial(self, initial: str, syllable: str, position: Optional[int] = None) -> None:
        """
        Record that a syllable's initial doesn't exist in this romanization method.

        Args:
            initial: The invalid initial that was found.
            syllable: The full syllable being processed.
            position: Where in the original text this occurred, if known.
        """
        self.add_error(
            ErrorType.INVALID_INITIAL,
            ErrorType.INVALID_INITIAL.format_message(initial=initial),
            syllable,
            position,
            initial=initial
        )

    def add_invalid_final(self, final: str, syllable: str, initial: str = "", position: Optional[int] = None) -> None:
        """
        Record that a syllable's final doesn't exist in this romanization method.

        Args:
            final: The invalid final that was found.
            syllable: The full syllable being processed.
            initial: The syllable's initial, if it has one.
            position: Where in the original text this occurred, if known.
        """
        details = {"final": final}
        if initial:
            details["initial"] = initial

        self.add_error(
            ErrorType.INVALID_FINAL,
            ErrorType.INVALID_FINAL.format_message(final=final),
            syllable,
            position,
            **details
        )

    def add_invalid_syllable(
        self,
        syllable: str,
        initial: str,
        final: str,
        position: Optional[int] = None
    ) -> None:
        """
        Record that an initial and final are each valid on their own, but
        don't form a valid syllable together.

        Args:
            syllable: The full invalid syllable.
            initial: The initial component.
            final: The final component.
            position: Where in the original text this occurred, if known.
        """
        self.add_error(
            ErrorType.INVALID_SYLLABLE,
            ErrorType.INVALID_SYLLABLE.format_message(initial=initial, final=final),
            syllable,
            position,
            initial=initial,
            final=final
        )

    def add_illegal_character(
        self,
        character: str,
        syllable: str,
        reason: str = "",
        position: Optional[int] = None
    ) -> None:
        """
        Record that the text contains a character that shouldn't appear in
        romanized Mandarin text at all (a digit, stray punctuation, etc.).

        Args:
            character: The illegal character that was found.
            syllable: The syllable containing the illegal character.
            reason: A short explanation of why it's illegal, if available.
            position: Where in the original text this occurred, if known.
        """
        message = ErrorType.ILLEGAL_CHARACTER.format_message(character=character)
        if reason:
            message += f" - {reason}"

        details = {"character": character}
        if reason:
            details["reason"] = reason

        self.add_error(
            ErrorType.ILLEGAL_CHARACTER,
            message,
            syllable,
            position,
            **details
        )

    def add_rare_syllable(
        self,
        syllable: str,
        romanization_method: str,
        position: Optional[int] = None
    ) -> None:
        """
        Record that a syllable is valid, but unusual enough to flag.

        Args:
            syllable: The rare syllable.
            romanization_method: Which method this was checked against
                (e.g. 'py', 'wg').
            position: Where in the original text this occurred, if known.
        """
        self.add_error(
            ErrorType.RARE_SYLLABLE,
            ErrorType.RARE_SYLLABLE.format_message(syllable=syllable),
            syllable,
            position,
            method=romanization_method
        )

    def has_errors(self) -> bool:
        """
        Returns:
            True if anything has been recorded, False if this tracker is
            still empty.
        """
        return len(self.errors) > 0

    def get_error_count(self, error_type: Optional[ErrorType] = None) -> int:
        """
        Count how many problems have been recorded.

        Args:
            error_type: If given, count only that category. If omitted,
                count everything.

        Returns:
            The count of matching errors.
        """
        if error_type is None:
            return len(self.errors)
        return self._error_counts[error_type]

    def get_error_summary(self) -> Dict[str, int]:
        """
        Returns:
            A dictionary mapping each category name that actually occurred
            (e.g. "invalid_initial") to how many times it occurred.
            Categories with zero occurrences are left out.
        """
        return {
            error_type.value: count
            for error_type, count in self._error_counts.items()
            if count > 0
        }

    def generate_report(
        self,
        compact: bool = False,
        max_errors: Optional[int] = None,
        include_summary: bool = True,
        include_details: bool = True
    ) -> str:
        """
        Build a human-readable report of everything this tracker has recorded.

        Args:
            compact: If True, return a short one-line error count (e.g.
                "2 errors") - good for showing in a spreadsheet/table cell.
                If False, return a detailed multi-line report.
            max_errors: For the detailed report only, the most individual
                errors to list before summarizing the rest as "...and N
                more". None means list every error.
            include_summary: For the detailed report only, whether to
                include the per-category count summary at the top.
            include_details: For the detailed report only, whether to
                include the numbered list of individual errors.

        Returns:
            The formatted report string.
        """
        if not self.has_errors():
            return "No errors detected."

        # Compact format for tabular data
        if compact:
            return self._generate_compact_report()

        # Detailed format for analysis
        return self._generate_verbose_report(include_summary, include_details, max_errors)

    def _generate_compact_report(self) -> str:
        """
        Build the one-line "N errors" report. Only called when at least one
        error is present (generate_report() already handles the zero-error
        case above), so this never needs to say "0 errors".

        Returns:
            A string like "1 error" or "3 errors".
        """
        error_count = len(self.errors)
        return "1 error" if error_count == 1 else f"{error_count} errors"

    def _generate_verbose_report(
        self,
        include_summary: bool,
        include_details: bool,
        max_errors: Optional[int] = None
    ) -> str:
        """
        Build the detailed, multi-line report: an optional summary of counts
        per category, followed by an optional numbered list of every
        individual error (or the first `max_errors` of them).

        Args:
            include_summary: Whether to include the per-category summary.
            include_details: Whether to include the numbered error list.
            max_errors: The most individual errors to list in the numbered
                section before summarizing the rest.

        Returns:
            The formatted, multi-line report string.
        """
        report_lines: List[str] = []

        if include_summary:
            report_lines.append("=== Error Summary ===")
            summary = self.get_error_summary()
            for error_name, count in summary.items():
                report_lines.append(f"  {error_name}: {count}")
            report_lines.append(f"  Total: {len(self.errors)}")

        if include_details and self.errors:
            if include_summary:
                report_lines.append("")
            report_lines.append("=== Detailed Errors ===")

            errors_to_report = self.errors[:max_errors] if max_errors else self.errors
            for i, error in enumerate(errors_to_report, 1):
                report_lines.append(f"{i}. {error}")

            # If we truncated, add indicator
            if max_errors and len(self.errors) > max_errors:
                remaining = len(self.errors) - max_errors
                report_lines.append(f"... and {remaining} more error(s)")

        return "\n".join(report_lines)

    def merge(self, other: "ErrorTracker") -> None:
        """
        Absorb another tracker's recorded errors into this one.

        Used when combining several syllables' individual trackers into one
        tracker for the whole word (see word.py's Word class), so the
        word-level error report reflects every syllable's problems.

        Args:
            other: Another ErrorTracker whose errors should be added to
                this one's.
        """
        self.errors.extend(other.errors)
        for error_type, count in other._error_counts.items():
            self._error_counts[error_type] += count

    def get_first_error_string(self) -> str:
        """
        Describe just the first recorded error, compactly - handy for a
        table column where you only have room for one short string per row.

        Returns:
            A string like `ERROR - invalid_initial - "xyz"`, or an empty
            string if nothing has been recorded.
        """
        if not self.has_errors():
            return ""

        error = self.errors[0]
        detail = error.details.get('initial') or error.details.get('final') or \
                 error.details.get('character') or error.syllable
        return f"ERROR - {error.error_type.value} - \"{detail}\""

    def get_error_types_list(self) -> List[str]:
        """
        Returns:
            The distinct category names that occurred at least once (e.g.
            ['invalid_initial', 'rare_syllable']), useful for grouping or
            filtering results when analyzing many syllables at once.
        """
        return [error_type.value for error_type, count in self._error_counts.items() if count > 0]
