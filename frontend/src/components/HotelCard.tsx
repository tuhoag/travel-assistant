import type { Hotel } from "@/lib/chat";

interface HotelCardProps {
  hotel: Hotel;
}

export function HotelCard({ hotel }: HotelCardProps) {
  const cheapestFirst = [...hotel.rooms].sort((a, b) => a.price - b.price);

  return (
    <div className="flex w-72 shrink-0 flex-col overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-800">
      {hotel.images[0] ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={hotel.images[0]} alt={hotel.name} className="h-36 w-full object-cover" />
      ) : (
        <div className="flex h-36 w-full items-center justify-center bg-zinc-100 text-xs text-zinc-400 dark:bg-zinc-700">
          No image
        </div>
      )}

      <div className="flex flex-1 flex-col gap-2 p-3">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-[14px] font-semibold leading-snug text-zinc-900 dark:text-zinc-50">{hotel.name}</h3>
          <span className="shrink-0 text-xs font-medium text-amber-500" aria-label={`${hotel.star_rating} stars`}>
            {"★".repeat(hotel.star_rating)}
          </span>
        </div>

        <p className="text-xs text-zinc-500 dark:text-zinc-400">{hotel.address}</p>

        <p className="line-clamp-2 text-xs text-zinc-600 dark:text-zinc-300">{hotel.description}</p>

        {hotel.amenities.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {hotel.amenities.slice(0, 4).map((amenity) => (
              <span
                key={amenity}
                className="rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] text-zinc-600 dark:bg-zinc-700 dark:text-zinc-300"
              >
                {amenity.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        )}

        {cheapestFirst.length > 0 && (
          <div className="mt-auto flex flex-col gap-1 border-t border-zinc-100 pt-2 dark:border-zinc-700">
            {cheapestFirst.slice(0, 2).map((room) => (
              <div key={room.id} className="flex items-center justify-between text-xs">
                <span className="text-zinc-500 dark:text-zinc-400">{room.room_type}</span>
                <span className="font-medium text-zinc-800 dark:text-zinc-100">
                  {room.price.toFixed(0)} {room.currency}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
