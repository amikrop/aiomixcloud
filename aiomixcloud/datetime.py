"""
Datetime formatting
~~~~~~~~~~~~~~~~~~~

This module contains functions about presenting datetimes
in various formats.  Specifically:

    - :func:`format_datetime`, returning a
      "YYYY-MM-DDTHH:MM:SSZ"-formatted datetime string out of a
      datetime-like value.

    - :func:`to_timestamp`, returning a UNIX timestamp out of a
      datetime-like value.

The datetime-like argument of those functions can be a
:class:`~datetime.datetime` object, a human-readable datetime string
or a timestamp.  Timezone-naive values will be treated as being in the
local timezone.  Result will be converted in UTC, if not already there.
"""

from datetime import datetime, timezone

import dateutil.parser
from dateutil.tz import tzlocal


def _as_utc(dt):
    """Convert and return given `dt` in UTC.  If it is timezone-naive,
    treat it as being in the local timezone.
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt = dt.replace(tzinfo=tzlocal())
    return dt.astimezone(timezone.utc)


def _to_datetime(value):
    """Return a :class:`~datetime.datetime` object out of a
    datetime-like `value`.  Raise :exc:`TypeError` on invalid argument.
    """
    if isinstance(value, datetime):
        # Already a datetime, turn it to UTC and return it.
        return _as_utc(value)

    try:
        # Try to parse it as a human-readable string.
        parsed = dateutil.parser.parse(value)
    except (TypeError, ValueError):
        # Try to treat it as a timestamp.
        try:
            value = int(value)
        except ValueError:
            message = 'expected datetime.datetime object, valid datetime ' \
                      'string or timestamp'
            raise TypeError(message) from None
        return datetime.fromtimestamp(value, timezone.utc)

    return _as_utc(parsed)


def format_datetime(value):
    """Return a datetime string in the "YYYY-MM-DDTHH:MM:SSZ" format,
    out of a datetime-like `value`.
    """
    iso = _to_datetime(value).isoformat()
    return f'{iso[:-6]}Z'


def to_timestamp(value):
    """Return a UNIX timestamp out of a datetime-like `value`."""
    timestamp = _to_datetime(value).timestamp()
    return int(timestamp)
