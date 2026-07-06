"""
Command-line interface (CLI) for RoManTools: Romanized Mandarin text processing utilities.

This module provides the main entry point for the RoManTools package, enabling users to perform various text processing actions via the command line, including:
- Segmenting text into syllables.
- Converting between romanization standards.
- Cherry-picking romanized words for conversion.
- Counting syllables.
- Detecting romanization methods.
- Validating romanized text.

Functions:
    main(arg_list: Optional[List[str]] = None):
        Parses command-line arguments and dispatches the appropriate processing action.

Usage Example:
    $ romantools segment "Zhongguo ti'an tianqi" -m py
    [['zhong', 'guo'], ['ti', 'an'], ['tian', 'qi']]
"""

import argparse
from typing import Optional, List, Dict, Callable
from .config import Config
from .actions import convert_text, cherry_pick, segment_text, syllable_count, detect_method, validator
from .constants import method_shorthand_to_full, supported_methods, supported_actions, supported_config
from .cli_validators import (
    normalize_method,
    validate_error_reporting_args,
    validate_action_specified,
    normalize_action_key
)


def _normalize_method(method: str) -> str:
    """
    Normalize a romanization method string to a standard shorthand format.
    
    This is a wrapper around the cli_validators.normalize_method function
    that provides the necessary constants from this module's scope.

    Args:
        method (str): The romanization method string (e.g., 'pinyin', 'py', 'wade-giles', 'wg').

    Returns:
        str: The normalized shorthand for the romanization method (e.g., 'py', 'wg').

    Raises:
        argparse.ArgumentTypeError: If the method is not recognized.
    """
    return normalize_method(method, supported_methods, method_shorthand_to_full)


# ACTION FUNCTIONS #
def _segment_action(args: argparse.Namespace, config: Config):
    return segment_text(args.text, args.method, config)


def _validator_action(args: argparse.Namespace, config: Config):
    return validator(args.text, args.method, args.per_word, config)


def _convert_action(args: argparse.Namespace, config: Config):
    return convert_text(args.text, args.convert_from, args.convert_to, config)


def _cherry_pick_action(args: argparse.Namespace, config: Config):
    config.error_skip = True  # Set the specific value for cherry_pick
    return cherry_pick(args.text, args.convert_from, args.convert_to, config)


def _syllable_count_action(args: argparse.Namespace, config: Config):
    return syllable_count(args.text, args.method, config)


def _detect_method_action(args: argparse.Namespace, config: Config):
    return detect_method(args.text, args.per_word, config)


# Map actions to functions
ACTIONS: Dict[str, Callable[[argparse.Namespace, Config], object]] = {
    "segment": _segment_action,
    "validator": _validator_action,
    "convert": _convert_action,
    "cherry_pick": _cherry_pick_action,
    "syllable_count": _syllable_count_action,
    "detect_method": _detect_method_action
}


