-- IDs are plain INTEGER, not SERIAL: the ingestion CSVs assign their own
-- sequential ids up front (hotel_amenities/rooms/hotel_images reference
-- hotels.id directly), so every insert supplies an explicit id rather than
-- relying on a sequence.

CREATE TABLE IF NOT EXISTS amenities (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS hotels (
    id           INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    city_slug    TEXT NOT NULL,
    address      TEXT,
    description  TEXT,
    star_rating  INTEGER,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name, city_slug)
);
CREATE INDEX IF NOT EXISTS idx_hotels_city_slug ON hotels (city_slug);

CREATE TABLE IF NOT EXISTS hotel_amenities (
    hotel_id   INTEGER NOT NULL REFERENCES hotels (id) ON DELETE CASCADE,
    amenity_id INTEGER NOT NULL REFERENCES amenities (id) ON DELETE CASCADE,
    PRIMARY KEY (hotel_id, amenity_id)
);
CREATE INDEX IF NOT EXISTS idx_hotel_amenities_amenity_id ON hotel_amenities (amenity_id);

CREATE TABLE IF NOT EXISTS rooms (
    id                 INTEGER PRIMARY KEY,
    hotel_id           INTEGER NOT NULL REFERENCES hotels (id) ON DELETE CASCADE,
    room_type          TEXT NOT NULL,
    price              NUMERIC(10, 2) NOT NULL,
    currency           TEXT NOT NULL,
    availability_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE (hotel_id, room_type)
);
CREATE INDEX IF NOT EXISTS idx_rooms_hotel_id ON rooms (hotel_id);

CREATE TABLE IF NOT EXISTS hotel_images (
    id       INTEGER PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels (id) ON DELETE CASCADE,
    url      TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 1,
    UNIQUE (hotel_id, position)
);
CREATE INDEX IF NOT EXISTS idx_hotel_images_hotel_id ON hotel_images (hotel_id);
