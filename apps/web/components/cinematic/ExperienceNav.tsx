'use client';

import React, { useState, useEffect } from 'react';
import { Shield, Database, Cpu, Activity, Play, Radio } from 'lucide-react';
import { SystemHealth } from '../../types';

interface ExperienceNavProps {
  health?: SystemHealth | null;
  activeChamber: number;
  onSelectChamber: (index: number) => void;
  onOpenDemo: () => void;
}

const CHAMBERS = [
  { id: 0, label: 'VAULT' },
  { id: 1, label: 'INGEST' },
  { id: 2, label: 'VECTOR MEMORY' },
  { id: 3, label: 'REASONING' },
  { id: 4, label: 'TEMPORAL DRIFT' },
  { id: 5, label: 'GOVERNED SAGA' },
  { id: 6, label: 'VERIFICATION' },
  { id: 7, label: 'CDC LEARNING' },
  { id: 8, label: 'BENCHMARK' },
];

export default function ExperienceNav({ health, activeChamber, onSelectChamber, onOpenDemo }: ExperienceNavProps) {
  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toTimeString().split(' ')[0] + ' UTC');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 px-6 py-3 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-xl transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Brand & Project Identity */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-emerald-500/40 flex items-center justify-center shadow-lg shadow-emerald-950/50">
            <Shield className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-wider text-sm text-zinc-100 font-mono">GHOSTOPS</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/70 border border-emerald-800/50 text-emerald-300">
                v1.0.0-PROD
              </span>
            </div>
            <span className="text-[10px] text-zinc-400 font-mono hidden sm:inline-block">
              INSTITUTIONAL MEMORY & REASONING ENGINE
            </span>
          </div>
        </div>

        {/* Chamber Chapter Navigation */}
        <nav className="hidden lg:flex items-center gap-1 p-1 rounded-xl bg-zinc-900/60 border border-zinc-800/60">
          {CHAMBERS.map((ch) => {
            const isActive = activeChamber === ch.id;
            return (
              <button
                key={ch.id}
                onClick={() => onSelectChamber(ch.id)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-mono transition-all duration-200 ${
                  isActive
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40 font-semibold shadow-sm'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
                }`}
              >
                {ch.id.toString().padStart(2, '0')} {ch.label}
              </button>
            );
          })}
        </nav>

        {/* Real-time System Indicators & CTA */}
        <div className="flex items-center gap-3">
          {/* CockroachDB Status */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-zinc-900/80 border border-zinc-800 text-[11px] font-mono">
            <Database className={`w-3 h-3 ${health?.database_connected ? 'text-emerald-400' : 'text-amber-400'}`} />
            <span className="text-zinc-300">CRDB CLOUD</span>
            <span className={`w-1.5 h-1.5 rounded-full ${health?.database_connected ? 'bg-emerald-400' : 'bg-amber-400'} animate-pulse`} />
          </div>

          {/* AI Reasoning Mode Status */}
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-zinc-900/80 border border-zinc-800 text-[11px] font-mono">
            <Cpu className="w-3 h-3 text-emerald-400" />
            <span className="text-zinc-300">BEDROCK MANTLE</span>
            <span className="text-emerald-400 font-semibold">LIVE</span>
          </div>

          {/* System Clock */}
          <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-zinc-900/40 border border-zinc-800/60 text-[10px] font-mono text-zinc-400">
            <Activity className="w-3 h-3 text-zinc-500" />
            <span>{timeStr || 'LIVE'}</span>
          </div>

          {/* Primary CTA: Launch Incident Demo Runner */}
          <button
            onClick={onOpenDemo}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-semibold text-xs font-mono transition-all duration-200 shadow-lg shadow-emerald-500/20 active:scale-95"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>DEMO REPLAY</span>
          </button>
        </div>
      </div>
    </header>
  );
}
