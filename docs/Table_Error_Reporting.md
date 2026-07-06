# Table-Friendly Error Reporting

## Overview

If you're validating a whole column of romanized text - in a pandas DataFrame (the table-shaped object the popular pandas data-analysis library uses), a spreadsheet exported to CSV, or a database table - you usually want one short result per row, not a full multi-line report. RoManTools's `table_utils` module is built for exactly that: pass it one syllable at a time (for example via `df['column'].apply(...)`), and get back a validation result sized to fit in a table cell.

**Note:** `table_utils` isn't included in `from RoManTools import *` - it's a separate, opt-in module, kept out of the main package so the everyday `segment_text`/`convert_text`/etc. API stays small and focused. Import it explicitly:

```python
from RoManTools.table_utils import get_validation_column
```

## Quick Start for Table Users

### Simplest Approach: Single Validation Column

```python
from RoManTools.table_utils import get_validation_column

# Returns "OK" if valid, or a short description of the first problem if not
df['validation'] = df['syllable'].apply(get_validation_column)
```

**Example Output:**
```
syllable    validation
--------    ----------
beijing     OK
mha         ERROR - invalid_initial - "mh"
pia         ERROR - rare_syllable - "pia"
ma1         ERROR - illegal_character - "1"
```

## Error Report Formats

There are two report formats, and it's important to know which functions give you which:

### Compact Format: just a count

`ErrorTracker.generate_report(compact=True)` - used internally by `validate_syllable()` and `validate_text()` below when `compact=True` (their default) - returns nothing more than how many problems were found:

- `''` (empty string) if the syllable is valid.
- `'1 error'` if exactly one problem was found.
- `'2 errors'`, `'3 errors'`, and so on otherwise.

It does **not** say what the problems were - just how many there are. This is intentionally minimal: it's meant for a quick "does this column need attention" glance, not diagnosis.

### First-Error Format: what's wrong, briefly

If you need to know *what* went wrong (not just how many things did), use `get_validation_column()` or `ErrorTracker.get_first_error_string()` instead - both return a string like:

```
ERROR - invalid_initial - "mh"
```

This describes only the *first* problem found, even if there are more - it's meant to fit in one table cell, not to be exhaustive. For every problem, use the detailed format below.

### Detailed Format: everything, multi-line

`generate_report(compact=False)` returns a full multi-line breakdown - a per-category count summary, followed by every individual problem found:

```
=== Error Summary ===
  invalid_initial: 1
  invalid_final: 1
  Total: 2

=== Detailed Errors ===
1. [invalid_initial] Invalid initial: 'xyz' (initial='xyz')
2. [invalid_final] Invalid final: '' (final='', initial='xyz')
```

Pass `max_errors=N` to cap how many individual problems are listed in this detailed format (with a `... and N more error(s)` line if there were more) - this has no effect on the compact or first-error formats, since neither of those lists individual problems in the first place.

## Python API

### table_utils Module

Three functions for table processing:

#### 1. `get_validation_column(text, method='py')` - Simplest

Returns `"OK"`, or the first-error-format description of the first problem found.

```python
from RoManTools.table_utils import get_validation_column

# Invalid syllable
result = get_validation_column('mha')
# Returns: 'ERROR - invalid_initial - "mh"'

# Valid syllable
result = get_validation_column('beijing')
# Returns: 'OK'

# With a DataFrame
df['validation'] = df['syllable'].apply(get_validation_column)
```

#### 2. `validate_syllable(text, method='py', compact=True, max_errors=1)` - Flexible

Returns the compact-format error count by default (empty string if valid); pass `compact=False` for the detailed format instead.

```python
from RoManTools.table_utils import validate_syllable

# Compact (default): just a count
error = validate_syllable('xyz')
# Returns: '2 errors'

# Detailed, capped to the first problem
error = validate_syllable('xyz', compact=False, max_errors=1)
# Returns: "=== Error Summary ===\n  invalid_initial: 1\n  invalid_final: 1\n  Total: 2\n\n=== Detailed Errors ===\n1. [invalid_initial] Invalid initial: 'xyz' (initial='xyz')\n... and 1 more error(s)"

# With a DataFrame
df['errors'] = df['syllable'].apply(lambda x: validate_syllable(x))
```

#### 3. `validate_text(text, method='py', compact=True, max_errors=0)` - Most Detailed

