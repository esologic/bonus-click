# Changelog

## Roadmap

* Easy log config decorator.
* Click types for `HH:MM:SS` timedelta strings.

## Versions

### 0.4.0 - (2026-06-13)

* The function `create_enum_option` now accepts an `option_factory` arg to support passing in other
option sources, like those from `click_option_group`.


### 0.3.0 - (2026-01-14)

* Adds optional `None` defaults in `create_enum_option` and the corresponding similar logic for the
multiple case.


### 0.2.1 - (2026-01-12)

* Allows `multiple` to be configured in the enum option.


### 0.1.0 - (2025-11-13)

* Project created and published.
* Implements `create_enum_option` for going from an `Enum` to a series of different click choices.
