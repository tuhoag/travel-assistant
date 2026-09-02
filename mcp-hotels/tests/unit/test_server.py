from unittest.mock import patch

from src.server import _slugify_city, search_hotels


def test_slugify_city_lowercases_and_joins_with_underscores():
    assert _slugify_city("Paris") == "paris"
    assert _slugify_city("Washington DC") == "washington_dc"


def test_slugify_city_strips_punctuation():
    assert _slugify_city("Washington, D.C.") == "washington_dc"


def test_slugify_city_collapses_extra_whitespace():
    assert _slugify_city("  New   York  ") == "new_york"


def test_search_hotels_slugifies_city_before_querying_db():
    with patch("src.server.db.search_hotels_query") as mock_query:
        mock_query.return_value = []
        search_hotels(city="Washington, D.C.", max_price=300.0, min_stars=4, amenities=["pool"])

    mock_query.assert_called_once_with(
        city_slug="washington_dc", max_price=300.0, min_stars=4, amenities=["pool"]
    )


def test_search_hotels_returns_db_results_unchanged():
    fake_hotels = [{"id": 1, "name": "Ritz Paris"}]
    with patch("src.server.db.search_hotels_query", return_value=fake_hotels):
        result = search_hotels(city="Paris")

    assert result == fake_hotels
