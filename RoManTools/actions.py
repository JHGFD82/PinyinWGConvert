"""
The six things you can do with RoManTools: segment, convert, cherry-pick,
count syllables, detect a method, and validate text.

Every one of these functions follows the same basic recipe: split the input
into syllables (see chunker.py), then do something specific with the
result. `main.py` (the command-line tool) and `RoManTools/__init__.py`
(the `from RoManTools import ...` API) both just call the functions defined
here - this module is where the actual work happens.

Functions:
    segment_text(text, method, config=None, **kwargs): Split text into its
        syllables.
    convert_text(text, convert_from, convert_to, config=None, **kwargs):
        Convert text from one romanization method to another.
    cherry_pick(text, convert_from, convert_to, config=None, **kwargs):
        Convert only the valid romanized Mandarin words in a mixed-language
        text, leaving everything else untouched.
    syllable_count(text, method, config=None, **kwargs): Count the
        syllables in each word of the text.
    detect_method(text, per_word=False, config=None, **kwargs): Work out
        which romanization method(s) a piece of text could be.
    validator(text, method, per_word=False, config=None, **kwargs): Check
        whether text is valid for a given romanization method.

Why repeated calls are fast:
    Every function below remembers results it's already computed - a
    technique generally called caching. If you call `convert_text("Zhongguo",
    ...)` a thousand times in a loop (for example, once per row of a
    spreadsheet), only the first call actually does the work; the other 999
    get the answer back instantly from memory. This matters a lot for the
    kind of workloads RoManTools is built for: processing a whole dataset,
    or a document where the same words come up again and again.

    The one exception: if you turn on `crumbs` (a step-by-step trace of what
    the program is doing) or `error_report` (a report on what went wrong),
    caching is skipped and the function runs fresh every time. Both of
    those settings produce printed output as a side effect of doing the
    work - if a cached answer were returned instead, that output simply
    wouldn't happen, which would be confusing. Every other setting doesn't
    have this problem: it's already baked into what gets cached, so using
    different settings just gives you separate, independently-cached
    answers rather than needing to skip the cache altogether.

Usage Example:
    >>> from RoManTools import segment_text, convert_text, cherry_pick, syllable_count, detect_method, validator
    >>> segment_text("Zhongguo ti'an tianqi", method="py")
    [['zhong', 'guo'], ['ti', 'an'], ['tian', 'qi']]
    >>> convert_text("Zhongguo", convert_from="py", convert_to="wg")
    'Chung-kuo'
    >>> cherry_pick("This is Zhongguo.", convert_from="py", convert_to="wg")
    'This is Chung-kuo.'
    >>> syllable_count("Zhongguo", method="py")
    [2]
    >>> detect_method("Zhongguo")
    ['py']
    >>> validator("Zhongguo", method="py")
    True
"""

from functools import lru_cache
from typing import Dict, Union, List, Set, Optional, Sequence
from .config import Config
from .chunker import TextChunkProcessor
from .syllable import Syllable
from .word import WordProcessor
from .data_loader import load_method_params, load_stopwords
from .constants import method_shorthand_to_full, supported_methods

__all__ = ['segment_text', 'convert_text', 'cherry_pick', 'syllable_count', 'detect_method', 'validator']


def _should_bypass_cache(config: Config) -> bool:
    """
    Whether a call should skip the cache and run fresh - see "Why repeated
    calls are fast" in this module's docstring for the full explanation.
    Only `crumbs` and `error_report` need this: both print output as a side
    effect of running, which a cache hit would silently skip. Every other
    setting (like `error_skip`) is already part of what gets cached, so
    different settings simply get their own separate cache entries instead
    of needing to bypass caching entirely.
    """
    return config.crumbs or config.error_report


# Processing actions
def _process_text_impl(text: str, method: str, config: Config) -> Sequence[Union[Sequence[Syllable], Syllable, str]]:
    processor = TextChunkProcessor(text, config, load_method_params(method))
    return processor.get_chunks()


_cached_process_text = lru_cache(maxsize=1000000)(_process_text_impl)


