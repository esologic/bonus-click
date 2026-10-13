"""
Exposes the set of custom click types implemented in the project.
"""

# pylint: disable=protected-access

from bonus_click._types.timedelta_type import TimedeltaParamType

Timedelta = TimedeltaParamType()

__all__ = ["Timedelta"]
