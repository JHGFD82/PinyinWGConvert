# RoManTools - Copilot Instructions

## Architecture Overview

RoManTools is a Python package for processing romanized Mandarin text, supporting conversion between Pinyin and Wade-Giles romanization systems. The codebase uses a **Strategy pattern** for romanization methods with a **data-driven approach** using CSV files for syllable validation.

### Core Components

- **`main.py`**: CLI entry point with argparse subcommands (`segment`, `convert`, `cherry-pick`, `validator`, `detect-method`, `syllable-count`)
- **`strategies/`**: Strategy pattern implementation for romanization methods (`PinyinStrategy`, `WadeGilesStrategy`)
- **`data/`**: CSV files defining valid syllable combinations (`pyDF.csv`, `wgDF.csv`, `conversion_mapping.csv`)
- **`syllable.py`**: Core syllable processing logic using strategy pattern
- **`chunker.py`**: Text segmentation into processable chunks
- **`config.py`**: Configuration object for debugging features (`crumbs`, `error_skip`, `error_report`)

### Key Design Patterns

1. **Strategy Pattern**: `RomanizationStrategy` base class with method-specific implementations
2. **Factory Pattern**: `RomanizationStrategyFactory` creates appropriate strategy instances
3. **Data-Driven Validation**: CSV files define valid initial-final combinations per romanization method
4. **Configuration-Based Debugging**: `Config` object controls verbose output and error handling

## Development Workflow

### Running Tests
```bash
PYTHONPATH=$(pwd) pytest --doctest-modules --junitxml=junit/test-results.xml
PYTHONPATH=$(pwd) pytest --cov=tests/ --cov=RoManTools/ --cov-branch --cov-report=xml
```

### CLI Testing
```bash
python -m RoManTools.main segment "Zhongguo ti'an tianqi" -m py
RoManTools convert "Zhongguo" -f py -t wg
```

### Adding New Romanization Methods

1. Create strategy class in `strategies/` inheriting from `RomanizationStrategy`
2. Add CSV data file in `data/` with initial-final combinations
3. Update `constants.py` `supported_methods` dictionary
4. Register in `factory.py`

## Project-Specific Conventions

### Error Handling
- `Config.error_skip=True` for non-fatal errors (used by `cherry-pick` automatically)
- `Config.error_report=True` includes error details in output
- `Config.crumbs=True` enables step-by-step processing traces

### Data Structure Patterns
- **Syllable validation**: Uses 2D boolean tuples from CSV data (`ar` arrays)
- **Method normalization**: `_normalize_method()` converts user input to standard shorthands (`py`, `wg`)
- **Stopwords**: English words excluded from romanization conversion (7396 words in `stopwords.txt`)

### CLI Argument Patterns
- Hyphenated subcommands in CLI become underscored in code (`cherry-pick` → `cherry_pick`)
- Method arguments accept both full names (`pinyin`) and shorthands (`py`)
- Common parent parser for shared options (`-C`, `-S`, `-R`)

## Testing & Coverage

- Target: 100% code coverage (current status shown in README badge)
- Tests use `decorators.py` for timing measurements
- Multi-Python version testing (3.9-3.13) via GitHub Actions
- Doctests embedded in module docstrings

## Package Structure

- Entry point: `RoManTools.main:main` (console script)
- Data files included via `setuptools.package-data`
- No external dependencies (pure Python)
- Support for both CLI and programmatic import usage
