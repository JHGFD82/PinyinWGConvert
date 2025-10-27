# RoManTools - Romanized Mandarin Tools

![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Flake8](https://img.shields.io/badge/code%20style-flake8-brightgreen)
![Pylint](https://img.shields.io/badge/pylint-10.0%2F10-brightgreen)

This package comprises a set of tools designed to facilitate the handling of romanized Mandarin text. It is currently under active development by Jeff Heller, Digital Project Specialist for the Department of East Asian Studies at Princeton University. This is a beta release, open for testing and forking for Python 3.9+.

## Features Planned for Version 1.0

Version 1.0 of this project will include the following features:

- **Conversion between Romanization Standards**: Support for converting between Pinyin and Wade-Giles (with Yale and additional standards to be added in future versions).
- **Cherry Pick**: Converts only identified romanized Chinese terms, excluding any English words or those in a stopword list.
- **Text Segmentation**: Segments text into meaningful chunks, a feature that will be utilized by other features but also available for direct use by the user.
- **Syllable Count**: Counts the number of syllables per word and reports the list to the user.
- **Method Detect**: Identifies the romanization standard used in the input text and returns the detected standard(s) to the user as either a single standard or a list of multiple standards.
- **Validator**: Basic validation of supplied text.

## Prerequisites

There are no prerequisites. RoManTools was originally built using Numpy 2D arrays, but this has since been replaced with nested tuples.

## Installation

To install RoManTools, the easiest method is through pip:

``pip -m install RoManTools``

You can also download the package directly from the GitHub repository. This method is ***not recommended*** as it requires a specific execution process, detailed in the last bullet point below.

## Execution

RoManTools can be executed in three ways.

* From the command-line using the installed command:

```bash
RoManTools [action] -i [input] [other parameters]
```

* From within the Python console or scripts via import:

```python
from RoManTools import *
[action]([input], [other parameters])
```

* From the command-line after downloading the package directly from GitHub:

```bash
python -m RoManTools.main [action] -i [input] [other parameters]
```

Documentation on command-line execution can be found in [CLI.md](https://github.com/JHGFD82/RoManTools/blob/main/docs/CLI.md), as well as execution within Python from [Python.md](https://github.com/JHGFD82/RoManTools/blob/main/docs/Python.md). Please refer to [Input_Requirements.md](https://github.com/JHGFD82/RoManTools/blob/main/docs/Input_Requirements.md) for guidelines on how text should be formatted for input, and [Methodology.md](https://github.com/JHGFD82/RoManTools/blob/main/docs/Methodology.md) will provide details on the text analysis process.

## Possible Future Goals (suggestions welcome!)

* **IPA Pronunciation**: Convert between romanized text and the International Phonetic Alphabet.
* **Tone Marking Conversion**: Convert between tone marking systems (numerical and IPA).
* **Audio Pronunciation**: Produce audio recordings of inputted text.
* **Flashcards/Quizzes**: Gamification of text input and pronunciation.
* To submit suggestions for future updates, contact main developer Jeff Heller via [Github issues](https://github.com/JHGFD82/RoManTools/issues) or via [e-mail](mailto:jh43@princeton.edu).

## Origin

This project originated as the `syllable_count` function developed for use with the Tang History Database, led by Professor Anna Shields of the Department of East Asian Studies at Princeton University. The objective was to validate user input of romanized Mandarin, facilitating the incorporation of data from Harvard University's Chinese Biographical Database (CBDB). By analyzing the syllable structure of romanized Mandarin strings and comparing them to corresponding Chinese characters, the function initially focused on validating the entry of Tang dynasty figures' names. As the project evolved, it expanded to include robust error handling, detection of both Pinyin and Wade-Giles romanization systems, and cross-system translation, even within mixed English text. The motivation to release this tool as a publicly available package stems from the need for a fast, efficient solution to validate romanized Mandarin text, promoting consistency in future datasets and ensuring flawless adherence to romanization standards.
