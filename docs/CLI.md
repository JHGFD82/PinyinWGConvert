# Command-line Execution

## Table of Contents

1. [Initial Execution Instruction](#1-initial-execution-instruction)
2. [Commands](#2-commands)
3. [Required Arguments](#3-required-arguments)
4. [Optional Parameters for Additional Features](#4-optional-parameters-for-additional-features)
5. [Optional Parameters for Debugging Purposes](#5-optional-parameters-for-debugging-purposes)
6. [Examples](#examples)
7. [Common Errors and Troubleshooting](#common-errors-and-troubleshooting)

## 1. Initial Execution Instruction

After installing the package through pip or conda, RoManTools can be executed from the command line by typing `RoManTools` in your terminal or Jupyter Notebooks. Please note that use of capital letters in package names is unconventional—the vast majority of Python packages are written in lowercase.

Upon running `RoManTools` you will receive an error. This is because required arguments are not being supplied. However, all supported arguments will be listed.

## 2. Commands

`convert`: Support for converting between Pinyin and Wade-Giles (with Yale and additional standards to be added in future versions).

`cherry_pick`: Converts only identified romanized Chinese terms, excluding any English words or those in a stopword list.

`segment`: Segments text into meaningful chunks, a feature that will be utilized by other actions and also available for direct use by the user.

`syllable_count`: Counts the number of syllables per word and provides a report to the user.

`detect_method`: Identifies the romanization standard used in the input text and returns the detected standard(s) to the user as either a single standard or a list of multiple standards.

`validator`: Basic validation of supplied text.

## 3. Required Arguments

### Note: "methods" refers to currently supported Mandarin romanization methods:

- Pinyin (entered as `py` or `pinyin`)
- Wade-Giles (entered as `wg` or `wage-giles`)

`-i / --input`: The text to be analyzed/converted.

`-m / --method`: The romanization method of the supplied text.

`-f / --convert_from`: The originating romanization method to be analyzed.

`-t / --convert_to`: The method to which the text is being converted.

## 4. Optional Parameters for Additional Features

`-w / --per_word`: For supported actions, return results of analysis on a per-word basis. Performing an action without this parameter will result in a single response.

## 5. Optional Parameters for Debugging and Error Reporting

`-C / --crumbs`: Reports a breadcrumb trail from the analysis process, showing step-by-step processing details.

`-S / --error_skip`: Skip errors instead of aborting. Useful for processing text that may contain invalid romanization.

`-R / --error_report`: **Primary flag** - Enable error reporting. When enabled, validation errors will be included in the output. This is the master switch that must be set for any error reporting to occur.

### Error Reporting Options (require `-R`)

The following options configure error reporting behavior and are only meaningful when `--error_report` (`-R`) is enabled:

`--error_compact`: Use compact one-line error format instead of detailed format. Suitable for tables and scripts. **Requires `-R`**.

`--error_max N`: Maximum number of errors to report. `0` means all errors (default), `1` means first error only, etc. **Requires `-R`**.

**Note**: Attempting to use `--error_compact` or `--error_max` without enabling `-R` will result in an error message: "error: --error_compact and --error_max require --error_report (-R) to be enabled"

### Error Reporting Examples

```bash
# Enable error reporting with default detailed format
RoManTools validator "xyz" -m py -R

# Enable error reporting with compact format
RoManTools validator "xyz" -m py -R --error_compact

# Limit to first error only
RoManTools validator "xyz" -m py -R --error_max 1

# Compact format with error limit
RoManTools validator "xyz" -m py -R --error_compact --error_max 1

# INVALID: error_compact without -R (will fail)
RoManTools validator "xyz" -m py --error_compact
# Error: --error_compact and --error_max require --error_report (-R)
```


## Examples

### Convert

- `RoManTools convert --input "Bai Juyi" --convert_from py --convert_to wg`
  - Output: `Pai Chüi`

### Cherry Pick

- `RoManTools cherry_pick -i "This is a biography of Bai Juyi." -f py -t wg`
  - Output: `This is the biography of Pai Chüi.`

### Segment

- `RoManTools segment -i "Bai Juyi" -m py`
  - Output: `['Bai', ['Ju', 'yi']]`

### Syllable Count

- `RoManTools syllable_count -i "Bai Juyi" -m py`
  - Output: `[1, 2]`

### Detect Method

- `RoManTools detect_method -i "Bai Juyi"`
  - Output: `py`
- `RoManTools detect_method -i "Bai Juyi" --per_word`
  - Output: `[{'word': 'Bai', 'methods': ['py']}, {'word': 'Juyi', 'methods': ['py', 'wg']}]`

### Validator

- `RoManTools validator -i "Bai Julyi" -m py`
  - Output: `False`
- `RoManTools validator -i "Bai Julyi" -m py --per_word`
  - Output: `[{'word': 'bai', 'syllables': ['bai'], 'valid': [True]}, {'word': 'julyi', 'syllables': ['ju', 'lyi'], 'valid': [True, False]}]`
- `RoManTools validator -i "xyz" -m py -R`
  - Output: `False` (with detailed error report showing invalid initial and final)
- `RoManTools validator -i "xyz" -m py -R --error_compact`
  - Output: `False` (with compact one-line error format)

### Error Reporting with Validator

- `RoManTools validator -i "zh'ng" -m py -R`
  - Output: `False` with detailed error report:
    ```
    === Error Summary ===
      illegal_character: 1
      invalid_final: 1
      Total: 2
    
    === Detailed Errors ===
    1. [illegal_character] Illegal character: "'" - apostrophes are not valid in Pinyin
    2. [invalid_final] Invalid final: 'zh'
    ```
- `RoManTools validator -i "zh'ng" -m py -R --error_compact`
  - Output: `False` with compact format:
    ```
    ERROR - illegal_character - "'"; ERROR - invalid_final - "zh"
    ```

### Debugging Example with Crumbs

- `RoManTools validator -i "Bai Julyi" -m py -wC`
  - Output:
    ```
    ### Analyzing Bai Julyi ###
    # Processing Bai
    # Initial: B
    # Final: ai
    # Valid: True
    ```

## Common Errors and Troubleshooting

- **Error**: `No command supplied`
  - **Solution**: Ensure you are providing a valid command after `RoManTools`.
- **Error**: `Invalid method`
  - **Solution**: Check that the romanization method provided is one of the supported methods (`py`, `pinyin`, `wg`, `wade-giles`).
- **Error**: `--error_compact and --error_max require --error_report (-R) to be enabled`
  - **Solution**: You must enable error reporting with `-R` before using formatting options. For example, use `RoManTools validator "text" -m py -R --error_compact` instead of `RoManTools validator "text" -m py --error_compact`.
- **Note**: Error reporting options (`--error_compact`, `--error_max`) are secondary flags that only work when the primary flag `-R` is set. This hierarchical structure ensures that formatting options are only used when error reporting is actually enabled.

For further assistance, refer to the official documentation or contact main developer Jeff Heller via [Github issues](https://github.com/JHGFD82/RoManTools/issues) or via [e-mail](mailto:jh43@princeton.edu).
