"""
Loading RoManTools' reference data from disk.

RoManTools doesn't hard-code which syllables are valid Pinyin or
Wade-Giles - it reads that information from CSV files (CSV = "comma-separated
values", a plain-text spreadsheet format) shipped in the `data/` folder next
to this module. This module is the only place that opens those files. Every
other part of the package asks one of the functions below for the data it
needs, rather than reading files directly.

Each function is decorated with `@lru_cache`, meaning the first call reads
the file from disk and remembers the result; every call after that (with the
same arguments) returns the remembered result instantly instead of reading
the file again. This matters if you're processing a large number of words
in a loop - without it, every single call would reopen and re-parse the same
CSV file from scratch.

Functions:
    load_romanization_data(file_path): Read one method's syllable-validity
        file and return its initials, finals, and the table of which
        combinations are valid.
    load_conversion_data(): Read the table that maps each syllable between
        romanization methods.
    load_rare_syllables(): Read which syllables are flagged as rare/unusual.
    load_method_params(method): The main entry point most code uses -
        load everything needed to validate syllables for one method ('py'
        or 'wg').
    load_stopwords(): Read the list of English words that should never be
        treated as romanized Mandarin.
"""

from functools import lru_cache
from typing import Tuple, List, Dict, Union
import os
import csv


base_path = os.path.dirname(__file__)


@lru_cache(maxsize=None)
def load_romanization_data(file_path: str) -> Tuple[List[str], List[str], Tuple[Tuple[bool, ...], ...]]:
    """
    Read one romanization method's syllable-validity table from a CSV file
    (e.g. `data/pyDF.csv`) and unpack it into three pieces of data.

    The CSV is laid out as a grid: the first row lists every possible final
    (the vowel-and-beyond part of a syllable), the first column of every
    other row lists every possible initial (the consonant part), and each
    cell is "1" or "0" saying whether that initial+final combination is a
    real syllable.

    Args:
        file_path (str): Path to the CSV file to read.

    Returns:
        A tuple of:
            - The list of initials (the row labels).
            - The list of finals (the column labels).
            - A nested tuple of True/False values, one row per initial, one
              column per final, where `ar[i][f]` is True if that initial+
              final combination is a valid syllable.
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
    Read the conversion table (`data/conversion_mapping.csv`) that lists,
    for every syllable, its spelling in each supported romanization method.
    This is what makes `convert_text()`/`cherry_pick()` possible - converting
    a syllable is just looking up its row in this table.

    Cached for the life of the program, since the file never changes while
    RoManTools is running. The returned data is shared between every part of
    the program that asks for it, so treat it as read-only - modifying it in
    place would affect every other caller too.

    Returns:
        A list of dictionaries, one per syllable, each mapping a
        romanization method's shorthand ('py', 'wg') to that syllable's
        spelling in that method.
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
    Read which syllables are marked "rare" in the conversion table - valid,
    but unusual enough that RoManTools flags them for a second look rather
    than silently accepting them (see Syllable._check_rare_syllable in
    syllable.py).

    Cached for the life of the program; the returned dictionary is shared
    between callers, so treat it as read-only.

    Returns:
        A dictionary mapping each romanization method's shorthand to the set
        of syllables flagged as rare in that method, e.g.
        `{'py': {'ong', 'pia', 'pun'}, 'wg': set()}`.
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
    Load everything needed to validate syllables for one romanization
    method. This is the function most of the rest of the package actually
    calls - it wraps `load_romanization_data()` above, using the naming
    convention that method "py" is stored in `data/pyDF.csv`, method "wg"
    in `data/wgDF.csv`, and so on.

    Cached per method for the life of the program; the returned dictionary
    is shared between callers, so treat it as read-only.

    Args:
        method (str): The romanization method's shorthand (e.g. 'py', 'wg').

    Returns:
        A dictionary with keys 'ar' (the valid-combinations table), 'init_list',
        'fin_list', and 'method' - everything `SyllableProcessor` (see
        syllable.py) needs to validate syllables for this method.
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
    Read the list of English words (`data/stopwords.txt`) that should never
    be treated as romanized Mandarin, even if they happen to also be valid
    syllables - words like "China" or "Beijing" that are already standard
    English spellings and shouldn't be "corrected" by convert_text() or
    cherry_pick().

    Cached for the life of the program; the returned list is shared between
    callers, so treat it as read-only.

    Returns:
        List[str]: The list of stopwords.
    """

    file_path = os.path.join(base_path, 'data', 'stopwords.txt')
    with open(file_path, encoding='utf-8') as f:
        stopwords = f.read().splitlines()
    return stopwords
