# RoManTools Function Call Documentation

This document provides an overview of the public functions available when importing the RoManTools package directly (`from RoManTools import ...`). All are re-exported from `RoManTools/actions.py` via `RoManTools/__init__.py`. All examples below were verified against the current package.

## A note on performance

If you call any of these functions repeatedly with the same input - for example, looping over a column of a dataset with `df['name'].apply(lambda x: convert_text(x, convert_from="py", convert_to="wg"))` - only the first call for a given input actually does the work. After that, RoManTools returns the answer from a cache (a saved copy of the previous result) instead of redoing it, so processing a large, repetitive dataset is much faster than the first call alone would suggest.

## Public Methods

### `convert_text`

Convert the given text from one romanization method to another.

**Arguments:**

- `text` (str): The text to be converted.
- `convert_from` (str): The romanization method of the input text.
- `convert_to` (str): The romanization method to which the text is being converted.

**Returns:**

- `str`: The converted text.

**Example:**

```python
from RoManTools import convert_text

result = convert_text("Bai Juyi", convert_from="py", convert_to="wg")
print(result)  # Output: 'Pai Chü-i'
```

### `cherry_pick`

Convert only identified romanized Mandarin terms in the given text, excluding any English words or those in the stopword list. Non-romanized words are left unchanged.

**Arguments:**

- `text` (str): The text to be processed.
- `convert_from` (str): The romanization method of the input text.
- `convert_to` (str): The romanization method to which the text is being converted.

**Returns:**

- `str`: The text with only the identified romanized Chinese terms converted.

**Example:**

```python
from RoManTools import cherry_pick

result = cherry_pick("This is a biography of Bai Juyi.", convert_from="py", convert_to="wg")
print(result)  # Output: 'This is a biography of Pai Chü-i.'
```

### `segment_text`

Segment the text into syllables.

**Arguments:**

- `text` (str): The text to be segmented.
- `method` (str): The romanization method of the input text.

**Returns:**

- `list`: A list where each entry is either a list of syllable strings (one entry per word) or a string (a non-text segment, e.g. punctuation/whitespace).

**Example:**

```python
from RoManTools import segment_text

result = segment_text("Bai Juyi", method="py")
print(result)  # Output: [['bai'], ['ju', 'yi']]
```

### `detect_method`

Identify the romanization method(s) used in the input text.

**Arguments:**

- `text` (str): The text to be analyzed.
- `per_word` (bool, optional): If `True`, returns detection results for each word individually. Defaults to `False`.

**Returns:**

- `list`: If `per_word` is `False`, a list of method shorthands valid for the whole text (e.g. `['py']`). If `per_word` is `True`, a list of dicts with `'word'` and `'methods'` keys for each word.

**Example:**

```python
from RoManTools import detect_method

text = "Bai Juyi"

# Detect the method(s) for the entire text
result = detect_method(text)
print(result)  # Output: ['py']

# Detect the method(s) for each word individually
result_per_word = detect_method(text, per_word=True)
print(result_per_word)  # Output: [{'word': 'Bai', 'methods': ['py']}, {'word': 'Juyi', 'methods': ['py', 'wg']}]
```

### `validator`

Validate the supplied text against a romanization method.

> Note: the importable function is named `validator`, not `validate_text`.
> `RoManTools.table_utils.validate_text` is a separate, unrelated helper for
> pandas-style workflows — see [Table_Error_Reporting.md](Table_Error_Reporting.md).

**Arguments:**

- `text` (str): The text to be validated.
- `method` (str): The romanization method of the input text.
- `per_word` (bool, optional): If `True`, returns validation results for each word individually. Defaults to `False`.

**Returns:**

- `bool` or `list`: `True` if every syllable in the text is valid, `False` otherwise. If `per_word` is `True`, returns a list of dicts with `'word'`, `'syllables'`, and `'valid'` keys for each word.

**Example:**

```python
from RoManTools import validator

text = "Bai Julyi"
method = "py"

result = validator(text, method)
print(result)  # Output: False

result = validator(text, method, per_word=True)
print(result)  # Output: [{'word': 'bai', 'syllables': ['bai'], 'valid': [True]}, {'word': 'julyi', 'syllables': ['ju', 'lyi'], 'valid': [True, False]}]
```

### `syllable_count`

Count the number of syllables in each word of the given text.

**Arguments:**

- `text` (str): The text to be analyzed.
- `method` (str): The romanization method of the input text (required — there is no default).

**Returns:**

- `list[int]`: The syllable count for each word in the text.

**Example:**

```python
from RoManTools import syllable_count

result = syllable_count("Bai Juyi", method="py")
print(result)  # Output: [1, 2]
```
