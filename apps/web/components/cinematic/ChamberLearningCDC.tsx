'use client';

import React from 'react';
import { Database, GitCommit, Sparkles, RefreshCw, Layers, ShieldCheck } from 'lucide-react';

export default function ChamberLearningCDC() {
  const cdcEvents = [
    {
      timestamp: '18:33:02.110 UTC',
      op: 'INSERT',
      table: 'ghostops.memories',
      key: 'mem_2026_0904_db_contention',
      vectorDim: 1536,
      trustScore: 0.92,
      details: 'New institutional precedent consolidated from verified Incident #2026-904.'
    },
    {
      timestamp: '18:33:02.450 UTC',
      op: 'UPDATE',
      table: 'ghostops.precedent_trust_ledger',
      key: 'prec_1402_trust_update',
      vectorDim: 1536,
      trustScore: 0.94,
      details: 'Trust increased from 0.88 -> 0.94 (+0.06) following successful adaptive resolution.'
    },
    {
      timestamp: '18:33:03.012 UTC',
      op: 'CDC_EMIT',
      table: 'changefeed://ghostops-cdc-stream',
      key: 'cdc_sink_verified_event',
      vectorDim: 1536,
      trustScore: 0.92,
      details: 'Event broadcast to downstream sentinel monitors and regional replicas.'
    }
  ];

  return (
    <section className="py-20 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-10 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <span>CHAMBER 08</span>
          <span>·</span>
          <span>POST-REMEDIATION LEARNING & COCKROACHDB CDC CHANGEFEED</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100 mb-3">
          Continuous Institutional Consolidation & Durable CDC Streams
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          When an incident is verified, GhostOps extracts structured insights, calculates trust score updates, and inserts a 1536-dimensional vector embedding into CockroachDB. Real CDC changefeeds stream the memory across the fleet.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Memory Consolidation Pipeline */}
        <div className="lg:col-span-5 space-y-4">
          <div className="vault-panel p-5 rounded-xl border border-zinc-800 bg-zinc-950/80">
            <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 font-semibold mb-4">
              <Sparkles className="w-4 h-4" />
              <span>CONSOLIDATION PIPELINE</span>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div className="p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] uppercase block">1. Extraction & Generalization</span>
                <div className="text-zinc-200 mt-1">Symptom abstracted: "CockroachDB Range Hotspot Contention"</div>
              </div>

              <div className="p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] uppercase block">2. Vector Embedding Generation</span>
                <div className="text-emerald-400 mt-1">1536-dim vector generated via Titan Text Embeddings V2</div>
              </div>

              <div className="p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] uppercase block">3. Trust Propagation Ledger</span>
                <div className="text-zinc-200 mt-1">Base: 0.85 &rarr; Verified Outcome: +0.07 &rarr; New Trust: <span className="text-emerald-400 font-bold">0.92</span></div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Live CockroachDB CDC Feed */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-zinc-400 pb-1 border-b border-zinc-800">
            <span className="flex items-center gap-2">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              COCKROACHDB CHANGE DATA CAPTURE (CDC)
            </span>
            <span className="text-emerald-400">STREAMING ACTIVE</span>
          </div>

          <div className="space-y-2.5">
            {cdcEvents.map((evt, idx) => (
              <div key={idx} className="vault-card p-4 rounded-xl border border-zinc-800/80 bg-zinc-950/70">
                <div className="flex items-center justify-between mb-1.5 text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/40 font-bold text-[10px]">
                      {evt.op}
                    </span>
                    <span className="text-zinc-300 font-semibold">{evt.table}</span>
                  </div>
                  <span className="text-zinc-500 text-[10px]">{evt.timestamp}</span>
                </div>

                <div className="text-[11px] font-mono text-zinc-400 p-2 rounded bg-zinc-900/60 border border-zinc-800/60 mb-2">
                  <span className="text-zinc-500">Key: </span>
                  <span className="text-zinc-200">{evt.key}</span> · <span className="text-emerald-400">VECTOR({evt.vectorDim})</span> · <span className="text-emerald-400 font-semibold">Trust: {evt.trustScore}</span>
                </div>

                <p className="text-xs text-zinc-300 leading-relaxed">{evt.details}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
