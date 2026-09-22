"use client";

import { useState } from "react";
import { api, Me } from "@/lib/api";

function ExperiencePicker({ me }: { me: Me }) {
  const [places, setPlaces] = useState<Array<{ id?: string; placeId?: string; displayName?: string }> | null>(
    null
  );
  const [loadingUniverse, setLoadingUniverse] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  if (me.available_universes.length <= 1) return null;

  const loadPlaces = async (universeId: string) => {
    setLoadingUniverse(universeId);
    setError("");
    try {
      const res = await api.experiencePlaces(universeId);
      setPlaces(res.places);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
      setPlaces(null);
    }
  };

  const select = async (universeId: string, placeId: string) => {
    setSaving(true);
    try {
      await api.selectExperience(universeId, placeId);
      location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
      setSaving(false);
    }
  };

  return (
    <div className="modal-section">
      <div className="modal-section-title">Expérience ciblée</div>
      <p className="muted">Tu as autorisé plusieurs expériences — choisis celle que ProbloxDev doit gérer.</p>
      <div className="experience-list">
        {me.available_universes.map((u) => {
          const universeId = String(u.id || u.universeId || "");
          const isActive = universeId === me.selected_universe_id;
          const isLoading = loadingUniverse === universeId;
          return (
            <div key={universeId} className="experience-item">
              <button
                className={`experience-universe ${isActive ? "active" : ""}`}
                onClick={() => loadPlaces(universeId)}
              >
                {u.displayName || u.name || `Univers ${universeId}`}
                {isActive && <span className="tag">actif</span>}
              </button>
              {isLoading && places && (
                <div className="experience-places">
                  {places.length === 0 && <p className="muted">Aucune place trouvée.</p>}
                  {places.map((p) => {
                    const placeId = String(p.id || p.placeId || "");
                    return (
                      <button
                        key={placeId}
                        className="btn btn-secondary"
                        disabled={saving}
                        onClick={() => select(universeId, placeId)}
                      >
                        {p.displayName || `Place ${placeId}`}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
      {error && <p className="error-text">{error}</p>}
    </div>
  );
}

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

        {me?.connected && <ExperiencePicker me={me} />}

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
