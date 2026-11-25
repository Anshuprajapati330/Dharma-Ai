import unittest
from unittest.mock import patch

from daily_wisdom import get_daily_wisdom


class DailyWisdomTests(unittest.TestCase):
    @patch(
        "daily_wisdom._load_wisdom_items",
        return_value=(
            {"key": "first", "english": "First", "hindi": "पहला", "reference": "Source 1"},
            {"key": "second", "english": "Second", "hindi": "दूसरा", "reference": "Source 2"},
        ),
    )
    def test_next_wisdom_excludes_previous_quote(self, _load_items):
        wisdom = get_daily_wisdom({"key": "first"})

        self.assertEqual(wisdom["key"], "second")


if __name__ == "__main__":
    unittest.main()