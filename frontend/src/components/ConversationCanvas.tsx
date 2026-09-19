"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { MessageSquare, User, Bot, Shield, CheckCircle, Edit3, ArrowUpRight, Loader2, Send } from "lucide-react";
import clsx from "clsx";
import type { Ticket } from "@/types";
import { logOverride } from "@/lib/api";

interface ConversationCanvasProps {
  ticket: Ticket | null;
  onOverride: (ticketId: string, action: string, editedReply?: string) => void;
  onSendReply?: (text: string) => void;
  isProcessing?: boolean;
}

function ChatBubble({
  role,
  text,
  isLatest = false,
}: {
  role: "customer" | "agent";
  text: string;
  isLatest?: boolean;
}) {
  const isCustomer = role === "customer";

  return (
    <motion.div
      initial={isLatest ? { opacity: 0, y: 12 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
      className={clsx(
        "flex gap-3 max-w-2xl",
        isCustomer ? "self-start" : "self-end flex-row-reverse"
      )}
    >
      <div className={clsx(
        "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
        isCustomer ? "bg-slate-200" : "bg-brand-600"
      )}>
        {isCustomer ? <User className="w-4 h-4 text-slate-600" /> : <Bot className="w-4 h-4 text-white" />}
      </div>

      <div className={clsx(
        "rounded-2xl px-4 py-3 text-sm leading-relaxed",
        isCustomer ? "bg-slate-100 text-slate-800 rounded-tl-md" : "bg-brand-600 text-white rounded-tr-md"
      )}>
        {text}
      </div>
    </motion.div>
  );
}

function HumanActionBar({
  ticket,
  onOverride,
}: {
  ticket: Ticket;
  onOverride: (ticketId: string, action: string, editedReply?: string) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedReply, setEditedReply] = useState(
    ticket.agentResponse?.reply.generated_draft || ticket.agentResponse?.reply.reply || ""
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAction = async (action: "approve" | "edit" | "route_human") => {
    setIsSubmitting(true);
    try {
      await logOverride(ticket.id, action, action === "edit" ? editedReply : undefined);
      onOverride(ticket.id, action, action === "edit" ? editedReply : undefined);
    } catch (e) {
      console.error("Override failed:", e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 25, delay: 0.3 }}
      className="glass-card p-5 mx-6 mb-4"
    >
      <div className="flex items-center gap-2 mb-3">
        <Shield className="w-4 h-4 text-amber-600" />
        <h4 className="text-sm font-semibold text-slate-800">Human Review Required</h4>
        <span className="pill-escalated text-[10px]">Escalated</span>
      </div>

      <p className="text-xs text-slate-500 mb-3">
        This ticket was escalated: {ticket.agentResponse?.escalation.reason}
      </p>

      <div className="mb-4">
        <label className="text-xs font-medium text-slate-500 mb-1 block">
          AI Draft Reply:
        </label>
        {isEditing ? (
          <textarea
            value={editedReply}
            onChange={(e) => setEditedReply(e.target.value)}
            className="w-full p-3 text-sm border border-surface-border rounded-lg 
                       focus:outline-none focus:ring-2 focus:ring-brand-500/20 
                       resize-none h-24"
          />
        ) : (
          <div className="p-3 bg-surface-bg rounded-lg text-sm text-slate-700 border border-dashed border-surface-border">
            {ticket.agentResponse?.reply.generated_draft || ticket.agentResponse?.reply.reply}
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <motion.button
          whileTap={{ scale: 0.96 }}
          onClick={() => handleAction("approve")}
          disabled={isSubmitting}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold
                     bg-emerald-600 text-white hover:bg-emerald-700 transition-colors disabled:opacity-50"
        >
          <CheckCircle className="w-3.5 h-3.5" />
          Approve & Send Draft
        </motion.button>

        <motion.button
          whileTap={{ scale: 0.96 }}
          onClick={() => {
            if (isEditing) handleAction("edit");
            else setIsEditing(true);
          }}
          disabled={isSubmitting}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold
                     bg-brand-600 text-white hover:bg-brand-700 transition-colors disabled:opacity-50"
        >
          <Edit3 className="w-3.5 h-3.5" />
          {isEditing ? "Send Edited Reply" : "Edit Reply"}
        </motion.button>

        <motion.button
          whileTap={{ scale: 0.96 }}
          onClick={() => handleAction("route_human")}
          disabled={isSubmitting}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold
                     border border-surface-border text-slate-600 hover:bg-surface-hover 
                     transition-colors disabled:opacity-50"
        >
          <ArrowUpRight className="w-3.5 h-3.5" />
          Route to Tier-2
        </motion.button>
      </div>
    </motion.div>
  );
}

export default function ConversationCanvas({ ticket, onOverride, onSendReply, isProcessing = false }: ConversationCanvasProps) {
  const [replyInput, setReplyInput] = useState("");

  if (!ticket) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400">
        <div className="text-center">
          <MessageSquare className="w-12 h-12 mx-auto mb-3 text-slate-300" />
          <p className="text-sm font-medium">No ticket selected</p>
          <p className="text-xs mt-1">Submit a message or select a ticket from the queue.</p>
        </div>
      </div>
    );
  }

  const isLocalProcessing = ticket.status === "processing" || isProcessing;
  const isEscalated = ticket.status === "escalated" && !ticket.humanOverride;
  const agentReply = ticket.agentResponse?.reply;

  const handleSend = () => {
    if (!replyInput.trim() || isLocalProcessing || !onSendReply) return;
    onSendReply(replyInput.trim());
    setReplyInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="h-full flex flex-col"
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-surface-border bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-800">
              {ticket.customer_handle}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {ticket.device_info || "Device info not available"} · Ticket {ticket.id}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {ticket.agentResponse && (
              <span className="text-[10px] text-slate-400 font-mono">
                {ticket.agentResponse.processing_time_ms.toFixed(0)}ms
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 flex flex-col">
        {ticket.conversation_history.map((msg, i) => (
          <ChatBubble key={i} role={msg.role} text={msg.text} />
        ))}

        <ChatBubble role="customer" text={ticket.message} isLatest />

        {isLocalProcessing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="self-end flex items-center gap-2 text-sm text-slate-400"
          >
            <Loader2 className="w-4 h-4 animate-spin" />
            Agent is thinking…
          </motion.div>
        )}

        {agentReply && !isEscalated && (
          <ChatBubble
            role="agent"
            text={
              ticket.humanOverride?.editedReply ||
              agentReply.generated_draft ||
              agentReply.reply
            }
            isLatest
          />
        )}

        {ticket.humanOverride && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="self-center flex items-center gap-1.5 text-xs text-emerald-600 
                       bg-emerald-50 px-3 py-1.5 rounded-full border border-emerald-200"
          >
            <CheckCircle className="w-3.5 h-3.5" />
            {ticket.humanOverride.action === "approve"
              ? "Approved by human agent"
              : ticket.humanOverride.action === "edit"
              ? "Edited and sent by human agent"
              : "Routed to Tier-2 specialist"}
          </motion.div>
        )}
      </div>

      {/* Human Action Bar (for escalated tickets) */}
      {isEscalated && (
        <HumanActionBar ticket={ticket} onOverride={onOverride} />
      )}

      {/* Inline Customer Reply Bar */}
      <div className="p-4 border-t border-surface-border bg-white">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={replyInput}
            onChange={(e) => setReplyInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isLocalProcessing ? "Agent is replying..." : "Type your customer reply here..."}
            disabled={isLocalProcessing}
            className="flex-1 px-4 py-2.5 rounded-xl text-sm bg-surface-bg border border-surface-border focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400 placeholder:text-slate-400 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!replyInput.trim() || isLocalProcessing}
            className={clsx(
              "flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold transition-colors",
              replyInput.trim() && !isLocalProcessing
                ? "bg-brand-600 text-white hover:bg-brand-700"
                : "bg-slate-100 text-slate-400 cursor-not-allowed"
            )}
          >
            <Send className="w-4 h-4" />
            <span>Reply</span>
          </button>
        </div>
      </div>
    </motion.div>
  );
}