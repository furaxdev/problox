"use client";

import { api, Me } from "@/lib/api";

export function AccountChip({ me, loading }: { me: Me | null; loading: boolean }) {
  if (loading) return <span className="muted">…</span>;
  if (me?.connected) {
    const label = me.user?.preferred_username || me.user?.name || "connecté";
    return (
      <button
        className="account-chip"
        onClick={() => api.logout().then(() => location.reload())}
        title="Se déconnecter"
      >
        <span className="avatar">{label.slice(0, 1).toUpperCase()}</span>
        {label}
      </button>
    );
  }
  return (
    <a className="account-chip connect" href={api.loginUrl()}>
      Connecter Roblox
    </a>
  );
}
