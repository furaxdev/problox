"use client";

import { api, Me } from "@/lib/api";

export function SettingsModal({ me, onClose }: { me: Me | null; onClose: () => void }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Paramètres</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Fermer">
            ×
          </button>
        </div>

        <div className="modal-section">
          <div className="modal-section-title">Compte Roblox</div>
          {me?.connected ? (
            <>
              <p className="muted">
                Connecté en tant que{" "}
                <strong>{me.user?.preferred_username || me.user?.name || "utilisateur"}</strong>.
              </p>
              {me.selected_universe_id && (
                <p className="muted">
                  Expérience ciblée: univers {me.selected_universe_id}
                  {me.selected_place_id ? ` / place ${me.selected_place_id}` : ""}
                </p>
              )}
              <button className="btn btn-secondary" onClick={() => api.logout().then(() => location.reload())}>
                Déconnecter
              </button>
            </>
          ) : (
            <>
              <p className="muted">Non connecté — l&apos;agent tourne en dry-run (pas de publication).</p>
              <a className="btn btn-primary" href={api.loginUrl()}>
                Connecter Roblox
              </a>
            </>
          )}
        </div>

        <div className="modal-section">
          <div className="modal-section-title">Modèle</div>
          <p className="muted">
            ProbloxDev utilise Claude pour concevoir le game design (si une clé Anthropic est
            configurée côté serveur), sinon un design “starter kit” prédéfini. Le choix du modèle
            n&apos;est pas encore configurable depuis l&apos;interface.
          </p>
        </div>

        <div className="modal-section">
          <div className="modal-section-title">Données locales</div>
          <p className="muted">
            L&apos;historique des chats et des projets est stocké uniquement dans ce navigateur
            (localStorage) — rien n&apos;est envoyé à un serveur pour l&apos;instant.
          </p>
        </div>
      </div>
    </div>
  );
}
