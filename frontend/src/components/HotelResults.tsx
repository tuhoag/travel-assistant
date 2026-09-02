import { HotelCard } from "@/components/HotelCard";
import type { Hotel } from "@/lib/chat";

interface HotelResultsProps {
  hotels: Hotel[];
}

export function HotelResults({ hotels }: HotelResultsProps) {
  if (hotels.length === 0) return null;

  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {hotels.map((hotel) => (
        <HotelCard key={hotel.id} hotel={hotel} />
      ))}
    </div>
  );
}
