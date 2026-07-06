"""
Checks on the command-line arguments the user typed, beyond what argparse
handles on its own.

`argparse` (see main.py) takes care of the basics - is a required argument
present, does a flag's value have the right type - but a few rules need
custom checks that argparse can't express by itself: some flags only make
sense in combination with others, and romanization method names need to be
normalized before the rest of the package sees them. That's what the
functions here do.

Functions:
    normalize_method: Turn any accepted spelling of a romanization method
        into its standard shorthand ('py', 'wg').
    validate_error_reporting_args: Make sure --error_compact/--error_max are
        only used together with --error_report.
    validate_action_specified: Make sure the user actually picked a
        subcommand (segment, convert, etc.).
    normalize_action_key: Turn a hyphenated subcommand name ('cherry-pick')
        into the underscored form used internally ('cherry_pick').
"""

import argparse
from typing import Dict


def normalize_method(method: str, supported_methods: Dict[str, Dict[str, str]], method_shorthand_to_full: Dict[str, str]) -> str:
    """
    Accept any of the ways a user might type a romanization method
    ('pinyin', 'py', 'Wade-Giles', 'wg', ...) and return the standard
    two-letter shorthand.

    Args:
        method (str): Whatever the user typed for the method.
        supported_methods (dict): The full method-name-to-metadata mapping
            (see constants.supported_methods).
        method_shorthand_to_full (dict): The shorthand-to-full-name mapping
            (see constants.method_shorthand_to_full).

    Returns:
        str: The standard shorthand ('py' or 'wg').

    Raises:
        argparse.ArgumentTypeError: If the method isn't recognized.

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
    Make sure `--error_compact`/`--error_max` are only used alongside
    `--error_report` (`-R`) - on their own, they'd have no effect, which
    would be confusing rather than useful, so this rejects that combination
    with a clear command-line error instead of silently ignoring it.

    Args:
        args (argparse.Namespace): The parsed command-line arguments (the
            object argparse produces after reading the command line).
        parser (argparse.ArgumentParser): The parser to report the error
            through, so the message is formatted the same way as any other
            argparse error.

    Raises:
        SystemExit: If the invalid combination was used - `parser.error()`
            prints a usage message and exits, the same as any other invalid
            argument combination argparse itself would catch.

    Example:
        >>> parser = argparse.ArgumentParser()
        >>> args = argparse.Namespace(error_report=True, error_compact=True, error_max=0)
        >>> validate_error_reporting_args(args, parser)  # Fine - error_report is on
    """
    if not hasattr(args, 'error_report') or not hasattr(args, 'error_compact'):
        # If these attributes don't exist, no validation needed (e.g., --list-methods)
        return

    if (args.error_compact or args.error_max != 0) and not args.error_report:
        parser.error("--error_compact and --error_max require --error_report (-R) to be enabled")


def validate_action_specified(args: argparse.Namespace, parser: argparse.ArgumentParser) -> bool:
    """
    Make sure the user actually picked a subcommand (segment, convert,
    etc.). If not, print the same help text `RoManTools --help` would show,
    rather than failing with a less helpful error.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.
        parser (argparse.ArgumentParser): The parser to print help from.

    Returns:
        bool: True if a subcommand was given. False if not (in which case
            the help text has already been printed, and main() should stop
            without trying to run anything).

    Example:
        >>> parser = argparse.ArgumentParser()
        >>> args = argparse.Namespace(action='segment')
        >>> validate_action_specified(args, parser)
        True
    """
    if not args.action:
        parser.print_help()
        return False
    return True


def normalize_action_key(action: str) -> str:
    """
    Turn a hyphenated subcommand name into the underscored form used
    internally - the CLI accepts `cherry-pick` (hyphens read more naturally
    on a command line), but Python identifiers can't contain hyphens, so
    internal lookups (like the ACTIONS dictionary in main.py) use
    `cherry_pick` instead.

    Args:
        action (str): The subcommand name as typed on the command line.

    Returns:
        str: The same name with hyphens replaced by underscores.

    Example:
        >>> normalize_action_key('cherry-pick')
        'cherry_pick'
        >>> normalize_action_key('segment')
        'segment'
    """
    return action.replace('-', '_')
