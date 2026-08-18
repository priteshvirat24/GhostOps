'use client';

import React, { useState } from 'react';
import { ArrowRight, Play, Database, Cpu, ShieldCheck, Layers, GitCompare, Sparkles, ChevronDown } from 'lucide-react';
import HeroVaultScene from '../3d/scenes/HeroVaultScene';
import { NodePoint } from '../../lib/3d-math';

interface Scene01HeroProps {
  onOpenDemo: () => void;
  onExploreMemory: () => void;
  onExploreBenchmark: () => void;
  onSelectNode?: (node: NodePoint) => void;
}

export default function Scene01_Hero({ onOpenDemo, onExploreMemory, onExploreBenchmark, onSelectNode }: Scene01HeroProps) {
  const [activeConcept, setActiveConcept] = useState<{ title: string; count: string; desc: string } | null>(null);

  const handleNodeSelect = (node: NodePoint) => {
    if (onSelectNode) onSelectNode(node);
    if (node.category === 'MEMORY') {
      setActiveConcept({
        title: 'INSTITUTIONAL MEMORY',
        count: '46 Precedents Seeded',
        desc: 'CockroachDB native VECTOR(1536) hybrid operational index.'
      });
    } else if (node.category === 'TEMPORAL') {
      setActiveConcept({
        title: 'TEMPORAL REASONING',
        count: '9-Dimension Drift Diff',
        desc: 'Deterministic environment comparison proving whether old fixes still apply.'
      });
    } else if (node.category === 'VERIFICATION') {
      setActiveConcept({
        title: 'INDEPENDENT VERIFICATION',
        count: '100% Invariant Proved',
        desc: 'Out-of-band AWS CloudWatch & EC2 telemetry reader delta checks.'
      });
    } else {
      setActiveConcept({
        title: node.label,
        count: `Confidence: ${((node.confidence || 0.9) * 100).toFixed(0)}%`,
        desc: node.details || 'Active operational node in GhostOps reasoning graph.'
      });
    }
  };

  return (
    <section className="relative min-h-screen pt-24 pb-16 px-6 flex flex-col justify-center items-center overflow-hidden">
      {/* 3D Living Background Canvas */}
      <div className="absolute inset-0 z-0 opacity-90">
        <HeroVaultScene onSelectNode={handleNodeSelect} activeChamberIndex={0} />
      </div>

      {/* Grid Pattern Overlay with Radial Mask */}
      <div className="absolute inset-0 grid-bg radial-mask pointer-events-none z-1" />

      {/* Hero Content Container */}
      <div className="relative z-10 max-w-5xl mx-auto text-center flex flex-col items-center mt-4">
        {/* Status Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-zinc-900/85 border border-emerald-500/40 text-emerald-400 text-xs font-mono mb-6 backdrop-blur-md shadow-lg shadow-emerald-950/40">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="font-semibold tracking-wide">OPERATIONAL MEMORY VAULT</span>
          <span className="text-zinc-500">|</span>
          <span className="text-zinc-300">COCKROACHDB VECTOR(1536)</span>
        </div>

        {/* The Hook */}
        <h1 className="text-3xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight text-gradient-ivory mb-6 max-w-4xl leading-[1.15]">
          Production incidents repeat <br className="hidden sm:inline" />
          <span className="text-zinc-400 font-light">because organizations forget.</span> <br />
          <span className="text-gradient-sage">GhostOps turns operational history into governed memory.</span>
        </h1>

        {/* Differentiator Callout Box */}
        <div className="p-4 sm:p-5 rounded-2xl bg-zinc-950/80 border border-emerald-500/30 backdrop-blur-xl max-w-3xl mb-8 shadow-2xl shadow-emerald-950/30">
          <p className="text-sm sm:text-base text-zinc-200 leading-relaxed font-mono">
            <span className="text-emerald-400 font-bold block mb-1 uppercase tracking-wider text-xs">
              ⚡ The Core Differentiator:
            </span>
            GhostOps does not merely retrieve old incidents. It deterministically computes whether historical fixes still apply to today's drifted infrastructure before touching production.
          </p>
        </div>

        {/* Action CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 mb-10">
          <button
            onClick={onOpenDemo}
            className="flex items-center gap-2.5 px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold text-sm font-mono transition-all shadow-xl shadow-emerald-500/25 active:scale-95"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>INITIATE LIVE INVESTIGATION</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={onExploreMemory}
            className="flex items-center gap-2 px-5 py-3 rounded-xl bg-zinc-900/85 hover:bg-zinc-800 border border-zinc-700/80 text-zinc-200 text-sm font-mono transition-all backdrop-blur-md"
          >
            <Database className="w-4 h-4 text-emerald-400" />
            <span>EXPLORE MEMORY VAULT</span>
          </button>

          <button
            onClick={onExploreBenchmark}
            className="flex items-center gap-2 px-5 py-3 rounded-xl bg-zinc-900/85 hover:bg-zinc-800 border border-zinc-700/80 text-zinc-200 text-sm font-mono transition-all backdrop-blur-md"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>REGRESSION BENCHMARK</span>
          </button>
        </div>

        {/* Dynamic Concept Hover Card */}
        {activeConcept && (
          <div className="mb-8 p-3.5 rounded-xl bg-zinc-900/90 border border-emerald-500/40 text-left max-w-xl animate-fade-in font-mono shadow-xl">
            <div className="flex items-center justify-between text-xs text-emerald-400 font-bold mb-1">
              <span>{activeConcept.title}</span>
              <span className="text-zinc-300 font-semibold">{activeConcept.count}</span>
            </div>
            <p className="text-xs text-zinc-400">{activeConcept.desc}</p>
          </div>
        )}

        {/* High-Density Operational Counters */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 w-full max-w-4xl">
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
              <span>TEMPORAL DRIFT</span>
            </div>
            <div className="text-2xl font-bold text-zinc-100 font-mono">9 Dimensions</div>
            <div className="text-[11px] text-zinc-400 font-mono mt-0.5">Deterministic diff checks</div>
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
