import unittest
from unittest.mock import patch

from game.timer import TimeControl
from game.types import Color


class TimeControlUnitTests(unittest.TestCase):
    def test_untimed_clock_reports_infinity_and_no_timeout(self):
        timer = TimeControl(0, 0)

        self.assertEqual(timer.get_time(Color.WHITE), float("inf"))
        self.assertFalse(timer.is_time_out(Color.WHITE))
        self.assertEqual(timer.format_time(Color.WHITE), "∞")

    @patch("game.timer.time.time")
    def test_start_update_and_increment_flow(self, mock_time):
        timer = TimeControl(1, 2)

        # start turn at t=100.0
        mock_time.return_value = 100.0
        timer.start_turn(Color.WHITE)

        # elapsed 5.5 seconds at update
        mock_time.side_effect = [105.5, 105.5]
        timer.update_time()
        self.assertAlmostEqual(timer.white_time, 54.5, places=2)

        # end turn applies increment and pauses
        mock_time.side_effect = [106.5, 106.5]
        timer.end_turn(Color.WHITE, apply_increment=True)
        self.assertAlmostEqual(timer.white_time, 55.5, places=2)
        self.assertTrue(timer.is_paused)

    def test_display_color_thresholds(self):
        timer = TimeControl(1, 0)
        timer.white_time = 25
        self.assertEqual(timer.get_display_color(Color.WHITE), (255, 255, 255))

        timer.white_time = 15
        self.assertEqual(timer.get_display_color(Color.WHITE), (255, 200, 50))

        timer.white_time = 8
        self.assertEqual(timer.get_display_color(Color.WHITE), (255, 50, 50))


if __name__ == "__main__":
    unittest.main()