def _process_text(text: str, method: str, config: Config) -> Sequence[Union[Sequence[Syllable], Syllable, str]]:
    """
    Run the shared first step behind every action: split `text` into
    chunks and parse each word-chunk into Syllable objects (see
    chunker.TextChunkProcessor).

    Args:
        text (str): The text to process.
        method (str): Which romanization method to use.
        config (Config): The settings for this run.

    Returns:
        The processed chunks - see TextChunkProcessor.get_chunks in
        chunker.py for exactly what this looks like.
    """
    # TextChunkProcessor prints breadcrumb traces as a side effect of parsing;
    # a cache hit would silently skip that output, so bypass the cache here
    # whenever crumbs are on (there's no equivalent concern for error_report:
    # nothing inside parsing is gated on it, and cached Syllable objects still
    # carry their fully-populated error_tracker either way).
    if config.crumbs:
        return _process_text_impl(text, method, config)
    return _cached_process_text(text, method, config)


# Segmentation actions
def _segment_text_impl(text: str, method: str, config: Config) -> List[Union[List[str], str]]:
    chunks = _process_text(text, method, config)
    segmented_result: List[Union[List[str], str]] = []
    config.print_crumb(1, 'Segment Text', 'Assembling segments', True)
    for chunk in chunks:
        if isinstance(chunk, list):
            # Return the full syllable attribute for each Syllable object
            segmented_result.append([syl.text_attr.full_syllable for syl in chunk])
        elif isinstance(chunk, str):
            # Return the non-text elements as strings
            segmented_result.append(chunk)
    return segmented_result


_cached_segment_text = lru_cache(maxsize=1000000)(_segment_text_impl)


def segment_text(text: str, method: str, config: Optional[Config] = None, **kwargs: bool) -> List[Union[List[str], str]]:
    """
    Split text into its syllables.

    Args:
        text (str): The text to segment.
        method (str): Which romanization method the text is in.
        config (Config, optional): The settings for this run. If not
            given, one is built from **kwargs.
        **kwargs: Settings to build a Config from, if you didn't pass one
            directly (see config.py's Config for the available settings).

    Returns:
        A list where each entry is either a list of syllable strings (one
        entry per word) or a plain string (a stretch of non-text content,
        like punctuation, left as-is).

    Example:
        >>> segment_text("Zhongguo ti'an tianqi", method="py")
        [['zhong', 'guo'], ['ti', 'an'], ['tian', 'qi']]
    """
    if config is None:
        config = Config(**kwargs)
    if _should_bypass_cache(config):
        return _segment_text_impl(text, method, config)
    return _cached_segment_text(text, method, config)


# Conversion actions
def _conversion_processing(text: str, convert: Dict[str, str], config: Config, stopwords: Set[str], include_spaces: bool) -> str:
    """
    Shared logic behind convert_text() and cherry_pick(): parse the text,
    convert each word, and join the results back into one string.

    Args:
        text (str): The text to convert.
        convert (Dict[str, str]): The romanization methods to convert
            between, as `{"from": ..., "to": ...}`.
        config (Config): The settings for this run.
        stopwords (Set[str]): Words to leave unconverted (e.g. "China").
        include_spaces (bool): Whether to rejoin words with spaces
            (convert_text) or run them back together with no separator
            (cherry_pick, which needs to preserve the original spacing
            found in the text itself rather than adding its own).

    Returns:
        str: The converted text.
    """
    word_processor = WordProcessor(config, convert['from'], convert['to'], stopwords)
    concat_text: List[str] = []

    chunks = _process_text(text, convert['from'], config)

    # Print conversion crumb after text analysis, before conversion
    if config.crumbs:
        from_pretty = supported_methods[method_shorthand_to_full[convert["from"]]]["pretty"]
        to_pretty = supported_methods[method_shorthand_to_full[convert["to"]]]["pretty"]
        config.print_crumb(1, "Converting text", f'{from_pretty} -> {to_pretty}')

    for chunk in chunks:
        if isinstance(chunk, list):
            word = word_processor.create_word(chunk)
            concat_text.append(word.process_syllables())
        elif isinstance(chunk, str):
            concat_text.append(chunk)
    config.print_crumb(footer=True)
    return " ".join(concat_text) if include_spaces else "".join(concat_text)


def _convert_text_impl(text: str, convert_from: str, convert_to: str, config: Config) -> str:
    stopwords = set(load_stopwords())
    convert = {"from": convert_from, "to": convert_to}
    return _conversion_processing(text, convert, config, stopwords, include_spaces=True)


_cached_convert_text = lru_cache(maxsize=1000000)(_convert_text_impl)


