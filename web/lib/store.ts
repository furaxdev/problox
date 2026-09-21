"use client";

// Persistance locale (navigateur) des chats/projets — le backend actuel
// n'a qu'une seule session/AgentState linéaire (voir problox/web.py), pas
// de vrai modèle multi-conversations/multi-projets côté serveur. En
// attendant une vraie persistance serveur (DB), on organise l'historique
// côté client: chaque chat sauvegardé est une photo figée d'une
// conversation passée (lecture seule), regroupable en "projets".

export type StoredTurn = {
  userText: string;
  status: "running" | "done" | "error";
  logLines: string[];
  design: Record<string, unknown> | null;
  buildAvailable: boolean;
  error: string | null;
};

export type ChatRecord = {
  id: string;
  title: string;
  createdAt: number;
  projectId: string | null;
  turns: StoredTurn[];
};

export type ProjectRecord = {
  id: string;
  name: string;
  createdAt: number;
};

const CHATS_KEY = "probloxdev.chats.v1";
const PROJECTS_KEY = "probloxdev.projects.v1";

function safeParse<T>(raw: string | null, fallback: T): T {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function read<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    return safeParse(window.localStorage.getItem(key), fallback);
  } catch {
    // Safari navigation privée / quota / storage bloqué: on continue sans
    // persistance plutôt que de casser l'app.
    return fallback;
  }
}

function write<T>(key: string, value: T): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* stockage indisponible — on n'interrompt pas l'usage de l'app */
  }
}

export function loadChats(): ChatRecord[] {
  return read<ChatRecord[]>(CHATS_KEY, []).sort((a, b) => b.createdAt - a.createdAt);
}

export function saveChat(chat: ChatRecord): void {
  const chats = read<ChatRecord[]>(CHATS_KEY, []);
  const idx = chats.findIndex((c) => c.id === chat.id);
  if (idx >= 0) chats[idx] = chat;
  else chats.unshift(chat);
  write(CHATS_KEY, chats);
}

export function deleteChat(id: string): void {
  const chats = read<ChatRecord[]>(CHATS_KEY, []).filter((c) => c.id !== id);
  write(CHATS_KEY, chats);
}

export function loadProjects(): ProjectRecord[] {
  return read<ProjectRecord[]>(PROJECTS_KEY, []).sort((a, b) => b.createdAt - a.createdAt);
}

export function createProject(name: string): ProjectRecord {
  const project: ProjectRecord = { id: `proj_${Date.now()}`, name, createdAt: Date.now() };
  const projects = read<ProjectRecord[]>(PROJECTS_KEY, []);
  projects.unshift(project);
  write(PROJECTS_KEY, projects);
  return project;
}

export function deleteProject(id: string): void {
  const projects = read<ProjectRecord[]>(PROJECTS_KEY, []).filter((p) => p.id !== id);
  write(PROJECTS_KEY, projects);
  // Les chats du projet supprimé redeviennent "sans projet" plutôt que
  // d'être perdus.
  const chats = read<ChatRecord[]>(CHATS_KEY, []).map((c) =>
    c.projectId === id ? { ...c, projectId: null } : c
  );
  write(CHATS_KEY, chats);
}

export function newChatId(): string {
  return `chat_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}
