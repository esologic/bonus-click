"""
Unit tests for `TimedeltaParamType` in `bonus_click.types`.

These tests cover the accepted input formats (ISO 8601 durations and
clock-style strings), error conditions (malformed or unsupported durations),
and round-tripping through generated ISO strings. Parsing tests are anchored on a single value,
12h 15m 30.5s, so that the equivalence of the various spellings is obvious.
"""

from datetime import timedelta

import click
import pytest
from click.testing import CliRunner

from bonus_click.bonus_types import Timedelta

EXAMPLE = timedelta(hours=12, minutes=15, seconds=30, milliseconds=500)


def to_iso(td: timedelta) -> str:
    """
    Test helper that renders a timedelta as an ISO 8601 duration string,
    e.g. PT12H15M30.5S, used to generate inputs for round-trip tests.

    :param td: The timedelta to serialize.
    :return: The ISO 8601 duration string.
    """
    sign = "-" if td < timedelta(0) else ""
    td = abs(td)
    hours, rem = divmod(td.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    secs = seconds + td.microseconds / 1_000_000
    out = f"{sign}P"
    if td.days:
        out += f"{td.days}D"
    time_part = ""
    if hours:
        time_part += f"{hours}H"
    if minutes:
        time_part += f"{minutes}M"
    if secs or not (td.days or hours or minutes):
        time_part += f"{secs:g}S"
    return out + ("T" + time_part if time_part else "")


def make_cli() -> click.Command:
    """
    Helper function to generate a CLI command with a single `--duration` option.

    :return: A Click command that echoes the repr of the parsed timedelta.
    """

    @click.command()
    @click.option("--duration", type=Timedelta)
    def cli(duration: timedelta) -> None:
        click.echo(repr(duration))

    return cli


@pytest.mark.parametrize(
    "duration_value,expected_output",
    [
        # ISO 8601 spellings of the example value
        ("PT12H15M30.5S", EXAMPLE),
        ("PT12H15M30,5S", EXAMPLE),
        ("pt12h15m30.5s", EXAMPLE),
        ("PT735M30.5S", EXAMPLE),
        ("PT44130.5S", EXAMPLE),
        # Clock-style spellings of the example value
        ("12:15:30.5", EXAMPLE),
        ("12:15:30.500000", EXAMPLE),
        # Other units and sign handling
        ("P1DT12H15M30.5S", timedelta(days=1) + EXAMPLE),
        ("1 day, 12:15:30.5", timedelta(days=1) + EXAMPLE),
        ("3 days, 00:00:00", timedelta(days=3)),
        ("P1W", timedelta(weeks=1)),
        ("P2D", timedelta(days=2)),
        ("PT0S", timedelta(0)),
        ("-PT12H15M30.5S", -EXAMPLE),
        ("-12:15:30.5", -EXAMPLE),
        ("+PT5S", timedelta(seconds=5)),
    ],
)
def test_timedelta_parse(duration_value: str, expected_output: timedelta) -> None:
    """
    Verify that `Timedelta` parses every supported input format into the
    expected `timedelta`, including case-insensitive ISO strings, comma
    decimal separators, un-normalized units, and negative durations.

    :param duration_value: The CLI input string provided by the user.
    :param expected_output: The timedelta the input should resolve to.
    :return: None
    """
    runner = CliRunner()

    result = runner.invoke(make_cli(), ["--duration", duration_value])

    assert result.exit_code == 0
    assert result.output.strip() == repr(expected_output)


@pytest.mark.parametrize(
    "invalid_input",
    [
        "",  # empty
        "P",  # designator with no components
        "PT",  # time designator with no components
        "P1M",  # months have no fixed length
        "P1Y",  # years have no fixed length
        "PT1H2S3M",  # components out of order
        "12:15",  # seconds missing
        "12:15:3",  # seconds not two digits
        "1:2:3.5x",  # trailing garbage
        "12h15m",  # not ISO, not clock
        "44130.5",  # bare number
    ],
)
def test_timedelta_invalid_value(invalid_input: str) -> None:
    """
    Verify that `Timedelta` rejects malformed or unsupported durations with
    a non-zero exit code and a helpful error message.

    :param invalid_input: A malformed or unsupported CLI argument.
    :return: None
    """
    runner = CliRunner()

    result = runner.invoke(make_cli(), ["--duration", invalid_input])

    assert result.exit_code != 0
    assert "is not a valid duration" in result.output
    assert "PT1H30M5.5S" in result.output


def test_timedelta_default_string() -> None:
    """
    Verify that a string default is converted through the param type,
    so the command receives a `timedelta` rather than the raw string.

    :return: None
    """
    runner = CliRunner()

    @click.command()
    @click.option("--duration", type=Timedelta, default="PT12H15M30.5S")
    def cli(duration: timedelta) -> None:
        click.echo(repr(duration))

    result = runner.invoke(cli, [])

    assert result.exit_code == 0
    assert result.output.strip() == repr(EXAMPLE)


def test_timedelta_default_timedelta_instance() -> None:
    """
    Verify that a `timedelta` default is passed through unchanged, which
    also covers `convert` being handed an already-converted value.

    :return: None
    """
    runner = CliRunner()

    @click.command()
    @click.option("--duration", type=Timedelta, default=EXAMPLE)
    def cli(duration: timedelta) -> None:
        click.echo(repr(duration))

    result = runner.invoke(cli, [])

    assert result.exit_code == 0
    assert result.output.strip() == repr(EXAMPLE)


def test_timedelta_metavar_in_help() -> None:
    """
    Verify that the param type's name appears as the metavar in help output.

    :return: None
    """
    runner = CliRunner()

    result = runner.invoke(make_cli(), ["--help"])

    assert result.exit_code == 0
    assert "--duration DURATION" in result.output


@pytest.mark.parametrize(
    "value",
    [EXAMPLE, -EXAMPLE, timedelta(0), timedelta(days=10, seconds=1), timedelta(milliseconds=1)],
)
def test_to_iso_round_trips_through_param_type(value: timedelta) -> None:
    """
    Verify that generated ISO 8601 strings are accepted by `Timedelta` and
    parse back to the original value, covering sign, day, and sub-second
    components together.

    :param value: The timedelta to round-trip.
    :return: None
    """
    assert Timedelta.convert(to_iso(value), None, None) == value
