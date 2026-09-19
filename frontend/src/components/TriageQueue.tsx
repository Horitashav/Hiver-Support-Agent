"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Inbox, CheckCircle2, AlertTriangle, Clock } from "lucide-react";
import clsx from "clsx";
import type { Ticket, TicketStatus } from "@/types";

interface TriageQueueProps {
  tickets: Ticket[];
  activeTicketId: string | null;
  onSelectTicket: (id: string) => void;
}

type FilterTab = "all" | "auto_handled" | "escalated";

function StatusPill({ status }: { status: TicketStatus }) {
  const config = {
    processing:    { label: "Processing",    className: "pill-processing", icon: Clock },
    auto_handled:  { label: "Auto-Handled",  className: "pill-auto",      icon: CheckCircle2 },
    escalated:     { label: "Escalated",     className: "pill-escalated", icon: AlertTriangle },
    resolved:      { label: "Resolved",      className: "pill-auto",      icon: CheckCircle2 },
  };
  const { label, className, icon: Icon } = config[status];

  return (
    <span className={className}>
      <Icon className="w-3 h-3 mr-1" />
      {label}
    </span>
  );
}

export default function TriageQueue({ tickets, activeTicketId, onSelectTicket }: TriageQueueProps) {
  const [filter, setFilter] = useState<FilterTab>("all");

  const filteredTickets = tickets.filter((t) => {
    if (filter === "all") return true;
    if (filter === "auto_handled") return t.status === "auto_handled" || t.status === "resolved";
    if (filter === "escalated") return t.status === "escalated";
    return true;
  });

  const counts = {
    all: tickets.length,
    auto_handled: tickets.filter((t) => t.status === "auto_handled" || t.status === "resolved").length,
    escalated: tickets.filter((t) => t.status === "escalated").length,
  };

  return (
    <div className="h-full flex flex-col bg-surface-bg">
      <div className="p-4 border-b border-surface-border bg-white">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Inbox className="w-5 h-5 text-slate-600" />
            <h2 className="text-sm font-semibold text-slate-800">Triage Queue</h2>
          </div>
          <span className="text-xs text-slate-500 font-medium bg-slate-100 px-2 py-0.5 rounded-full">
            {tickets.length}
          </span>
        </div>

        <div className="flex gap-1 bg-surface-bg rounded-lg p-0.5">
          {(["all", "auto_handled", "escalated"] as FilterTab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={clsx(
                "flex-1 text-xs font-medium py-1.5 rounded-md transition-all duration-200",
                filter === tab
                  ? "bg-white text-slate-800 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              )}
            >
              {tab === "all" ? "All" : tab === "auto_handled" ? "Auto" : "Escalated"}
              <span className="ml-1 text-[10px] opacity-60">{counts[tab]}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
        <AnimatePresence>
          {filteredTickets.length === 0 && (
            <div className="text-center text-sm text-slate-400 mt-12 px-4">
              <Inbox className="w-8 h-8 mx-auto mb-2 text-slate-300" />
              <p>No tickets yet.</p>
              <p className="text-xs mt-1">Use the top bar to submit a message.</p>
            </div>
          )}

          {filteredTickets.map((ticket, index) => (
            <motion.button
              key={ticket.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ delay: index * 0.05, type: "spring", stiffness: 300, damping: 25 }}
              onClick={() => onSelectTicket(ticket.id)}
              className={clsx(
                "w-full text-left p-3 rounded-xl transition-all duration-200",
                "border",
                activeTicketId === ticket.id
                  ? "bg-brand-50/60 border-brand-200 shadow-glass"
                  : "bg-white border-transparent hover:border-surface-border hover:shadow-glass"
              )}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-semibold text-slate-600 font-mono">
                  {ticket.customer_handle}
                </span>
                <StatusPill status={ticket.status} />
              </div>
              <p className="text-sm text-slate-800 line-clamp-2 leading-relaxed">
                {ticket.preview}
              </p>
              <div className="flex items-center justify-between mt-2">
                <span className="text-[10px] text-slate-400">
                  {new Date(ticket.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                {ticket.device_info && (
                  <span className="text-[10px] text-slate-400 truncate max-w-[120px]">
                    {ticket.device_info}
                  </span>
                )}
              </div>
            </motion.button>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}