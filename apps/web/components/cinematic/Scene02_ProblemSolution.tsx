'use client';

import React, { useState } from 'react';
import { AlertTriangle, ShieldCheck, ArrowRight, XCircle, CheckCircle2, RefreshCw, Zap, Cpu, Database } from 'lucide-react';

export default function Scene02_ProblemSolution() {
  const [activeSide, setActiveSide] = useState<'both' | 'typical' | 'ghostops'>('both');

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-12 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <span>SCENE 02</span>
          <span>·</span>
          <span>THE OPERATIONAL PARADIGM SHIFT</span>
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-zinc-100 mb-4">
          Why Traditional Incident Response Fails & How GhostOps Fixes It
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          Standard on-call engineering relies on manual search, stale runbooks, and dangerous trial-and-error. GhostOps establishes a verifiable closed-loop memory and temporal governance boundary.
        </p>
      </div>

      {/* Split Comparison Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
        {/* Left: The Typical Chaotic Incident Process */}
        <div className="vault-panel p-6 sm:p-8 rounded-2xl border border-red-900/40 bg-zinc-950/90 shadow-2xl flex flex-col justify-between relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-red-950/20 blur-3xl pointer-events-none" />
          <div>
            <div className="flex items-center justify-between pb-3 mb-6 border-b border-zinc-800/80">
              <div className="flex items-center gap-2 text-red-400 font-mono text-xs font-bold uppercase tracking-wider">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                <span>Typical Incident Response</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-950/60 border border-red-800/50 text-red-300">
                CHAOTIC & FRAGMENTED
              </span>
            </div>

            {/* Stepped Linear Failure Cascade */}
            <div className="space-y-3 font-mono text-xs">
              <div className="p-3.5 rounded-xl bg-zinc-900/80 border border-zinc-800 flex items-center justify-between">
                <span className="text-zinc-300 font-semibold">1. Production Outage Occurs</span>
                <span className="text-red-400 text-[10px]">PagerDuty Alert</span>
              </div>
              <div className="p-3.5 rounded-xl bg-zinc-900/80 border border-zinc-800 flex items-center justify-between">
                <span className="text-zinc-300 font-semibold">2. Manual Search in Slack & Jira</span>
                <span className="text-zinc-500 text-[10px]">Keyword Guesswork</span>
              </div>
              <div className="p-3.5 rounded-xl bg-zinc-900/80 border border-zinc-800 flex items-center justify-between">
                <span className="text-zinc-300 font-semibold">3. Follow Outdated 2024 Wiki Runbook</span>
                <span className="text-amber-400 text-[10px]">Untested Precedent</span>
              </div>
              <div className="p-3.5 rounded-xl bg-zinc-900/80 border border-red-900/50 flex items-center justify-between bg-red-950/20">
                <span className="text-red-300 font-semibold">4. Unsafe Execution on Drifted VPC</span>
                <span className="text-red-400 text-[10px]">Blind SSH Mutation</span>
              </div>
              <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-700/60 flex items-center justify-between">
                <span className="text-red-200 font-bold">5. Cascading Outage / Zero Learning</span>
                <span className="text-red-400 font-bold text-[10px]">Outage Repeats in 6 Mos</span>
              </div>
            </div>
          </div>

          <div className="mt-8 pt-4 border-t border-zinc-800/80 text-[11px] font-mono text-zinc-400 flex items-center justify-between">
            <span>Result:</span>
            <span className="text-red-400 font-bold flex items-center gap-1">
              <XCircle className="w-3.5 h-3.5" /> High MTTR & Recurring Failures
            </span>
          </div>
        </div>

        {/* Right: GhostOps Governed Intelligence Loop */}
        <div className="vault-panel p-6 sm:p-8 rounded-2xl border border-emerald-500/50 bg-zinc-950/90 shadow-2xl shadow-emerald-950/30 flex flex-col justify-between relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-950/20 blur-3xl pointer-events-none" />
          <div>
            <div className="flex items-center justify-between pb-3 mb-6 border-b border-zinc-800/80">
              <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs font-bold uppercase tracking-wider">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>GhostOps Autonomous Governance</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-800/60 text-emerald-300 font-bold">
                CLOSED-LOOP INTELLIGENCE
              </span>
            </div>

            {/* Stepped Governed Memory Loop */}
            <div className="space-y-3 font-mono text-xs">
              <div className="p-3.5 rounded-xl bg-zinc-900/80 border border-emerald-900/40 flex items-center justify-between">
                <span className="text-zinc-200 font-semibold">1. Telemetry Ingestion + SHA-256 Hash</span>
                <span className="text-emerald-400 text-[10px]">Immutable Evidence</span>
              </div>
              <div className="p-3.5 rounded-xl bg-zinc-900/80 border border-emerald-900/40 flex items-center justify-between">
                <span className="text-zinc-200 font-semibold">2. CockroachDB 1536-Dim Vector Retrieval</span>
                <span className="text-emerald-400 text-[10px]">Hybrid Precedent Search</span>
              </div>
              <div className="p-3.5 rounded-xl bg-zinc-900/80 border border-amber-500/40 flex items-center justify-between bg-amber-950/20">
                <span className="text-amber-300 font-semibold">3. Deterministic 9D Temporal Drift Diff</span>
                <span className="text-amber-400 font-bold text-[10px]">Rejects Incompatible Fixes</span>
              </div>
              <div className="p-3.5 rounded-xl bg-zinc-900/80 border border-emerald-900/40 flex items-center justify-between">
                <span className="text-zinc-200 font-semibold">4. Governed 2PC Saga Plan Execution</span>
                <span className="text-emerald-400 text-[10px]">Schema & Policy Gated</span>
              </div>
              <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/60 flex items-center justify-between">
                <span className="text-emerald-200 font-bold">5. Independent Verification + CDC Learning</span>
                <span className="text-emerald-400 font-bold text-[10px]">Trust Propagates to Memory</span>
              </div>
            </div>
          </div>

          <div className="mt-8 pt-4 border-t border-zinc-800/80 text-[11px] font-mono text-zinc-400 flex items-center justify-between">
            <span>Result:</span>
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> 0% Unsafe Replay & Continuous Learning
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
