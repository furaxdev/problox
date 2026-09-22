"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, Me } from "@/lib/api";
import { AccountChip } from "@/components/AccountChip";

const SUGGESTIONS = [
  "Tycoon spatial avec des usines",
  "Obby parkour ultra rapide",
  "Arena PvP casual entre potes",
];

const FEATURES = [
  { emoji: "💰", title: "Monnaie persistante", desc: "DataStoreService, sauvegardée à chaque déconnexion." },
  { emoji: "🏆", title: "Leaderboard global", desc: "Classement OrderedDataStore, compétition sociale visible en permanence." },
  { emoji: "🎁", title: "Récompense quotidienne", desc: "Streak croissant, relance le joueur J+1." },
  { emoji: "📍", title: "Checkpoints", desc: "Progression sauvegardée, jamais reperdue." },
  { emoji: "🛒", title: "Boutique & gamepasses", desc: "Monétisation Robux via MarketplaceService." },
  { emoji: "🏭", title: "Tycoon (parcelles)", desc: "Droppers, réclamation de plot — généré selon le thème choisi." },
];

export default function Home() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [meLoading, setMeLoading] = useState(true);
  const [input, setInput] = useState("");

  useEffect(() => {
    api
      .me()
      .then((data) => {
        setMe(data);
        if (data.connected) router.replace("/dashboard");
      })
      .catch(() => setMe(null))
      .finally(() => setMeLoading(false));
  }, [router]);

  const start = (theme: string) => {
    const text = theme.trim();
    if (!text) return;
    router.push(`/dashboard?theme=${encodeURIComponent(text)}`);
  };

  // Connecté: on redirige vers /dashboard (useEffect ci-dessus) — le temps
  // que ça arrive, on n'affiche pas la landing pour éviter un flash.
  if (!meLoading && me?.connected) return null;

  return (
    <div className="simple-page">
      <div className="topbar">
        <div className="topbar-left">
          <a className="brand" href="/">
            <img src="/icon.svg" alt="" />
            <span>
              Problox<b>Dev</b>
            </span>
          </a>
        </div>
        <AccountChip me={me} loading={meLoading} />
      </div>

      <div className="hero-wrap">
        <div className="hero-inner">
          <img src="/icon.svg" alt="" className="hero-logo" />
          <h1>Quel jeu Roblox on construit ?</h1>
          <p className="sub">
            Décris l&apos;idée, l&apos;agent conçoit une boucle de jeu addictive, écrit le code
            Luau, et publie directement sur ton expérience — via ton propre compte, jamais le
            nôtre.
          </p>
          <div className="composer-wrap floating">
            <div className="composer">
              <textarea
                rows={1}
                placeholder="Décris le jeu Roblox que tu veux créer…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    start(input);
                  }
                }}
              />
              <div className="composer-actions">
                <button className="send-btn" disabled={!input.trim()} onClick={() => start(input)}>
                  ↑
                </button>
              </div>
            </div>
            <p className="composer-hint">
              Sans compte connecté, l&apos;agent tourne en dry-run (pas de publication).
            </p>
          </div>
          <div className="chips">
            {SUGGESTIONS.map((s) => (
              <button key={s} className="chip" onClick={() => start(s)}>
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="section">
        <div className="section-title">Ce que l&apos;agent génère</div>
        <div className="features-grid">
          {FEATURES.map((f) => (
            <div className="feature-card" key={f.title}>
              <span className="emoji">{f.emoji}</span>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="section">
        <div className="section-title">Le dashboard</div>
        <div className="screenshot-frame">
          <img
            src="/dashboard-preview.png"
            alt="Dashboard ProbloxDev : chat avec l'agent, logs en direct, design généré"
          />
        </div>
      </div>
    </div>
  );
}
