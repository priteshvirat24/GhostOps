'use client';

import React from 'react';
import { ArrowRight, Play, Database, Cpu, ShieldCheck, Layers, GitCompare } from 'lucide-react';
import HeroVaultScene from '../3d/scenes/HeroVaultScene';
import { NodePoint } from '@/lib/3d-math';

interface ChamberHeroProps {
  onOpenDemo: () => void;
  onExploreMemory: () => void;
  onExploreBenchmark: () => void;
  onSelectNode?: (node: NodePoint) => void;
}

export default function ChamberHero({ onOpenDemo, onExploreMemory, onExploreBenchmark, onSelectNode }: ChamberHeroProps) {
  return (
    <section className="relative min-h-screen pt-24 pb-16 px-6 flex flex-col justify-center items-center overflow-hidden">
      {/* 3D Background Canvas */}
      <div className="absolute inset-0 z-0 opacity-90">
        <HeroVaultScene onSelectNode={onSelectNode} activeChamberIndex={0} />
      </div>

      {/* Grid Pattern Overlay with Radial Mask */}
      <div className="absolute inset-0 grid-bg radial-mask pointer-events-none z-1" />

      {/* Hero Content Container */}
      <div className="relative z-10 max-w-5xl mx-auto text-center flex flex-col items-center mt-6">
        {/* Status Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-6 backdrop-blur-md">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="font-medium tracking-wide">AUTONOMOUS INCIDENT MEMORY ENGINE</span>
          <span className="text-zinc-500">|</span>
          <span className="text-zinc-400">COCKROACHDB VECTOR(1536)</span>
        </div>

        {/* Cinematic Headline */}
        <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-gradient-ivory mb-6 max-w-4xl leading-[1.1]">
          Production forgets. <br />
          <span className="text-gradient-sage">GhostOps remembers.</span>
        </h1>

        {/* Narrative Description */}
        <p className="text-base sm:text-lg md:text-xl text-zinc-300 max-w-3xl mb-8 leading-relaxed font-normal">
          Reconstructs what happened from raw telemetry, queries institutional memory via native vectors,
          proves whether historical precedents still apply through <span className="text-emerald-400 font-medium">9-dimension temporal reasoning</span>,
          and executes governed 2PC sagas before touching production.
        </p>

        {/* Action CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 mb-12">
          <button
            onClick={onOpenDemo}
            className="flex items-center gap-2.5 px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold text-sm font-mono transition-all duration-200 shadow-xl shadow-emerald-500/25 active:scale-95"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>INITIATE INVESTIGATION</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={onExploreMemory}
            className="flex items-center gap-2 px-5 py-3 rounded-xl bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-700/80 text-zinc-200 text-sm font-mono transition-all duration-200 backdrop-blur-md"
          >
            <Database className="w-4 h-4 text-emerald-400" />
            <span>EXPLORE MEMORY VAULT</span>
          </button>

          <button
            onClick={onExploreBenchmark}
            className="flex items-center gap-2 px-5 py-3 rounded-xl bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-700/80 text-zinc-200 text-sm font-mono transition-all duration-200 backdrop-blur-md"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>EMPIRICAL BENCHMARK</span>
          </button>
        </div>

        {/* High-Density Operational Counters */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full max-w-4xl">
          <div className="vault-card p-4 rounded-xl text-left border border-zinc-800/80 bg-zinc-950/70">
            <div className="flex items-center gap-2 text-zinc-400 text-xs font-mono mb-1">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <span>INSTITUTIONAL MEMORY</span>
            </div>
            <div className="text-2xl font-bold text-zinc-100 font-mono">46 Precedents</div>
            <div className="text-[11px] text-zinc-400 font-mono mt-0.5">CockroachDB native vector</div>
          </div>

          <div className="vault-card p-4 rounded-xl text-left border border-zinc-800/80 bg-zinc-950/70">
            <div className="flex items-center gap-2 text-zinc-400 text-xs font-mono mb-1">
              <Layers className="w-3.5 h-3.5 text-emerald-400" />
              <span>EMBEDDING SPACE</span>
            </div>
            <div className="text-2xl font-bold text-zinc-100 font-mono">1,536-Dim</div>
            <div className="text-[11px] text-zinc-400 font-mono mt-0.5">Titan / Bedrock Mantle</div>
          </div>

          <div className="vault-card p-4 rounded-xl text-left border border-zinc-800/80 bg-zinc-950/70">
            <div className="flex items-center gap-2 text-zinc-400 text-xs font-mono mb-1">
              <GitCompare className="w-3.5 h-3.5 text-emerald-400" />
              <span>TEMPORAL DIFFING</span>
            </div>
            <div className="text-2xl font-bold text-zinc-100 font-mono">9 Dimensions</div>
            <div className="text-[11px] text-zinc-400 font-mono mt-0.5">Deterministic drift check</div>
          </div>

          <div className="vault-card p-4 rounded-xl text-left border border-zinc-800/80 bg-zinc-950/70">
            <div className="flex items-center gap-2 text-zinc-400 text-xs font-mono mb-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>UNSAFE REPLAY RATE</span>
            </div>
            <div className="text-2xl font-bold text-emerald-400 font-mono">0.00%</div>
            <div className="text-[11px] text-zinc-400 font-mono mt-0.5">Regression gate: PASSED</div>
          </div>
        </div>
      </div>
    </section>
  );
}
