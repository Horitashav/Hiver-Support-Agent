import type { ProcessResponse, PresetScenario } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }

  return res.json();
}

export async function checkHealth(): Promise<{ status: string; agent_loaded: boolean }> {
  return apiFetch("/api/health");
}

export async function getPresets(): Promise<PresetScenario[]> {
  return apiFetch("/api/presets");
}

export async function processMessage(
  message: string,
  conversationHistory: { role: string; text: string }[] = [],
  ticketId?: string
): Promise<ProcessResponse> {
  return apiFetch("/api/process", {
    method: "POST",
    body: JSON.stringify({
      message,
      conversation_history: conversationHistory,
      ticket_id: ticketId,
    }),
  });
}

export async function logOverride(
  ticketId: string,
  action: "approve" | "edit" | "route_human",
  editedReply?: string
): Promise<{ status: string }> {
  return apiFetch("/api/override", {
    method: "POST",
    body: JSON.stringify({
      ticket_id: ticketId,
      action,
      edited_reply: editedReply,
    }),
  });
}