Despite the name, this validates one syllable at a time too (same as `validate_syllable` - "text" here just matches the parameter name used elsewhere in the package). Returns a dictionary with everything about the result at once, which is useful for building several DataFrame columns from a single pass.

```python
from RoManTools.table_utils import validate_text

result = validate_text('xyz')
# Returns:
# {
#     'valid': False,
#     'error_count': 2,
#     'error_types': ['invalid_initial', 'invalid_final'],
#     'error_report': '2 errors',
#     'first_error': 'ERROR - invalid_initial - "xyz"'
# }

# With a DataFrame - create multiple columns from one pass
validation_results = df['syllable'].apply(validate_text)
df['valid'] = validation_results.apply(lambda x: x['valid'])
df['error_count'] = validation_results.apply(lambda x: x['error_count'])
df['error_types'] = validation_results.apply(lambda x: ', '.join(x['error_types']))
df['first_error'] = validation_results.apply(lambda x: x['first_error'])
```

### ErrorTracker Methods

If you're working with the core API directly rather than through `table_utils`, `ErrorTracker` (see errors.py) has the same table-friendly methods built in:

```python
from RoManTools.config import Config
from RoManTools.syllable import SyllableProcessor
from RoManTools.data_loader import load_method_params

config = Config(error_report=False)
processor = SyllableProcessor(config, load_method_params('py'))
syllable = processor.create_syllable('xyz')

# First problem only, briefly
first_error = syllable.error_tracker.get_first_error_string()
# Returns: 'ERROR - invalid_initial - "xyz"'

# Which categories of problem occurred
error_types = syllable.error_tracker.get_error_types_list()
# Returns: ['invalid_initial', 'invalid_final']

# Compact report: just a count
report = syllable.error_tracker.generate_report(compact=True)
# Returns: '2 errors'

# Detailed report
report = syllable.error_tracker.generate_report(compact=False)
# Returns the multi-line detailed report shown above
```

## Command-Line Interface

### Error Reporting Flags

**Primary Flag:**
- `-R, --error_report`: Turn on error reporting.

**Secondary Flags (require `-R`):**
- `--error_compact`: Use the compact (count-only) format instead of the detailed one (the default is detailed).
- `--error_max N`: In the detailed format, list at most N individual problems (0 = all of them). Has no effect on the compact format.

**Note:** `-R` must currently be used with the `convert` or `cherry-pick` subcommands to have any visible effect - `validator`, `segment`, `syllable-count`, and `detect-method` don't currently report errors this way, regardless of `-R`. See [CLI.md](CLI.md) for the full flag reference.

**Note:** The secondary flags can only be used together with `-R`. Using them without it produces an error rather than being silently ignored.

### Examples

```bash
# Detailed format, all problems listed (the default once -R is on)
RoManTools convert "mhazhong dyng" -f py -t wg -R

# Compact format: just a count per word
RoManTools convert "mhazhong dyng" -f py -t wg -R --error_compact

# Detailed format, capped to the first problem per word
RoManTools convert "mhazhong dyng" -f py -t wg -R --error_max 1

# Invalid: --error_compact without -R
RoManTools convert "mhazhong dyng" -f py -t wg --error_compact
# Error: --error_compact and --error_max require --error_report (-R) to be enabled
```

**Output with `-R` (detailed, default):**
```
WARNING: # Errors in word: 'mhazhong':
=== Detailed Errors ===
1. [invalid_initial] Invalid initial: 'mh' (initial='mh')
2. [invalid_final] Invalid final: 'azhong' (final='azhong', initial='mh')
3. [invalid_initial] Invalid initial: 'mh' (initial='mh')
WARNING: # Errors in word: 'dyng':
=== Detailed Errors ===
1. [invalid_initial] Invalid initial: 'dyng' (initial='dyng')
2. [invalid_final] Invalid final: '' (final='', initial='dyng')
mha(!)-chung dyng(!)
```

**Output with `-R --error_compact`:**
```
WARNING: # Errors in word: 'mhazhong': 3 errors
WARNING: # Errors in word: 'dyng': 2 errors
mha(!)-chung dyng(!)
```

**Output with `-R --error_max 1`:**
```
WARNING: # Errors in word: 'mhazhong':
=== Detailed Errors ===
1. [invalid_initial] Invalid initial: 'mh' (initial='mh')
... and 2 more error(s)
WARNING: # Errors in word: 'dyng':
=== Detailed Errors ===
1. [invalid_initial] Invalid initial: 'dyng' (initial='dyng')
... and 1 more error(s)
mha(!)-chung dyng(!)
```

