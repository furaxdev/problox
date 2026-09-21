"use client";

import { ChatRecord, ProjectRecord } from "@/lib/store";

export function Sidebar({
  open,
  onClose,
  chats,
  projects,
  activeChatId,
  onNewChat,
  onSelectChat,
  onDeleteChat,
  onCreateProject,
  onDeleteProject,
  onOpenSettings,
}: {
  open: boolean;
  onClose: () => void;
  chats: ChatRecord[];
  projects: ProjectRecord[];
  activeChatId: string | null;
  onNewChat: () => void;
  onSelectChat: (id: string) => void;
  onDeleteChat: (id: string) => void;
  onCreateProject: () => void;
  onDeleteProject: (id: string) => void;
  onOpenSettings: () => void;
}) {
  const chatsByProject = new Map<string | null, ChatRecord[]>();
  for (const chat of chats) {
    const list = chatsByProject.get(chat.projectId) || [];
    list.push(chat);
    chatsByProject.set(chat.projectId, list);
  }
  const unfiled = chatsByProject.get(null) || [];

  return (
    <>
      {open && <div className="sidebar-backdrop" onClick={onClose} />}
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="sidebar-top">
          <a className="brand" href="/">
            <img src="/icon.svg" alt="" />
            <span>
              Problox<b>Dev</b>
            </span>
          </a>
          <button className="icon-btn" onClick={onOpenSettings} title="Paramètres" aria-label="Paramètres">
            ⚙
          </button>
        </div>

        <button className="new-chat-btn" onClick={onNewChat}>
          + Nouveau chat
        </button>

        <div className="sidebar-scroll">
          <div className="sidebar-section">
            <div className="sidebar-section-header">
              <span>Projets</span>
              <button className="icon-btn small" onClick={onCreateProject} title="Nouveau projet">
                +
              </button>
            </div>
            {projects.length === 0 && (
              <p className="sidebar-empty">
                Un projet regroupe plusieurs chats autour d&apos;une même expérience Roblox.
              </p>
            )}
            {projects.map((project) => (
              <div key={project.id} className="project-group">
                <div className="project-name">
                  <span>📁 {project.name}</span>
                  <button
                    className="icon-btn small ghost"
                    onClick={() => onDeleteProject(project.id)}
                    title="Supprimer le projet"
                  >
                    ×
                  </button>
                </div>
                {(chatsByProject.get(project.id) || []).map((chat) => (
                  <ChatItem
                    key={chat.id}
                    chat={chat}
                    active={chat.id === activeChatId}
                    onSelect={onSelectChat}
                    onDelete={onDeleteChat}
                    indent
                  />
                ))}
              </div>
            ))}
          </div>

          <div className="sidebar-section">
            <div className="sidebar-section-header">
              <span>Chats</span>
            </div>
            {unfiled.length === 0 && <p className="sidebar-empty">Ta conversation actuelle apparaîtra ici.</p>}
            {unfiled.map((chat) => (
              <ChatItem key={chat.id} chat={chat} active={chat.id === activeChatId} onSelect={onSelectChat} onDelete={onDeleteChat} />
            ))}
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="credits-chip">
            <span>✨ Crédits</span>
            <span className="muted">bêta — illimité</span>
          </div>
          <a className="sidebar-link" href="/pricing">
            💳 Acheter des crédits
          </a>
          <a className="sidebar-link highlight" href="/pricing">
            🚀 Tarifs — passer Pro
          </a>
        </div>
      </aside>
    </>
  );
}

function ChatItem({
  chat,
  active,
  indent,
  onSelect,
  onDelete,
}: {
  chat: ChatRecord;
  active: boolean;
  indent?: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <div className={`chat-item ${active ? "active" : ""} ${indent ? "indent" : ""}`}>
      <button className="chat-item-btn" onClick={() => onSelect(chat.id)}>
        {chat.title || "Sans titre"}
      </button>
      <button
        className="icon-btn small ghost"
        onClick={(e) => {
          e.stopPropagation();
          onDelete(chat.id);
        }}
        title="Supprimer"
      >
        ×
      </button>
    </div>
  );
}
