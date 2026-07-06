# Command-line Execution

## Table of Contents

1. [Initial Execution Instruction](#1-initial-execution-instruction)
2. [Commands](#2-commands)
3. [Required Arguments](#3-required-arguments)
4. [Optional Parameters for Additional Features](#4-optional-parameters-for-additional-features)
5. [Optional Parameters for Debugging Purposes](#5-optional-parameters-for-debugging-and-error-reporting)
6. [Examples](#examples)
7. [Common Errors and Troubleshooting](#common-errors-and-troubleshooting)

## 1. Initial Execution Instruction

After installing the package through pip, RoManTools can be executed from the command line by typing `RoManTools` in your terminal or Jupyter Notebooks. Please note that use of capital letters in package names is unconventional—the vast majority of Python packages are written in lowercase.

Upon running `RoManTools` with no arguments you will see the help message listing all supported commands.

Every command takes the text to process as a positional argument - meaning you just place it directly after the command name, rather than naming it with a flag first (a flag is a `-x` or `--something` marker, like `-m` below, that labels what a piece of information means). There is no `-i`/`--input` flag for the text itself:

```bash
RoManTools <command> "text to process" [options]
```

## 2. Commands

`convert`: Converts text between Pinyin and Wade-Giles.

`cherry-pick`: Converts only identified romanized Chinese terms, excluding any English words or those in the stopword list. Non-romanized words are left unchanged in the output.

`segment`: Segments text into syllables, a feature that will be utilized by other actions and is also available for direct use.

`syllable-count`: Counts the number of syllables per word and returns the counts as a list.

`detect-method`: Identifies the romanization method(s) used in the input text.

`validator`: Validates whether supplied text conforms to a given romanization method.

Run `RoManTools --list-methods` to print the currently supported romanization methods, or `RoManTools --version` for the installed package version.

## 3. Required Arguments

### Note: "methods" refers to currently supported Mandarin romanization methods:

- Pinyin (entered as `py` or `pinyin`)
- Wade-Giles (entered as `wg` or `wade-giles`)

`text`: Positional argument — the text to be analyzed/converted. Always the first argument after the command name.

`-m / --method`: The romanization method of the supplied text. Required for `segment`, `syllable-count`, and `validator`.

`-f / --from`: The originating romanization method to convert from. Required for `convert` and `cherry-pick`.

`-t / --to`: The romanization method to convert to. Required for `convert` and `cherry-pick`.

## 4. Optional Parameters for Additional Features

`-w / --per-word`: For `detect-method` and `validator`, return results on a per-word basis instead of a single result for the whole input.

## 5. Optional Parameters for Debugging and Error Reporting

`-C / --crumbs`: Reports a breadcrumb trail from the analysis process, showing step-by-step processing details.

`-S / --error_skip`: Skip errors instead of aborting. Used automatically by `cherry-pick`.

`-R / --error_report`: Enable error reporting. **Currently only affects `convert` and `cherry-pick`** — it has no effect on `segment`, `syllable-count`, `detect-method`, or `validator`, which don't consult this flag.

### Error Reporting Options (require `-R`, and only apply to `convert`/`cherry-pick`)

`--error_compact`: Report errors as a one-line error count (e.g. `2 errors`) instead of a detailed multi-line report. **Requires `-R`**.

`--error_max N`: Maximum number of errors to include in a **detailed** (non-compact) report. `0` means all errors (default). Has no effect when `--error_compact` is set. **Requires `-R`**.

**Note**: Using `--error_compact` or `--error_max` without `-R` will produce: `error: --error_compact and --error_max require --error_report (-R) to be enabled`

### Error Reporting Examples

```bash
# Enable error reporting with default detailed format (convert/cherry-pick only)
RoManTools convert "xyz" -f py -t wg -R

# Enable error reporting with compact (count-only) format
RoManTools convert "xyz" -f py -t wg -R --error_compact

# Limit a detailed report to the first error only
RoManTools convert "xyz" -f py -t wg -R --error_max 1

# INVALID: error_compact without -R (will fail)
RoManTools convert "xyz" -f py -t wg --error_compact
# Error: --error_compact and --error_max require --error_report (-R)
```

## Examples

All examples below were run against the current CLI and show verified output.

### Convert

```bash
RoManTools convert "Bai Juyi" -f py -t wg
```
Output: `Pai Chü-i`

### Cherry Pick

```bash
RoManTools cherry-pick "This is a biography of Bai Juyi." -f py -t wg
```
Output: `This is a biography of Pai Chü-i.`

### Segment

```bash
RoManTools segment "Bai Juyi" -m py
```
Output: `[['bai'], ['ju', 'yi']]`

Each word becomes a list of its syllables; non-text characters (spaces, punctuation) pass through as their own string entries.

### Syllable Count

```bash
RoManTools syllable-count "Bai Juyi" -m py
```
Output: `[1, 2]`

### Detect Method

```bash
RoManTools detect-method "Bai Juyi"
```
Output: `['py']`

```bash
RoManTools detect-method "Bai Juyi" --per-word
```
Output: `[{'word': 'Bai', 'methods': ['py']}, {'word': 'Juyi', 'methods': ['py', 'wg']}]`

### Validator

```bash
RoManTools validator "Bai Julyi" -m py
```
Output: `False`

```bash
RoManTools validator "Bai Julyi" -m py --per-word
```
Output: `[{'word': 'bai', 'syllables': ['bai'], 'valid': [True]}, {'word': 'julyi', 'syllables': ['ju', 'lyi'], 'valid': [True, False]}]`

Note: `-R`/`--error_report` has no effect on `validator` output (see the note in section 5) — use `convert` or `cherry-pick` with `-R` if you need a structured error report, or the `RoManTools.table_utils` helpers for programmatic validation with error detail.

### Error Reporting with Convert

```bash
RoManTools convert "zh'ng" -f py -t wg -R
```
Output:
```
WARNING: # Errors in word: 'zh'ng':
=== Detailed Errors ===
1. [invalid_final] Invalid final: '' (final='', initial='zh')
2. [illegal_character] Illegal character: ''' - apostrophes not used in Pinyin syllables (character=''', reason='apostrophes not used in Pinyin syllables')
3. [invalid_initial] Invalid initial: 'ng' (initial='ng')
4. [invalid_final] Invalid final: '' (final='', initial='ng')
zh(!)-ng(!)
```

```bash
RoManTools convert "zh'ng" -f py -t wg -R --error_compact
```
Output:
```
WARNING: # Errors in word: 'zh'ng': 4 errors
zh(!)-ng(!)
```

### Debugging Example with Crumbs

```bash
RoManTools validator "Bai Julyi" -m py -wC
```
Output (abridged):
```
 INFO: # Start: 2026-07-06 09:15:07
 INFO: # Performing action: Validator
 INFO: # Configuration: Print Crumbs
 INFO: ---
 INFO: # Analyzing text as Pinyin: Bai
 INFO: ## initial found: b
 INFO: ## final found: ai
 INFO: ### Syllable: "bai" valid: True
 INFO: # Word Validation: "bai" is valid
 INFO: ---
 INFO: # Analyzing text as Pinyin: Julyi
 INFO: ## initial found: j
 INFO: ## final found: u
 INFO: ### Syllable: "ju" valid: True
 INFO: ## initial found: ly
 INFO: ## final found: i
ERROR: ### Validation: invalid initial: 'ly'
ERROR: ### Syllable: "lyi" valid: False
 INFO: # Word Validation: "julyi" is invalid
 INFO: ---
 INFO: # End: 2026-07-06 09:15:07
[{'word': 'bai', 'syllables': ['bai'], 'valid': [True]}, {'word': 'julyi', 'syllables': ['ju', 'lyi'], 'valid': [True, False]}]
```

## Common Errors and Troubleshooting

- **Error**: `the following arguments are required: -m/--method` (or `-f/--from`, `-t/--to`)
  - **Solution**: Make sure you've supplied the required arguments for the command you're running (see [section 3](#3-required-arguments)).
- **Error**: `unrecognized arguments: -i ...`
  - **Solution**: There is no `-i`/`--input` flag. Pass the text as a plain positional argument: `RoManTools segment "text" -m py`.
- **Error**: `Invalid romanization method: ...`
  - **Solution**: Check that the romanization method provided is one of the supported methods (`py`, `pinyin`, `wg`, `wade-giles`), or run `RoManTools --list-methods`.
- **Error**: `--error_compact and --error_max require --error_report (-R) to be enabled`
  - **Solution**: Add `-R` before using `--error_compact`/`--error_max`, e.g. `RoManTools convert "text" -f py -t wg -R --error_compact`.

For further assistance, refer to the official documentation or contact main developer Jeff Heller via [Github issues](https://github.com/JHGFD82/RoManTools/issues) or via [e-mail](mailto:jh43@princeton.edu).
