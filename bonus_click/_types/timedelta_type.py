"""
Click parameter type that parses a duration string into datetime.timedelta.

For example, let's take a standard duration (12 hours, 15 minutes, 30 seconds and 500 milliseconds)
and show it as strings in the different supported formats:

  ISO 8601 duration     PT12H15M30.5S
                        PT12H15M30,5S     (comma decimal separator, also ISO)
                        PT735M30.5S       (units need not be normalized)
                        PT44130.5S
  Clock-style           12:15:30.5
                        12:15:30.500000   (what str(timedelta) prints)

Days and weeks are accepted in ISO form (P1DT12H15M30.5S, P1W) and in
clock form as a str(timedelta) prefix ("1 day, 12:15:30.5"). A leading '-'
negates the whole duration: -PT12H15M30.5S. Months and years (P1M, P1Y)
are rejected because they have no fixed timedelta.
"""

import re
from datetime import timedelta
from typing import Dict

import click
from click.core import Context, Parameter

_NUM = r"\d+(?:[.,]\d+)?"

_ISO = re.compile(
    rf"^P(?:(?P<weeks>{_NUM})W)?(?:(?P<days>{_NUM})D)?"
    rf"(?:T(?:(?P<hours>{_NUM})H)?(?:(?P<minutes>{_NUM})M)?(?:(?P<seconds>{_NUM})S)?)?$",
    re.IGNORECASE,
)

_CLOCK = re.compile(
    r"^(?:(?P<days>\d+) days?, )?(?P<hours>\d+):(?P<minutes>\d{2}):(?P<seconds>\d{2}(?:\.\d+)?)$"
)


class TimedeltaParamType(click.ParamType):
    """
    Click type that converts common timedelta string representations to actual `datetime.timedelta`
    objects.
    """

    name = "duration"

    def convert(self, value: str, param: Parameter, ctx: Context) -> timedelta:
        """
        Parses the string, converts it to a timedelta object.
        :param value: Input from user to convert.
        :param param: From click invocation.
        :param ctx: From click invocation.
        :return: Parsed `datetime.timedelta` object.
        """

        if isinstance(value, timedelta):
            return value

        text = str(value).strip()
        sign = -1 if text.startswith("-") else 1
        body = text.lstrip("+-")
        match = _ISO.match(body) or _CLOCK.match(body)

        if match is None or body.upper() in ("P", "PT"):
            self.fail(
                f"{value!r} is not a valid duration "
                "(expected ISO 8601 like PT1H30M5.5S, or HH:MM:SS[.ffffff])",
                param,
                ctx,
            )

        parts: Dict[str, float] = {
            unit: float(num.replace(",", "."))
            for unit, num in match.groupdict().items()
            if num is not None
        }

        return sign * timedelta(**parts)
