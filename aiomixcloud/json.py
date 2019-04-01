"""
JSON decoder
~~~~~~~~~~~~

This module contains the class responsible for decoding the JSON data
retrieved from the API requests.  Specifically:

    - :class:`MixcloudJSONDecoder`, turning datetime-like strings
      to :class:`~datetime.datetime` objects.
"""

from json import JSONDecoder

import dateutil.parser


class MixcloudJSONDecoder(JSONDecoder):
    """Handles datetime values."""

    def __init__(self, *args, **kwargs):
        """Pass custom object hook to super's `__init__`."""
        super().__init__(*args, object_hook=self.object_hook, **kwargs)

    @staticmethod
    def object_hook(obj):
        """Turn eligible values to :class:`~datetime.datetime`
        objects and leave the rest unchanged.
        """
        result = {}
        for k, v in obj.items():
            try:
                value = dateutil.parser.parse(v)
            except (TypeError, ValueError):
                # Not a datetime-like string, just keep original value.
                value = v
            result[k] = value
        return result
