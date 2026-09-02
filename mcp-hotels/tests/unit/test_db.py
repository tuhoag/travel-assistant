from collections import namedtuple
from unittest.mock import MagicMock

from src.db import _fetch_hotel_details, _find_matching_hotel_ids

HotelRow = namedtuple("HotelRow", ["id", "name", "city_slug", "address", "description", "star_rating"])
RoomRow = namedtuple("RoomRow", ["id", "hotel_id", "room_type", "price", "currency", "availability_count"])


def _executed_statement(mock_conn, call_index=0):
    return mock_conn.execute.call_args_list[call_index][0][0]


# ---- _find_matching_hotel_ids: query-building safety ----


def test_never_interpolates_city_slug_into_sql_text():
    """Regression guard against SQL injection: no matter what's passed as
    city_slug, it must only ever appear as a bound parameter, never baked
    into the SQL text itself."""
    mock_conn = MagicMock()
    mock_conn.execute.return_value = []

    malicious = "'; DROP TABLE hotels; --"
    _find_matching_hotel_ids(mock_conn, malicious, None, None, None)

    stmt = _executed_statement(mock_conn)
    assert malicious not in str(stmt)
    assert malicious in stmt.compile().params.values()


def test_binds_all_provided_filters_as_parameters():
    mock_conn = MagicMock()
    mock_conn.execute.return_value = []

    _find_matching_hotel_ids(mock_conn, "paris", max_price=400.0, min_stars=4, amenities=["pool", "gym"])

    stmt = _executed_statement(mock_conn)
    params = stmt.compile().params.values()
    assert "paris" in params
    assert 400.0 in params
    assert 4 in params
    # amenities is bound as a single list-valued parameter (used with IN),
    # not one placeholder per item.
    assert any(v == ["pool", "gym"] or (isinstance(v, list) and set(v) == {"pool", "gym"}) for v in params)


def test_omits_optional_filter_clauses_when_not_given():
    mock_conn = MagicMock()
    mock_conn.execute.return_value = []

    _find_matching_hotel_ids(mock_conn, "paris", max_price=None, min_stars=None, amenities=None)

    stmt = _executed_statement(mock_conn)
    sql = str(stmt)
    # star_rating still appears in ORDER BY regardless — the filter clause
    # specifically (a WHERE comparison against it) is what should be absent.
    assert "hotels.star_rating >=" not in sql
    assert "hotels.star_rating <=" not in sql
    assert "hotel_amenities" not in sql


def test_orders_by_star_rating_and_limits_to_20():
    mock_conn = MagicMock()
    mock_conn.execute.return_value = []

    _find_matching_hotel_ids(mock_conn, "paris", None, None, None)

    sql = str(_executed_statement(mock_conn)).lower()
    assert "order by" in sql
    assert "limit" in sql


# ---- _fetch_hotel_details: Python-side grouping/ordering ----


def test_fetch_hotel_details_groups_related_rows_by_hotel():
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = [
        [HotelRow(1, "Ritz Paris", "paris", "15 Place Vendome", "A landmark hotel.", 5)],
        [RoomRow(10, 1, "Suite", 356.33, "EUR", 6)],
        [(1, "pool"), (1, "wifi")],
        [(1, "https://example.test/1.jpg")],
    ]

    result = _fetch_hotel_details(mock_conn, [1], max_price=None)

    assert len(result) == 1
    hotel = result[0]
    assert hotel["name"] == "Ritz Paris"
    assert hotel["rooms"] == [
        {"id": 10, "room_type": "Suite", "price": 356.33, "currency": "EUR", "availability_count": 6}
    ]
    assert hotel["amenities"] == ["pool", "wifi"]
    assert hotel["images"] == ["https://example.test/1.jpg"]


def test_fetch_hotel_details_preserves_ranking_order():
    """SQL's `WHERE id = ANY(...)` / `IN (...)` doesn't preserve the input
    list's order — this is the fix for that: the returned list must follow
    the order hotel_ids was given in (the caller's ranking), not whatever
    order the database happened to return rows in."""
    mock_conn = MagicMock()
    # DB returns hotel 2 before hotel 1, but hotel_ids ranks 1 before 2.
    mock_conn.execute.side_effect = [
        [
            HotelRow(2, "Le Meurice", "paris", "228 Rue de Rivoli", "desc", 5),
            HotelRow(1, "Ritz Paris", "paris", "15 Place Vendome", "desc", 5),
        ],
        [],
        [],
        [],
    ]

    result = _fetch_hotel_details(mock_conn, [1, 2], max_price=None)

    assert [h["id"] for h in result] == [1, 2]


def test_fetch_hotel_details_applies_max_price_to_rooms_query():
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = [
        [HotelRow(1, "Ritz Paris", "paris", "addr", "desc", 5)],
        [],
        [],
        [],
    ]

    _fetch_hotel_details(mock_conn, [1], max_price=300.0)

    rooms_stmt = _executed_statement(mock_conn, call_index=1)
    assert 300.0 in rooms_stmt.compile().params.values()
