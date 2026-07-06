"""
Utilities for handling romanized Mandarin validation and conversion.

This module provides helper functions and methods used across the RoManTools package. It includes functionality for:
- Detecting romanization patterns.
- Validating input text.
- Segmenting text into syllables.
- Converting text between different romanization standards.
- Counting syllables in text.

Functions:
    segment_text(text: str, method: str, config: Optional[Config] = None, **kwargs: bool) -> List[Union[List[str], str]]:
        Segments the given text into syllables based on the selected method.
    convert_text(text: str, convert_from: str, convert_to: str, config: Optional[Config] = None, **kwargs: bool) -> str:
        Converts the given text from one romanization standard to another.
    cherry_pick(text: str, convert_from: str, convert_to: str, config: Optional[Config] = None, **kwargs: bool) -> str:
        Converts only valid romanized Mandarin words in the text from one standard to another.
    syllable_count(text: str, method: str, config: Optional[Config] = None, **kwargs: bool) -> list[int]:
        Returns the count of syllables for each word in the processed text.
    detect_method(text: str, per_word: bool = False, config: Optional[Config] = None, **kwargs: bool) -> Union[List[str], List[Dict[str, List[str]]]]:
        Detects the romanization method(s) of the given text or individual words.
    validator(text: str, method: str, per_word: bool = False, config: Optional[Config] = None, **kwargs: bool) -> Union[bool, list[dict]]:
        Validates the processed text or individual words based on the selected method.

Caching:
    Every function below is backed by a module-level lru_cache keyed on its
    arguments (including `config`, which compares equal across instances with
    the same settings — see Config.__eq__). This means repeated calls with the
    same text/method/config — e.g. in a loop over many rows of a dataset, or
    the same syllable recurring throughout a large document — are only
    processed once for the life of the process.

    Caching is bypassed (the function always runs fresh) when `config.crumbs`
    or `config.error_report` is set, since both produce output as a side
    effect of processing that must happen on every call, not just on a cache
    miss.

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
    Whether a call should skip the cache and run fresh.

    Only settings that produce output as a side effect of processing
    (breadcrumb traces, error-report logging) need to bypass caching — a cache
    hit would otherwise silently swallow that output. `error_skip` and similar
    purely-behavioral settings don't need this: they're already part of the
    Config value used as the cache key, so different settings simply produce
    different (correctly separate) cache entries.
    """
    return config.crumbs or config.error_report


# Processing actions
def _process_text_impl(text: str, method: str, config: Config) -> Sequence[Union[Sequence[Syllable], Syllable, str]]:
    processor = TextChunkProcessor(text, config, load_method_params(method))
    return processor.get_chunks()


_cached_process_text = lru_cache(maxsize=1000000)(_process_text_impl)


def _process_text(text: str, method: str, config: Config) -> Sequence[Union[Sequence[Syllable], Syllable, str]]:
    """
    Processes the given text using the specified method and configuration.

    Args:
        text (str): The text to be processed.
        method (str): The method to apply for text processing.
        config (Config): The configuration object containing processing settings.

    Returns:
        Sequence[Union[Sequence[Syllable], Syllable, str]]: A sequence of processed text chunks,
        which could be individual syllables, sequences of syllables, or strings.
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
    Segments the given text into syllables based on the selected romanization method.

    Args:
        text (str): The text to be segmented.
        method (str): The romanization method to use for segmentation.
        config (Config, optional): Configuration object for processing settings. Defaults to None.
        **kwargs: Additional keyword arguments to initialize the Config object if not provided.

    Returns:
        List[Union[List[str], str]]: A list where each element is either a list of syllable strings (for words)
            or a string (for non-text elements).

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
    Converts the given text from one romanization standard to another.

    Args:
        text (str): The text to be converted.
        convert (Dict[str, str]): Dictionary with 'from' and 'to' keys specifying conversion standards.
        config (Config): Configuration object for processing settings.
        stopwords (Set[str]): Set of stopwords to exclude from conversion.
        include_spaces (bool): Whether to include spaces between converted words.

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
    Converts the given text from one romanization standard to another.

    Args:
        text (str): The text to be converted.
        convert_from (str): The romanization standard to convert from.
        convert_to (str): The romanization standard to convert to.
        config (Config, optional): Configuration object for processing settings. Defaults to None.
        **kwargs: Additional keyword arguments to initialize the Config object if not provided.

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
    Converts only valid romanized Mandarin words in the text from one standard to another.
    Non-romanized words are left unchanged.

    Args:
        text (str): The text to be processed.
        convert_from (str): The romanization standard to convert from.
        convert_to (str): The romanization standard to convert to.
        config (Config, optional): Configuration object for processing settings. Defaults to None.
        **kwargs: Additional keyword arguments to initialize the Config object if not provided.

    Returns:
        str: The text with valid romanized Mandarin words converted.

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
    Returns the count of syllables for each word in the processed text.

    Args:
        text (str): The text to be analyzed.
        method (str): The romanization method for the supplied text.
        config (Config, optional): Configuration object for processing settings. Defaults to None.
        **kwargs: Additional keyword arguments to initialize the Config object if not provided.

    Returns:
        list[int]: A list of syllable counts for each valid word in the text.

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
    Detects the valid processing methods for a given chunk of romanized Mandarin text.

    Args:
        chunk (str): A segment of romanized Mandarin text to be analyzed.
        config (Config): The configuration object containing processing settings.
        crumbs (bool, optional): Whether to include intermediate outputs (crumbs) during processing. Defaults to False.

    Returns:
        List[str]: A list of methods that are valid for processing the given chunk.
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
    Detects the romanization method(s) of the given text or of each word.

    Args:
        text (str): The text to be analyzed.
        per_word (bool, optional): If True, returns methods for each word separately. Defaults to False.
        config (Config, optional): Configuration object for processing settings. Defaults to None.
        **kwargs: Additional keyword arguments to initialize the Config object if not provided.

    Returns:
        Union[List[str], List[Dict[str, Union[str, List[str]]]]]:
            If per_word is False, returns a list of valid methods for the entire text.
            If per_word is True, returns a list of dicts with 'word' and 'methods' keys for each word.

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
    Validates the processed text or individual words based on the selected romanization method.

    Args:
        text (str): The text to be validated.
        method (str): The romanization method to use for validation.
        per_word (bool, optional): If True, returns validation for each word separately. Defaults to False.
        config (Config, optional): Configuration object for processing settings. Defaults to None.
        **kwargs: Additional keyword arguments to initialize the Config object if not provided.

    Returns:
        Union[bool, list[dict[str, Union[str, list[str], list[bool]]]]]:
            If per_word is False, returns True if all syllables are valid, else False.
            If per_word is True, returns a list of dicts with 'word', 'syllables', and 'valid' keys for each word.

    Example:
        >>> validator("Zhongguo", method="py")
        True
    """
    if config is None:
        config = Config(**kwargs)
    if _should_bypass_cache(config):
        return _validator_impl(text, method, per_word, config)
    return _cached_validator(text, method, per_word, config)
