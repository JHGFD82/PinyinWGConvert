"""
Unit tests for CLI argument validation functions.

This module tests the validation logic for command-line arguments to ensure
that invalid argument combinations are properly detected and reported.
"""

import unittest
import argparse
from RoManTools.cli_validators import (
    normalize_method,
    validate_error_reporting_args,
    validate_action_specified,
    normalize_action_key
)


class TestCLIValidators(unittest.TestCase):
    """Test cases for CLI validation functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = argparse.ArgumentParser()
        self.supported_methods = {
            'pinyin': {'shorthand': 'py', 'pretty': 'Pinyin'},
            'wade-giles': {'shorthand': 'wg', 'pretty': 'Wade-Giles'}
        }
        self.method_shorthand_to_full = {
            'py': 'pinyin',
            'wg': 'wade-giles'
        }

    # Tests for normalize_method
    def test_normalize_method_full_name_pinyin(self):
        """Test normalizing full method name 'pinyin' to 'py'."""
        result = normalize_method('pinyin', self.supported_methods, self.method_shorthand_to_full)
        self.assertEqual(result, 'py')

    def test_normalize_method_full_name_wade_giles(self):
        """Test normalizing full method name 'wade-giles' to 'wg'."""
        result = normalize_method('wade-giles', self.supported_methods, self.method_shorthand_to_full)
        self.assertEqual(result, 'wg')

    def test_normalize_method_shorthand_py(self):
        """Test that shorthand 'py' remains 'py'."""
        result = normalize_method('py', self.supported_methods, self.method_shorthand_to_full)
        self.assertEqual(result, 'py')

    def test_normalize_method_shorthand_wg(self):
        """Test that shorthand 'wg' remains 'wg'."""
        result = normalize_method('wg', self.supported_methods, self.method_shorthand_to_full)
        self.assertEqual(result, 'wg')

    def test_normalize_method_case_insensitive(self):
        """Test that method normalization is case-insensitive."""
        result = normalize_method('PINYIN', self.supported_methods, self.method_shorthand_to_full)
        self.assertEqual(result, 'py')

    def test_normalize_method_invalid(self):
        """Test that invalid method raises ArgumentTypeError."""
        with self.assertRaises(argparse.ArgumentTypeError) as cm:
            normalize_method('invalid', self.supported_methods, self.method_shorthand_to_full)
        self.assertIn('Invalid romanization method', str(cm.exception))

    # Tests for validate_error_reporting_args
    def test_validate_error_reporting_args_valid_with_all_flags(self):
        """Test that validation passes when error_report is True with error_compact."""
        args = argparse.Namespace(
            error_report=True,
            error_compact=True,
            error_max=0
        )
        # Should not raise an error
        validate_error_reporting_args(args, self.parser)

    def test_validate_error_reporting_args_valid_without_compact(self):
        """Test that validation passes when error_report is False and no dependent flags are set."""
        args = argparse.Namespace(
            error_report=False,
            error_compact=False,
            error_max=0
        )
        # Should not raise an error
        validate_error_reporting_args(args, self.parser)

    def test_validate_error_reporting_args_invalid_compact_without_report(self):
        """Test that validation fails when error_compact is True but error_report is False."""
        args = argparse.Namespace(
            error_report=False,
            error_compact=True,
            error_max=0
        )
        with self.assertRaises(SystemExit) as cm:
            validate_error_reporting_args(args, self.parser)
        self.assertEqual(cm.exception.code, 2)

    def test_validate_error_reporting_args_invalid_max_without_report(self):
        """Test that validation fails when error_max is set but error_report is False."""
        args = argparse.Namespace(
            error_report=False,
            error_compact=False,
            error_max=5
        )
        with self.assertRaises(SystemExit) as cm:
            validate_error_reporting_args(args, self.parser)
        self.assertEqual(cm.exception.code, 2)

    def test_validate_error_reporting_args_missing_attributes(self):
        """Test that validation handles missing attributes gracefully."""
        args = argparse.Namespace()
        # Should not raise an error when attributes are missing
        validate_error_reporting_args(args, self.parser)

    def test_validate_error_reporting_args_partial_attributes(self):
        """Test that validation handles partial attributes gracefully."""
        args = argparse.Namespace(error_report=True)
        # Should not raise an error when only some attributes are present
        validate_error_reporting_args(args, self.parser)

    # Tests for validate_action_specified
    def test_validate_action_specified_with_action(self):
        """Test that validation returns True when action is specified."""
        args = argparse.Namespace(action='segment')
        result = validate_action_specified(args, self.parser)
        self.assertTrue(result)

    def test_validate_action_specified_without_action(self):
        """Test that validation returns False when no action is specified."""
        args = argparse.Namespace(action=None)
        result = validate_action_specified(args, self.parser)
        self.assertFalse(result)

    def test_validate_action_specified_empty_string(self):
        """Test that validation returns False when action is empty string."""
        args = argparse.Namespace(action='')
        result = validate_action_specified(args, self.parser)
        self.assertFalse(result)

    # Tests for normalize_action_key
    def test_normalize_action_key_with_hyphens(self):
        """Test that hyphens are converted to underscores."""
        result = normalize_action_key('cherry-pick')
        self.assertEqual(result, 'cherry_pick')

    def test_normalize_action_key_with_multiple_hyphens(self):
        """Test that multiple hyphens are all converted."""
        result = normalize_action_key('some-multi-word-action')
        self.assertEqual(result, 'some_multi_word_action')

    def test_normalize_action_key_no_hyphens(self):
        """Test that action keys without hyphens remain unchanged."""
        result = normalize_action_key('segment')
        self.assertEqual(result, 'segment')

    def test_normalize_action_key_already_underscores(self):
        """Test that underscores are preserved."""
        result = normalize_action_key('some_action')
        self.assertEqual(result, 'some_action')


if __name__ == '__main__':
    unittest.main()
