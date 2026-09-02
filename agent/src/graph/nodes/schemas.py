from pydantic import BaseModel


class Intent(BaseModel):
    city_search: bool
    hotel_search: bool


class HotelSearchParams(BaseModel):
    city: str
    max_price: float | None = None
    min_stars: int | None = None
    amenities: list[str] | None = None


class Reflection(BaseModel):
    passes: bool
    feedback: str | None = None


class CoverageCheck(BaseModel):
    covered: bool
