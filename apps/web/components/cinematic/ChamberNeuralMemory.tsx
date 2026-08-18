'use client';

import React, { useState } from 'react';
import { Database, Sliders, Layers, Sparkles, Clock, Compass } from 'lucide-react';
import MemoryConstellationScene from '../3d/scenes/MemoryConstellationScene';

export default function ChamberNeuralMemory() {
  const [stalenessDays, setStalenessDays] = useState<number>(14);
  const [selectedCluster, setSelectedCluster] = useState<string>('all');

  // Exponential half-life decay formula: exp(-0.05 * days)
  const decayMultiplier = Math.exp(-0.05 * stalenessDays);

  const mockPrecedents = [
    {
      id: 'PREC-1847',
      title: 'VPC Ingress Unauthorized SSH Exposure',
      category: 'Network/Security',
      createdDaysAgo: 60,
      vectorScore: 0.94,
      structuredScore: 0.90,
      baseScore: 0.92,
      trustScore: 0.95,
      compatibility: 'DRIFT_DETECTED',
      verdict: 'DO_NOT_EXECUTE',
      remediationSummary: 'Historical fix modified security group ingress rule directly.'
    },
    {
      id: 'PREC-1402',
      title: 'CockroachDB Range Leaseholder Contention',
      category: 'Database',
      createdDaysAgo: 12,
      vectorScore: 0.89,
      structuredScore: 0.85,
      baseScore: 0.88,
      trustScore: 0.92,
      compatibility: 'COMPATIBLE',
      verdict: 'SAFE_TO_EXECUTE',
      remediationSummary: 'Auto-rebalanced range leaseholders across node 1 and 3.'
    },
    {
      id: 'PREC-1109',
      title: 'Auth-Service Connection Pool Starvation',
      category: 'Application',
      createdDaysAgo: 5,
      vectorScore: 0.91,
      structuredScore: 0.88,
      baseScore: 0.90,
      trustScore: 0.89,
      compatibility: 'COMPATIBLE',
      verdict: 'SAFE_TO_EXECUTE',
      remediationSummary: 'Drained stale connections and scaled replica count to 4.'
    }
  ];

  return (
    <section className="py-20 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-10 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <span>CHAMBER 03</span>
          <span>·</span>
          <span>LIVING NEURAL MEMORY & NATIVE HYBRID RETRIEVAL</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100 mb-3">
          CockroachDB Native VECTOR(1536) & 6-Factor Hybrid Scoring
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          GhostOps stores 46 curated institutional memory precedents in CockroachDB Serverless. Vector cosine similarity is fused with structured filters, trust weights, and continuous temporal staleness decay.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: 3D Vector Space Constellation */}
        <div className="lg:col-span-7 flex flex-col justify-between">
          <div className="h-[400px] w-full mb-4">
            <MemoryConstellationScene stalenessWeight={decayMultiplier} highlightCategory={selectedCluster} />
          </div>

          {/* Hybrid Formula Breakdown Bar */}
          <div className="vault-panel p-4 rounded-xl border border-zinc-800 bg-zinc-950/80">
            <div className="text-xs font-mono text-emerald-400 font-semibold mb-2 flex items-center gap-2">
              <Sliders className="w-3.5 h-3.5" />
              <span>HYBRID SCORING WEIGHT FORMULA</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-center text-[10px] font-mono">
              <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-400">VECTOR</span>
                <div className="text-emerald-400 font-bold text-xs mt-0.5">40%</div>
              </div>
              <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-400">STRUCTURED</span>
                <div className="text-emerald-400 font-bold text-xs mt-0.5">30%</div>
              </div>
              <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-400">OUTCOME</span>
                <div className="text-emerald-400 font-bold text-xs mt-0.5">15%</div>
              </div>
              <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-400">STALENESS</span>
                <div className="text-amber-400 font-bold text-xs mt-0.5">15%</div>
              </div>
              <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-400">TRUST</span>
                <div className="text-emerald-400 font-bold text-xs mt-0.5">10%</div>
              </div>
              <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-400">COMPAT</span>
                <div className="text-emerald-400 font-bold text-xs mt-0.5">10%</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Staleness Decay Controller & Precedents List */}
        <div className="lg:col-span-5 space-y-4">
          {/* Interactive Staleness Decay Slider */}
          <div className="vault-panel p-4 rounded-xl border border-zinc-800 bg-zinc-950/80">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono text-zinc-300 font-semibold flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-amber-400" />
                TEMPORAL STALENESS SIMULATOR
              </span>
              <span className="text-xs font-mono text-amber-400 font-bold">{stalenessDays} Days Elapsed</span>
            </div>
            <input
              type="range"
              min="1"
              max="90"
              value={stalenessDays}
              onChange={(e) => setStalenessDays(Number(e.target.value))}
              className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"
            />
            <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500 mt-2">
              <span>Day 1 (1.0x Fresh)</span>
              <span className="text-amber-300 font-medium">Decay: {(decayMultiplier * 100).toFixed(1)}% Multiplier</span>
              <span>Day 90 (0.01x Stale)</span>
            </div>
          </div>

          {/* Retrieved Precedents */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between text-xs font-mono text-zinc-400 pb-1">
              <span>TOP RETRIEVED PRECEDENTS</span>
              <span className="text-emerald-400">COCKROACHDB VECTOR SCAN</span>
            </div>

            {mockPrecedents.map((p) => {
              const adjustedScore = (p.baseScore * (p.createdDaysAgo > 30 ? decayMultiplier : 1.0)).toFixed(3);
              return (
                <div key={p.id} className="vault-card p-3.5 rounded-xl border border-zinc-800/80 bg-zinc-950/60">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-zinc-100">{p.id}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300">
                        {p.category}
                      </span>
                    </div>
                    <span className="text-xs font-mono font-bold text-emerald-400">
                      Score: {adjustedScore}
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-zinc-200 mb-1">{p.title}</div>
                  <p className="text-[11px] text-zinc-400 mb-2 leading-relaxed">{p.remediationSummary}</p>
                  <div className="flex items-center justify-between text-[10px] font-mono pt-2 border-t border-zinc-800/50">
                    <span className="text-zinc-500">{p.createdDaysAgo}d old · Trust: {p.trustScore}</span>
                    <span
                      className={`font-semibold ${
                        p.verdict === 'DO_NOT_EXECUTE' ? 'text-red-400' : 'text-emerald-400'
                      }`}
                    >
                      {p.verdict}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