def convert_text(text: str, convert_from: str, convert_to: str, config: Optional[Config] = None, **kwargs: bool) -> str:
    """
    Convert text from one romanization method to another.

    Args:
        text (str): The text to convert.
        convert_from (str): The romanization method to convert from.
        convert_to (str): The romanization method to convert to.
        config (Config, optional): The settings for this run. If not
            given, one is built from **kwargs.
        **kwargs: Settings to build a Config from, if you didn't pass one
            directly.

    Returns:
        str: The converted text.

    Example:
        >>> convert_text("Zhongguo", convert_from="py", convert_to="wg")
        'Chung-kuo'
    """
    if config is None:
        config = Config(**kwargs)
    if _should_bypass_cache(config):
        return _convert_text_impl(text, convert_from, convert_to, config)
    return _cached_convert_text(text, convert_from, convert_to, config)


def _cherry_pick_impl(text: str, convert_from: str, convert_to: str, config: Config) -> str:
    stopwords = set(load_stopwords())
    convert = {"from": convert_from, "to": convert_to}
    return _conversion_processing(text, convert, config, stopwords, include_spaces=False)


_cached_cherry_pick = lru_cache(maxsize=1000000)(_cherry_pick_impl)


def cherry_pick(text: str, convert_from: str, convert_to: str, config: Optional[Config] = None, **kwargs: bool) -> str:
    """
    Convert only the valid romanized Mandarin words in a mixed-language
    text, leaving English words, punctuation, and spacing untouched. Handy
    for converting Mandarin names embedded in an otherwise-English sentence
    or document, without needing to pull them out first.

    Args:
        text (str): The text to process.
        convert_from (str): The romanization method to convert from.
        convert_to (str): The romanization method to convert to.
        config (Config, optional): The settings for this run. If not
            given, one is built from **kwargs (with error_skip already
            turned on - see below).
        **kwargs: Settings to build a Config from, if you didn't pass one
            directly.

    Returns:
        str: The text, with valid romanized Mandarin words converted and
        everything else left as it was.

    Example:
        >>> cherry_pick("This is Zhongguo.", convert_from="py", convert_to="wg")
        'This is Chung-kuo.'
    """
    if config is None:
        config = Config(error_skip=True, **kwargs)
    if _should_bypass_cache(config):
        return _cherry_pick_impl(text, convert_from, convert_to, config)
    return _cached_cherry_pick(text, convert_from, convert_to, config)


# Counting actions
def _syllable_count_impl(text: str, method: str, config: Config) -> List[int]:
    chunks = _process_text(text, method, config)
    config.print_crumb(1, 'Syllable Count', 'Assembling counts', True)
    # Return the length of each chunk if all syllables are valid, otherwise return 0 (will change to error messages
    # in later update)
    return [len(chunk) for chunk in chunks if isinstance(chunk, list)]


_cached_syllable_count = lru_cache(maxsize=1000000)(_syllable_count_impl)


def syllable_count(text: str, method: str, config: Optional[Config] = None, **kwargs: bool) -> List[int]:
    """
    Count the syllables in each word of the text.

    Args:
        text (str): The text to analyze.
        method (str): Which romanization method the text is in.
        config (Config, optional): The settings for this run. If not
            given, one is built from **kwargs.
        **kwargs: Settings to build a Config from, if you didn't pass one
            directly.

    Returns:
        list[int]: The syllable count for each word in the text, in order.

    Example:
        >>> syllable_count("Zhongguo", method="py")
        [2]
    """
    if config is None:
        config = Config(**kwargs)
    if _should_bypass_cache(config):
        return _syllable_count_impl(text, method, config)
    return _cached_syllable_count(text, method, config)


# Detection and validation actions
def _detect_for_chunk(chunk: str, config: Config, crumbs: bool = False) -> List[str]:
    """
    Work out which romanization method(s) `chunk` could validly be, by
    trying each supported method in turn and checking whether every
    syllable in the chunk parses as valid under it.

    Args:
        chunk (str): The text to check (the whole input, or a single word,
            depending on whether detect_method was called with per_word).
        config (Config): The settings for this run.
        crumbs (bool, optional): Whether to print a summary breadcrumb
            after checking. Defaults to False.

    Returns:
        List[str]: The romanization methods this chunk is valid for.
    """
    result: List[str] = []
    for method in method_shorthand_to_full.keys():
        processed_chunks = _process_text(chunk, method, config)
        syllable_chunks: List[Syllable] = []
        for processed_chunk in processed_chunks:
            if isinstance(processed_chunk, list):
                for syllable in processed_chunk:
                    syllable_chunks.append(syllable)
        if syllable_chunks and all(syllable.valid for syllable in syllable_chunks):
            result.append(method)
    if crumbs:
        config.print_crumb(1, 'Detect Method', 'Assembling methods for all syllables', True)
    return result


