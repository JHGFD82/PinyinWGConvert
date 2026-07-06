# RoManTools - Project Guide

## What this project is

RoManTools converts and validates romanized Mandarin text, currently supporting
Pinyin and Wade-Giles. Its target audience is digital humanities researchers and
developers, many without a computer science background - so code comments,
docstrings, and the docs in `docs/` are all written in plain language, defining
technical terms the first time they come up in each file rather than assuming
prior CS knowledge. Keep that audience in mind when adding to this codebase.

Each romanization method's parsing rules live in their own small class (a
"strategy" - see `strategies/base.py` for the full explanation), so adding a
method mostly means adding one new file, not editing existing ones.

### Core Components

- **`main.py`**: The CLI entry point. Uses Python's `argparse` to define
  subcommands (`segment`, `convert`, `cherry-pick`, `syllable-count`,
  `detect-method`, `validator`) - hyphenated on the command line, but
  normalized to underscored keys internally (`normalize_action_key`) and
  dispatched via the `ACTIONS` dict.
- **`cli_validators.py`**: Argument-validation helpers used by `main.py`
  (method-name normalization, error-reporting-flag combination checks,
  action-key normalization).
- **`config.py`**: The `Config` class - the settings object every action
  takes (`crumbs` for a step-by-step trace, `error_skip`, `error_report`,
  `error_report_compact`, `error_report_max`). `Config.from_args()` builds
  one from an argparse `Namespace` or a plain dict. `Config` defines
  `__eq__`/`__hash__` based on its settings, so two separately-created
  `Config` instances with identical settings are treated as the same cache
  key (see "Caching" below).
- **`constants.py`**: Character sets (`vowels`, `apostrophes`, `dashes`,
  `supported_contractions`), method/action/config metadata dicts, and the
  shorthand/full-name alias maps.
- **`data_loader.py`**: Loads the CSV-backed syllable validity tables
  (`pyDF.csv`, `wgDF.csv`), `conversion_mapping.csv`, rare-syllable sets, and
  `stopwords.txt`. Every loader function is cached (`@lru_cache`) - each file
  is read from disk once per process, not once per call.
- **`chunker.py`** (`TextChunkProcessor`): Splits raw input into word /
  non-word segments, splits each word into syllable-candidate substrings, and
  feeds them to `SyllableProcessor` to build `Syllable` objects. Its
  intra-call syllable cache is a plain per-instance dict, not a class-level
  `@lru_cache` - the latter would pin every instance in memory forever
  (`self` becomes part of the cache key).
- **`syllable.py`**: `SyllableProcessor` (per-method validation data +
  strategy instance + rare-syllable set + `ErrorTracker`) and `Syllable`
  (parses initial/final, validates, tracks capitalization/apostrophe/dash
  status and errors).
- **`strategies/`**: One file per romanization method's parsing rules
  (`RomanizationStrategy` base class, `PinyinStrategy`, `WadeGilesStrategy`,
  `RomanizationStrategyFactory`). Only `find_final`,
  `handle_apostrophe_in_initial`, `handle_dash_in_initial`, and
  `check_illegal_characters` are actually called through the strategy object
  - `Syllable._find_initial` in syllable.py parses initials directly rather
  than delegating. `bopomofo_example.py` and `yale_example.py` are worked
  examples for adding a method, not live code - neither is registered in
  `factory.py` or `constants.supported_methods`.
- **`conversion.py`** (`RomanizationConverter`): Looks up rows in
  `conversion_mapping.csv` to convert a single syllable between methods. The
  per-syllable lookup cache (`_convert_syllable`) is module-level, shared
  across every `RomanizationConverter` instance - not a per-instance cache.
- **`word.py`** (`WordProcessor` / `Word`): Converts a word's syllables,
  re-applies capitalization and apostrophes/dashes, handles contractions and
  stopwords, aggregates per-word errors.
- **`errors.py`**: `ErrorType` (a fixed set of problem categories),
  `ValidationError` (one recorded problem), and `ErrorTracker` (collects
  `ValidationError`s and builds compact or detailed reports from them).
- **`table_utils.py`**: pandas-friendly wrappers (`validate_syllable`,
  `validate_text`, `get_validation_column`) that use `SyllableProcessor`
  directly, bypassing the segmentation/word pipeline. Not exported from
  `RoManTools/__init__.py` - import from `RoManTools.table_utils` directly.
- **`actions.py`**: The six public actions (`segment_text`, `convert_text`,
  `cherry_pick`, `syllable_count`, `detect_method`, `validator`), re-exported
  from `RoManTools/__init__.py`. Named `actions.py` rather than `utils.py` on
  purpose - it holds one cohesive thing (the package's public actions plus
  their shared processing/caching plumbing), not an unrelated grab-bag.

## Development Workflow

### Running Tests

```bash
PYTHONPATH=$(pwd) pytest --doctest-modules --junitxml=junit/test-results.xml
PYTHONPATH=$(pwd) pytest --cov=tests/ --cov=RoManTools/ --cov-branch --cov-report=xml
```

### CLI Testing

The text argument is positional (there is no `-i`/`--input` flag):

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
  `ErrorTracker`/`ErrorType` (see `errors.py`). Currently only has an
  observable effect for `convert`/`cherry-pick` (via `Word.process_syllables`)
  - `validator`, `segment`, `syllable-count`, and `detect-method` don't
  consult this flag.
- `Config.crumbs=True` enables step-by-step processing traces through
  `Config.print_crumb`.

### Data Structure Patterns

- **Syllable validation**: nested tuples of booleans loaded from CSV data
  (`ar` in `SyllableProcessor`) - one row per initial, one column per final.
- **Method normalization**: CLI input is normalized to standard shorthands
  (`py`, `wg`) via `cli_validators.normalize_method`.
- **Stopwords**: English words excluded from romanization conversion
  (`data/stopwords.txt`).

### Caching

Every function in `actions.py`, every loader in `data_loader.py`, and the
per-syllable lookup in `conversion.py` are cached so that repeated calls
with the same input - looping over a dataset, or a document where the same
words recur - don't redo work. Caching is intentionally bypassed when
`config.crumbs` or `config.error_report` is set, since both produce printed
output as a side effect of running that a cache hit would silently skip;
every other setting (like `error_skip`) is already part of what gets
cached, so different settings just produce separate cache entries rather
than needing to skip the cache.

If you add a new cached function, make sure whatever you key the cache on
has real value equality (`__eq__`/`__hash__`) - see `Config` above for why
this matters: without it, two logically-identical inputs built as separate
objects look like different cache keys, and the cache silently never hits.

## Testing & Coverage

- Target: 100% code coverage (see README badge).
- Tests use `decorators.py` for timing measurements.
- Multi-Python version testing (3.9-3.13) via GitHub Actions
  (`.github/workflows/python-test-artifact.yml`).
- Doctests embedded in module docstrings - keep them in sync with actual CLI
  behavior when changing argument parsing.
- Tests are explicitly exempt from the plain-language documentation rule
  above (they don't need to explain jargon to end users) - the rest of the
  codebase isn't.

## Package Structure

- Entry point: `RoManTools.main:main` (console script).
- Data files included via `setuptools.package-data`.
- No runtime dependencies (pure Python); `requirements.txt` only pins a build
  tool (`setuptools`) for CI, not package runtime dependencies.
- Supports both CLI and programmatic import usage.
