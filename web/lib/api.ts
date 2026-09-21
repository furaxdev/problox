const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8787";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

export type Me = {
  connected: boolean;
  user: { name?: string; preferred_username?: string; sub?: string } | null;
  available_universes: Array<{ id?: string; universeId?: string; name?: string; displayName?: string }>;
  selected_universe_id: string | null;
  selected_place_id: string | null;
};

export type Status = {
  run: { status: "idle" | "running" | "done" | "error"; theme: string | null; error: string | null };
  config: { anthropic_ready: boolean; oauth_configured: boolean; roblox_connected: boolean };
  tools: Record<string, boolean>;
  agent_state: { iteration: number; theme: string | null; last_place_version: number | null };
  build_available: boolean;
};

export type GameDesign = {
  title: string;
  genre: string;
  core_loop: string;
  systems: Array<{ name: string; description: string }>;
  monetization: {
    currency_name: string;
    gamepasses: Array<{ name: string; effect: string; suggested_price_robux: number }>;
  };
  zones_or_levels: Array<{ name: string; description: string }>;
  retention_hooks: string[];
};

export const api = {
  apiUrl: API_URL,
  loginUrl: () => `${API_URL}/api/auth/roblox/login`,
  buildDownloadUrl: () => `${API_URL}/api/build/place.rbxlx`,
  me: () => apiFetch<Me>("/api/me"),
  status: () => apiFetch<Status>("/api/status"),
  logs: (offset: number) => apiFetch<{ lines: string[]; offset: number }>(`/api/logs?offset=${offset}`),
  design: () => apiFetch<GameDesign>("/api/design"),
  run: (theme: string, autonomous: boolean, maxIterations: number) =>
    apiFetch<{ started: boolean }>("/api/run", {
      method: "POST",
      body: JSON.stringify({ theme, autonomous, max_iterations: maxIterations }),
    }),
  logout: () => apiFetch<{ ok: boolean }>("/api/auth/logout", { method: "POST" }),
};
