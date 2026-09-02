"""Runs against a live Postgres — the local docker-compose instance, already
seeded with real hotel data by pipelines-prefect/flows/hotels_ingest_flow.py.
"""

import pytest
from sqlalchemy import text

from src.db import get_engine, search_hotels_query


@pytest.mark.integration
def test_search_hotels_returns_results_for_a_seeded_city():
    results = search_hotels_query("paris")

    assert results
    assert all(hotel["city_slug"] == "paris" for hotel in results)
    for hotel in results:
        assert hotel["rooms"], "every returned hotel should have at least one available room"


@pytest.mark.integration
def test_search_hotels_filters_by_max_price():
    results = search_hotels_query("paris", max_price=400.0)

    assert results
    for hotel in results:
        for room in hotel["rooms"]:
            assert room["price"] <= 400.0


@pytest.mark.integration
def test_search_hotels_filters_by_min_stars():
    results = search_hotels_query("paris", min_stars=5)

    assert results
    assert all(hotel["star_rating"] >= 5 for hotel in results)


@pytest.mark.integration
def test_search_hotels_amenities_filter_requires_all_not_any():
    all_paris = search_hotels_query("paris")
    with_both = search_hotels_query("paris", amenities=["pool", "spa"])

    assert len(with_both) <= len(all_paris)
    for hotel in with_both:
        assert "pool" in hotel["amenities"]
        assert "spa" in hotel["amenities"]


@pytest.mark.integration
def test_search_hotels_returns_empty_for_unknown_city():
    assert search_hotels_query("nowhereland") == []


@pytest.mark.integration
def test_search_hotels_injection_attempt_returns_empty_and_leaves_table_intact():
    malicious = "'; DROP TABLE hotels; --"

    results = search_hotels_query(malicious)
    assert results == []

    # The table must still exist and still have real rows in it.
    engine = get_engine()
    with engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM hotels")).scalar()
    assert count > 0
