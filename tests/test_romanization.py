# tests/test_romanization.py

import unittest
from Tools import syllable_count, convert_romanization
from io import StringIO
from unittest.mock import patch


class TestRomanization(unittest.TestCase):
    def test_syllable_count(self):
        result = syllable_count('ni hao', method='PY')
        self.assertEqual(result, [[1, 1]])

    @patch('sys.stdout', new_callable=StringIO)
    def test_syllable_count_output(self, mock_stdout):
        syllable_count('ni hao', method='PY', crumbs=True)
        expected_output = ('# Analyzing ni hao #\n'
                           'n [initial]\n'
                           'n|i [final]\n'
                           'ni valid: True\n'
                           'ni syllable count: 1\n'
                           '-----------\n'
                           'h [initial]\n'
                           'h|ao [final]\n'
                           'hao valid: True\n'
                           'hao syllable count: 1\n'
                           '-----------\n')
        self.assertEqual(mock_stdout.getvalue(), expected_output)

    def test_convert_romanization(self):
        result = convert_romanization('hao', 'PYWG')
        self.assertEqual(result, 'hao')


if __name__ == '__main__':
    unittest.main()
