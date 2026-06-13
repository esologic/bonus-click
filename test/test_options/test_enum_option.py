"""
Unit tests for `create_enum_option` in `bonus_click.options`.

These tests cover both error conditions (invalid indices or enum names)
and happy paths (valid names, indices, multiple flags, and lookup functions).
Tests are parameterized where appropriate to ensure a variety of cases
are exercised without duplication.
"""

from enum import Enum
from typing import Tuple

import click
import pytest
from click.testing import CliRunner
from click_option_group import optgroup

from bonus_click.options import create_enum_option


class OutputFormat(Enum):
    """Mock enum used for testing the Click option generator."""

    JSON = "json"
    YAML = "yaml"
    TEXT = "text"


@pytest.mark.parametrize(
    "input_value,expected_output",
    [
        ("json", "json"),
        ("0", "json"),
        ("yaml", "yaml"),
        ("1", "yaml"),
        ("text", "text"),
        ("2", "text"),
    ],
)
def test_enum_option_accepts_name_and_index(input_value: str, expected_output: str) -> None:
    """
    Verify that `create_enum_option` correctly parses both exact string
    matches of the enum values and their corresponding integer indices.

    :param input_value: The CLI input string or index provided by the user.
    :param expected_output: The expected string value of the resolved enum.
    :return: None
    """
    runner = CliRunner()

    @click.command()
    @create_enum_option("--output-format", "Output format", OutputFormat)  # type: ignore[arg-type]
    def cli(output_format: OutputFormat) -> None:
        click.echo(output_format.value)

    result = runner.invoke(cli, ["--output-format", input_value])

    assert result.exit_code == 0
    assert result.output.strip() == expected_output


@pytest.mark.parametrize(
    "invalid_input,expected_match",
    [
        ("not_real", "Invalid choice. Valid names: json, yaml, text, or indices 0-2."),
        ("99", "Index out of range. Valid range: 0-2."),
    ],
)
def test_enum_option_invalid_value(invalid_input: str, expected_match: str) -> None:
    """
    Verify that `create_enum_option` raises appropriate CLI errors for
    invalid string names and out-of-bounds indices.

    :param invalid_input: A malformed or out-of-bounds CLI argument.
    :param expected_match: The expected substring in the error output.
    :return: None
    """
    runner = CliRunner()

    @click.command()
    @create_enum_option("--output-format", "Output format", OutputFormat)  # type: ignore[arg-type]
    def cli(output_format: OutputFormat) -> None:
        click.echo(output_format.value)

    result = runner.invoke(cli, ["--output-format", invalid_input])

    assert result.exit_code != 0
    assert expected_match in result.output


def test_enum_option_multiple() -> None:
    """
    Verify that when `multiple=True` is provided, the CLI option accepts
    multiple inputs and correctly parses them into a tuple of enums.

    :return: None
    """
    runner = CliRunner()

    @click.command()
    @create_enum_option(  # type: ignore[arg-type]
        "--output-format", "Output format", OutputFormat, multiple=True
    )
    def cli(output_format: Tuple[OutputFormat, ...]) -> None:
        click.echo(",".join(f.value for f in output_format))

    result = runner.invoke(cli, ["--output-format", "json", "--output-format", "yaml"])

    assert result.exit_code == 0
    assert result.output.strip() == "json,yaml"


def test_enum_option_with_lookup_fn() -> None:
    """
    Verify that if a `lookup_fn` is provided, the resolved enum value is
    passed through the lookup function before being passed to the CLI command.

    :return: None
    """
    runner = CliRunner()

    def lookup(e: OutputFormat) -> str:
        return f"LOOKUP:{e.value}"

    @click.command()
    @create_enum_option(
        "--output-format",
        "Output format",
        OutputFormat,
        lookup_fn=lookup,
    )
    def cli(output_format: str) -> None:
        click.echo(output_format)

    result = runner.invoke(cli, ["--output-format", "yaml"])

    assert result.exit_code == 0
    assert result.output.strip() == "LOOKUP:yaml"


def make_cli_with_optgroup() -> click.Command:
    """
    Helper function to generate a CLI command utilizing the optgroup factory.

    :return: A Click command decorated with the enum option via optgroup.
    """

    @optgroup.group("Output Options")
    @click.command()
    @create_enum_option(  # type: ignore[arg-type]
        "--output-format",
        "Output format",
        OutputFormat,
        option_factory=optgroup.option,
    )
    def cli(output_format: OutputFormat) -> None:
        click.echo(output_format.value)

    return cli


def make_cli_without_optgroup() -> click.Command:
    """
    Helper function to generate a CLI command utilizing standard click options,
    intentionally bypassing the optgroup factory for integration testing.

    :return: A Click command decorated with the standard enum option.
    """

    @optgroup.group("Output Options")
    @click.command()
    @create_enum_option(  # type: ignore[arg-type]
        "--output-format",
        "Output format",
        OutputFormat,
        option_factory=click.option,  # ❌ wrong on purpose
    )
    def cli(output_format: OutputFormat) -> None:
        click.echo(output_format.value)

    return cli


def test_both_clis_execute() -> None:
    """
    Verify that the enum option executes correctly regardless of the
    option factory used (optgroup vs standard click.option).

    :return: None
    """
    runner = CliRunner()

    cli_good = make_cli_with_optgroup()
    cli_bad = make_cli_without_optgroup()

    r1 = runner.invoke(cli_good, ["--output-format", "json"])
    r2 = runner.invoke(cli_bad, ["--output-format", "json"])

    assert r1.exit_code == 0
    assert r2.exit_code == 0

    assert r1.output.strip() == "json"
    assert r2.output.strip() == "json"


def test_optgroup_integration_behavior() -> None:
    """
    Verify that help messages generate correctly when comparing standard
    click options against click-option-group integrated options.

    :return: None
    """
    runner = CliRunner()

    cli_good = make_cli_with_optgroup()
    cli_bad = make_cli_without_optgroup()

    good_help = runner.invoke(cli_good, ["--help"])
    bad_help = runner.invoke(cli_bad, ["--help"])

    assert good_help.exit_code == 0
    assert bad_help.exit_code == 0

    assert "Output Options" in good_help.output
