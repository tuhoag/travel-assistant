import { config } from "@/lib/config";

export interface ChatResult {
  query: string;
  answer: string;
  chunks?: { page_content: string; metadata: Record<string, unknown> }[];
}

export class BackendClient {
  private baseUrl: string;
  private assistantId: string;

  constructor(baseUrl: string = config.backendUrl, assistantId: string = config.assistantId) {
    this.baseUrl = baseUrl;
    this.assistantId = assistantId;
  }

  async chat(threadId: string, query: string): Promise<ChatResult> {
    const res = await fetch(`${this.baseUrl}/threads/${threadId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        assistant_id: this.assistantId,
        input: { query },
      }),
    });

    if (!res.ok) {
      throw new Error(`travel-assistant-backend request failed: ${res.status}`);
    }

    return res.json() as Promise<ChatResult>;
  }
}

export const backendClient = new BackendClient();
