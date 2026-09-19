"use client";

import { Activity, Wifi, WifiOff } from "lucide-react";

interface StatusBarProps {
  isReady: boolean;
  ticketCount: number;
}

export default function StatusBar({ isReady, ticketCount }: StatusBarProps) {
  return (
    <div className="h-8 bg-slate-900 text-white flex items-center justify-between px-4 text-xs font-medium">
      <div className="flex items-center gap-3">
        <Activity className="w-3.5 h-3.5 text-brand-400" />
        <span className="text-slate-300">Hiver AI Support Agent</span>
        <span className="text-slate-500">v1.0</span>
      </div>

      <div className="flex items-center gap-4">
        <span className="text-slate-400">{ticketCount} tickets</span>
        <div className="flex items-center gap-1.5">
          {isReady ? (
            <>
              <Wifi className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400">Connected</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3.5 h-3.5 text-rose-400" />
              <span className="text-rose-400">Disconnected</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}