# Input Requirements

This document explains how to format your text so RoManTools can read it correctly, whether you're using the command line or importing the package into Python. The examples below use Python (`from RoManTools import ...`), but the same rules apply no matter how you run RoManTools - see [CLI.md](CLI.md) for the equivalent command-line syntax.

## Important Notes

You can type apostrophes and dashes in any of their common forms (straight quote `'`, curly quotes `’ ‘`, hyphen `-`, en dash `–`, em dash `—`, and a few others) - RoManTools accepts all of them as equivalent, and always produces the standard straight apostrophe (`'`) or hyphen (`-`) in its output. These rules don't apply to the `detect_method` action, though they're still a useful guideline for how it recognizes which romanization method your text is in.

## Pinyin Input Requirements

Pinyin can usually be typed without any extra punctuation. RoManTools works out where one syllable ends and the next begins mainly by watching for the switch from consonants to vowels (so "Xiaoyu" splits into `['Xiao', 'yu']`), and it also knows how to handle syllables ending in "n", "ng", or "er" (so "Luanfeng" splits into `['Luan', 'feng']`, "Yongtao" into `['Yong', 'tao']`, and "Sheer" into `['She', 'er']`).

Some words are genuinely ambiguous without help, though - "changan" could be "Chan-gan" or "Chang-an", and there's no way to tell which one you mean from the letters alone. In cases like that, split the syllables yourself with an apostrophe (`Chang'an`) to get the result you actually want. Skipping this step won't cause an error, but it may silently give you the wrong split.

### Examples

The examples below show Python code, but the same input rules apply if you're using the command line instead (see [CLI.md](CLI.md)).

#### changan

```python
from RoManTools import segment_text

result = segment_text("changan", method="py")
print(result)  # Output: [['chan', 'gan']]
```

```python
from RoManTools import segment_text

result = segment_text("chang'an", method="py")
print(result)  # Output: [['chang', 'an']]
```

#### xian

```python
from RoManTools import segment_text, syllable_count

result = segment_text("xian", method="py")
print(result)  # Output: [['xian']]

result = syllable_count("xian", method="py")
print(result)  # Output: [1]
```

```python
from RoManTools import segment_text, syllable_count

result = segment_text("xi'an", method="py")
print(result)  # Output: [['xi', 'an']]

result = syllable_count("xi'an", method="py")
print(result)  # Output: [2]
```

## Wade-Giles Input Requirements

For Wade-Giles, RoManTools strongly recommends using a hyphen (`-`) or dash (`–`, `—`) between syllables in a multi-syllable word. RoManTools can work out some syllable boundaries on its own even without one (particularly around the "erh" final), but explicit hyphens are the most reliable way to avoid ambiguity around letters like "h", "ss", "ng", and pairs of vowels.

Every form of apostrophe is understood as part of a syllable's initial (as in Wade-Giles spellings like "ch'i"), and whichever form you type, RoManTools's output will always use the standard straight apostrophe (`'`).

### Examples

```python
from RoManTools import segment_text

# Recommended: with explicit hyphens
result = segment_text("ch'i-hsiao", method="wg")
print(result)  # Output: [["ch'i", 'hsiao']]
```

```python
from RoManTools import segment_text

# Simple cases may still work without hyphens, but hyphens are still recommended
result = segment_text("ch'ihsiao", method="wg")
print(result)  # Output: [["ch'ih", 'siao']]
```
