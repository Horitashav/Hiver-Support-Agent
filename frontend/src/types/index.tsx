export interface IntentResult {
  intent: string;
  confidence: number;
  reasoning: string;
}

export interface RetrievedExample {
  customer: string;
  brand: string;
  similarity: number;
}

export interface ReplyResult {
  reply: string;
  retrieved_examples: RetrievedExample[];
  confidence: number;
  generated_draft?: string | null;
}

export interface EscalationResult {
  escalate: boolean;
  reason: string;
  reasons: string[];
  confidence: number;
}

export interface ProcessResponse {
  ticket_id: string;
  timestamp: string;
  intent: IntentResult;
  reply: ReplyResult;
  escalation: EscalationResult;
  auto_handled: boolean;
  processing_time_ms: number;
}

export interface PresetScenario {
  id: string;
  label: string;
  category: string;
  severity: "low" | "medium" | "high" | "critical";
  customer_handle: string;
  device_info: string | null;
  message: string;
  conversation_history: ConversationMessage[];
}

export interface ConversationMessage {
  role: "customer" | "agent";
  text: string;
}

export type TicketStatus = "processing" | "auto_handled" | "escalated" | "resolved";

export interface Ticket {
  id: string;
  customer_handle: string;
  device_info: string | null;
  message: string;
  preview: string;
  timestamp: string;
  status: TicketStatus;
  conversation_history: ConversationMessage[];
  agentResponse?: ProcessResponse;
  humanOverride?: {
    action: string;
    editedReply?: string;
    timestamp: string;
  };
}