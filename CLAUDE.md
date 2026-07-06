# RoManTools - Project Guide

## Architecture Overview

RoManTools is a Python package for processing romanized Mandarin text, supporting
conversion between Pinyin and Wade-Giles romanization systems. The codebase uses a
**Strategy pattern** for romanization methods with a **data-driven approach** using
CSV files for syllable validation.

### Core Components

- **`main.py`**: CLI entry point with argparse subcommands (`segment`, `convert`,
  `cherry-pick`, `syllable-count`, `detect-method`, `validator`). Subcommands are
  hyphenated on the CLI but normalized to underscored keys internally
  (`normalize_action_key`) and dispatched via the `ACTIONS` dict.
- **`cli_validators.py`**: Pure argument-validation helpers used by `main.py`
  (method normalization, error-reporting-flag combination checks, action-key
  normalization).
- **`config.py`**: `Config` object controlling `crumbs` (step-by-step trace
  output), `error_skip`, `error_report`, `error_report_compact`,
  `error_report_max`. `Config.from_args()` builds one from an argparse
  `Namespace` or a dict.
- **`constants.py`**: Character sets (`vowels`, `apostrophes`, `dashes`,
  `supported_contractions`), method/action/config metadata dicts, and the
  shorthand/full-name alias maps.
- **`data_loader.py`**: Loads the CSV-backed syllable validity arrays
  (`pyDF.csv`, `wgDF.csv`), `conversion_mapping.csv`, rare-syllable sets, and
  `stopwords.txt`.
- **`chunker.py`** (`TextChunkProcessor`): Splits raw input into word /
  non-word segments, splits each word into syllable-candidate substrings, and
  feeds them to `SyllableProcessor` to build `Syllable` objects.
- **`syllable.py`**: `SyllableProcessor` (per-method validation data + strategy
  instance + rare-syllable set + `ErrorTracker`) and `Syllable` (parses
  initial/final, validates, tracks capitalization/apostrophe/dash status and
  errors).
- **`strategies/`**: Strategy pattern implementation (`RomanizationStrategy`
  base class, `PinyinStrategy`, `WadeGilesStrategy`, `RomanizationStrategyFactory`).
  `bopomofo_example.py` and `yale_example.py` are reference scaffolding for
  future methods — neither is registered in `factory.py` or
  `constants.supported_methods`, so they are not live code paths yet.
- **`conversion.py`** (`RomanizationConverter`): Looks up rows in
  `conversion_mapping.csv` to convert a single syllable between methods.
- **`word.py`** (`WordProcessor` / `Word`): Converts a word's syllables,
  re-applies capitalization and apostrophes/dashes, handles contractions and
  stopwords, aggregates per-word errors.
- **`errors.py`**: `ErrorType` enum, `ValidationError` dataclass, and
  `ErrorTracker` for structured validation error collection/reporting (compact
  and verbose report formats).
- **`table_utils.py`**: pandas-friendly convenience wrappers
  (`validate_syllable`, `validate_text`, `get_validation_column`) that use
  `SyllableProcessor` directly, bypassing the segmentation/word pipeline.
- **`utils.py`**: Public API (`segment_text`, `convert_text`, `cherry_pick`,
  `syllable_count`, `detect_method`, `validator`) re-exported from
  `RoManTools/__init__.py`.

## Development Workflow

### Running Tests

```bash
PYTHONPATH=$(pwd) pytest --doctest-modules --junitxml=junit/test-results.xml
PYTHONPATH=$(pwd) pytest --cov=tests/ --cov=RoManTools/ --cov-branch --cov-report=xml
```

### CLI Testing

The text argument is **positional** (there is no `-i`/`--input` flag, despite
some stale examples in older docs):

```bash
python -m RoManTools.main segment "Zhongguo ti'an tianqi" -m py
RoManTools convert "Zhongguo" -f py -t wg
```

### Adding New Romanization Methods

1. Create a strategy class in `strategies/` inheriting from `RomanizationStrategy`
   (see `bopomofo_example.py` / `yale_example.py` for a starting point).
2. Add a CSV data file in `data/` with initial-final combinations.
3. Update `constants.py`'s `supported_methods` dictionary.
4. Register the strategy in `strategies/factory.py`.

## Project-Specific Conventions

### Error Handling

- `Config.error_skip=True` for non-fatal errors (forced `True` internally for
  `cherry-pick` regardless of what the user passed).
- `Config.error_report=True` includes error details in output via
  `ErrorTracker`/`ErrorType` (see `errors.py`).
- `Config.crumbs=True` enables step-by-step processing traces through
  `Config.print_crumb`.

### Data Structure Patterns

- **Syllable validation**: 2D boolean tuples loaded from CSV data (`ar` arrays).
- **Method normalization**: CLI input is normalized to standard shorthands
  (`py`, `wg`) via `cli_validators.normalize_method`.
- **Stopwords**: English words excluded from romanization conversion
  (`data/stopwords.txt`).

### Known Gotchas (read before touching caching/strategy code)

- `Config` has no `__eq__`/`__hash__`, so the several `@lru_cache`-wrapped
  inner functions in `utils.py` that key on a `Config` instance only hit when
  the *exact same* object is reused across calls. Since callers typically
  construct a fresh `Config` per top-level call, treat these caches as
  effectively per-call only — don't assume cross-call reuse without checking.
- `TextChunkProcessor._cached_syllable_processor` in `chunker.py` is an
  instance method decorated with `@lru_cache`. That pins `self` (and the whole
  processor instance) in a class-level cache for the life of the process — be
  careful before relying on or extending this pattern.
- `RomanizationStrategy.find_initial` / `validate_syllable` are implemented per
  method but are **not** called anywhere in the live code path — `Syllable`
  parses initials directly (`_find_initial`) and validates via
  `processor.validate_final_using_array`. Only `find_final`,
  `handle_apostrophe_in_initial`, and `check_illegal_characters` are actually
  invoked through the strategy object. Keep this in mind if you're tempted to
  "fix a bug" in the strategy's `find_initial` — it won't change behavior.

## Testing & Coverage

- Target: 100% code coverage (see README badge).
- Tests use `decorators.py` for timing measurements.
- Multi-Python version testing (3.9-3.13) via GitHub Actions
  (`.github/workflows/python-test-artifact.yml`).
- Doctests embedded in module docstrings — keep them in sync with actual CLI
  behavior when changing argument parsing.

## Package Structure

- Entry point: `RoManTools.main:main` (console script).
- Data files included via `setuptools.package-data`.
- No runtime dependencies (pure Python); `requirements.txt` only pins a build
  tool (`setuptools`) for CI, not package runtime dependencies.
- Supports both CLI and programmatic import usage.
