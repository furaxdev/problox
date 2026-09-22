"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, GameDesign, Me } from "@/lib/api";
import { Sidebar } from "@/components/Sidebar";
import { SettingsModal } from "@/components/SettingsModal";
import {
  ChatRecord,
  ProjectRecord,
  StoredTurn,
  createProject,
  deleteChat as deleteStoredChat,
  deleteProject as deleteStoredProject,
  loadChats,
  loadProjects,
  newChatId,
  saveChat,
} from "@/lib/store";

type Turn = StoredTurn;

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
  const d = turn.design as unknown as GameDesign | null;
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
      {turn.logLines.length > 0 && <div className="log-block">{turn.logLines.join("\n")}</div>}
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

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [chats, setChats] = useState<ChatRecord[]>([]);
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [archived, setArchived] = useState(false);

  const offsetRef = useRef(0);
  const pollingRef = useRef(false);
  const activeChatIdRef = useRef<string | null>(null);
  const activeProjectIdRef = useRef<string | null>(null);
  const conversationEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .me()
      .then(setMe)
      .catch(() => setMe(null))
      .finally(() => setMeLoading(false));
    setChats(loadChats());
    setProjects(loadProjects());
    if (typeof window !== "undefined" && window.innerWidth >= 900) setSidebarOpen(true);
  }, []);

  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  const persist = useCallback((id: string, snapshot: Turn[], title: string) => {
    saveChat({
      id,
      title,
      createdAt: Date.now(),
      projectId: activeProjectIdRef.current,
      turns: snapshot.map((t) => ({ ...t, logLines: t.logLines.slice(-200) })),
    });
    setChats(loadChats());
  }, []);

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

  const poll = useCallback(
    async (chatId: string, title: string) => {
      if (pollingRef.current) return;
      pollingRef.current = true;
      let consecutiveFailures = 0;
      try {
        while (true) {
          let status, logs;
          try {
            [status, logs] = await Promise.all([api.status(), api.logs(offsetRef.current)]);
            consecutiveFailures = 0;
          } catch (err) {
            consecutiveFailures += 1;
            // Un raté isolé (réseau, cold start du backend) ne doit pas
            // planter silencieusement le polling — mais 5 échecs d'affilée
            // (~10s) veut dire que le backend est vraiment injoignable.
            if (consecutiveFailures >= 5) {
              const message = err instanceof Error ? err.message : "Backend injoignable";
              patchLastTurn({ status: "error", error: `Connexion perdue: ${message}` });
              break;
            }
            await new Promise((r) => setTimeout(r, 1500));
            continue;
          }
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
              patchLastTurn({
                status: "done",
                design: design as unknown as Record<string, unknown> | null,
                buildAvailable: status.build_available,
              });
            }
            break;
          }
          await new Promise((r) => setTimeout(r, 1200));
        }
      } finally {
        pollingRef.current = false;
        setTurns((current) => {
          if (activeChatIdRef.current === chatId) persist(chatId, current, title);
          return current;
        });
      }
    },
    [appendLogLines, patchLastTurn, persist]
  );

  const send = useCallback(
    async (theme: string) => {
      const text = theme.trim();
      if (!text || pollingRef.current) return;
      setInput("");
      setCooldownHint("");
      setArchived(false);

      let chatId = activeChatIdRef.current;
      if (!chatId) {
        chatId = newChatId();
        activeChatIdRef.current = chatId;
        setActiveChatId(chatId);
      }
      const title = text.length > 46 ? `${text.slice(0, 46)}…` : text;

      setTurns((prev) => [
        ...prev,
        {
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
        poll(chatId, title);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Erreur inconnue";
        patchLastTurn({ status: "error", error: message });
        if (message.toLowerCase().includes("attendre")) setCooldownHint(message);
      }
    },
    [autonomous, poll, patchLastTurn]
  );

  const handleNewChat = useCallback((projectId: string | null = null) => {
    activeChatIdRef.current = null;
    activeProjectIdRef.current = projectId;
    setActiveChatId(null);
    setActiveProjectId(projectId);
    setTurns([]);
    setArchived(false);
    offsetRef.current = 0;
    if (typeof window !== "undefined" && window.innerWidth < 900) setSidebarOpen(false);
  }, []);

  const handleNewChatInProject = useCallback(
    (projectId: string) => handleNewChat(projectId),
    [handleNewChat]
  );

  const handleSelectChat = useCallback(
    (id: string) => {
      const chat = chats.find((c) => c.id === id);
      if (!chat) return;
      activeChatIdRef.current = id;
      activeProjectIdRef.current = chat.projectId;
      setActiveChatId(id);
      setActiveProjectId(chat.projectId);
      setTurns(chat.turns);
      setArchived(true);
      if (typeof window !== "undefined" && window.innerWidth < 900) setSidebarOpen(false);
    },
    [chats]
  );

  const handleDeleteChat = useCallback(
    (id: string) => {
      deleteStoredChat(id);
      setChats(loadChats());
      if (activeChatIdRef.current === id) handleNewChat();
    },
    [handleNewChat]
  );

  const handleCreateProject = useCallback(() => {
    const name = typeof window !== "undefined" ? window.prompt("Nom du projet ?") : null;
    if (!name || !name.trim()) return;
    createProject(name.trim());
    setProjects(loadProjects());
  }, []);

  const handleDeleteProject = useCallback((id: string) => {
    deleteStoredProject(id);
    setProjects(loadProjects());
    setChats(loadChats());
  }, []);

  const started = turns.length > 0;
  const busy = turns.length > 0 && turns[turns.length - 1].status === "running";
  const inputDisabled = busy || archived;

  const activeProjectName = projects.find((p) => p.id === activeProjectId)?.name;

  const composer = (
    <div className={`composer-wrap ${started ? "" : "floating"}`}>
      {!archived && activeProjectName && (
        <p className="composer-hint">📁 Ce chat sera rangé dans le projet « {activeProjectName} »</p>
      )}
      {archived && (
        <p className="composer-hint" style={{ color: "var(--warn)" }}>
          Conversation archivée (lecture seule) — clique &quot;Nouveau chat&quot; pour continuer.
        </p>
      )}
      <div className="composer">
        <textarea
          rows={1}
          placeholder="Décris le jeu Roblox que tu veux créer…"
          value={input}
          disabled={inputDisabled}
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
          <button className="send-btn" disabled={inputDisabled || !input.trim()} onClick={() => send(input)}>
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
    <div className="page-root">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        chats={chats}
        projects={projects}
        activeChatId={activeChatId}
        activeProjectId={activeProjectId}
        onNewChat={() => handleNewChat()}
        onNewChatInProject={handleNewChatInProject}
        onSelectChat={handleSelectChat}
        onDeleteChat={handleDeleteChat}
        onCreateProject={handleCreateProject}
        onDeleteProject={handleDeleteProject}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      <div className="app-shell">
        <div className="topbar">
          <div className="topbar-left">
            <button
              className="hamburger-btn"
              onClick={() => setSidebarOpen((v) => !v)}
              aria-label="Menu"
              title="Menu"
            >
              ☰
            </button>
            <a className="brand" href="/">
              <img src="/icon.svg" alt="" />
              <span>
                Problox<b>Dev</b>
              </span>
            </a>
          </div>
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
                {turns.map((t, i) => (
                  <div key={i} style={{ display: "contents" }}>
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

      {settingsOpen && <SettingsModal me={me} onClose={() => setSettingsOpen(false)} />}
    </div>
  );
}
