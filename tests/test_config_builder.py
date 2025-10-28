"""
Unit tests for Config builder pattern.

This module tests the Config.from_args() factory method to ensure
proper Config object creation from argparse.Namespace and dict.
"""

import unittest
import argparse
from RoManTools.config import Config


class TestConfigBuilder(unittest.TestCase):
    """Test cases for Config builder pattern."""

    def test_from_args_namespace_all_true(self):
        """Test creating Config from Namespace with all flags enabled."""
        args = argparse.Namespace(
            crumbs=True,
            error_skip=True,
            error_report=True,
            error_compact=True,
            error_max=5
        )
        config = Config.from_args(args)
        
        self.assertTrue(config.crumbs)
        self.assertTrue(config.error_skip)
        self.assertTrue(config.error_report)
        self.assertTrue(config.error_report_compact)
        self.assertEqual(config.error_report_max, 5)

    def test_from_args_namespace_all_false(self):
        """Test creating Config from Namespace with all flags disabled."""
        args = argparse.Namespace(
            crumbs=False,
            error_skip=False,
            error_report=False,
            error_compact=False,
            error_max=0
        )
        config = Config.from_args(args)
        
        self.assertFalse(config.crumbs)
        self.assertFalse(config.error_skip)
        self.assertFalse(config.error_report)
        self.assertFalse(config.error_report_compact)
        self.assertIsNone(config.error_report_max)  # 0 converts to None

    def test_from_args_namespace_mixed(self):
        """Test creating Config from Namespace with mixed values."""
        args = argparse.Namespace(
            crumbs=True,
            error_skip=False,
            error_report=True,
            error_compact=False,
            error_max=10
        )
        config = Config.from_args(args)
        
        self.assertTrue(config.crumbs)
        self.assertFalse(config.error_skip)
        self.assertTrue(config.error_report)
        self.assertFalse(config.error_report_compact)
        self.assertEqual(config.error_report_max, 10)

    def test_from_args_namespace_missing_attributes(self):
        """Test creating Config from Namespace with missing attributes (uses defaults)."""
        args = argparse.Namespace()
        config = Config.from_args(args)
        
        # All should default to False/None
        self.assertFalse(config.crumbs)
        self.assertFalse(config.error_skip)
        self.assertFalse(config.error_report)
        self.assertFalse(config.error_report_compact)
        self.assertIsNone(config.error_report_max)

    def test_from_args_namespace_partial_attributes(self):
        """Test creating Config from Namespace with some attributes."""
        args = argparse.Namespace(
            crumbs=True,
            error_report=True
        )
        config = Config.from_args(args)
        
        self.assertTrue(config.crumbs)
        self.assertFalse(config.error_skip)  # Default
        self.assertTrue(config.error_report)
        self.assertFalse(config.error_report_compact)  # Default
        self.assertIsNone(config.error_report_max)  # Default

    def test_from_args_dict_all_true(self):
        """Test creating Config from dict with all flags enabled."""
        args: dict[str, bool | int] = {
            'crumbs': True,
            'error_skip': True,
            'error_report': True,
            'error_compact': True,
            'error_max': 5
        }
        config = Config.from_args(args)
        
        self.assertTrue(config.crumbs)
        self.assertTrue(config.error_skip)
        self.assertTrue(config.error_report)
        self.assertTrue(config.error_report_compact)
        self.assertEqual(config.error_report_max, 5)

    def test_from_args_dict_all_false(self):
        """Test creating Config from dict with all flags disabled."""
        args: dict[str, bool | int] = {
            'crumbs': False,
            'error_skip': False,
            'error_report': False,
            'error_compact': False,
            'error_max': 0
        }
        config = Config.from_args(args)
        
        self.assertFalse(config.crumbs)
        self.assertFalse(config.error_skip)
        self.assertFalse(config.error_report)
        self.assertFalse(config.error_report_compact)
        self.assertIsNone(config.error_report_max)

    def test_from_args_dict_empty(self):
        """Test creating Config from empty dict (uses defaults)."""
        args: dict[str, bool | int] = {}
        config = Config.from_args(args)
        
        # All should default to False/None
        self.assertFalse(config.crumbs)
        self.assertFalse(config.error_skip)
        self.assertFalse(config.error_report)
        self.assertFalse(config.error_report_compact)
        self.assertIsNone(config.error_report_max)

    def test_from_args_dict_partial(self):
        """Test creating Config from dict with only some keys."""
        args: dict[str, bool | int] = {
            'crumbs': True,
            'error_report': True
        }
        config = Config.from_args(args)
        
        self.assertTrue(config.crumbs)
        self.assertFalse(config.error_skip)  # Default
        self.assertTrue(config.error_report)
        self.assertFalse(config.error_report_compact)  # Default
        self.assertIsNone(config.error_report_max)  # Default

    def test_from_args_equivalence_namespace_vs_dict(self):
        """Test that Namespace and dict produce equivalent Config objects."""
        namespace = argparse.Namespace(
            crumbs=True,
            error_skip=False,
            error_report=True,
            error_compact=True,
            error_max=3
        )
        
        dict_args: dict[str, bool | int] = {
            'crumbs': True,
            'error_skip': False,
            'error_report': True,
            'error_compact': True,
            'error_max': 3
        }
        
        config_from_namespace = Config.from_args(namespace)
        config_from_dict = Config.from_args(dict_args)
        
        self.assertEqual(config_from_namespace.crumbs, config_from_dict.crumbs)
        self.assertEqual(config_from_namespace.error_skip, config_from_dict.error_skip)
        self.assertEqual(config_from_namespace.error_report, config_from_dict.error_report)
        self.assertEqual(config_from_namespace.error_report_compact, config_from_dict.error_report_compact)
        self.assertEqual(config_from_namespace.error_report_max, config_from_dict.error_report_max)

    def test_from_args_error_max_zero_becomes_none(self):
        """Test that error_max of 0 is converted to None."""
        args = argparse.Namespace(
            crumbs=False,
            error_skip=False,
            error_report=True,
            error_compact=False,
            error_max=0
        )
        config = Config.from_args(args)
        
        self.assertIsNone(config.error_report_max)

    def test_from_args_error_max_positive_preserved(self):
        """Test that positive error_max values are preserved."""
        for value in [1, 5, 10, 100]:
            args = argparse.Namespace(
                crumbs=False,
                error_skip=False,
                error_report=True,
                error_compact=False,
                error_max=value
            )
            config = Config.from_args(args)
            self.assertEqual(config.error_report_max, value)

    def test_from_args_maintains_logger(self):
        """Test that Config created with from_args has a logger."""
        args = argparse.Namespace(
            crumbs=False,
            error_skip=False,
            error_report=False,
            error_compact=False,
            error_max=0
        )
        config = Config.from_args(args)
        
        self.assertIsNotNone(config.logger)


if __name__ == '__main__':
    unittest.main()
