from motherload_projet.data_mining.recuperation_article.run_unpaywall_batch import (
    _normalize_doi,
)


def test_normalize_doi_strips_prefixes() -> None:
    assert _normalize_doi("https://doi.org/10.1000/xyz") == "10.1000/xyz"
    assert _normalize_doi("http://doi.org/10.1000/xyz") == "10.1000/xyz"
    assert _normalize_doi("doi:10.1000/xyz") == "10.1000/xyz"
    assert _normalize_doi(" 10.1000/xyz ") == "10.1000/xyz"


def test_normalize_doi_handles_missing() -> None:
    assert _normalize_doi(None) == ""
    assert _normalize_doi("") == ""
    assert _normalize_doi("nan") == ""
    assert _normalize_doi(float("nan")) == ""
