import { NextRequest, NextResponse } from "next/server";
import { backendClient } from "@/lib/backendClient";

export async function POST(request: NextRequest) {
  const { threadId, query } = await request.json();
  console.log(`Thread id: ${threadId} and query ${query}`)
  const result = await backendClient.chat(threadId, query);
  return NextResponse.json(result);
}
