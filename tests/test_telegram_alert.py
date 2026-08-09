import unittest

from telegram_alert import format_telegram_message


class FormatTelegramMessageTests(unittest.TestCase):
    def test_uses_saved_history_for_yesterday_to_today_gmp_change(self):
        categories = {
            "last_day": [
                {
                    "company_short_name": "Example IPO",
                    "issue_open_dt": "2026-08-10T00:00:00.000Z",
                    "issue_end_dt": "2026-08-14T00:00:00.000Z",
                    "ipo_price": "100",
                    "gmp": "100",
                    "gmp_percent_calc": "25",
                    "url": "https://example.com/ipo",
                }
            ],
            "open_now": [],
            "upcoming": [],
        }
        history = {"Example IPO": {"last_gmp_percent": 23.0}}

        message = format_telegram_message(categories, history)

        self.assertIn("Yesterday → Today GMP", message)
        self.assertIn("23.0% → 25.0%", message)
        self.assertIn("+2.0%", message)
        self.assertIn("https://example.com/ipo", message)


if __name__ == "__main__":
    unittest.main()