def main(arg_list: Optional[List[str]] = None):
    """
    Main entry point for the RoManTools CLI. Parses arguments and dispatches the requested action.

    Args:
        arg_list (Optional[List[str]]): List of arguments to parse (for testing or programmatic use). If None, uses sys.argv.

    Raises:
        argparse.ArgumentError: If invalid arguments are provided.

    Example:
        >>> main(['segment', "Zhongguo ti'an tianqi", '-m', 'py'])
        [['zhong', 'guo'], ['ti', 'an'], ['tian', 'qi']]
    """

    from .__init__ import __version__
    
    parser = argparse.ArgumentParser(description='RoManTools: Romanized Mandarin Tools')
    
    # Global arguments
    parser.add_argument('--version', action='version', version=f'RoManTools {__version__}')
    parser.add_argument('--list-methods', action='store_true', 
                       help='List all supported romanization methods')
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest='action', help='Available actions')

    # Create a parent parser for common arguments shared by all subcommands
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-C', '--crumbs', action='store_true',
                              help='Include step-by-step analysis in the output')
    parent_parser.add_argument('-S', '--error_skip', action='store_true',
                              help='Skip errors instead of aborting')
    parent_parser.add_argument('-R', '--error_report', action='store_true',
                              help='Enable error reporting. When enabled, validation errors will be included in the output')
    
    # Error reporting options (only meaningful when --error_report is used)
    error_report_group = parent_parser.add_argument_group(
        'error reporting options',
        'These options configure error reporting behavior and require --error_report (-R) to be enabled'
    )
    error_report_group.add_argument('--error_compact', action='store_true',
                              help='Use compact one-line error format (suitable for tables). Requires --error_report')
    error_report_group.add_argument('--error_max', type=int, default=0,
                              help='Maximum number of errors to report (0 = all errors). Requires --error_report')
    
    # SEGMENT subcommand
    segment_parser = subparsers.add_parser('segment', help='Segment text into syllables', parents=[parent_parser])
    segment_parser.add_argument('text', help='Text to segment')
    segment_parser.add_argument('-m', '--method', type=_normalize_method, required=True,
                              help='Romanization method (pinyin/py, wade-giles/wg)')
    
    # CONVERT subcommand
    convert_parser = subparsers.add_parser('convert', help='Convert between romanization methods', parents=[parent_parser])
    convert_parser.add_argument('text', help='Text to convert')
    convert_parser.add_argument('-f', '--from', type=_normalize_method, required=True,
                              dest='convert_from', help='Source romanization method')
    convert_parser.add_argument('-t', '--to', type=_normalize_method, required=True,
                              dest='convert_to', help='Target romanization method')
    
    # CHERRY_PICK subcommand
    cherry_parser = subparsers.add_parser('cherry-pick', help='Cherry-pick romanized words for conversion', parents=[parent_parser])
    cherry_parser.add_argument('text', help='Text to process')
    cherry_parser.add_argument('-f', '--from', type=_normalize_method, required=True,
                             dest='convert_from', help='Source romanization method')
    cherry_parser.add_argument('-t', '--to', type=_normalize_method, required=True,
                             dest='convert_to', help='Target romanization method')
    
    # SYLLABLE_COUNT subcommand
    syllable_parser = subparsers.add_parser('syllable-count', help='Count syllables in text', parents=[parent_parser])
    syllable_parser.add_argument('text', help='Text to analyze')
    syllable_parser.add_argument('-m', '--method', type=_normalize_method, required=True,
                               help='Romanization method (pinyin/py, wade-giles/wg)')
    
    # DETECT_METHOD subcommand
    detect_parser = subparsers.add_parser('detect-method', help='Detect romanization method', parents=[parent_parser])
    detect_parser.add_argument('text', help='Text to analyze')
    detect_parser.add_argument('-w', '--per-word', action='store_true',
                             help='Perform detection on each word separately')
    
    # VALIDATOR subcommand
    validator_parser = subparsers.add_parser('validator', help='Validate romanized text', parents=[parent_parser])
    validator_parser.add_argument('text', help='Text to validate')
    validator_parser.add_argument('-m', '--method', type=_normalize_method, required=True,
                                help='Romanization method (pinyin/py, wade-giles/wg)')
    validator_parser.add_argument('-w', '--per-word', action='store_true',
                                help='Validate each word separately')
    
    # Parse arguments
    if arg_list is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(arg_list)
    
    # Handle special cases
    if args.list_methods:
        _list_methods()
        return
    
    # Validate that an action was specified
    if not validate_action_specified(args, parser):
        return
    
    # Validate that error_compact and error_max are only used with error_report
    validate_error_reporting_args(args, parser)
    
    # Create the Config object from parsed arguments
    config = Config.from_args(args)
    
    # Print starting timestamp if crumbs is enabled
    from datetime import datetime
    config.print_crumb(level=1, stage='Start', message=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # Normalize action key (convert hyphens to underscores)
    action_key = normalize_action_key(args.action)
    pretty_action = supported_actions[action_key]['pretty']
    config.print_crumb(level=1, stage='Performing action', message=f'{pretty_action}')
    
    # Report configuration if crumbs is enabled
    enabled_configs = [supported_config[key]['pretty'] for key, val in config.__dict__.items() if val and key in supported_config]
    if enabled_configs:
        config.print_crumb(level=1, stage='Configuration', message=', '.join(enabled_configs))
        config.print_crumb(footer=True)
    
    # Handle cherry-pick special case
    if args.action == 'cherry-pick':
        config.error_skip = True
        args.action = 'cherry_pick'  # Normalize for ACTIONS dict
    
    # Call the appropriate function with the Config object
    result = ACTIONS[action_key](args, config)
    
    # Print ending timestamp if crumbs is enabled
    config.print_crumb(level=1, stage='End', message=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    print(str(result))


def _list_methods():
    """List all supported romanization methods."""
    print("Supported romanization methods:")
    for key, value in supported_methods.items():
        print(f"  {key} or {value['shorthand']}: {value['pretty']}")


if __name__ == '__main__':  # pragma: no cover
    main()
