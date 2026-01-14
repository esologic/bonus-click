"""
Uses enums to define different choices the user can make in your CLI.
"""

from enum import Enum
from typing import Callable, Optional, Tuple, TypeVar, Union, cast

import click
from click import Context, Parameter
from click.decorators import FC

E = TypeVar("E", bound=Enum)
T = TypeVar("T")

ClickDefault = Optional[Union[str, int, Tuple[Union[str, int], ...]]]


def create_enum_option(  # pylint: disable=too-many-positional-arguments
    arg_flag: str,
    help_message: str,
    input_enum: type[E],
    default: Optional[E] = None,
    multiple: bool = False,
    envvar: Optional[str] = None,
    lookup_fn: Optional[Callable[[E], T]] = None,
) -> Callable[[FC], FC]:
    """
    Creates a Click option for an Enum type. Inputs may be given as either the
    enum's value or its index.

    If ``multiple`` is False:
        - Option omitted  -> None
        - Option provided -> E or T

    If ``multiple`` is True:
        - Option omitted  -> ()
        - Option provided -> tuple[E | T, ...]

    :param arg_flag: The argument flag for the Click option (e.g., "--output").
    :param help_message: Will be included in the --help message alongside the acceptable inputs
    to the Enum.
    :param default: The default value for the Click option, must be a member of `input_enum` or
    `None`.
    :param input_enum: The Enum class from which the option values are derived.
    :param multiple: If given, the corresponding `multiple` flag will be set in the output option,
    allowing the option to be given multiple times.
    :param envvar: Passed to the click option.
    :param lookup_fn: If given, the resolved value will be passed to this function, then the click
    command will get whatever is returned as an argument.
    :return: A Click option configured for the specified Enum.
    """

    if default is not None:
        try:
            input_enum(default)
        except ValueError as exc:
            raise ValueError("Default value was not a member of the enum") from exc

    enum_options = list(input_enum)

    options_string = "\n".join(
        f"   {idx}: {member.value}" for idx, member in enumerate(enum_options)
    )

    help_string = (
        f"\b\n{help_message}\nOptions below. Either provide index or value:\n{options_string}"
    )

    def convert_single_value(value: str | int) -> "T | E":
        """
        Performs a single conversion from the input to the output enum.
        :param value: Either the index or the string version of the enum.
        :return: Input in it's enum form.
        """
        try:
            index = int(value)
            if 0 <= index < len(enum_options):
                resolved: E = enum_options[index]
            else:
                raise click.BadParameter(
                    f"Index out of range. Valid range: 0-{len(enum_options) - 1}."
                )
        except ValueError:
            try:
                resolved = input_enum(value)
            except ValueError as e:
                valid_choices = ", ".join([e.value for e in enum_options])
                raise click.BadParameter(
                    "Invalid choice. "
                    f"Valid names: {valid_choices}, or indices 0-{len(enum_options) - 1}."
                ) from e

        return lookup_fn(resolved) if lookup_fn else resolved

    def callback(
        _ctx: Context,
        _param: Parameter,
        value: Union[str | int, Tuple[str | int, ...], None],
    ) -> Union[E, T, Tuple[Union[E, T], ...], None]:
        """
        Callback to decorate the input and create the function.
        :param _ctx: Unused.
        :param _param: Unused.
        :param value: To convert.
        :return: Converted value or values.
        """

        if multiple:
            values = cast(Tuple[str | int, ...], value or ())
            return tuple(convert_single_value(v) for v in values)

        if value is None:
            return None

        return convert_single_value(cast(str | int, value))

    if default is None:
        click_default: ClickDefault = None if not multiple else ()
    else:
        click_default = (default.value,) if multiple else default.value

    return click.option(
        arg_flag,
        type=click.STRING,
        callback=callback,
        help=help_string,
        default=click_default,
        envvar=envvar,
        multiple=multiple,
        show_default=default is not None,
        show_envvar=True,
    )
