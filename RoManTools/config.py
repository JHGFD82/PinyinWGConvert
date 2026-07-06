"""
Settings that control how RoManTools processes text.

Every action in RoManTools (segment, convert, validate, and so on) takes an
optional `Config` object that turns on extra behavior: a step-by-step trace
of what the program is doing (`crumbs`), tolerance for text that doesn't
fully match a romanization method (`error_skip`), and detailed reporting on
what went wrong when text is invalid (`error_report` and its two related
settings). If you don't pass a `Config`, every action uses the defaults
(everything off), which is what most users want most of the time.

Classes:
    Config: Holds the settings described above and knows how to print a
        breadcrumb trace when `crumbs` is turned on.
"""

import logging
import argparse
from typing import Union, Dict, Any, Optional, Tuple


class Config:
    """
    Holds the optional settings for a single RoManTools action.

    Most of these settings are just about how much output you see -
    `error_skip` is the one exception, since it's required whenever your
    input text mixes romanized Mandarin with other text (English words,
    punctuation, etc.) that shouldn't be treated as invalid romanization.
    """

    def __init__(
        self,
        crumbs: bool = False,
        error_skip: bool = False,
        error_report: bool = False,
        error_report_compact: bool = False,
        error_report_max: int = 0
    ):
        """
        Create a Config with the given settings (all off by default).

        Args:
            crumbs (bool): If True, prints a step-by-step trace of how the
                text is being analyzed - useful when you want to see why a
                particular word was judged valid or invalid.
            error_skip (bool): If True, text that doesn't match the
                romanization method is passed through unchanged instead of
                stopping the whole action. Turn this on whenever your input
                is a mix of romanized Mandarin and other text.
            error_report (bool): If True, prints a report describing what,
                specifically, was wrong with any invalid text encountered.
            error_report_compact (bool): If True, that report is a short
                one-line error count. If False, it's a detailed multi-line
                breakdown. Only matters when error_report is True.
            error_report_max (int): For the detailed report, the most
                errors to list before saying "...and N more". 0 means show
                every error found.
        """

        self.crumbs = crumbs
        self.error_skip = error_skip
        self.error_report = error_report
        self.error_report_compact = error_report_compact
        self.error_report_max = error_report_max if error_report_max > 0 else None
        self.logger = logging.getLogger(__name__)
        if not logging.getLogger().hasHandlers():  # pragma: no cover
            logging.basicConfig(level=logging.INFO, format='%(levelname)5s: %(message)s')  # pragma: no cover

    def _key(self) -> Tuple[bool, bool, bool, bool, Optional[int]]:
        return (self.crumbs, self.error_skip, self.error_report, self.error_report_compact, self.error_report_max)

    def __eq__(self, other: object) -> bool:
        """
        Two Configs with the same settings are treated as equal, even if
        they're two separate objects in memory.

        This matters because several functions elsewhere in the package
        remember ("cache") results they've already computed, keyed on their
        inputs - including the Config used. Without this, two Config(...)
        calls with identical settings would look like different inputs, and
        RoManTools would end up redoing work it had already done.
        """
        if not isinstance(other, Config):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    @staticmethod
    def from_args(args: Union[argparse.Namespace, Dict[str, Any]]) -> "Config":
        """
        Build a Config from parsed command-line arguments or a plain dict.

        `args` is normally an `argparse.Namespace` - the object Python's
        built-in `argparse` library produces after reading the command line
        (the CLI entry point in main.py creates one of these when you run
        `RoManTools ...`). This method reads the relevant fields off of it
        and builds a matching Config, so the rest of the package never has
        to know or care whether a setting came from the command line or was
        set directly in Python code.

        Args:
            args: Either an argparse.Namespace from CLI parsing, or a dict
                  with the same keys. Recognized keys:
                  - crumbs (bool)
                  - error_skip (bool)
                  - error_report (bool)
                  - error_compact (bool)
                  - error_max (int)

        Returns:
            Config: A new Config instance with values from args.

        Examples:
            >>> # From argparse.Namespace
            >>> args = argparse.Namespace(crumbs=True, error_skip=False, error_report=True,
            ...                           error_compact=False, error_max=0)
            >>> config = Config.from_args(args)

            >>> # From dictionary
            >>> config = Config.from_args({'crumbs': True, 'error_report': True})
        """
        # Handle both Namespace and dict
        if isinstance(args, dict):
            return Config(
                crumbs=args.get('crumbs', False),
                error_skip=args.get('error_skip', False),
                error_report=args.get('error_report', False),
                error_report_compact=args.get('error_compact', False),
                error_report_max=args.get('error_max', 0)
            )
        else:
            # argparse.Namespace
            return Config(
                crumbs=getattr(args, 'crumbs', False),
                error_skip=getattr(args, 'error_skip', False),
                error_report=getattr(args, 'error_report', False),
                error_report_compact=getattr(args, 'error_compact', False),
                error_report_max=getattr(args, 'error_max', 0)
            )

    def print_crumb(self, level: int = 0, stage: str = '', message: str = '', footer: bool = False, log_level: int = logging.INFO):
        """
        Print one line of the step-by-step trace, if `crumbs` is turned on.

        If `crumbs` is False, this method does nothing - it's safe to call
        everywhere in the codebase without checking the setting first.

        Args:
            level (int): How deeply nested this line is, shown as that many
                '#' characters before the message (0 for none). Deeper
                levels represent more detailed sub-steps of an outer step.
            stage (str): A short label for what's happening (e.g.
                'Segmentation', 'Converted text').
            message (str): The detail to show after the label.
            footer (bool): If True, also prints a '---' separator line
                after the message, to mark the end of a section.
            log_level (int): Which logging severity to print at
                (logging.INFO, logging.ERROR, etc.) - defaults to INFO.

        Example:
            config = Config(crumbs=True)
            config.print_crumb(1, 'Segmentation', 'Processing text')
            config.print_crumb(2, 'Cached', '"foo" -> "bar"')
            config.print_crumb(2, 'Invalid combination', 'initial: "foo", final: "bar"', log_level=logging.ERROR)
            config.print_crumb(footer=True)
        """
        if self.crumbs:
            assert self.logger is not None  # Logger is always initialized when crumbs is True
            if message:
                prefix = '#' * level + ' ' if level > 0 else ''
                stage_str = f'{stage}: ' if stage else ''
                self.logger.log(log_level, f'{prefix}{stage_str}{message}')
            if footer:
                self.logger.info('---')
