"""
Uses enums to define different choices the user can make in your CLI.
"""

from enum import Enum
from typing import Callable, Optional, TypeVar

import click
from click import Context, Parameter
from click.decorators import FC

# A generic type variable for Enum subclasses, essentially any enum subclass.
E = TypeVar("E", bound=Enum)
T = TypeVar("T")


def create_enum_option(  # pylint: disable=too-many-positional-arguments
    arg_flag: str,
    help_message: str,
    default: E,
    input_enum: type[E],
    lookup_fn: Optional[Callable[[E], T]] = None,
    envvar: Optional[str] = None,
) -> Callable[[FC], FC]:
    """
    Creates a Click option for an Enum type. Resulting input can be given as an index or as the
    string value from the enum.

    :param arg_flag: The argument flag for the Click option (e.g., "--output").
    :param help_message: Will be included in the --help message alongside the acceptable inputs
    to the Enum.
    :param default: The default value for the Click option, must be a member of `input_enum`.
    :param lookup_fn: If given, the resolved value will be passed to this function, then the click
    command will get whatever is returned as an argument.
    :param input_enum: The Enum class from which the option values are derived.
    :param envvar: Passed to the click option.
    :return: A Click option configured for the specified Enum.
    """

    try:
        input_enum(default)
    except ValueError as e:
        raise ValueError("Default value was not a member of the enum!") from e

    options_string = "\n".join(
        [f"   {idx}: {enum_member.value}" for idx, enum_member in enumerate(input_enum)]
    )

    help_string = (
        f"\b\n{help_message}\nOptions below. Either provide index or value:\n{options_string}"
    )

    def callback(_ctx: Context, _param: Parameter, value: str) -> "T | E":
        enum_options = list(input_enum)
        try:
            # Try interpreting as an index
            index = int(value)
            if 0 <= index < len(enum_options):
                return enum_options[index]
            else:
                raise click.BadParameter(
                    f"Index out of range. Valid range: 0-{len(enum_options)-1}."
                )
        except ValueError:
            # If not an index, validate as a string
            try:
                resolved: E = input_enum(value)
                return lookup_fn(resolved) if lookup_fn else resolved
            except ValueError as e:
                valid_choices = ", ".join([e.value for e in enum_options])
                raise click.BadParameter(
                    "Invalid choice. "
                    f"Valid names: {valid_choices}, or indices 0-{len(enum_options)-1}."
                ) from e

    return click.option(
        arg_flag,
        type=click.STRING,
        callback=callback,
        help=help_string,
        default=default.value,  # Ensure we use the string value for the default
        show_default=True,
        envvar=envvar,
        show_envvar=True,
    )
