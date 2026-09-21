"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, GameDesign, Me } from "@/lib/api";

type Turn = {
  id: string;
  userText: string;
  status: "running" | "done" | "error";
  logLines: string[];
  design: GameDesign | null;
  buildAvailable: boolean;
  error: string | null;
};

const SUGGESTIONS = [
  "Tycoon spatial avec des usines",
  "Obby parkour ultra rapide",
  "Arena PvP casual entre potes",
];

function AccountChip({ me, loading }: { me: Me | null; loading: boolean }) {
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

function ResultCard({ turn }: { turn: Turn }) {
  const d = turn.design;
  if (!d) return null;
  return (
    <div className="result-card">
      <h3>{d.title}</h3>
      <div className="genre">{d.genre}</div>
      <p className="core-loop">{d.core_loop}</p>
      <div className="tag-row">
        {d.systems?.map((s) => (
          <span className="tag" key={s.name}>
            {s.name}
          </span>
        ))}
      </div>
      {d.monetization?.gamepasses?.length > 0 && (
        <div className="tag-row">
          {d.monetization.gamepasses.map((g) => (
            <span className="tag" key={g.name}>
              💎 {g.name} — {g.suggested_price_robux} R$
            </span>
          ))}
        </div>
      )}
      <div className="result-actions">
        {turn.buildAvailable && (
          <a className="btn btn-primary" href={api.buildDownloadUrl()}>
            ⬇ Télécharger place.rbxlx
          </a>
        )}
        <span className="muted" style={{ alignSelf: "center" }}>
          {turn.buildAvailable
            ? "Ouvre-le dans Roblox Studio, ou connecte Roblox pour publier directement."
            : "Installe la toolchain (Rojo) côté serveur pour builder — voir docs/DEPLOY.md."}
        </span>
      </div>
    </div>
  );
}

function AssistantTurn({ turn }: { turn: Turn }) {
  return (
    <div className="msg-assistant">
      <div className="msg-assistant-header">
        <span className="badge">🤖</span>
        {turn.status === "running" && <span className="spinner" />}
        <span className={`status-tag ${turn.status}`}>
          {turn.status === "running" ? "génération…" : turn.status === "done" ? "terminé" : "erreur"}
        </span>
      </div>
      {turn.logLines.length > 0 && (
        <div className="log-block">{turn.logLines.join("\n")}</div>
      )}
      {turn.error && <p className="error-text">{turn.error}</p>}
      {turn.status === "done" && <ResultCard turn={turn} />}
    </div>
  );
}

export default function Home() {
  const [me, setMe] = useState<Me | null>(null);
  const [meLoading, setMeLoading] = useState(true);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [autonomous, setAutonomous] = useState(false);
  const [cooldownHint, setCooldownHint] = useState("");

  const offsetRef = useRef(0);
  const pollingRef = useRef(false);
  const conversationEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .me()
      .then(setMe)
      .catch(() => setMe(null))
      .finally(() => setMeLoading(false));
  }, []);

  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  const patchLastTurn = useCallback((patch: Partial<Turn>) => {
    setTurns((prev) => {
      if (prev.length === 0) return prev;
      const copy = [...prev];
      copy[copy.length - 1] = { ...copy[copy.length - 1], ...patch };
      return copy;
    });
  }, []);

  const appendLogLines = useCallback((lines: string[]) => {
    if (!lines.length) return;
    setTurns((prev) => {
      if (prev.length === 0) return prev;
      const copy = [...prev];
      const last = copy[copy.length - 1];
      copy[copy.length - 1] = { ...last, logLines: [...last.logLines, ...lines] };
      return copy;
    });
  }, []);

  const poll = useCallback(async () => {
    if (pollingRef.current) return;
    pollingRef.current = true;
    try {
      while (true) {
        const [status, logs] = await Promise.all([api.status(), api.logs(offsetRef.current)]);
        if (logs.lines.length) {
          appendLogLines(logs.lines);
          offsetRef.current = logs.offset;
        }
        if (status.run.status !== "running") {
          if (status.run.status === "error") {
            patchLastTurn({ status: "error", error: status.run.error || "Erreur inconnue" });
          } else {
            let design: GameDesign | null = null;
            try {
              design = await api.design();
            } catch {
              /* pas de design si le run a échoué très tôt */
            }
            patchLastTurn({ status: "done", design, buildAvailable: status.build_available });
          }
          break;
        }
        await new Promise((r) => setTimeout(r, 1200));
      }
    } finally {
      pollingRef.current = false;
    }
  }, [appendLogLines, patchLastTurn]);

  const send = useCallback(
    async (theme: string) => {
      const text = theme.trim();
      if (!text || pollingRef.current) return;
      setInput("");
      setCooldownHint("");
      setTurns((prev) => [
        ...prev,
        {
          id: `${Date.now()}`,
          userText: text,
          status: "running",
          logLines: [],
          design: null,
          buildAvailable: false,
          error: null,
        },
      ]);
      try {
        await api.run(text, autonomous, autonomous ? 3 : 1);
        poll();
      } catch (err) {
        const message = err instanceof Error ? err.message : "Erreur inconnue";
        patchLastTurn({ status: "error", error: message });
        if (message.toLowerCase().includes("attendre")) setCooldownHint(message);
      }
    },
    [autonomous, poll, patchLastTurn]
  );

  const started = turns.length > 0;
  const busy = turns.length > 0 && turns[turns.length - 1].status === "running";

  const composer = (
    <div className={`composer-wrap ${started ? "" : "floating"}`}>
      <div className="composer">
        <textarea
          rows={1}
          placeholder="Décris le jeu Roblox que tu veux créer…"
          value={input}
          disabled={busy}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send(input);
            }
          }}
        />
        <div className="composer-actions">
          <button
            type="button"
            className={`mode-toggle ${autonomous ? "active" : ""}`}
            onClick={() => setAutonomous((v) => !v)}
            title="Mode autonome: l'agent itère plusieurs fois sur le design"
          >
            {autonomous ? "Auto ✓" : "Auto"}
          </button>
          <button className="send-btn" disabled={busy || !input.trim()} onClick={() => send(input)}>
            {busy ? <span className="spinner" /> : "↑"}
          </button>
        </div>
      </div>
      {cooldownHint && (
        <p className="composer-hint" style={{ color: "var(--warn)" }}>
          {cooldownHint}
        </p>
      )}
      {!started && (
        <p className="composer-hint">
          Sans compte connecté, l&apos;agent tourne en dry-run (pas de publication).
        </p>
      )}
    </div>
  );

  return (
    <div className="app-shell">
      <div className="topbar">
        <a className="brand" href="/">
          <img src="/icon.svg" alt="" />
          <span>
            Problox<b>Dev</b>
          </span>
        </a>
        <AccountChip me={me} loading={meLoading} />
      </div>

      {!started ? (
        <div className="hero-wrap">
          <div className="hero-inner">
            <h1>Quel jeu Roblox on construit ?</h1>
            <p className="sub">
              Décris l&apos;idée, l&apos;agent conçoit une boucle de jeu addictive, écrit le
              code Luau, et publie directement sur ton expérience — via ton propre compte.
            </p>
            {composer}
            <div className="chips">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="chip" onClick={() => send(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="conversation">
            <div className="conversation-inner">
              {turns.map((t) => (
                <div key={t.id} style={{ display: "contents" }}>
                  <div className="msg-user">{t.userText}</div>
                  <AssistantTurn turn={t} />
                </div>
              ))}
              <div ref={conversationEndRef} />
            </div>
          </div>
          {composer}
        </>
      )}
    </div>
  );
}
