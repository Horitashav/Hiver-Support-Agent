"use client";

import { useState, useEffect, useCallback } from "react";
import { AnimatePresence } from "framer-motion";
import type { Ticket, PresetScenario, ConversationMessage } from "@/types";
import { getPresets, processMessage, checkHealth } from "@/lib/api";

import TopBar from "@/components/TopBar";
import TriageQueue from "@/components/TriageQueue";
import ConversationCanvas from "@/components/ConversationCanvas";
import TelemetryDrawer from "@/components/TelemetryDrawer";
import StatusBar from "@/components/StatusBar";

export default function Home() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [activeTicketId, setActiveTicketId] = useState<string | null>(null);
  const [presets, setPresets] = useState<PresetScenario[]>([]);
  const [isBackendReady, setIsBackendReady] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const activeTicket = tickets.find((t) => t.id === activeTicketId) || null;

  useEffect(() => {
    async function init() {
      try {
        const [health, presetData] = await Promise.all([
          checkHealth(),
          getPresets(),
        ]);
        setIsBackendReady(health.agent_loaded);
        setPresets(presetData);
      } catch {
        setIsBackendReady(false);
      }
    }
    init();
  }, []);

  const handleSubmit = useCallback(
    async (message: string, preset?: PresetScenario) => {
      if (isProcessing) return;
      setIsProcessing(true);

      const tempId = `TKT-${Date.now().toString(36).toUpperCase()}`;
      const newTicket: Ticket = {
        id: tempId,
        customer_handle: preset?.customer_handle || "@custom_user",
        device_info: preset?.device_info || null,
        message,
        preview: message.slice(0, 80) + (message.length > 80 ? "…" : ""),
        timestamp: new Date().toISOString(),
        status: "processing",
        conversation_history: preset?.conversation_history || [],
      };

      setTickets((prev) => [newTicket, ...prev]);
      setActiveTicketId(tempId);

      try {
        const response = await processMessage(
          message,
          preset?.conversation_history || [],
          tempId
        );

        setTickets((prev) =>
          prev.map((t) =>
            t.id === tempId
              ? {
                  ...t,
                  id: response.ticket_id,
                  status: response.auto_handled ? "auto_handled" : "escalated",
                  agentResponse: response,
                }
              : t
          )
        );
        setActiveTicketId(response.ticket_id);
      } catch {
        setTickets((prev) =>
          prev.map((t) =>
            t.id === tempId ? { ...t, status: "escalated" } : t
          )
        );
      } finally {
        setIsProcessing(false);
      }
    },
    [isProcessing]
  );

  const handleSendReply = useCallback(
    async (replyText: string) => {
      if (!activeTicket || isProcessing) return;
      setIsProcessing(true);

      // 1. Pack previous turn into conversation_history
      const updatedHistory: ConversationMessage[] = [
        ...activeTicket.conversation_history,
        { role: "customer", text: activeTicket.message },
      ];

      const agentReplyText =
        activeTicket.humanOverride?.editedReply ||
        activeTicket.agentResponse?.reply.generated_draft ||
        activeTicket.agentResponse?.reply.reply;

      if (agentReplyText) {
        updatedHistory.push({ role: "agent", text: agentReplyText });
      }

      // 2. Set optimistic pending state on current ticket
      setTickets((prev) =>
        prev.map((t) =>
          t.id === activeTicket.id
            ? {
                ...t,
                message: replyText,
                preview: replyText.slice(0, 80) + (replyText.length > 80 ? "…" : ""),
                conversation_history: updatedHistory,
                status: "processing",
              }
            : t
        )
      );

      try {
        // 3. Call backend with the ongoing ticket ID and history
        const response = await processMessage(
          replyText,
          updatedHistory,
          activeTicket.id
        );

        setTickets((prev) =>
          prev.map((t) =>
            t.id === activeTicket.id
              ? {
                  ...t,
                  status: response.auto_handled ? "auto_handled" : "escalated",
                  agentResponse: response,
                }
              : t
          )
        );
      } catch {
        setTickets((prev) =>
          prev.map((t) =>
            t.id === activeTicket.id ? { ...t, status: "escalated" } : t
          )
        );
      } finally {
        setIsProcessing(false);
      }
    },
    [activeTicket, isProcessing]
  );

  const handleOverride = useCallback(
    (ticketId: string, action: string, editedReply?: string) => {
      setTickets((prev) =>
        prev.map((t) =>
          t.id === ticketId
            ? {
                ...t,
                status: "resolved" as const,
                humanOverride: {
                  action,
                  editedReply,
                  timestamp: new Date().toISOString(),
                },
              }
            : t
        )
      );
    },
    []
  );

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <StatusBar isReady={isBackendReady} ticketCount={tickets.length} />

      <TopBar
        presets={presets}
        onSubmit={handleSubmit}
        isProcessing={isProcessing}
        isReady={isBackendReady}
      />

      <div className="flex-1 flex overflow-hidden">
        <div className="w-80 border-r border-surface-border flex-shrink-0 overflow-y-auto">
          <TriageQueue
            tickets={tickets}
            activeTicketId={activeTicketId}
            onSelectTicket={setActiveTicketId}
          />
        </div>

        <div className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            <ConversationCanvas
              key={activeTicketId || "empty"}
              ticket={activeTicket}
              onOverride={handleOverride}
              onSendReply={handleSendReply}
              isProcessing={isProcessing}
            />
          </AnimatePresence>
        </div>

        <div className="w-96 border-l border-surface-border flex-shrink-0 overflow-y-auto">
          <TelemetryDrawer ticket={activeTicket} />
        </div>
      </div>
    </div>
  );
}