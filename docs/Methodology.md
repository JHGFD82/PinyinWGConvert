# Text Processing Methodology

This document explains, in plain terms, how RoManTools actually analyzes your text - it's a more narrative version of the explanations already in the code's own docstrings and comments. It applies no matter which way you use RoManTools (see [CLI.md](CLI.md) or [Python.md](Python.md) for the command-line and Python-import instructions, respectively).

1. Chunk Processing
   1. Segment Generation
   2. Syllable Processing
   3. Conversion (Word Processing)
2. Actions
   1. Segment Text
   2. Validator
   3. Detect Method
   4. Syllable Count
   5. Convert
   6. Cherry Pick

## 1. Chunk Processing

### 1.1. Segment Generation

Every action starts the same way: breaking the input text into pieces RoManTools can work with, one at a time. RoManTools calls each of these pieces a "chunk" - either one word (letters, plus any apostrophes/dashes that are part of it), or a stretch of everything else (spaces, punctuation, numbers).

#### Key Steps

1. **Text Splitting**:
   * The input text is split into chunks using a regular expression (regex) - a pattern-matching tool built into Python for finding text that fits a certain shape, rather than checking it character by character by hand.
   * Within a word-chunk, RoManTools further looks for **segments** - separated by whichever punctuation marks the current romanization method treats as syllable separators:
     * Apostrophes and dashes, for Pinyin.
     * Dashes, for Wade-Giles.
2. **Symbol and Space Handling**:
   * Numbers, symbols, and spaces become their own separate chunks.
   * By default these non-text chunks are simply dropped from the result; setting `error_skip` to `True` keeps them instead, in their original position.
3. **Segment Definition**:
   * A segment can contain more than one syllable. If a word has no apostrophes or dashes marking syllable boundaries, several syllables can end up grouped into a single segment, to be split further in the next step.

#### Input Requirements

See [Input Requirements](Input_Requirements.md) for the specific formatting rules for each romanization method.

#### Examples

**Entered Text**:
`Huli gei ji bai nian.`

**Results with `error_skip=False`** (the default):

```python
[['hu', 'li'], ['gei'], ['ji'], ['bai'], ['nian']]
```

**Results with `error_skip=True`**:

```python
[['hu', 'li'], ' ', ['gei'], ' ', ['ji'], ' ', ['bai'], ' ', ['nian'], '.']
```

Breaking the text into chunks this way is what lets every other action build on the same foundation, whether it's counting syllables, converting between romanization methods, or just checking whether the text is valid.

---

### 1.2. Syllable Processing

Next, each segment is turned into one or more Syllable objects - RoManTools's internal representation of a single syllable, including its structural breakdown. This step works out:

1. **Initial Detection**:
   The initial - typically a consonant sound, like the "n" in "ni" - is identified first. RoManTools reads letters from the start of the segment until it hits a vowel, and everything read up to that point is the initial. If a syllable starts with a vowel instead (e.g. "An"), there's no initial at all - internally, RoManTools marks this with the placeholder symbol `ø` rather than leaving it blank, so "no initial" is never confused with "haven't checked yet."
2. **Final Detection**:
   Whatever's left is analyzed to find the final - typically one or more vowels (the "i" in "ni", or "ao" in "hao"), though it can include trailing consonants under specific rules:

   * **Pinyin & Wade-Giles**: finals ending in "n" (as in "chan") or "ng" (as in "chang").
   * **Pinyin**: an "r" after "e" (as in "sheer").
   * **Wade-Giles**: "rh" after "e" (as in "sheerh"), or "h" after "i" (as in "Chih").

   Any letters left over after the final start the next syllable.
3. **Validation**:
   Once a syllable's initial and final are both known, RoManTools checks whether that specific combination is actually a real syllable, by looking it up in a table of valid combinations for the romanization method in use. Invalid combinations are flagged rather than silently accepted.

