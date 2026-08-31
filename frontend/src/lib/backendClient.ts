import { config } from "@/lib/config";

export interface ChatResult {
  query: string;
  answer: string;
  chunks?: { page_content: string; metadata: Record<string, unknown> }[];
}

export class BackendClient {
  private baseUrl: string | undefined;
  private assistantId: string;

  constructor(baseUrl: string | undefined, assistantId: string = config.assistantId) {
    this.baseUrl = baseUrl;
    this.assistantId = assistantId;
  }

  async chat(threadId: string, query: string): Promise<ChatResult> {
    if (!this.baseUrl) {
      throw new Error("AGENT_URL is not set.");
    }

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

export const backendClient = new BackendClient(config.backendUrl, config.assistantId);
