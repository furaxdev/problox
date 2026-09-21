"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, Me, Status } from "@/lib/api";

export default function Dashboard() {
  const [me, setMe] = useState<Me | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [logLines, setLogLines] = useState<string[]>([]);
  const [design, setDesign] = useState<string>("Aucun design pour l'instant.");
  const [theme, setTheme] = useState("");
  const [autonomous, setAutonomous] = useState(false);
  const [maxIterations, setMaxIterations] = useState(1);
  const [runHint, setRunHint] = useState("");

  const offsetRef = useRef(0);
  const loadedDesignRef = useRef(false);

  const refresh = useCallback(async () => {
    const [meData, statusData, logsData] = await Promise.all([
      api.me().catch(() => null),
      api.status().catch(() => null),
      api.logs(offsetRef.current).catch(() => null),
    ]);
    if (meData) setMe(meData);
    if (statusData) setStatus(statusData);
    if (logsData) {
      if (logsData.lines.length) setLogLines((prev) => [...prev, ...logsData.lines]);
      offsetRef.current = logsData.offset;
    }
    if (statusData && (statusData.run.status === "done" || statusData.run.status === "error") && !loadedDesignRef.current) {
      loadedDesignRef.current = true;
      api
        .design()
        .then((d) => setDesign(JSON.stringify(d, null, 2)))
        .catch(() => {});
    }
    if (statusData?.run.status === "running") loadedDesignRef.current = false;
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 1500);
    return () => clearInterval(id);
  }, [refresh]);

  const launch = async () => {
    if (!theme.trim()) return;
    offsetRef.current = 0;
    setLogLines([]);
    setRunHint("");
    try {
      await api.run(theme, autonomous, maxIterations);
    } catch (err) {
      setRunHint(err instanceof Error ? err.message : "Erreur inconnue");
    }
  };

  const running = status?.run.status === "running";

  return (
    <main>
      <div className="grid">
        <div>
          <div className="panel">
            <h2>Compte Roblox</h2>
            {me?.connected ? (
              <>
                <p>Connecté en tant que <strong>{me.user?.preferred_username || me.user?.name || "utilisateur"}</strong></p>
                <p className="muted">
                  Expérience ciblée: {me.selected_universe_id ? `univers ${me.selected_universe_id}` : "aucune"}
                  {me.selected_place_id ? ` / place ${me.selected_place_id}` : ""}
                </p>
                <button
                  className="secondary"
                  onClick={() => api.logout().then(() => location.reload())}
                >
                  Déconnecter
                </button>
              </>
            ) : (
              <>
                <p className="muted">Non connecté — l&apos;agent tournera en dry-run (pas de publication).</p>
                <a className="button" href={api.loginUrl()}>Connecter Roblox</a>
              </>
            )}
          </div>

          <div className="panel">
            <h2>Nouveau run</h2>
            <label htmlFor="theme">Thème du jeu</label>
            <input
              id="theme"
              type="text"
              placeholder="ex: obby simulateur de course"
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
            />
            <div className="row">
              <input
                id="autonomous"
                type="checkbox"
                checked={autonomous}
                onChange={(e) => setAutonomous(e.target.checked)}
              />
              <label htmlFor="autonomous">Mode autonome (itère plusieurs fois)</label>
            </div>
            <label htmlFor="maxIterations">Itérations max</label>
            <input
              id="maxIterations"
              type="number"
              min={1}
              max={20}
              value={maxIterations}
              onChange={(e) => setMaxIterations(parseInt(e.target.value, 10) || 1)}
            />
            <button onClick={launch} disabled={running}>
              {running ? `En cours: ${status?.run.theme}…` : "Lancer l'agent"}
            </button>
            {(runHint || status?.run.error) && (
              <p className="muted" style={{ marginTop: 10 }}>{runHint || status?.run.error}</p>
            )}
          </div>

          <div className="panel">
            <h2>Toolchain backend</h2>
            <ul className="status-list">
              {status &&
                Object.entries(status.tools).map(([name, ok]) => (
                  <li key={name}>
                    <span><span className={`dot ${ok ? "ok" : "err"}`} />{name}</span>
                    <span>{ok ? "trouvé" : "absent"}</span>
                  </li>
                ))}
            </ul>
          </div>
        </div>

        <div>
          <div className="panel">
            <h2>
              Logs
              {status && (
                <span className={`pill ${status.run.status}`} style={{ float: "right" }}>
                  {status.run.status}
                </span>
              )}
            </h2>
            <div id="logs">{logLines.length ? logLines.join("\n") : "En attente d'un run…"}</div>
          </div>

          <div className="panel">
            <h2>Dernier design généré</h2>
            <div id="design">{design}</div>
            {status?.build_available && (
              <a className="button" style={{ marginTop: 12, width: "auto", display: "inline-block" }} href={api.buildDownloadUrl()}>
                ⬇ Télécharger place.rbxlx
              </a>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
