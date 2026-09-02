"""Postgres access for hotel search via SQLAlchemy Core. Queries are built
with the expression language (select/where), never raw/string-interpolated
SQL, so every value is parameterized automatically — no free-form or
LLM-generated SQL, no injection surface.
"""

from __future__ import annotations

import json

import boto3
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    and_,
    create_engine,
    desc,
    exists,
    func,
    select,
)
from sqlalchemy.engine import Engine

from . import config

metadata = MetaData()

# Mirrors pipelines-prefect/flows/hotels_schema.sql — this module only reads,
# it doesn't create or migrate the schema (ingestion owns that).
hotels_table = Table(
    "hotels",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
    Column("city_slug", String),
    Column("address", String),
    Column("description", String),
    Column("star_rating", Integer),
)

amenities_table = Table(
    "amenities",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
)

hotel_amenities_table = Table(
    "hotel_amenities",
    metadata,
    Column("hotel_id", Integer, primary_key=True),
    Column("amenity_id", Integer, primary_key=True),
)

rooms_table = Table(
    "rooms",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("hotel_id", Integer),
    Column("room_type", String),
    Column("price", Numeric(10, 2)),
    Column("currency", String),
    Column("availability_count", Integer),
)

hotel_images_table = Table(
    "hotel_images",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("hotel_id", Integer),
    Column("url", String),
    Column("position", Integer),
)

_engine: Engine | None = None


def _fetch_credentials() -> tuple[str, str]:
    # Local dev (docker-compose Postgres): plain env credentials, no AWS call.
    if config.PGUSER and config.PGPASSWORD:
        return config.PGUSER, config.PGPASSWORD

    # Production (real RDS): fetch from the RDS-managed Secrets Manager secret.
    if not config.HOTELS_DB_SECRET_ARN:
        raise RuntimeError("Neither PGUSER/PGPASSWORD nor HOTELS_DB_SECRET_ARN is set (see .env)")

    secrets_client = boto3.client("secretsmanager", region_name=config.AWS_REGION)
    secret = json.loads(secrets_client.get_secret_value(SecretId=config.HOTELS_DB_SECRET_ARN)["SecretString"])
    return secret["username"], secret["password"]


def get_engine() -> Engine:
    """SQLAlchemy engine, created once on first use — its connection pool
    replaces the ingestion flow's one-shot-per-run connection, since this
    is a long-running service."""
    global _engine
    if _engine is None:
        username, password = _fetch_credentials()
        url = (
            f"postgresql+psycopg://{username}:{password}"
            f"@{config.PGHOST}:{config.PGPORT}/{config.PGDATABASE}"
        )
        _engine = create_engine(url, pool_size=5, pool_pre_ping=True)
    return _engine


def search_hotels_query(
    city_slug: str,
    max_price: float | None = None,
    min_stars: int | None = None,
    amenities: list[str] | None = None,
) -> list[dict]:
    """Search hotels in a city, optionally filtered by max room price
    (only rooms with availability_count > 0 and price <= max_price are
    included/counted), minimum star rating, and required amenities (a
    hotel must have ALL of them). Up to 20 hotels, best-rated first."""
    engine = get_engine()
    with engine.connect() as conn:
        hotel_ids = _find_matching_hotel_ids(conn, city_slug, max_price, min_stars, amenities)
        if not hotel_ids:
            return []
        return _fetch_hotel_details(conn, hotel_ids, max_price)


def _find_matching_hotel_ids(
    conn,
    city_slug: str,
    max_price: float | None,
    min_stars: int | None,
    amenities: list[str] | None,
) -> list[int]:
    h = hotels_table
    r = rooms_table

    stmt = select(h.c.id).where(h.c.city_slug == city_slug)

    if min_stars is not None:
        stmt = stmt.where(h.c.star_rating >= min_stars)

    room_conditions = [r.c.hotel_id == h.c.id, r.c.availability_count > 0]
    if max_price is not None:
        room_conditions.append(r.c.price <= max_price)
    stmt = stmt.where(exists(select(1).where(and_(*room_conditions))))

    if amenities:
        ha = hotel_amenities_table
        a = amenities_table
        matching_amenity_count = (
            select(func.count(func.distinct(ha.c.amenity_id)))
            .select_from(ha.join(a, a.c.id == ha.c.amenity_id))
            .where(and_(ha.c.hotel_id == h.c.id, a.c.name.in_(amenities)))
            .scalar_subquery()
        )
        stmt = stmt.where(matching_amenity_count == len(amenities))

    stmt = stmt.order_by(desc(h.c.star_rating), h.c.name).limit(20)

    return [row.id for row in conn.execute(stmt)]


def _fetch_hotel_details(conn, hotel_ids: list[int], max_price: float | None) -> list[dict]:
    h = hotels_table
    hotels_by_id = {
        row.id: {
            "id": row.id,
            "name": row.name,
            "city_slug": row.city_slug,
            "address": row.address,
            "description": row.description,
            "star_rating": row.star_rating,
            "rooms": [],
            "amenities": [],
            "images": [],
        }
        for row in conn.execute(select(h).where(h.c.id.in_(hotel_ids)))
    }

    r = rooms_table
    room_stmt = select(r).where(r.c.hotel_id.in_(hotel_ids), r.c.availability_count > 0)
    if max_price is not None:
        room_stmt = room_stmt.where(r.c.price <= max_price)
    room_stmt = room_stmt.order_by(r.c.price)
    for row in conn.execute(room_stmt):
        hotels_by_id[row.hotel_id]["rooms"].append({
            "id": row.id,
            "room_type": row.room_type,
            "price": float(row.price),
            "currency": row.currency,
            "availability_count": row.availability_count,
        })

    ha = hotel_amenities_table
    a = amenities_table
    amenity_stmt = (
        select(ha.c.hotel_id, a.c.name)
        .select_from(ha.join(a, a.c.id == ha.c.amenity_id))
        .where(ha.c.hotel_id.in_(hotel_ids))
        .order_by(a.c.name)
    )
    for hotel_id, name in conn.execute(amenity_stmt):
        hotels_by_id[hotel_id]["amenities"].append(name)

    img = hotel_images_table
    image_stmt = (
        select(img.c.hotel_id, img.c.url)
        .where(img.c.hotel_id.in_(hotel_ids))
        .order_by(img.c.position)
    )
    for hotel_id, url in conn.execute(image_stmt):
        hotels_by_id[hotel_id]["images"].append(url)

    # `IN` doesn't preserve input order — re-apply the ranking from
    # _find_matching_hotel_ids.
    return [hotels_by_id[hid] for hid in hotel_ids if hid in hotels_by_id]
