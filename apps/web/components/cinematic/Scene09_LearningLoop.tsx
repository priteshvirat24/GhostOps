'use client';

import React from 'react';
import { Sparkles, Database, Layers, ArrowRight, CheckCircle2, ShieldCheck } from 'lucide-react';

export default function Scene09_LearningLoop() {
  const learningSteps = [
    {
      step: 1,
      title: 'Verified Incident Outcome',
      desc: 'Incident #2026-904 resolved with zero regressions. Invariant recovery proved via independent reader.'
    },
    {
      step: 2,
      title: 'Insight Abstraction & Generalization',
      desc: 'Synthesizes canonical lesson: "Adaptive leaseholder transfer on range hotspots restores latency without SG mutations."'
    },
    {
      step: 3,
      title: '1536-Dim Semantic Embedding',
      desc: 'Titan Text Embeddings V2 generates native 1536-dimensional vector representation for nearest-neighbor hybrid search.'
    },
    {
      step: 4,
      title: 'CockroachDB Memory Ingestion',
      desc: 'Durable insert into `memories` table with verified trust level = 0.92 and immutable provenance record.'
    }
  ];

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-12 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <span>SCENE 09</span>
          <span>·</span>
          <span>THE CLOSED-LOOP LEARNING PIPELINE</span>
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-zinc-100 mb-4">
          The Intelligence Loop Closes: Institutional Memory Consolidation
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          GhostOps does not let knowledge evaporate into stale wikis. Once verified, insights are abstracted, embedded into 1536-dimensional vector space, and durably written to CockroachDB Serverless.
        </p>
      </div>

      {/* 4-Stage Learning Cycle Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {learningSteps.map((s) => (
          <div key={s.step} className="vault-panel p-5 rounded-2xl border border-zinc-800 bg-zinc-950/80 shadow-xl flex flex-col justify-between font-mono text-xs">
            <div>
              <div className="flex items-center justify-between mb-3 text-emerald-400 font-bold">
                <span className="w-6 h-6 rounded-full bg-emerald-950 border border-emerald-500/40 flex items-center justify-center text-[10px]">
                  0{s.step}
                </span>
                <span className="text-[10px] text-zinc-500">STAGE 0{s.step}</span>
              </div>
              <h4 className="text-sm font-bold text-zinc-100 mb-2">{s.title}</h4>
              <p className="text-zinc-400 text-[11px] leading-relaxed">{s.desc}</p>
            </div>

            <div className="mt-4 pt-3 border-t border-zinc-800 text-[10px] text-emerald-400 flex items-center gap-1 font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5" /> PROCESSED
            </div>
          </div>
        ))}
      </div>

      {/* Newly Generated Memory Card */}
      <div className="vault-card p-6 rounded-2xl border border-emerald-500/40 bg-zinc-950/90 shadow-2xl shadow-emerald-950/30 font-mono text-xs">
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-800">
          <div className="flex items-center gap-2 text-emerald-400 font-bold">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <span>NEWLY CONSOLIDATED INSTITUTIONAL MEMORY</span>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold">
            MEM-2026-0904-CONSOLIDATED
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 my-3">
          <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
            <span className="text-zinc-500 text-[10px] block uppercase">Vector Representation</span>
            <span className="text-zinc-200 font-bold mt-0.5 block">1536-Dim Float Array</span>
            <span className="text-[10px] text-emerald-400">[0.0412, -0.0194, 0.0812, ...]</span>
          </div>

          <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
            <span className="text-zinc-500 text-[10px] block uppercase">Trust Level</span>
            <span className="text-emerald-400 font-bold text-sm mt-0.5 block">0.92 (HIGH_TRUST)</span>
            <span className="text-[10px] text-zinc-400">Propagated fleet-wide</span>
          </div>

          <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
            <span className="text-zinc-500 text-[10px] block uppercase">Database Target</span>
            <span className="text-zinc-200 font-bold mt-0.5 block">CockroachDB Serverless</span>
            <span className="text-[10px] text-zinc-400">Table: institutional_memories</span>
          </div>
        </div>

        <p className="text-zinc-300 text-xs leading-relaxed bg-zinc-900/60 p-3 rounded-xl border border-zinc-800/60 mt-2">
          "When CockroachDB client connection pool exhausts due to range contention hotspots on port 26257, perform adaptive lease relocation to an idle node and drain stale idle connections. Do NOT alter security group ingress rules."
        </p>
      </div>
    </section>
  );
}
