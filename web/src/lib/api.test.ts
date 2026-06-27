import { describe, expect, it, vi } from "vitest";

import { createRun, toApiUrl } from "./api";

describe("api URL handling", () => {
  it("uses same-origin API paths by default", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({
        thread_id: "local-test",
        conversation_id: "conv-test",
        turn_id: "turn-test",
        status: "created",
        fixture: "welcome",
        events_url: "/api/runs/local-test/events",
        provider: { mode: "fixture" },
      }), { status: 200, headers: { "Content-Type": "application/json" } }),
    );

    await createRun({ prompt: "hello" });

    expect(fetchMock).toHaveBeenCalledWith("/api/runs", expect.objectContaining({ method: "POST" }));
    fetchMock.mockRestore();
  });

  it("joins relative API paths with explicit base overrides", () => {
    expect(toApiUrl("/api/runs/local-test/events", "http://127.0.0.1:9000")).toBe(
      "http://127.0.0.1:9000/api/runs/local-test/events",
    );
    expect(toApiUrl("api/health", "http://127.0.0.1:9000/")).toBe("http://127.0.0.1:9000/api/health");
    expect(toApiUrl("/api/health", "/kira/")).toBe("/kira/api/health");
  });

  it("keeps absolute event stream URLs unchanged", () => {
    expect(toApiUrl("https://example.test/api/runs/local-test/events", "http://127.0.0.1:9000")).toBe(
      "https://example.test/api/runs/local-test/events",
    );
  });
});
