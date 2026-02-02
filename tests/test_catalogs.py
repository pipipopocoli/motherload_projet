import unittest

import pandas as pd

from motherload_projet.catalogs.exporters import assign_citekeys
from motherload_projet.catalogs.scoring import CompletenessConfig, is_complete
from motherload_projet.catalogs.scanner import _apply_preprint_replacements


class CatalogTests(unittest.TestCase):
    def test_citekey_collision(self) -> None:
        df = pd.DataFrame(
            [
                {"authors": "Smith, John", "year": "2020", "type": "article"},
                {"authors": "Smith, John", "year": "2020", "type": "article"},
            ]
        )
        keys = assign_citekeys(df)
        self.assertEqual(keys[0], "Smith_2020")
        self.assertEqual(keys[1], "Smith_2020_2")

    def test_completeness_article(self) -> None:
        cfg = CompletenessConfig()
        entry = {
            "type": "article",
            "title": "T",
            "authors": "A",
            "year": "2020",
            "doi": "10.1/xyz",
        }
        self.assertTrue(is_complete(entry, cfg))
        entry2 = {
            "type": "article",
            "title": "T",
            "authors": "A",
            "year": "2020",
            "journal": "J",
            "volume": "1",
            "issue": "2",
            "pages": "1-2",
        }
        self.assertTrue(is_complete(entry2, cfg))
        entry3 = {
            "type": "article",
            "title": "T",
            "authors": "A",
            "year": "",
            "doi": "10.1/xyz",
        }
        self.assertFalse(is_complete(entry3, cfg))

    def test_preprint_replacement(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "fingerprint": "t|smith|2020",
                    "primary_id": "doi:10.1/xyz",
                    "version": "final",
                    "type": "article",
                },
                {
                    "fingerprint": "t|smith|2020",
                    "primary_id": "doi:10.2/abc",
                    "version": "preprint",
                    "type": "article",
                },
            ]
        )
        updated = _apply_preprint_replacements(df)
        self.assertEqual(updated.loc[1, "replaced_by"], "doi:10.1/xyz")


if __name__ == "__main__":
    unittest.main()
