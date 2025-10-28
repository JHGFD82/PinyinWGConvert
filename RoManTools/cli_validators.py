"""
CLI argument validation utilities for RoManTools.

This module provides validation functions for command-line arguments to ensure
that argument combinations are valid and meet the requirements of the tool.

Functions:
    normalize_method: Normalize romanization method string to standard shorthand format.
    validate_error_reporting_args: Validates that error reporting options are only used with --error_report.
    validate_action_specified: Validates that an action was specified or handles special cases.
    normalize_action_key: Normalizes action names (converts hyphens to underscores).
"""

import argparse
from typing import Dict


def normalize_method(method: str, supported_methods: Dict[str, Dict[str, str]], method_shorthand_to_full: Dict[str, str]) -> str:
    """
    Normalize a romanization method string to a standard shorthand format.
    
    This function accepts various forms of romanization method names (e.g., 'pinyin', 'py',
    'wade-giles', 'wg') and converts them to the canonical shorthand format.

    Args:
        method (str): The romanization method string (e.g., 'pinyin', 'py', 'wade-giles', 'wg').
        supported_methods (dict): Dictionary of supported methods with their metadata.
        method_shorthand_to_full (dict): Mapping from shorthand to full method names.

    Returns:
        str: The normalized shorthand for the romanization method (e.g., 'py', 'wg').

    Raises:
        argparse.ArgumentTypeError: If the method is not recognized.
        
    Example:
        >>> normalize_method('pinyin', {'pinyin': {'shorthand': 'py'}}, {'py': 'pinyin'})
        'py'
        >>> normalize_method('wg', {'wade-giles': {'shorthand': 'wg'}}, {'wg': 'wade-giles'})
        'wg'
    """
    method = method.lower()
    if method in supported_methods:
        return supported_methods[method]['shorthand']
    if method in method_shorthand_to_full:
        return method
    raise argparse.ArgumentTypeError(f"Invalid romanization method: {method}")


def validate_error_reporting_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """
    Validate that error reporting options are only used when --error_report is enabled.
    
    This ensures that --error_compact and --error_max are not specified without
    the main --error_report flag, as they have no effect without error reporting enabled.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments.
        parser (argparse.ArgumentParser): The argument parser instance for error reporting.
    
    Raises:
        SystemExit: If validation fails, exits with an error message.
    
    Example:
        >>> parser = argparse.ArgumentParser()
        >>> args = argparse.Namespace(error_report=False, error_compact=True, error_max=0)
        >>> validate_error_reporting_args(args, parser)  # Will raise error
    """
    if not hasattr(args, 'error_report') or not hasattr(args, 'error_compact'):
        # If these attributes don't exist, no validation needed (e.g., --list-methods)
        return
    
    if (args.error_compact or args.error_max != 0) and not args.error_report:
        parser.error("--error_compact and --error_max require --error_report (-R) to be enabled")


def validate_action_specified(args: argparse.Namespace, parser: argparse.ArgumentParser) -> bool:
    """
    Validate that an action was specified in the command-line arguments.
    
    If no action is provided, displays the parser help message.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments.
        parser (argparse.ArgumentParser): The argument parser instance for displaying help.
    
    Returns:
        bool: True if an action was specified, False if no action (help was printed).
    
    Example:
        >>> parser = argparse.ArgumentParser()
        >>> args = argparse.Namespace(action=None)
        >>> validate_action_specified(args, parser)  # Will print help
        False
    """
    if not args.action:
        parser.print_help()
        return False
    return True


def normalize_action_key(action: str) -> str:
    """
    Normalize action names by converting hyphens to underscores.
    
    This allows CLI commands to use hyphenated names (e.g., 'cherry-pick')
    while using Python-friendly names internally (e.g., 'cherry_pick').
    
    Args:
        action (str): The action name from command-line (may contain hyphens).
    
    Returns:
        str: The normalized action name with underscores.
    
    Example:
        >>> normalize_action_key('cherry-pick')
        'cherry_pick'
        >>> normalize_action_key('segment')
        'segment'
    """
    return action.replace('-', '_')
