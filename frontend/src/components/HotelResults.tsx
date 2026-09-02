import { HotelCard } from "@/components/HotelCard";
import type { Hotel } from "@/lib/chat";

interface HotelResultsProps {
  hotels: Hotel[];
}

const MAX_HOTELS_SHOWN = 10;

export function HotelResults({ hotels }: HotelResultsProps) {
  if (hotels.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-3">
      {hotels.slice(0, MAX_HOTELS_SHOWN).map((hotel) => (
        <HotelCard key={hotel.id} hotel={hotel} />
      ))}
    </div>
  );
}
