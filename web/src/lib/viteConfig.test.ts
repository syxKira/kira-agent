import { describe, expect, it } from "vitest";

import { createApiProxyConfig, resolveApiProxyTarget } from "../../vite.proxy";

describe("Vite development proxy", () => {
  it("uses a configurable API proxy target", () => {
    expect(resolveApiProxyTarget({})).toBe("http://127.0.0.1:8000");
    expect(resolveApiProxyTarget({ VITE_KIRA_DEV_API_TARGET: "http://127.0.0.1:9000" })).toBe("http://127.0.0.1:9000");
    expect(resolveApiProxyTarget({ KIRA_DEV_API_TARGET: "http://127.0.0.1:9100" })).toBe("http://127.0.0.1:9100");
  });

  it("proxies same-origin /api development traffic", async () => {
    expect(createApiProxyConfig({})).toMatchObject({
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    });
  });
});
