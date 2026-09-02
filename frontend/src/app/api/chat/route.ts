import { NextRequest, NextResponse } from "next/server";
import { backendClient } from "@/lib/backendClient";

export async function POST(request: NextRequest) {
  const { threadId, query } = await request.json();
  console.log(`Thread id: ${threadId} and query ${query}`);
  const result = await backendClient.chat(threadId, query);
  // console.log(`Chat response: ${JSON.stringify(result)}`);
  // `chunks` (with its per-chunk embedding vectors, hundreds of floats
  // each) stays stripped — the UI never reads it and it'd needlessly
  // inflate the response. `hotels` is structured data the UI does render
  // (as cards), so unlike chunks it's passed through when present.
  return NextResponse.json({
    query: result.query,
    answer: result.answer,
    city_search: result.city_search,
    hotel_search: result.hotel_search,
    ...(result.hotels ? { hotels: result.hotels } : {}),
  });
}
