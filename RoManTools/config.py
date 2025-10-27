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
