# Copyright 2023-2024 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Common methods to use in communication with external systems."""

import logging


def initialize_request_logging():
    """Make sure calls to request lib are logged."""
    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def strip_empty(data):
    """Strip all empty data from nested datastructure."""
    if isinstance(data, dict):
        return {k: strip_empty(v) for k, v in data.items() if k and v}
    if isinstance(data, list):
        return [strip_empty(item) for item in data if item]
    if isinstance(data, tuple):
        return tuple(strip_empty(item) for item in data if item)
    if isinstance(data, set):
        return {strip_empty(item) for item in data if item}
    return strip_empty_spaces(data)


def strip_empty_spaces(string):
    """Remove all whitespace from end of string like item."""
    if isinstance(string, str):
        return string.strip()
    return string
