"use client";

import { useState, useRef } from "react";
import { motion } from "framer-motion";
import { Sparkles, Send, ChevronDown, Zap } from "lucide-react";
import clsx from "clsx";
import type { PresetScenario } from "@/types";

interface TopBarProps {
  presets: PresetScenario[];
  onSubmit: (message: string, preset?: PresetScenario) => void;
  isProcessing: boolean;
  isReady: boolean;
}

export default function TopBar({ presets, onSubmit, isProcessing, isReady }: TopBarProps) {
  const [input, setInput] = useState("");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = () => {
    if (!input.trim() || isProcessing || !isReady) return;
    onSubmit(input.trim());
    setInput("");
  };

  const handlePresetSelect = (preset: PresetScenario) => {
    setInput(preset.message);
    setIsDropdownOpen(false);
    onSubmit(preset.message, preset);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="bg-white border-b border-surface-border px-6 py-4">
      <div className="max-w-5xl mx-auto flex items-center gap-3">
        <div className="relative">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className={clsx(
              "flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium",
              "border border-surface-border hover:border-brand-300",
              "bg-surface-bg hover:bg-brand-50 transition-all duration-200",
              "text-slate-600 hover:text-brand-700"
            )}
          >
            <Zap className="w-4 h-4" />
            <span>Scenarios</span>
            <ChevronDown className={clsx(
              "w-4 h-4 transition-transform duration-200",
              isDropdownOpen && "rotate-180"
            )} />
          </button>

          {isDropdownOpen && (
            <motion.div
              initial={{ opacity: 0, y: -8, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.96 }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
              className="absolute top-full left-0 mt-2 w-80 bg-white rounded-xl border 
                         border-surface-border shadow-glass-lg z-50 py-2 max-h-96 overflow-y-auto"
            >
              {presets.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => handlePresetSelect(preset)}
                  className="w-full text-left px-4 py-3 hover:bg-surface-hover 
                             transition-colors duration-150"
                >
                  <div className="text-sm font-medium text-slate-800">
                    {preset.label}
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5 line-clamp-1">
                    {preset.message.slice(0, 60)}…
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={clsx(
                      "text-[10px] px-1.5 py-0.5 rounded-full font-medium",
                      preset.severity === "critical" && "bg-rose-50 text-rose-600",
                      preset.severity === "high" && "bg-amber-50 text-amber-600",
                      preset.severity === "medium" && "bg-blue-50 text-blue-600",
                      preset.severity === "low" && "bg-slate-50 text-slate-500",
                    )}>
                      {preset.severity}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      {preset.customer_handle}
                    </span>
                  </div>
                </button>
              ))}
            </motion.div>
          )}
        </div>

        <div className="flex-1 relative">
          <Sparkles className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isReady ? "Type a customer message or pick a scenario…" : "Waiting for backend…"}
            disabled={!isReady || isProcessing}
            className={clsx(
              "w-full pl-11 pr-4 py-2.5 rounded-xl text-sm",
              "bg-surface-bg border border-surface-border",
              "focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400",
              "placeholder:text-slate-400 transition-all duration-200",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          />
        </div>

        <motion.button
          onClick={handleSubmit}
          disabled={!input.trim() || isProcessing || !isReady}
          whileTap={{ scale: 0.92 }}
          whileHover={{ scale: 1.04 }}
          transition={{ type: "spring", stiffness: 400, damping: 17 }}
          className={clsx(
            "flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold",
            "transition-all duration-200",
            input.trim() && isReady && !isProcessing
              ? "bg-brand-600 text-white hover:bg-brand-700 shadow-md shadow-brand-600/20"
              : "bg-slate-100 text-slate-400 cursor-not-allowed"
          )}
        >
          {isProcessing ? (
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
          <span>{isProcessing ? "Processing…" : "Ingest"}</span>
        </motion.button>
      </div>
    </div>
  );
}