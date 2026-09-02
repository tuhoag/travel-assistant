import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { HotelCard } from "./HotelCard";
import type { Hotel } from "@/lib/chat";

const hotel: Hotel = {
  id: 1,
  name: "Ritz Paris",
  city_slug: "paris",
  address: "15 Place Vendome, 75001 Paris",
  description: "A landmark luxury hotel in the heart of Paris.",
  star_rating: 5,
  rooms: [
    { id: 2, room_type: "Deluxe Room", price: 477.83, currency: "EUR", availability_count: 5 },
    { id: 1, room_type: "Suite", price: 356.33, currency: "EUR", availability_count: 6 },
  ],
  amenities: ["wifi", "pool", "spa"],
  images: ["https://example.test/ritz.jpg"],
};

describe("HotelCard", () => {
  it("renders the hotel's name, address, and star rating", () => {
    render(<HotelCard hotel={hotel} />);

    expect(screen.getByText("Ritz Paris")).toBeInTheDocument();
    expect(screen.getByText("15 Place Vendome, 75001 Paris")).toBeInTheDocument();
    expect(screen.getByLabelText("5 stars")).toBeInTheDocument();
  });

  it("shows the cheapest room first, regardless of input order", () => {
    render(<HotelCard hotel={hotel} />);

    const priceTexts = screen.getAllByText(/EUR/).map((el) => el.textContent);
    expect(priceTexts[0]).toContain("356");
    expect(priceTexts[1]).toContain("478");
  });

  it("renders amenity pills with underscores replaced by spaces", () => {
    render(<HotelCard hotel={{ ...hotel, amenities: ["air_conditioning"] }} />);

    expect(screen.getByText("air conditioning")).toBeInTheDocument();
  });

  it("shows a placeholder when there are no images", () => {
    render(<HotelCard hotel={{ ...hotel, images: [] }} />);

    expect(screen.getByText("No image")).toBeInTheDocument();
  });
});