**Example** (conceptually - the actual return value's exact shape is documented under "Segment Text" below):

```python
# Input
segment = "zhongguo"
# Output
syllables = ["zhong", "guo"]
```

Each validated syllable is handed back to the chunk-processing step, grouped together with the other syllables from the same word.

---

### 1.3. Conversion (Word Processing)

Converting text (`convert_text` or `cherry_pick`) uses the chunks from step 1.1, together with the syllables from step 1.2, to reassemble and convert whole words. This involves:

1. **Preview Word Creation**:
   RoManTools reassembles a word's syllables into a lowercase "preview" - not shown to the user, just used internally for the next step.
2. **Validation**:

   * Each syllable is checked for validity (from step 1.2 above).
   * A word where only the last syllable is invalid, and that syllable looks like a common English contraction ending (`'s`, `'d`, `'ll`), is treated as a contraction rather than a conversion error - this matters for `cherry_pick`, which needs to process mixed English/Mandarin text without choking on "we've" or "it'll".
3. **Stopword Check**:
   The preview word is checked against a list of words that should never be converted, even if they happen to look like valid syllables - things like "China" or "Beijing", which are already standard English spellings.
4. **Syllable Conversion**:
   Each syllable is looked up in the conversion table and replaced with its spelling in the target method. A syllable that can't be converted (because it isn't valid, or isn't recognized) is marked with `(!)` in the output, so problems are visible rather than silently swallowed.
5. **Final Assembly**:

   * Capitalization from the original text is restored.
   * Apostrophes and dashes are added according to the target method's own rules:
     * **Pinyin**: apostrophes separate two syllables where leaving them out would be ambiguous (e.g. "ti'an").
     * **Wade-Giles**: dashes connect every syllable in a word (e.g. "Chih-p'ing").

   The finished word is combined with the rest of the text - either exactly preserving the original spacing and symbols (`error_skip=True`), or joined with single spaces (the default).

#### Examples

**Pinyin to Wade-Giles** (`convert_text`):

```python
# Input
text = "Yanjing li rong bu xia sharen."
# Output
"Yen-ching li jung pu hsia sha-jen"
```

**Wade-Giles to Pinyin** (`convert_text`):

```python
# Input
text = "Chih-p'ing shih Chung-kuo jen."
# Output
"Zhiping shi Zhongguo ren"
```

Note that `convert_text` tries to convert every word it finds - it isn't aware that a word might be English rather than Mandarin. For text that mixes the two languages, see Cherry Pick below.

## 2. Actions

Each action below builds on the chunk-processing and syllable-processing steps above, just using the results differently depending on what the action is for.

### 2.1. Segment Text

Splits the input text into a structured list of words and their syllables. Each inner list represents one word's syllables. If `error_skip=True`, spaces and symbols are also included as their own separate items.

#### Examples

**Input**:
`Huli gei ji bai nian.`

**Default Output**:

```python
[['hu', 'li'], ['gei'], ['ji'], ['bai'], ['nian']]
```

**Output with `error_skip=True`**:

```python
[['hu', 'li'], ' ', ['gei'], ' ', ['ji'], ' ', ['bai'], ' ', ['nian'], '.']
```

---

### 2.2. Validator

Checks whether the input text is valid according to the chosen romanization method's rules. By default, returns a single `True` or `False` for the whole text. With `per_word=True`, returns a detailed breakdown of each word and each of its syllables.

#### Examples

**Input**:
`Huli gei ji bai nion.`

**Default Output**:

```python
False
```

**Output with `per_word=True`**:

```python
[
    {'word': 'huli', 'syllables': ['hu', 'li'], 'valid': [True, True]},
    {'word': 'gei', 'syllables': ['gei'], 'valid': [True]},
    {'word': 'ji', 'syllables': ['ji'], 'valid': [True]},
    {'word': 'bai', 'syllables': ['bai'], 'valid': [True]},
    {'word': 'nion', 'syllables': ['ni', 'on'], 'valid': [True, False]}
]
```

---

### 2.3. Detect Method

Works out which romanization method(s) - Pinyin, Wade-Giles, or both - the input text could validly be. By default, returns the method(s) valid for the whole text. With `per_word=True`, checks and reports each word separately (useful since some words are valid in more than one method).

#### Examples

**Input**:
`Yanjing li rong bu xia sharen`

**Default Output**:

```python
['py']
```

**Output with `per_word=True`**:

```python
[
    {'word': 'Yanjing', 'methods': ['py']},
    {'word': 'li', 'methods': ['py', 'wg']},
    {'word': 'rong', 'methods': ['py']},
    {'word': 'bu', 'methods': ['py']},
    {'word': 'xia', 'methods': ['py']},
    {'word': 'sharen', 'methods': ['py']}
]
```

---

### 2.4. Syllable Count

Counts the number of syllables in each word.

#### Example

**Input**:
`Yanjing li rong bu xia sharen`

**Output**:

```python
[2, 1, 1, 1, 1, 2]
```

---

### 2.5. Convert

Converts the input text from one romanization method to another, returning the result as a single string with words separated by spaces. If `error_skip=True`, the original spacing and symbols are preserved instead of being standardized.

#### Examples

**Pinyin to Wade-Giles**:
**Input**:
`Yanjing li rong bu xia sharen.`

**Default Output**:

```python
"Yen-ching li jung pu hsia sha-jen"
```

**Output with `error_skip=True`**:

```python
"Yen-ching   li   rong   bu   hsia   sha-jen ."
```

---

### 2.6. Cherry Pick

Converts only the words that are valid romanized Mandarin, leaving everything else (English words, punctuation, spacing) untouched. Unlike `convert_text`, this is built specifically for text that mixes Mandarin with other languages - it always runs with `error_skip=True` internally.

#### Example

**Wade-Giles to Pinyin**:
**Input**:
`This is the biography of Chih-p'ing Chou. Chih-p'ing's specialty was in Chinese language.`

**Output:**

```python
"This is the biography of Zhiping Zhou. Zhiping's specialty was in Chinese language."
```
