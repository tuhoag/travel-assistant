import { describe, it, expect, vi, beforeEach } from "vitest";
import { BackendClient } from "./backendClient";

describe("BackendClient.chat", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("posts to the correct thread endpoint with assistant_id and query", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ query: "what is berlin?", answer: "Berlin is the capital of Germany." }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new BackendClient("http://example.test", "agent");
    const result = await client.chat("thread-123", "what is berlin?");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://example.test/threads/thread-123/chat",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          assistant_id: "agent",
          input: { query: "what is berlin?" },
        }),
      }),
    );
    expect(result.answer).toBe("Berlin is the capital of Germany.");
  });

  it("passes through hotels when the backend returns them", async () => {
    const hotels = [{ id: 1, name: "Ritz Paris", city_slug: "paris" }];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ query: "hotels in paris", answer: "Found 1 hotel.", hotels }),
      }),
    );

    const client = new BackendClient("http://example.test", "agent");
    const result = await client.chat("thread-123", "hotels in paris");

    expect(result.hotels).toEqual(hotels);
  });

  it("throws when the response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 404 }),
    );

    const client = new BackendClient("http://example.test", "agent");

    await expect(client.chat("thread-123", "hi")).rejects.toThrow(
      "travel-assistant-backend request failed: 404",
    );
  });
});
