"""
Picking the right strategy object for a given romanization method.

Every place in the codebase that needs a Pinyin-specific or Wade-Giles-
specific strategy object (see base.py for what a "strategy" is) asks this
module for one, instead of constructing `PinyinStrategy(...)` or
`WadeGilesStrategy(...)` directly. That keeps the "which method maps to
which class" decision in exactly one place. A class whose job is
specifically to build the right object for you, based on some input, is
often called a factory - hence the name.
"""

from typing import TYPE_CHECKING, Dict, Type
from .base import RomanizationStrategy
from .pinyin import PinyinStrategy
from .wade_giles import WadeGilesStrategy
from ..constants import method_shorthand_to_full

if TYPE_CHECKING:
    from ..syllable import SyllableProcessor


class RomanizationStrategyFactory:
    """
    Builds the correct strategy object for a given romanization method
    shorthand ('py', 'wg'). See the module docstring above for why this
    exists as its own class.
    """

    @staticmethod
    def create_strategy(method: str, processor: "SyllableProcessor") -> RomanizationStrategy:
        """
        Args:
            method: The romanization method's shorthand ('py', 'wg', etc.).
            processor: The SyllableProcessor the new strategy should work
                with (see base.py's RomanizationStrategy.__init__).

        Returns:
            The matching strategy instance.

        Raises:
            ValueError: If `method` isn't one RoManTools supports.
        """
        strategies: Dict[str, Type[RomanizationStrategy]] = {
            'py': PinyinStrategy,
            'wg': WadeGilesStrategy,
        }

        strategy_class = strategies.get(method)
        if strategy_class is None:
            available_methods = ', '.join(method_shorthand_to_full.keys())
            raise ValueError(f"Unsupported romanization method: '{method}'. Available methods: {available_methods}")

        return strategy_class(processor)

    @staticmethod
    def get_available_methods() -> list[str]:
        """
        Returns:
            list[str]: The shorthand of every romanization method currently
                supported.
        """
        return list(method_shorthand_to_full.keys())

    @staticmethod
    def register_strategy(method: str, strategy_class: Type[RomanizationStrategy]) -> None:
        """
        Placeholder for adding a new romanization method's strategy at
        runtime, without editing this file's `strategies` dictionary
        directly. Not implemented yet - for now, adding a method means
        adding it to that dictionary in create_strategy above (see
        CLAUDE.md's "Adding New Romanization Methods" section for the full
        set of steps).

        Args:
            method: The romanization method's shorthand.
            strategy_class: The strategy class to associate with it.

        Raises:
            NotImplementedError: Always, until this is built out.
        """
        raise NotImplementedError("Dynamic strategy registration not yet implemented")
