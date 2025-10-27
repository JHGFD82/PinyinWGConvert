"""
Utility functions for validating romanized Mandarin text in tabular data.

This module provides convenience functions for use with pandas DataFrames and other
tabular data structures, making it easy to validate romanized text and get error reports
suitable for table columns.

Functions:
    validate_syllable(text: str, method: str, compact: bool, max_errors: int) -> str:
        Validate a single syllable and return error report string.
    validate_text(text: str, method: str, compact: bool, max_errors: int) -> Dict[str, Any]:
        Validate text and return structured error information.
    get_validation_column(text: str, method: str) -> str:
        Get a simple validation result for a table column (OK or error).
"""

from typing import Dict, Any
from .config import Config
from .syllable import SyllableProcessor
from .data_loader import load_method_params


def validate_syllable(
    text: str,
    method: str = 'py',
    compact: bool = True,
    max_errors: int = 1
) -> str:
    """
    Validate a single syllable and return an error report string.
    
    Designed for use in pandas DataFrame apply() operations or similar table processing.
    
    Args:
        text: The syllable text to validate.
        method: Romanization method ('py' for Pinyin, 'wg' for Wade-Giles).
        compact: If True, return compact one-line format. If False, return detailed format.
        max_errors: Maximum number of errors to include (0 = all errors).
    
    Returns:
        Error report string, or empty string if no errors.
    
    Examples:
        >>> validate_syllable('beijing', method='py')
        ''
        >>> validate_syllable('xyz', method='py')
        'ERROR - invalid_initial - "xyz"'
        >>> validate_syllable('pia', method='py')
        'ERROR - rare_syllable - "pia"'
    """
    config = Config(error_report=False)
    method_params = load_method_params(method)
    processor = SyllableProcessor(config, method_params)
    
    syllable = processor.create_syllable(text)
    
    if not syllable.error_tracker.has_errors():
        return ""
    
    return syllable.error_tracker.generate_report(
        verbose=not compact,
        max_errors=max_errors if max_errors > 0 else None
    )


def validate_text(
    text: str,
    method: str = 'py',
    compact: bool = True,
    max_errors: int = 0
) -> Dict[str, Any]:
    """
    Validate text and return structured error information.
    
    Returns a dictionary with validation results, useful for creating multiple
    columns in a DataFrame.
    
    Args:
        text: The text to validate.
        method: Romanization method ('py' for Pinyin, 'wg' for Wade-Giles).
        compact: If True, use compact error format. If False, use detailed format.
        max_errors: Maximum number of errors to include (0 = all errors).
    
    Returns:
        Dictionary with keys:
            - 'valid': bool, True if no errors
            - 'error_count': int, number of errors detected
            - 'error_types': list of error type strings
            - 'error_report': str, formatted error report
            - 'first_error': str, first error only (compact format)
    
    Examples:
        >>> result = validate_text('beijing', method='py')
        >>> result['valid']
        True
        >>> result = validate_text('xyz', method='py')
        >>> result['valid']
        False
        >>> result['error_types']
        ['invalid_initial', 'invalid_final']
    """
    config = Config(error_report=False)
    method_params = load_method_params(method)
    processor = SyllableProcessor(config, method_params)
    
    syllable = processor.create_syllable(text)
    
    return {
        'valid': not syllable.error_tracker.has_errors(),
        'error_count': syllable.error_tracker.get_error_count(),
        'error_types': syllable.error_tracker.get_error_types_list(),
        'error_report': syllable.error_tracker.generate_report(
            verbose=not compact,
            max_errors=max_errors if max_errors > 0 else None
        ) if syllable.error_tracker.has_errors() else "",
        'first_error': syllable.error_tracker.get_first_error_string()
    }


def get_validation_column(text: str, method: str = 'py') -> str:
    """
    Get a simple validation result for a table column.
    
    Returns either "OK" if valid, or a compact error description if invalid.
    This is the simplest function for adding a validation column to a DataFrame.
    
    Args:
        text: The text to validate.
        method: Romanization method ('py' for Pinyin, 'wg' for Wade-Giles).
    
    Returns:
        "OK" if valid, or compact error string if invalid.
    
    Examples:
        >>> get_validation_column('beijing', method='py')
        'OK'
        >>> get_validation_column('mha', method='py')
        'ERROR - invalid_initial - "mh"'
    """
    config = Config(error_report=False)
    method_params = load_method_params(method)
    processor = SyllableProcessor(config, method_params)
    
    syllable = processor.create_syllable(text)
    
    if not syllable.error_tracker.has_errors():
        return "OK"
    
    return syllable.error_tracker.get_first_error_string()


# Example usage with pandas (docstring only, not executed):
"""
Example: Using with pandas DataFrame
====================================

import pandas as pd
from RoManTools.table_utils import validate_syllable, validate_text, get_validation_column

# Create a DataFrame with romanized text
df = pd.DataFrame({
    'syllable': ['beijing', 'shanghai', 'xyz', 'mha', 'pia', 'ma1']
})

# Option 1: Simple validation column (OK or error)
df['validation'] = df['syllable'].apply(get_validation_column)

# Option 2: Just get error messages (empty if valid)
df['errors'] = df['syllable'].apply(lambda x: validate_syllable(x, compact=True, max_errors=1))

# Option 3: Get detailed validation info
validation_results = df['syllable'].apply(validate_text)
df['valid'] = validation_results.apply(lambda x: x['valid'])
df['error_count'] = validation_results.apply(lambda x: x['error_count'])
df['error_types'] = validation_results.apply(lambda x: ', '.join(x['error_types']))
df['first_error'] = validation_results.apply(lambda x: x['first_error'])

# Option 4: Filter to only invalid syllables
df['is_valid'] = df['syllable'].apply(lambda x: validate_text(x)['valid'])
invalid_df = df[~df['is_valid']]

# Option 5: Get error type categories
df['has_rare_syllable'] = df['syllable'].apply(
    lambda x: 'rare_syllable' in validate_text(x)['error_types']
)
df['has_illegal_char'] = df['syllable'].apply(
    lambda x: 'illegal_character' in validate_text(x)['error_types']
)
"""