def _detect_method_impl(text: str, per_word: bool, config: Config) -> Union[List[str], List[Dict[str, Union[str, List[str]]]]]:
    if not per_word:
        # Perform detection for the entire text, returning a single list of valid methods
        return _detect_for_chunk(text, config, True)
    # Perform detection per word, returning the valid methods for each word
    words = text.split()
    results: List[Dict[str, Union[str, List[str]]]] = []
    for word in words:
        valid_methods = _detect_for_chunk(word, config)
        results.append({"word": word, "methods": valid_methods})
    config.print_crumb(1, 'Detect Method', 'Assembling methods', True)
    return results


_cached_detect_method = lru_cache(maxsize=1000000)(_detect_method_impl)


def detect_method(text: str, per_word: bool = False, config: Optional[Config] = None, **kwargs: bool) -> Union[List[str], List[Dict[str, Union[str, List[str]]]]]:
    """
    Work out which romanization method(s) a piece of text could be. Some
    text is ambiguous - for example, a word that's a valid syllable in both
    Pinyin and Wade-Giles - so the result is always a list, even when there
    turns out to be only one possible answer.

    Args:
        text (str): The text to analyze.
        per_word (bool, optional): If True, check each word separately
            instead of requiring the whole text to agree on one method.
            Defaults to False.
        config (Config, optional): The settings for this run. If not
            given, one is built from **kwargs.
        **kwargs: Settings to build a Config from, if you didn't pass one
            directly.

    Returns:
        If per_word is False: a list of the romanization methods valid for
        the whole text. If per_word is True: a list of dicts, each with a
        'word' and its own 'methods' list.

    Example:
        >>> detect_method("Zhongguo")
        ['py']
    """
    if config is None:
        config = Config(**kwargs)
    if _should_bypass_cache(config):
        return _detect_method_impl(text, per_word, config)
    return _cached_detect_method(text, per_word, config)


def _validator_impl(text: str, method: str, per_word: bool, config: Config) -> Union[bool, List[Dict[str, Union[str, List[str], List[bool]]]]]:
    chunks = _process_text(text, method, config)
    syllable_chunks: List[Syllable] = []
    for chunk in chunks:
        if isinstance(chunk, list):
            for syllable in chunk:
                syllable_chunks.append(syllable)
    if not per_word:
        # Perform validation for the entire text, returning a single boolean value
        return all(syllable.valid for syllable in syllable_chunks)
    # Perform validation per word, returning the validity of each word
    result: List[Dict[str, Union[str, List[str], List[bool]]]] = []
    for chunk in chunks:
        if isinstance(chunk, list):
            word_result: Dict[str, Union[str, List[str], List[bool]]] = {
                'word': ''.join(syl.text_attr.full_syllable for syl in chunk),
                'syllables': [syl.text_attr.full_syllable for syl in chunk],
                'valid': [bool(syl.valid) for syl in chunk]
            }
            result.append(word_result)
    return result


_cached_validator = lru_cache(maxsize=1000000)(_validator_impl)


def validator(text: str, method: str, per_word: bool = False, config: Optional[Config] = None, **kwargs: bool) -> Union[bool, List[Dict[str, Union[str, List[str], List[bool]]]]]:
    """
    Check whether text is valid for a given romanization method.

    Args:
        text (str): The text to validate.
        method (str): Which romanization method to validate against.
        per_word (bool, optional): If True, check and report each word
            separately instead of returning one overall answer. Defaults
            to False.
        config (Config, optional): The settings for this run. If not
            given, one is built from **kwargs.
        **kwargs: Settings to build a Config from, if you didn't pass one
            directly.

    Returns:
        If per_word is False: True if every syllable in the text is valid,
        False otherwise. If per_word is True: a list of dicts, each with a
        word, its syllables, and which of those syllables are valid.

    Example:
        >>> validator("Zhongguo", method="py")
        True
    """
    if config is None:
        config = Config(**kwargs)
    if _should_bypass_cache(config):
        return _validator_impl(text, method, per_word, config)
    return _cached_validator(text, method, per_word, config)
