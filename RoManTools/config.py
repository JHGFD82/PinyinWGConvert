"""
Configuration settings for romanized Mandarin text processing.

This module provides the `Config` class, which is used to manage various configuration options for text processing,
including:
- Including intermediate outputs (crumbs) during processing.
- Skipping error reporting on invalid characters.
- Reporting errors encountered during processing.

Classes:
    Config: Manages configuration settings for text processing.
"""

import logging
import argparse
from typing import Union, Dict, Any, Optional, Tuple


class Config:
    """
    Configuration settings for processing text. Options are ancillary to the main processing functions except
    error_skip which is essential for methods where non-romanized Mandarin characters are maintained in output.
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
        Initializes instances of the Config class.

        Args:
            crumbs (bool): If True, includes intermediate outputs (crumbs) during processing.
            error_skip (bool): If True, skips error reporting on invalid characters.
            error_report (bool): If True, reports errors encountered during processing.
            error_report_compact (bool): If True, generates compact one-line reports. If False, generates detailed error reports.
            error_report_max (int): Maximum number of errors to include in reports. 0 means all errors. Only first N errors will be shown.
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
        """Two Configs with the same settings are equal, regardless of identity.

        This makes Config usable as an lru_cache key across separate calls that
        build equivalent-but-distinct Config instances (the common case, since
        callers typically don't reuse one Config object across calls).
        """
        if not isinstance(other, Config):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    @staticmethod
    def from_args(args: Union[argparse.Namespace, Dict[str, Any]]) -> "Config":
        """
        Create a Config instance from argparse.Namespace or a dictionary.
        
        This factory method simplifies Config creation by automatically extracting
        the relevant attributes from CLI arguments or a dictionary.
        
        Args:
            args: Either an argparse.Namespace from CLI parsing or a dict with config parameters.
                  Expected attributes/keys:
                  - crumbs (bool): Include step-by-step analysis
                  - error_skip (bool): Skip errors instead of aborting
                  - error_report (bool): Enable error reporting
                  - error_compact (bool): Use compact error format
                  - error_max (int): Maximum number of errors to report
        
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
        Prints a crumb message based on the configuration settings using logging.

        Args:
            level (int): The number of '#' symbols to prefix the crumb (0 for none).
            stage (str): The stage or action of processing (e.g., 'Segmentation', 'Converted text').
            message (str): The main message or detail to display after the stage.
            footer (bool): If True, adds a '---' line as a crumb footer.
            log_level (int): The logging level to use (logging.INFO, logging.ERROR, etc.). Defaults to logging.INFO.

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
