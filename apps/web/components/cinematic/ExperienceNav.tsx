'use client';

import React, { useState, useEffect } from 'react';
import { Shield, Database, Cpu, Activity, Play, Radio, ChevronDown } from 'lucide-react';
import { SystemHealth } from '../../types';

interface ExperienceNavProps {
  health?: SystemHealth | null;
  activeChamber: number;
  onSelectChamber: (index: number) => void;
  onOpenDemo: () => void;
}

const CHAPTERS = [
  { id: 0, label: 'THE HOOK' },
  { id: 1, label: 'PROBLEM / SOLUTION' },
  { id: 2, label: 'MEMORY VAULT' },
  { id: 3, label: 'INVESTIGATION' },
  { id: 4, label: 'TEMPORAL CHAMBER' },
  { id: 5, label: 'GOVERNANCE' },
  { id: 6, label: '2PC SAGA' },
  { id: 7, label: 'VERIFICATION' },
  { id: 8, label: 'LEARNING LOOP' },
  { id: 9, label: 'CDC STREAM' },
  { id: 10, label: 'GHOST REPLAY' },
  { id: 11, label: 'BENCHMARK' },
];

export default function ExperienceNav({ health, activeChamber, onSelectChamber, onOpenDemo }: ExperienceNavProps) {
  const [timeStr, setTimeStr] = useState<string>('');
  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);

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
    <header className="fixed top-0 left-0 right-0 z-50 px-4 sm:px-6 py-2.5 border-b border-zinc-800/80 bg-zinc-950/85 backdrop-blur-2xl transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        {/* Brand & Project Identity */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-emerald-500/40 flex items-center justify-center shadow-lg shadow-emerald-950/50">
            <Shield className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-wider text-sm text-zinc-100 font-mono">GHOSTOPS</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-950/80 border border-emerald-800/50 text-emerald-300">
                PROD
              </span>
            </div>
            <span className="text-[10px] text-zinc-400 font-mono hidden sm:inline-block">
              INSTITUTIONAL MEMORY & REASONING VAULT
            </span>
          </div>
        </div>

        {/* Desktop Chapter Jump Navigation */}
        <nav className="hidden xl:flex items-center gap-0.5 p-1 rounded-xl bg-zinc-900/70 border border-zinc-800/70 overflow-x-auto">
          {CHAPTERS.map((ch) => {
            const isActive = activeChamber === ch.id;
            return (
              <button
                key={ch.id}
                onClick={() => onSelectChamber(ch.id)}
                className={`px-2 py-0.5 rounded-lg text-[10px] font-mono transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/50 font-bold shadow-sm'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
                }`}
              >
                {ch.id.toString().padStart(2, '0')} {ch.label}
              </button>
            );
          })}
        </nav>

        {/* Mobile/Tablet Chapter Dropdown */}
        <div className="relative xl:hidden">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-300"
          >
            <span>SCENE {activeChamber.toString().padStart(2, '0')}: {CHAPTERS[activeChamber]?.label}</span>
            <ChevronDown className="w-3 h-3 text-zinc-400" />
          </button>
          {isDropdownOpen && (
            <div className="absolute top-full mt-1 right-0 w-48 rounded-xl bg-zinc-950 border border-zinc-800 shadow-2xl p-1.5 z-50 max-h-64 overflow-y-auto">
              {CHAPTERS.map((ch) => (
                <button
                  key={ch.id}
                  onClick={() => {
                    onSelectChamber(ch.id);
                    setIsDropdownOpen(false);
                  }}
                  className={`w-full text-left px-2.5 py-1 rounded-lg text-[11px] font-mono transition-all ${
                    activeChamber === ch.id
                      ? 'bg-emerald-950 text-emerald-300 font-bold'
                      : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
                  }`}
                >
                  {ch.id.toString().padStart(2, '0')} {ch.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Real-time System Indicators & Action CTA */}
        <div className="flex items-center gap-2.5">
          {/* CockroachDB Status */}
          <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-zinc-900/80 border border-zinc-800 text-[10px] font-mono">
            <Database className={`w-3 h-3 ${health?.database_connected ? 'text-emerald-400' : 'text-amber-400'}`} />
            <span className="text-zinc-300">CRDB CLOUD</span>
            <span className={`w-1.5 h-1.5 rounded-full ${health?.database_connected ? 'bg-emerald-400' : 'bg-amber-400'} animate-pulse`} />
          </div>

          {/* Bedrock AI Mode */}
          <div className="hidden md:flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-zinc-900/80 border border-zinc-800 text-[10px] font-mono">
            <Cpu className="w-3 h-3 text-emerald-400" />
            <span className="text-zinc-300">BEDROCK MANTLE</span>
            <span className="text-emerald-400 font-bold">LIVE</span>
          </div>

          {/* Live System Clock */}
          <div className="hidden lg:flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-zinc-900/40 border border-zinc-800/60 text-[10px] font-mono text-zinc-400">
            <Activity className="w-3 h-3 text-zinc-500" />
            <span>{timeStr || 'LIVE'}</span>
          </div>

          {/* Primary CTA */}
          <button
            onClick={onOpenDemo}
            className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold text-xs font-mono transition-all shadow-md shadow-emerald-500/20 active:scale-95 whitespace-nowrap"
          >
            <Play className="w-3 h-3 fill-current" />
            <span>DEMO REPLAY</span>
          </button>
        </div>
      </div>
    </header>
  );
}
