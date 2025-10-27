# Table-Friendly Error Reporting

## Overview

RoManTools provides flexible error reporting optimized for use with tabular data (pandas DataFrames, CSV files, database tables, etc.). You can choose between detailed reports and compact one-line formats suitable for table columns.

**Note:** The table utility functions are internal modules and must be imported via their submodule paths. They are not exposed in the main `RoManTools` namespace to keep the public API simple and focused.

## Quick Start for Table Users

### Simplest Approach: Single Validation Column

```python
from RoManTools.table_utils import get_validation_column

# Returns "OK" if valid, or a compact error if invalid
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

### Compact Format (Table-Friendly)

**Format:** `ERROR - error_type - "detail"`

**Examples:**
- `ERROR - invalid_initial - "mh"`
- `ERROR - invalid_final - "xyz"`
- `ERROR - rare_syllable - "pia"`
- `ERROR - illegal_character - "1"`

**Multiple errors (when max_errors not set to 1):**
- `ERROR - invalid_initial - "xyz"; ERROR - invalid_final - "xyz"`

**Truncated errors:**
- `ERROR - invalid_initial - "mh"; (+2 more)`

### Detailed Format (Analysis)

```
=== Error Summary ===
  invalid_initial: 1
  invalid_final: 1
  Total: 2

=== Detailed Errors ===
1. [invalid_initial] Invalid initial: 'xyz' (initial='xyz')
2. [invalid_final] Invalid final: '' (final='', initial='xyz')
```

## Python API

### table_utils Module

Three convenience functions for table processing:

#### 1. `get_validation_column(text, method='py')` - Simplest

Returns "OK" or first error in compact format.

```python
from RoManTools.table_utils import get_validation_column

# Single syllable
result = get_validation_column('mha')
# Returns: 'ERROR - invalid_initial - "mh"'

# Valid syllable
result = get_validation_column('beijing')
# Returns: 'OK'

# With DataFrame
df['validation'] = df['syllable'].apply(get_validation_column)
```

#### 2. `validate_syllable(text, method='py', compact=True, max_errors=1)` - Flexible

Returns error report string (empty if valid).

```python
from RoManTools.table_utils import validate_syllable

# First error only (default)
error = validate_syllable('xyz', max_errors=1)
# Returns: 'ERROR - invalid_initial - "xyz"; (+1 more)'

# All errors
error = validate_syllable('xyz', max_errors=0)
# Returns: 'ERROR - invalid_initial - "xyz"; ERROR - invalid_final - "xyz"'

# Detailed format
error = validate_syllable('xyz', compact=False)
# Returns detailed multi-line report

# With DataFrame
df['errors'] = df['syllable'].apply(
    lambda x: validate_syllable(x, compact=True, max_errors=1)
)
```

#### 3. `validate_text(text, method='py', compact=True, max_errors=0)` - Most Detailed

Returns dictionary with complete validation information.

```python
from RoManTools.table_utils import validate_text

result = validate_text('xyz')
# Returns:
# {
#     'valid': False,
#     'error_count': 2,
#     'error_types': ['invalid_initial', 'invalid_final'],
#     'error_report': 'ERROR - invalid_initial - "xyz"; ERROR - invalid_final - "xyz"',
#     'first_error': 'ERROR - invalid_initial - "xyz"'
# }

# With DataFrame - create multiple columns
validation_results = df['syllable'].apply(validate_text)
df['valid'] = validation_results.apply(lambda x: x['valid'])
df['error_count'] = validation_results.apply(lambda x: x['error_count'])
df['error_types'] = validation_results.apply(lambda x: ', '.join(x['error_types']))
df['first_error'] = validation_results.apply(lambda x: x['first_error'])
```

### ErrorTracker Methods

If you're working with the core API, ErrorTracker has new methods:

```python
from RoManTools.config import Config
from RoManTools.syllable import SyllableProcessor
from RoManTools.data_loader import load_method_params

config = Config(error_report=False)
processor = SyllableProcessor(config, load_method_params('py'))
syllable = processor.create_syllable('xyz')

