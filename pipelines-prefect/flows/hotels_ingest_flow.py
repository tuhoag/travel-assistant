"""
Hotels to Postgres ingestion — Prefect version.

Six tasks:
    1. connect            — fetch DB credentials from Secrets Manager, connect
                             to Postgres, apply hotels_schema.sql
    2. extract_hotel_data — read all data/hotels/*.csv seed files
    3. upload_images       — upload each local hotel image to S3 (skipping
                             ones already there), rewrite each row's url to
                             the public S3 URL
    4. ingest_hotel_data   — upsert every table in FK-safe order, using the
                             explicit ids already assigned in the CSVs
    5. report_results      — print rows-upserted per table
    6. disconnect          — close the connection

Auth is AWS SigV4/boto3's default credential chain for both Secrets Manager
and S3 — no static DB password or AWS keys anywhere in this file or .env,
matching cities_ingest_flow.py's approach. You need valid AWS credentials
active (e.g. `aws sso login`) before running this.

Usage:
    uv run flows/hotels_ingest_flow.py
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from prefect import flow, task
from prefect.cache_policies import NO_CACHE
from prefect.logging import get_run_logger

REPO_ROOT = Path(__file__).resolve().parents[2]

# Loads the repo-root .env if present, without overriding vars already set
# in the shell.
load_dotenv(REPO_ROOT / ".env")

HOTELS_DATA_DIR = Path(os.environ.get("HOTELS_DATA_DIR", REPO_ROOT / "data" / "hotels"))
SCHEMA_FILE = Path(__file__).resolve().parent / "hotels_schema.sql"

AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")
PGHOST = os.environ.get("PGHOST", "localhost")
PGPORT = os.environ.get("PGPORT", "5432")
PGDATABASE = os.environ.get("PGDATABASE", "hotels")
HOTELS_DB_SECRET_ARN = os.environ.get("HOTELS_DB_SECRET_ARN")  # RDS-managed secret ARN
ASSETS_BUCKET_NAME = os.environ.get("ASSETS_BUCKET_NAME")
ASSETS_IMAGE_PREFIX = "hotels/images/"


@task(retries=1, retry_delay_seconds=5, cache_policy=NO_CACHE)
def connect():
    """Fetch DB credentials from Secrets Manager, connect to Postgres, apply the schema."""
    import boto3
    import psycopg

    logger = get_run_logger()

    if not HOTELS_DB_SECRET_ARN:
        raise RuntimeError("HOTELS_DB_SECRET_ARN is not set (see .env)")

    secrets_client = boto3.client("secretsmanager", region_name=AWS_REGION)
    secret = json.loads(secrets_client.get_secret_value(SecretId=HOTELS_DB_SECRET_ARN)["SecretString"])

    conn = psycopg.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=secret["username"],
        password=secret["password"],
        connect_timeout=10,
    )
    conn.execute(SCHEMA_FILE.read_text())
    conn.commit()

    logger.info(f"Connected to Postgres at {PGHOST}:{PGPORT}/{PGDATABASE}, schema applied")
    return conn


@task(retries=1, retry_delay_seconds=5)
def extract_hotel_data() -> dict[str, list[dict]]:
    """Read all hotel seed CSVs from data/hotels/."""

    def read_csv(filename: str) -> list[dict]:
        with open(HOTELS_DATA_DIR / filename, newline="") as f:
            return list(csv.DictReader(f))

    return {
        "amenities": read_csv("amenities.csv"),
        "hotels": read_csv("hotels.csv"),
        "hotel_amenities": read_csv("hotel_amenities.csv"),
        "rooms": read_csv("rooms.csv"),
        "hotel_images": read_csv("hotel_images.csv"),
    }


@task(retries=1, retry_delay_seconds=5)
def upload_images(hotel_images: list[dict]) -> list[dict]:
    """Upload each local hotel image to S3 (skip if already there); return
    the rows with `url` rewritten to the public S3 URL."""
    import boto3
    from botocore.exceptions import ClientError

    logger = get_run_logger()

    if not ASSETS_BUCKET_NAME:
        raise RuntimeError("ASSETS_BUCKET_NAME is not set (see .env)")

    s3 = boto3.client("s3", region_name=AWS_REGION)
    uploaded = 0
    updated_rows = []

    for row in hotel_images:
        local_path = HOTELS_DATA_DIR / row["url"]
        key = f"{ASSETS_IMAGE_PREFIX}{local_path.name}"

        try:
            s3.head_object(Bucket=ASSETS_BUCKET_NAME, Key=key)
            already_uploaded = True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                already_uploaded = False
            else:
                raise

        if not already_uploaded:
            s3.upload_file(str(local_path), ASSETS_BUCKET_NAME, key, ExtraArgs={"ContentType": "image/jpeg"})
            uploaded += 1

        updated_rows.append({
            **row,
            "url": f"https://{ASSETS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}",
        })

    logger.info(f"Uploaded {uploaded} new images, {len(updated_rows) - uploaded} already present")
    return updated_rows


@task(retries=1, retry_delay_seconds=5, cache_policy=NO_CACHE)
def ingest_hotel_data(conn, data: dict[str, list[dict]]) -> dict[str, int]:
    """Upsert every table in FK-safe order, using the explicit ids already
    assigned in the CSVs (child tables reference hotels.id directly)."""
    logger = get_run_logger()
    counts = {}

    with conn.cursor() as cur:
        for row in data["amenities"]:
            cur.execute(
                """
                INSERT INTO amenities (id, name) VALUES (%s, %s)
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                """,
                (row["id"], row["name"]),
            )
        counts["amenities"] = len(data["amenities"])

        for row in data["hotels"]:
            cur.execute(
                """
                INSERT INTO hotels (id, name, city_slug, address, description, star_rating, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name, city_slug = EXCLUDED.city_slug,
                    address = EXCLUDED.address, description = EXCLUDED.description,
                    star_rating = EXCLUDED.star_rating, updated_at = now()
                """,
                (row["id"], row["name"], row["city_slug"], row["address"], row["description"], row["star_rating"]),
            )
        counts["hotels"] = len(data["hotels"])

        for row in data["hotel_amenities"]:
            cur.execute(
                """
                INSERT INTO hotel_amenities (hotel_id, amenity_id) VALUES (%s, %s)
                ON CONFLICT (hotel_id, amenity_id) DO NOTHING
                """,
                (row["hotel_id"], row["amenity_id"]),
            )
        counts["hotel_amenities"] = len(data["hotel_amenities"])

        for row in data["rooms"]:
            cur.execute(
                """
                INSERT INTO rooms (id, hotel_id, room_type, price, currency, availability_count)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    room_type = EXCLUDED.room_type, price = EXCLUDED.price,
                    currency = EXCLUDED.currency, availability_count = EXCLUDED.availability_count
                """,
                (row["id"], row["hotel_id"], row["room_type"], row["price"], row["currency"], row["availability_count"]),
            )
        counts["rooms"] = len(data["rooms"])

        for row in data["hotel_images"]:
            cur.execute(
                """
                INSERT INTO hotel_images (id, hotel_id, url, position)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET url = EXCLUDED.url, position = EXCLUDED.position
                """,
                (row["id"], row["hotel_id"], row["url"], row["position"]),
            )
        counts["hotel_images"] = len(data["hotel_images"])

    conn.commit()
    logger.info(f"Ingested: {counts}")
    return counts


@task
def report_results(counts: dict[str, int]) -> None:
    for table, count in counts.items():
        print(f"{table}: {count} rows upserted")


@task(cache_policy=NO_CACHE)
def disconnect(conn) -> None:
    conn.close()


@flow(name="hotels-ingest")
def hotels_ingest():
    conn = connect()

    data = extract_hotel_data()
    data["hotel_images"] = upload_images(data["hotel_images"])
    counts = ingest_hotel_data(conn, data)
    report_results(counts)

    disconnect(conn)


if __name__ == "__main__":
    hotels_ingest()
