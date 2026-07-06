"""
Error tracking and reporting utilities for romanized Mandarin text processing.

This module provides comprehensive error tracking for validation issues encountered
during romanization processing, including:
- Invalid initial consonants
- Invalid final components
- Invalid syllable combinations
- Illegal characters
- Rare syllables

Classes:
    ErrorType: Enumeration of error types.
    ValidationError: Represents a single validation error.
    ErrorTracker: Manages collection and reporting of validation errors.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


class ErrorType(Enum):
    """
    Enumeration of validation error types with message templates.
    
    Each error type includes a human-readable message template that can be
    formatted with specific error details.
    
    Attributes:
        INVALID_INITIAL: The initial component of a syllable is not valid for the romanization method.
        INVALID_FINAL: The final component of a syllable is not valid for the romanization method.
        INVALID_SYLLABLE: The initial-final combination is not a valid syllable.
        ILLEGAL_CHARACTER: The syllable contains characters not allowed in the romanization method.
        RARE_SYLLABLE: The syllable is valid but marked as rare or uncommon.
        UNKNOWN: An unspecified or unknown error type.
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
        Initialize an ErrorType with its value and message template.
        
        Args:
            value: The string value for the error type.
            message_template: A format string template for error messages.
        """
        self._value_ = value
        self.message_template = message_template
    
    def format_message(self, **kwargs: Any) -> str:
        """
        Format the error message template with provided values.
        
        Args:
            **kwargs: Values to substitute into the message template.
            
        Returns:
            Formatted error message string.
        """
        return self.message_template.format(**kwargs)


@dataclass
class ValidationError:
    """
    Represents a single validation error encountered during processing.
    
    Attributes:
        error_type: The type of error encountered.
        message: Human-readable error message.
        syllable: The syllable or text that caused the error.
        position: Optional position in the original text where the error occurred.
        details: Additional context-specific details about the error.
    """
    error_type: ErrorType
    message: str
    syllable: str
    position: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=lambda: {})
    
    def __str__(self) -> str:
        """
        Generate a human-readable string representation of the error.
        
        Returns:
            Formatted error message string.
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
    Tracks and manages validation errors during romanization processing.
    
    Provides methods to add errors, check for specific error types, and generate
    comprehensive error reports.
    """
    
    def __init__(self):
        """Initialize an empty error tracker."""
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
        Add a validation error to the tracker.
        
        Args:
            error_type: The type of error.
            message: Human-readable error message.
            syllable: The syllable or text that caused the error.
            position: Optional position in the original text.
            **details: Additional context-specific details.
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
        Add an invalid initial error.
        
        Args:
            initial: The invalid initial component.
            syllable: The full syllable being processed.
            position: Optional position in the original text.
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
        Add an invalid final error.
        
        Args:
            final: The invalid final component.
            syllable: The full syllable being processed.
            initial: The initial component (if any).
            position: Optional position in the original text.
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
        Add an invalid syllable combination error.
        
        Args:
            syllable: The full invalid syllable.
            initial: The initial component.
            final: The final component.
            position: Optional position in the original text.
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
        Add an illegal character error.
        
        Args:
            character: The illegal character found.
            syllable: The syllable containing the illegal character.
            reason: Optional explanation of why the character is illegal.
            position: Optional position in the original text.
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
        Add a rare syllable warning.
        
        Args:
            syllable: The rare syllable.
            romanization_method: The romanization method (e.g., 'py', 'wg').
            position: Optional position in the original text.
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
        Check if any errors have been tracked.
        
        Returns:
            True if errors exist, False otherwise.
        """
        return len(self.errors) > 0
    
    def get_error_count(self, error_type: Optional[ErrorType] = None) -> int:
        """
        Get the count of errors.
        
        Args:
            error_type: Optional specific error type to count. If None, returns total count.
        
        Returns:
            Count of errors.
        """
        if error_type is None:
            return len(self.errors)
        return self._error_counts[error_type]
    
    def get_error_summary(self) -> Dict[str, int]:
        """
        Get a summary of error counts by type.
        
        Returns:
            Dictionary mapping error type names to counts.
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
        Generate an error report with configurable verbosity and detail level.
        
        Args:
            compact: If True, generate compact one-line report. If False, generate detailed report.
            max_errors: Maximum number of errors to include. None means all errors.
            include_summary: Whether to include an error summary (only used when compact=False).
            include_details: Whether to include detailed error listings (only used when compact=False).
        
        Returns:
            Formatted error report string.
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
        Generate a compact one-line error report suitable for tabular data.
        Returns error count in format: 1 error | 2 errors | etc. Only called
        when errors are present (generate_report short-circuits otherwise).

        Returns:
            Compact error count string.
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
        Generate a verbose detailed error report.
        
        Args:
            include_summary: Whether to include an error summary.
            include_details: Whether to include detailed error listings.
            max_errors: Maximum number of errors to include in details.
        
        Returns:
            Verbose error report string.
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
        Merge errors from another ErrorTracker into this one.
        
        Args:
            other: Another ErrorTracker instance to merge from.
        """
        self.errors.extend(other.errors)
        for error_type, count in other._error_counts.items():
            self._error_counts[error_type] += count
    
    def get_first_error_string(self) -> str:
        """
        Get a compact string for the first error only.
        Useful for quick error display in tables.
        
        Returns:
            Compact error string for the first error, or empty string if no errors.
        """
        if not self.has_errors():
            return ""
        
        error = self.errors[0]
        detail = error.details.get('initial') or error.details.get('final') or \
                 error.details.get('character') or error.syllable
        return f"ERROR - {error.error_type.value} - \"{detail}\""
    
    def get_error_types_list(self) -> List[str]:
        """
        Get a list of unique error types present in this tracker.
        Useful for categorizing errors in data analysis.
        
        Returns:
            List of error type strings (e.g., ['invalid_initial', 'rare_syllable']).
        """
        return [error_type.value for error_type, count in self._error_counts.items() if count > 0]
