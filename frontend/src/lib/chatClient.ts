import type { Hotel } from "@/lib/chat";

export interface SendChatMessageResult {
  query: string;
  answer: string;
  hotels?: Hotel[];
  city_search?: boolean;
  hotel_search?: boolean;
}

export async function sendChatMessage(threadId: string, query: string): Promise<SendChatMessageResult> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ threadId, query }),
  });

  if (!res.ok) {
    throw new Error(`chat request failed: ${res.status}`);
  }

  return res.json() as Promise<SendChatMessageResult>;
}
