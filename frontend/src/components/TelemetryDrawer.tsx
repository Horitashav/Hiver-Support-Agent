"use client";

import { motion } from "framer-motion";
import { Brain, Target, ShieldAlert, Database, ChevronRight, TrendingUp, AlertTriangle, CheckCircle2 } from "lucide-react";
import clsx from "clsx";
import type { Ticket } from "@/types";

function ConfidenceMeter({ value, label }: { value: number; label: string }) {
  const percentage = Math.round(value * 100);
  const color = value >= 0.8 ? "bg-emerald-500" : value >= 0.5 ? "bg-amber-500" : "bg-rose-500";

  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs text-slate-500">{label}</span>
        <span className={clsx(
          "text-xs font-mono font-bold",
          value >= 0.8 ? "text-emerald-600" : value >= 0.5 ? "text-amber-600" : "text-rose-600"
        )}>
          {percentage}%
        </span>
      </div>
      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
          className={clsx("h-full rounded-full", color)}
        />
      </div>
    </div>
  );
}

function SimilarityBar({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-brand-400 rounded-full"
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </div>
      <span className="text-[10px] font-mono text-slate-500 w-10 text-right">
        {value.toFixed(3)}
      </span>
    </div>
  );
}

interface TelemetryDrawerProps {
  ticket: Ticket | null;
}

export default function TelemetryDrawer({ ticket }: TelemetryDrawerProps) {
  const response = ticket?.agentResponse;

  if (!ticket || !response) {
    return (
      <div className="h-full flex items-center justify-center p-6 text-slate-400">
        <div className="text-center">
          <Brain className="w-10 h-10 mx-auto mb-3 text-slate-300" />
          <p className="text-sm font-medium">AI Copilot Inspector</p>
          <p className="text-xs mt-1 max-w-[200px] mx-auto">
            Select a processed ticket to view the AI&apos;s decision trace.
          </p>
        </div>
      </div>
    );
  }

  const { intent, escalation, reply } = response;

  return (
    <div className="h-full bg-surface-bg overflow-y-auto">
      <div className="px-5 py-4 bg-white border-b border-surface-border sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-brand-600" />
          <h2 className="text-sm font-semibold text-slate-800">
            AI Decision Trace
          </h2>
        </div>
        <p className="text-[10px] text-slate-400 mt-0.5 font-mono">
          {response.ticket_id} · {response.processing_time_ms.toFixed(0)}ms
        </p>
      </div>

      <div className="p-5 space-y-5">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-4 h-4 text-brand-600" />
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Intent Classification
            </h3>
          </div>
          <div className="flex items-center gap-2 mb-3">
            <span className="px-3 py-1 bg-brand-50 text-brand-700 rounded-lg text-sm font-semibold border border-brand-200">
              {intent.intent.replace(/_/g, " ")}
            </span>
          </div>
          <ConfidenceMeter value={intent.confidence} label="Confidence" />
          <div className="mt-3 p-2.5 bg-surface-bg rounded-lg">
            <p className="text-xs text-slate-600 leading-relaxed">
              <span className="font-medium text-slate-500">Reasoning: </span>
              {intent.reasoning}
            </p>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Escalation Decision
            </h3>
          </div>
          <div className="flex items-center gap-2 mb-3">
            {escalation.escalate ? (
              <span className="flex items-center gap-1.5 px-3 py-1 bg-rose-50 text-rose-700 rounded-lg text-sm font-semibold border border-rose-200">
                <AlertTriangle className="w-3.5 h-3.5" />
                ESCALATED
              </span>
            ) : (
              <span className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-emerald-700 rounded-lg text-sm font-semibold border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5" />
                AUTO-HANDLED
              </span>
            )}
          </div>
          <ConfidenceMeter value={escalation.confidence} label="Decision Confidence" />
          <div className="mt-3 space-y-1.5">
            {(escalation.reasons?.length > 0 ? escalation.reasons : [escalation.reason]).map((reason, i) => (
              <div key={i} className="flex items-start gap-2 p-2 bg-surface-bg rounded-lg">
                <ChevronRight className="w-3 h-3 text-slate-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-slate-600 leading-relaxed">{reason}</p>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Database className="w-4 h-4 text-indigo-600" />
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              FAISS Vector Retrieval
            </h3>
          </div>
          <p className="text-[10px] text-slate-400 mb-3">
            Top-{reply.retrieved_examples.length} nearest neighbors from embedded tweet corpus
          </p>
          <div className="space-y-3">
            {reply.retrieved_examples.map((ex, i) => (
              <motion.div key={i} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 + i * 0.1 }} className="p-3 bg-surface-bg rounded-lg border border-slate-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-semibold text-slate-500">Match #{i + 1}</span>
                  <span className={clsx(
                    "text-[10px] font-mono font-bold",
                    ex.similarity >= 0.7 ? "text-emerald-600" : ex.similarity >= 0.4 ? "text-amber-600" : "text-slate-500"
                  )}>
                    cosine: {ex.similarity.toFixed(3)}
                  </span>
                </div>
                <SimilarityBar value={ex.similarity} />
                <div className="mt-2 space-y-1.5">
                  <div>
                    <span className="text-[10px] font-medium text-slate-400">Customer:</span>
                    <p className="text-xs text-slate-600 line-clamp-2">{ex.customer}</p>
                  </div>
                  <div>
                    <span className="text-[10px] font-medium text-slate-400">Brand Reply:</span>
                    <p className="text-xs text-slate-700 line-clamp-2 font-medium">{ex.brand}</p>
                  </div>
                </div>
              </motion.div>
            ))}
            {reply.retrieved_examples.length === 0 && (
              <p className="text-xs text-slate-400 text-center py-4">No retrieval data available</p>
            )}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="glass-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-slate-500" />
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Pipeline Metadata
            </h3>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-2.5 bg-surface-bg rounded-lg text-center">
              <div className="text-lg font-bold text-slate-800 font-mono">{response.processing_time_ms.toFixed(0)}</div>
              <div className="text-[10px] text-slate-500">Latency (ms)</div>
            </div>
            <div className="p-2.5 bg-surface-bg rounded-lg text-center">
              <div className="text-lg font-bold text-slate-800 font-mono">{reply.retrieved_examples.length}</div>
              <div className="text-[10px] text-slate-500">RAG Refs</div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}