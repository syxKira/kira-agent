export type ApiProxyEnv = Record<string, string | undefined>;

export function resolveApiProxyTarget(env: ApiProxyEnv): string {
  return env.VITE_KIRA_DEV_API_TARGET ?? env.KIRA_DEV_API_TARGET ?? "http://127.0.0.1:8000";
}

export function createApiProxyConfig(env: ApiProxyEnv) {
  return {
    "/api": {
      target: resolveApiProxyTarget(env),
      changeOrigin: true,
    },
  };
}