## pandas DataFrame Examples

### Example 1: Simple Validation Column

```python
import pandas as pd
from RoManTools.table_utils import get_validation_column

df = pd.DataFrame({
    'syllable': ['beijing', 'shanghai', 'xyz', 'mha', 'pia', 'ma1']
})

df['validation'] = df['syllable'].apply(get_validation_column)

print(df)
```

**Output:**
```
  syllable                       validation
0  beijing                               OK
1 shanghai                               OK
2      xyz  ERROR - invalid_initial - "xyz"
3      mha   ERROR - invalid_initial - "mh"
4      pia   ERROR - rare_syllable - "pia"
5      ma1 ERROR - illegal_character - "1"
```

### Example 2: Filter Invalid Syllables

```python
import pandas as pd
from RoManTools.table_utils import validate_text

df = pd.DataFrame({
    'syllable': ['beijing', 'shanghai', 'xyz', 'mha', 'pia']
})

# Get validation info
validation = df['syllable'].apply(validate_text)
df['is_valid'] = validation.apply(lambda x: x['valid'])
df['error_types'] = validation.apply(lambda x: ', '.join(x['error_types']))

# Filter to invalid only
invalid_df = df[~df['is_valid']]
print(invalid_df)
```

**Output:**
```
  syllable  is_valid                    error_types
2      xyz     False  invalid_initial, invalid_final
3      mha     False                 invalid_initial
4      pia     False                   rare_syllable
```

### Example 3: Categorize by Error Type

```python
import pandas as pd
from RoManTools.table_utils import validate_text

df = pd.DataFrame({
    'syllable': ['beijing', 'xyz', 'pia', 'ma1', "ch'a"]
})

# Get validation info
validation = df['syllable'].apply(validate_text)

# Create boolean columns for each error type
df['has_rare_syllable'] = validation.apply(
    lambda x: 'rare_syllable' in x['error_types']
)
df['has_illegal_char'] = validation.apply(
    lambda x: 'illegal_character' in x['error_types']
)
df['has_invalid_structure'] = validation.apply(
    lambda x: any(t in x['error_types']
                  for t in ['invalid_initial', 'invalid_final', 'invalid_syllable'])
)

print(df)
```

**Output:**
```
  syllable  has_rare_syllable  has_illegal_char  has_invalid_structure
0  beijing              False             False                  False
1      xyz              False             False                   True
2      pia               True             False                  False
3      ma1              False              True                  False
4     ch'a              False              True                   True
```

### Example 4: Summary Statistics

```python
import pandas as pd
from RoManTools.table_utils import validate_text

df = pd.DataFrame({
    'word_id': [1, 2, 3, 4, 5, 6],
    'syllable': ['beijing', 'shanghai', 'xyz', 'mha', 'pia', 'ma1']
})

# Get validation info
validation = df['syllable'].apply(validate_text)
df['error_count'] = validation.apply(lambda x: x['error_count'])
df['is_valid'] = validation.apply(lambda x: x['valid'])

# Summary statistics
print(f"Total syllables: {len(df)}")
print(f"Valid syllables: {df['is_valid'].sum()}")
print(f"Invalid syllables: {(~df['is_valid']).sum()}")
print(f"Total errors: {df['error_count'].sum()}")
print(f"Average errors per invalid syllable: {df[~df['is_valid']]['error_count'].mean():.2f}")
```

## Configuration Object

When using the core API with `Config` directly (see config.py):

```python
from RoManTools.config import Config

# Default: detailed reports, all problems listed
config = Config(error_report=True)

# Compact format (just a count)
config = Config(
    error_report=True,
    error_report_compact=True
)

# Detailed format, capped to the first problem
config = Config(
    error_report=True,
    error_report_compact=False,
    error_report_max=1
)
```

## Recommendations for Different Use Cases

### For a Quick Table Check
Use `get_validation_column()` - simplest, returns "OK" or a short description of the first problem.

### For Detailed Analysis
Use `validate_text()` - returns a dictionary with everything you might need.

### For Large Datasets
Use `validate_syllable()` (compact format, the default) - it only computes a count, which is the cheapest thing to compute and display.

### For Error Categorization
Use `validate_text()` and check its `error_types` list.

### For Debugging
Use the detailed format on the command line with `-R` (no `--error_compact`).
