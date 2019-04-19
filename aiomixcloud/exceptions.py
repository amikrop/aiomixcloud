"""
Exception types
~~~~~~~~~~~~~~~

This module contains custom exceptions raised during use
of the package.  Specifically:

    - :class:`MixcloudError`, indicating that API returned
      an error response.

    - :class:`MixcloudOAuthError`, indicating that something
      went wrong with the OAuth authorization process.
"""


class MixcloudError(Exception):
    """Raised when API responds with error message."""

    def __init__(self, data):
        """Store information as instance attributes."""
        info = data.get('error', {})
        #: Error type, as described by the API
        self.type = info.pop('type', '')
        #: Error message
        self.message = info.pop('message', '')
        #: Dictionary with additional information
        self.extra = info

    def __str__(self):
        """Return type, message and additional information,
        formatted appropriately.
        """
        # Build presentation of extra information.
        extra_items = []
        for k, v in self.extra.items():
            if v:
                extra_items.append(f'{k}: {v}')
        extra = ', '.join(extra_items)

        # Add available parts to error message, each with its
        # appropriate format.
        error_message = []
        if self.message:
            error_message.append(self.message)
        if extra:
            error_message.append(f'({extra})')
        if self.type:
            type = self.type
            if error_message:
                # If there are more parts than just `type`,
                # append a colon to it.
                type = f'{type}:'
            error_message.insert(0, type)

        return ' '.join(error_message)


class MixcloudOAuthError(Exception):
    """Raised when OAuth authorization fails."""

    def __init__(self, data):
        """Store error message as instance attribute."""
        #: Error message
        self.message = data.get('error', '')

    def __str__(self):
        """Return error message."""
        return self.message
