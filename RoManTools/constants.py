"""
Shared reference data used throughout RoManTools.

This module holds the small, fixed pieces of information that the rest of
the package needs to agree on: which characters count as vowels, which
punctuation marks are treated as apostrophes or dashes, which romanization
methods are supported, and so on. Nothing in this file changes while the
program runs - it's read-only reference data, not a place where
processing happens.

Constants:
    vowels (Set[str]): Vowel characters recognized in romanized Mandarin text.
    apostrophes (Set[str]): The different apostrophe-like characters a user
        might type (straight quote, curly quotes, etc.) - all of them are
        treated the same way during processing.
    dashes (Set[str]): The different dash-like characters a user might type.
    supported_contractions (Set[str]): English contraction endings (e.g. the
        "s" in "it's") that are allowed to appear after a Mandarin word
        without being mistaken for a romanization error.
    supported_methods (Dict): The romanization methods RoManTools understands
        (Pinyin, Wade-Giles), each with its two-letter shorthand ("py", "wg")
        and a human-readable display name.
    supported_actions (Dict): The CLI/API actions RoManTools offers (convert,
        segment, etc.), each with a human-readable display name used in
        breadcrumb output (see Config.print_crumb in config.py).
    supported_config (Dict): The debugging/output settings a user can turn
        on (crumbs, error_skip, error_report), each with a human-readable
        display name.
    nontext_chars (Dict): Whitespace characters, with a readable label for
        each (e.g. "[newline]" for "\\n") - used only when printing
        breadcrumb output, so the trace is legible instead of showing a raw
        invisible character.
"""

from typing import Dict, Tuple, Any

vowels = {'a', 'e', 'i', 'o', 'u', 'ü', 'v', 'ê', 'ŭ'}
apostrophes = {"'", "’", "‘", "ʼ", "ʻ", "`"}
dashes = {"-", "–", "—"}
supported_contractions = {"s", "d", "ll"}
supported_methods = {
    'pinyin': {'shorthand': 'py', 'pretty': 'Pinyin'},
    'wade-giles': {'shorthand': 'wg', 'pretty': 'Wade-Giles'}
}
supported_actions = {
    'convert': {'pretty': 'Convert Text'},
    'cherry_pick': {'pretty': 'Cherry Pick'},
    'segment': {'pretty': 'Segmentation'},
    'validator': {'pretty': 'Validator'},
    'syllable_count': {'pretty': 'Syllable Count'},
    'detect_method': {'pretty': 'Detect Method'}
}
supported_config = {
    'crumbs': {'pretty': 'Print Crumbs'},
    'error_skip': {'pretty': 'Skip Errors'},
    'error_report': {'pretty': 'Report Errors'}
}
nontext_chars = {
    ' ': {'pretty': '[space]'},
    '\n': {'pretty': '[newline]'},
    '\t': {'pretty': '[tab]'},
    '\r': {'pretty': '[carriage_return]'},
    '\f': {'pretty': '[form_feed]'},
    '\v': {'pretty': '[vertical_tab]'}
}


def alias_maps(support_dict: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Build a two-way lookup between a method's full name and its shorthand.

    `supported_methods` above stores each method once, under its full name
    ("pinyin"), with the shorthand ("py") tucked inside as a detail. That's
    convenient to write, but code elsewhere needs to go both directions -
    given "py", find "pinyin", and given "pinyin", find "py". Rather than
    writing that lookup logic twice, this function builds both directions
    once, from any dictionary shaped like `supported_methods`.

    Args:
        support_dict: A dictionary whose values are themselves dictionaries
            containing a 'shorthand' key (e.g. `supported_methods`).

    Returns:
        A pair of dictionaries: (shorthand -> full name, full name -> shorthand).
    """
    shorthand_to_full: Dict[str, str] = {v['shorthand']: k for k, v in support_dict.items()}
    full_to_shorthand: Dict[str, str] = {k: v['shorthand'] for k, v in support_dict.items()}
    return shorthand_to_full, full_to_shorthand


method_shorthand_to_full, method_full_to_shorthand = alias_maps(supported_methods)