# Get first error only (compact)
first_error = syllable.error_tracker.get_first_error_string()
# Returns: 'ERROR - invalid_initial - "xyz"'

# Get list of error types
error_types = syllable.error_tracker.get_error_types_list()
# Returns: ['invalid_initial', 'invalid_final']

# Generate compact report
report = syllable.error_tracker.generate_report(compact=True, max_errors=1)
# Returns: 'ERROR - invalid_initial - "xyz"; (+1 more)'

# Generate detailed report
report = syllable.error_tracker.generate_report(compact=False)
# Returns multi-line detailed report
```

## Command-Line Interface

### Error Reporting Flags (Hierarchical)

**Primary Flag:**
- `-R, --error_report`: Enable error reporting (master switch)

**Secondary Flags (require `-R`):**
- `--error_compact`: Use compact one-line error format instead of detailed (default: detailed)
- `--error_max N`: Report maximum N errors (0 = all errors, N = first N errors)

**Note:** The secondary flags (`--error_compact` and `--error_max`) can only be used when `-R` is enabled. Attempting to use them without `-R` will result in an error.

### Examples

```bash
# Basic error reporting (detailed format, all errors)
RoManTools validator "xyz" -m py -R

# Compact one-line format (requires -R)
RoManTools validator "xyz" -m py -R --error_compact

# First error only (requires -R)
RoManTools validator "xyz" -m py -R --error_max 1

# Compact format with error limit (requires -R)
RoManTools validator "xyz" -m py -R --error_compact --error_max 1

# Invalid: will produce error message
RoManTools validator "xyz" -m py --error_compact
# Error: --error_compact and --error_max require --error_report (-R) to be enabled
```

### Conversion with Error Reporting

```bash
# Detailed format (default)
RoManTools convert "mhazhong dyng" -f py -t wg -R

# Compact one-line format
RoManTools convert "mhazhong dyng" -f py -t wg -R --error_compact

# First error only per word
RoManTools convert "mhazhong dyng" -f py -t wg -R --error_compact --error_max 1
```

**Output with `-R --error_compact --error_max 1`:**
```
WARNING: # Errors in word: 'mhazhong': ERROR - invalid_initial - "mh"; (+2 more)
WARNING: # Errors in word: 'dyng': ERROR - invalid_initial - "dyng"; (+1 more)
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
3      mha     False              invalid_initial
4      pia     False                  rare_syllable
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

When using the core API with Config:

```python
from RoManTools.config import Config

# Default: detailed reports, all errors
config = Config(error_report=True)

# Compact format, first error only
config = Config(
    error_report=True,
    error_report_compact=True,
    error_report_max=1
)

# Compact format, all errors
config = Config(
    error_report=True,
    error_report_compact=True,
    error_report_max=0
)
```

## Recommendations for Different Use Cases

### For Quick Table Validation
Use `get_validation_column()` - simplest, returns "OK" or error.

### For Detailed Analysis
Use `validate_text()` - returns dictionary with all information.

### For Large Datasets
Use `validate_syllable()` with `max_errors=1` - faster, shows first error only.

### For Error Categorization
Use `validate_text()` and check `error_types` list.

### For Debugging
Use detailed format in command line with `-R` flag.

### For Production Systems
Use compact format with `max_errors=1` for performance and readability.

## Performance Tips

1. **Set max_errors=1** for large datasets - stops validation after first error
2. **Use compact format** - faster string generation
3. **Disable error_report in Config** when using table_utils - they don't need logging
4. **Cache method_params** if validating thousands of syllables:

```python
from RoManTools.data_loader import load_method_params
from RoManTools.config import Config
from RoManTools.syllable import SyllableProcessor

# Load once
config = Config(error_report=False)
method_params = load_method_params('py')
processor = SyllableProcessor(config, method_params)

# Reuse for all syllables
def validate_cached(text):
    syl = processor.create_syllable(text)
    if not syl.error_tracker.has_errors():
        return "OK"
    return syl.error_tracker.get_first_error_string()

df['validation'] = df['syllable'].apply(validate_cached)
```
