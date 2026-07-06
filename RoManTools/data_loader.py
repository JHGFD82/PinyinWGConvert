"""
Data loading utilities for romanized Mandarin text processing.

This module provides functions to load various data required for processing romanized Mandarin text, including:
- Romanization data (initials, finals, and valid combinations).
- Conversion mappings between different romanization methods.
- Method parameters for specific romanization methods.
- Stopwords list.
- Rare syllable information.

Functions:
    load_romanization_data(file_path: str) -> Tuple[List[str], List[str], Tuple[Tuple[bool, ...], ...]]:
        Load romanization data from a CSV file and return initials, finals, and a 2D array indicating valid combinations.
    load_conversion_data() -> List[Dict[str, str]]:
        Load the conversion mappings between different romanization methods.
    load_rare_syllables() -> Dict[str, set[str]]:
        Load rare syllable information from conversion mappings.
    load_method_params(method: str) -> Dict[str, Union[Tuple[Tuple[bool, ...], ...], List[str], str]]:
        Load romanization method parameters including initials, finals, and the valid combinations array.
    load_stopwords() -> List[str]:
        Load a list of stopwords from a text file.
"""

from functools import lru_cache
from typing import Tuple, List, Dict, Union
import os
import csv


base_path = os.path.dirname(__file__)


@lru_cache(maxsize=None)
def load_romanization_data(file_path: str) -> Tuple[List[str], List[str], Tuple[Tuple[bool, ...], ...]]:
    """
    Loads romanization data from a CSV file and returns the initials, finals, and a nested tuple indicating valid
    combinations.

    Args:
        file_path (str): The path to the CSV file containing romanization data.

    Returns:
        Tuple[List[str], List[str], Tuple[Tuple[bool, ...], ...]]]: A tuple containing the following:
            - List of initials.
            - List of finals.
            - A nested tuple representing valid initial-final combinations.
    """

    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)
    init_list = [row[0] for row in data[1:]]
    fin_list = data[0][1:]
    ar = tuple(tuple(cell == '1' for cell in row[1:]) for row in data[1:])
    return init_list, fin_list, ar


@lru_cache(maxsize=None)
def load_conversion_data() -> List[Dict[str, str]]:
    """
    Loads the conversion mappings based on the method combination specified during initialization.

    Cached for the life of the process (the CSV never changes at runtime). The
    returned list/dicts are shared across callers — treat as read-only.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing conversion mappings between different romanization methods.
    """

    source_file = os.path.join(base_path, 'data', 'conversion_mapping.csv')
    mappings: List[Dict[str, str]] = []
    with open(source_file, encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            mappings.append(row)
    return mappings


@lru_cache(maxsize=None)
def load_rare_syllables() -> Dict[str, set[str]]:
    """
    Loads rare syllable information from the conversion mapping CSV.

    Cached for the life of the process; the returned dict is shared across
    callers — treat as read-only.

    Returns:
        Dict[str, set[str]]: A dictionary mapping romanization method codes to sets of rare syllables.
                             For example: {'py': {'ong', 'pia', 'pun'}, 'wg': set()}
    """
    source_file = os.path.join(base_path, 'data', 'conversion_mapping.csv')
    rare_syllables: Dict[str, set[str]] = {'py': set(), 'wg': set()}
    
    with open(source_file, encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Check if the meta column indicates a rare syllable
            if row.get('meta', '').strip().lower() == 'rare':
                # Add to appropriate romanization method sets
                if row.get('py'):
                    rare_syllables['py'].add(row['py'].lower())
                if row.get('wg'):
                    rare_syllables['wg'].add(row['wg'].lower())
    
    return rare_syllables


@lru_cache(maxsize=None)
def load_method_params(method: str) -> Dict[str, Union[Tuple[Tuple[bool, ...], ...], List[str], str]]:
    """
    Loads romanization method parameters including initials, finals, and the valid combinations array.

    Cached per method for the life of the process; the returned dict is shared
    across callers — treat as read-only.

    Args:
        method (str): The romanization method (e.g., 'py', 'wg').

    Returns:
        Dict[str, List[str], np.ndarray]: A dictionary containing initials, finals, and the valid combinations array.
    """

    method_file = f'{method}DF'
    try:
        init_list, fin_list, ar = load_romanization_data(os.path.join(base_path, 'data', f'{method_file}.csv'))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Syllable array for method '{method}' not found.") from exc
    return {
        'ar': ar,
        'init_list': init_list,
        'fin_list': fin_list,
        'method': method
    }


@lru_cache(maxsize=None)
def load_stopwords() -> List[str]:
    """
    Loads a list of stopwords from a text file.

    Cached for the life of the process; the returned list is shared across
    callers — treat as read-only.

    Returns:
        List[str]: A list of stopwords.
    """

    file_path = os.path.join(base_path, 'data', 'stopwords.txt')
    with open(file_path, encoding='utf-8') as f:
        stopwords = f.read().splitlines()
    return stopwords
