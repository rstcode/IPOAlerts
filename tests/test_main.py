import unittest

from main import normalize_gmp_payload


class NormalizeGmpPayloadTests(unittest.TestCase):
    def test_normalizes_ipocentral_payload(self):
        payload = {
            "MB": [
                {
                    "name": "Behari Lal Engineering",
                    "url": "https://ipocentral.in/behari-lal-engineering-ipo-gmp-price-date-details/",
                    "date": "(12 - 14 Aug)",
                    "gmpText": "30 11%",
                    "num": "30",
                    "pct": "11%",
                    "state": "up",
                }
            ],
            "SME": [
                {
                    "name": "Optimystix Entertainment",
                    "url": "https://ipocentral.in/optimystix-entertainment-ipo-gmp-price-allotment/",
                    "date": "(7 - 11 Aug)",
                    "gmpText": "7 4%",
                    "num": "7",
                    "pct": "4%",
                    "state": "up",
                }
            ],
        }

        parsed = normalize_gmp_payload(payload)

        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]["company_short_name"], "Behari Lal Engineering")
        self.assertEqual(parsed[0]["gmp"], "30")
        self.assertEqual(parsed[0]["gmp_percent_calc"], "11")
        self.assertEqual(parsed[0]["ipo_status"], "Upcoming")
        self.assertEqual(parsed[0]["issue_open_dt"].startswith("2026"), False)
        self.assertEqual(parsed[0]["issue_end_dt"].startswith("2026"), False)
        self.assertEqual(parsed[1]["company_short_name"], "Optimystix Entertainment")
        self.assertEqual(parsed[1]["gmp_percent_calc"], "4")


if __name__ == "__main__":
    unittest.main()
