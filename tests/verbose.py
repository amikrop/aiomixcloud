import unittest


class VerboseTestCase(unittest.TestCase):
    """Testcase that shows the whole docstring of failing
    test methods.
    """

    def shortDescription(self):
        """Take the whole currently tested method's docstring, strip
        leading whitespace from each of its lines and return the
        concatenated result, leaving out the last, blank, line.
        """
        lines = [line.lstrip() for line in self._testMethodDoc.splitlines()]
        return '\n'.join(lines[:-1])
