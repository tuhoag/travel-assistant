import { NextRequest, NextResponse } from "next/server";
import { backendClient } from "@/lib/backendClient";

export async function POST(request: NextRequest) {
  const { threadId, query } = await request.json();
  console.log(`Thread id: ${threadId} and query ${query}`);
  const result = await backendClient.chat(threadId, query);
  console.log(`Chat response: ${JSON.stringify(result)}`);
  // The UI only ever reads `answer` — `chunks` (with its per-chunk embedding
  // vectors, hundreds of floats each) was being sent to the browser for
  // nothing, needlessly inflating the response the client has to parse.
  return NextResponse.json({ query: result.query, answer: result.answer });
}
