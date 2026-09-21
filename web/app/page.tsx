"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

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
    <main>
      <div className="hero">
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
    </main>
  );
}
