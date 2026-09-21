"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const FEATURES = [
  { emoji: "💰", title: "Monnaie persistante", desc: "DataStoreService, sauvegardée à chaque déconnexion." },
  { emoji: "🏆", title: "Leaderboard global", desc: "Classement OrderedDataStore, compétition sociale visible en permanence." },
  { emoji: "🎁", title: "Récompense quotidienne", desc: "Streak croissant, relance le joueur J+1." },
  { emoji: "📍", title: "Checkpoints", desc: "Progression sauvegardée, jamais reperdue." },
  { emoji: "🛒", title: "Boutique & gamepasses", desc: "Monétisation Robux via MarketplaceService." },
  { emoji: "🏭", title: "Tycoon (parcelles)", desc: "Droppers, réclamation de plot — généré selon le thème choisi." },
];

const STEPS = [
  { title: "Connecte ton compte", desc: "OAuth officiel Roblox — tu choisis toi-même quelles expériences autoriser." },
  { title: "Donne un thème", desc: "L'agent conçoit le game design, écrit le Luau, buildé via Rojo." },
  { title: "Publie", desc: "Le jeu part directement sur ta place, ou télécharge le .rbxlx pour Studio." },
];

export default function Home() {
  const [checking, setChecking] = useState(true);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    api
      .me()
      .then((me) => setConnected(me.connected))
      .catch(() => setConnected(false))
      .finally(() => setChecking(false));
  }, []);

  return (
    <main style={{ padding: 0 }}>
      <div className="hero-section">
        <div className="hero">
          <img src="/icon.svg" alt="" className="hero-logo" />
          <h1>Crée un jeu Roblox en autonomie</h1>
          <p>
            ProbloxDev conçoit une boucle de jeu addictive (monnaie, leaderboard,
            récompenses quotidiennes, checkpoints, boutique), génère le code
            Luau, et publie directement sur ton expérience Roblox — via ton
            propre compte, jamais le nôtre.
          </p>
          {checking ? (
            <p className="muted">Vérification de la connexion…</p>
          ) : connected ? (
            <a className="button" href="/dashboard">
              Ouvrir le dashboard
            </a>
          ) : (
            <a className="button" href={api.loginUrl()}>
              Connecter mon compte Roblox
            </a>
          )}
          <p className="muted" style={{ marginTop: 18 }}>
            À la connexion, tu choisis toi-même sur l&apos;écran Roblox quelles
            expériences ProbloxDev peut gérer. Aucun mot de passe ni cookie de
            session ne transite jamais par ce site.
          </p>
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
        <div className="section-title">Comment ça marche</div>
        <div className="steps">
          {STEPS.map((s, i) => (
            <div className="step" key={s.title}>
              <span className="num">{i + 1}</span>
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="section">
        <div className="section-title">Le dashboard</div>
        <div className="screenshot-frame">
          <img src="/dashboard-preview.png" alt="Dashboard ProbloxDev : thème, logs en direct, design généré" />
        </div>
      </div>
    </main>
  );
}
