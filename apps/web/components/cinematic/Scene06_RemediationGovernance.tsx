'use client';

import React, { useState } from 'react';
import { Lock, ShieldCheck, CheckCircle2, AlertTriangle, Play, RotateCcw, ArrowRight, ShieldAlert, Cpu } from 'lucide-react';

export default function Scene06_RemediationGovernance() {
  const [isApproved, setIsApproved] = useState<boolean>(true);

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-12 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <span>SCENE 06</span>
          <span>·</span>
          <span>REMEDIATION GOVERNANCE CHAMBER</span>
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-zinc-100 mb-4">
          LLM Recommends. Code Governs. Human Authorizes. System Executes.
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          GhostOps strictly enforces an execution governance boundary. Remediation proposals must pass deterministic schema checks, blast radius safety limits, and dual-phase human authorization before any production mutation is permitted.
        </p>
      </div>

      {/* Visual Governance Manifesto Banner */}
      <div className="p-6 rounded-2xl bg-zinc-950/90 border border-emerald-500/40 shadow-2xl shadow-emerald-950/30 mb-8 backdrop-blur-xl">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center font-mono">
          <div className="p-3 rounded-xl bg-zinc-900/80 border border-zinc-800">
            <span className="text-zinc-500 text-[10px] uppercase block">1. Proposal</span>
            <span className="text-zinc-200 font-bold text-sm mt-1 block">LLM RECOMMENDS</span>
          </div>
          <div className="p-3 rounded-xl bg-zinc-900/80 border border-emerald-900/50">
            <span className="text-emerald-400 text-[10px] uppercase block">2. Policy Gate</span>
            <span className="text-emerald-300 font-bold text-sm mt-1 block">CODE GOVERNS</span>
          </div>
          <div className="p-3 rounded-xl bg-zinc-900/80 border border-amber-900/50">
            <span className="text-amber-400 text-[10px] uppercase block">3. Safety Gate</span>
            <span className="text-amber-300 font-bold text-sm mt-1 block">HUMAN AUTHORIZES</span>
          </div>
          <div className="p-3 rounded-xl bg-emerald-950/50 border border-emerald-500/60">
            <span className="text-emerald-400 text-[10px] uppercase block">4. Boundary</span>
            <span className="text-emerald-400 font-bold text-sm mt-1 block">SYSTEM EXECUTES</span>
          </div>
        </div>
      </div>

      {/* Central Action Object & Governance Criteria Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Central Governed Action Card */}
        <div className="lg:col-span-7">
          <div className="vault-panel p-6 sm:p-7 rounded-2xl border border-zinc-800 bg-zinc-950/90 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                <span className="text-xs font-mono font-bold text-zinc-100 uppercase tracking-wide">
                  PLAN ID: PLAN-2026-904-A
                </span>
              </div>
              <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/60 font-bold">
                CONFIDENCE: 92%
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] uppercase block">Primary Action</span>
                <span className="text-emerald-400 font-bold text-sm">COCKROACH_RELOCATE_RANGE</span>
                <span className="text-zinc-400 block text-[10px] mt-0.5">Target: crdb://ranges/1042</span>
              </div>

              <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] uppercase block">Secondary Action</span>
                <span className="text-emerald-400 font-bold text-sm">DRAIN_CONNECTION_POOL</span>
                <span className="text-zinc-400 block text-[10px] mt-0.5">Target: service://auth-service/pool</span>
              </div>
            </div>

            {/* Structured Schema Properties */}
            <div className="space-y-2 text-xs font-mono bg-zinc-900/60 p-4 rounded-xl border border-zinc-800">
              <div className="flex items-center justify-between">
                <span className="text-zinc-500">Blast Radius:</span>
                <span className="text-zinc-200 font-semibold">LOCALIZED_TIER_2 (auth-service only)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-zinc-500">Historical Precedent:</span>
                <span className="text-emerald-400">PREC-1402 (Lease Contention Rebalance)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-zinc-500">Temporal Compatibility:</span>
                <span className="text-emerald-400 font-semibold">1.00 (Compatible across all 9 dimensions)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-zinc-500">Automatic Compensation:</span>
                <span className="text-emerald-400">ENABLED (State snapshot prior to mutation)</span>
              </div>
            </div>

            {/* Approval Controls */}
            <div className="pt-3 border-t border-zinc-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-zinc-400">Policy Authorization:</span>
                <span className="text-xs font-mono text-emerald-400 font-bold">APPROVED BY SRE ON-CALL</span>
              </div>
              <button
                onClick={() => setIsApproved(!isApproved)}
                className="px-3 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-mono text-zinc-200 transition-all"
              >
                TOGGLE GATE ({isApproved ? 'UNLOCKED' : 'LOCKED'})
              </button>
            </div>
          </div>
        </div>

        {/* Right: Policy & Blast Radius Verification Card */}
        <div className="lg:col-span-5 space-y-4">
          <div className="vault-panel p-6 rounded-2xl border border-zinc-800 bg-zinc-950/90 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 font-bold uppercase mb-4 pb-2 border-b border-zinc-800">
                <Lock className="w-4 h-4" />
                <span>GOVERNANCE VALIDATION CRITERIA</span>
              </div>

              <div className="space-y-3 font-mono text-xs">
                <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
                  <div className="flex items-center justify-between text-zinc-200 font-semibold mb-1">
                    <span>1. Strict Action Catalog Check</span>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  </div>
                  <p className="text-[11px] text-zinc-400">Both actions are strictly defined in Pydantic schema contracts. Raw shell commands are blocked.</p>
                </div>

                <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
                  <div className="flex items-center justify-between text-zinc-200 font-semibold mb-1">
                    <span>2. Blast Radius Enforcement</span>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  </div>
                  <p className="text-[11px] text-zinc-400">Restricted to localized service pool. Quorum replication remains unaffected.</p>
                </div>

                <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
                  <div className="flex items-center justify-between text-zinc-200 font-semibold mb-1">
                    <span>3. Rollback Invariant Test</span>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  </div>
                  <p className="text-[11px] text-zinc-400">Pre-execution state snapshot guarantees 100% reversible execution if verification fails.</p>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-zinc-800 text-[11px] font-mono text-zinc-500 flex items-center justify-between">
              <span>Execution Boundary</span>
              <span className="text-emerald-400 font-bold">READY FOR 2PC SAGA</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
