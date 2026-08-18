'use client';

import React, { useState } from 'react';
import { Cpu, CheckCircle2, XCircle, BrainCircuit, ShieldAlert, FileText, ChevronRight } from 'lucide-react';

export default function ChamberMultiTierReasoning() {
  const [activeTab, setActiveTab] = useState<'hypotheses' | 'tiers'>('hypotheses');

  const hypotheses = [
    {
      id: 'HYP-A',
      title: 'Database Range Contention Hotspot (Node 3)',
      status: 'SELECTED',
      confidence: 0.92,
      model: 'deepseek.v3.2',
      supporting: ['EVT-9041 (TCP Pool maxed)', 'EVT-9043 (sql.txn.restarts > 4.8%)', 'PREC-1402 (Historical match)'],
      contradicting: ['EVT-9042 (Security group modified 14 min prior)'],
      reasoning: 'Range 1042 leaseholder on node 3 is experiencing serialization retry storms. While SG rule changed, network connectivity remains open; root bottleneck is leaseholder imbalance.'
    },
    {
      id: 'HYP-B',
      title: 'Network Firewall Rule Block (Port 22/26257)',
      status: 'REJECTED',
      confidence: 0.34,
      model: 'zai.glm-4.7-flash',
      supporting: ['EVT-9042 (AuthorizeSecurityGroupIngress rule modification)'],
      contradicting: ['Active TCP sessions remain open', 'Internal service-to-db ping latency = 1.2ms'],
      reasoning: 'The security group change added SSH ingress, but did not alter the existing CockroachDB port 26257 ingress rules. Network path is not severed.'
    }
  ];

  return (
    <section className="py-20 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-10 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <span>CHAMBER 04</span>
          <span>·</span>
          <span>MULTI-TIER MODEL INVESTIGATION & COMPETING HYPOTHESES</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100 mb-3">
          Model-Driven Investigator & Grounded Evidence Citations
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          GhostOps runs a multi-tier model architecture. Fast models perform real-time triage while Deep Reasoning models form competing hypotheses strictly grounded in preserved evidence hashes.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Model Tier Routing Overview */}
        <div className="lg:col-span-4 space-y-4">
          <div className="vault-panel p-5 rounded-xl border border-zinc-800 bg-zinc-950/80">
            <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 font-semibold mb-4">
              <BrainCircuit className="w-4 h-4" />
              <span>ACTIVE BEDROCK MANTLE TIERS</span>
            </div>

            <div className="space-y-3">
              {/* Fast Tier Card */}
              <div className="p-3.5 rounded-xl bg-zinc-900/90 border border-zinc-800">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/40">
                    Fast Tier
                  </span>
                  <span className="text-xs font-mono text-zinc-400">$0.08 / 1M tokens</span>
                </div>
                <div className="text-xs font-bold font-mono text-zinc-100 mt-1.5">zai.glm-4.7-flash</div>
                <p className="text-[11px] text-zinc-400 mt-1">Sub-second event classification, log parsing, and preliminary triage.</p>
              </div>

              {/* Reasoning Tier Card */}
              <div className="p-3.5 rounded-xl bg-zinc-900/90 border border-emerald-500/40 shadow-sm shadow-emerald-950/30">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/40">
                    Reasoning Tier
                  </span>
                  <span className="text-xs font-mono text-zinc-400">$0.74 / 1M tokens</span>
                </div>
                <div className="text-xs font-bold font-mono text-zinc-100 mt-1.5">deepseek.v3.2</div>
                <p className="text-[11px] text-zinc-400 mt-1">Multi-step root cause synthesis, hypothesis battle, and saga plan derivation.</p>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-zinc-800 text-[10px] font-mono text-zinc-500 flex items-center justify-between">
              <span>Grounding Invariant</span>
              <span className="text-emerald-400 font-semibold">Min 0.85 Grounding Score</span>
            </div>
          </div>
        </div>

        {/* Right: Competing Hypotheses Card */}
        <div className="lg:col-span-8 space-y-4">
          <div className="flex items-center justify-between text-xs font-mono text-zinc-400 pb-1">
            <span>COMPETING ROOT CAUSE HYPOTHESES</span>
            <span className="text-emerald-400">EVIDENCE GROUNDING CHECK: PASSED</span>
          </div>

          {hypotheses.map((hyp) => {
            const isSelected = hyp.status === 'SELECTED';
            return (
              <div
                key={hyp.id}
                className={`vault-card p-5 rounded-xl border transition-all ${
                  isSelected
                    ? 'border-emerald-500/50 bg-zinc-950/90 shadow-xl shadow-emerald-950/20'
                    : 'border-zinc-800/70 bg-zinc-950/50 opacity-80'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-zinc-100">{hyp.id}</span>
                    <span
                      className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded ${
                        isSelected
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-700/50'
                          : 'bg-zinc-800 text-zinc-400'
                      }`}
                    >
                      {hyp.status}
                    </span>
                    <span className="text-[10px] font-mono text-zinc-400">via {hyp.model}</span>
                  </div>
                  <span className="text-xs font-mono font-bold text-emerald-400">
                    Confidence: {(hyp.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <h3 className="text-sm font-semibold text-zinc-100 mb-2">{hyp.title}</h3>
                <p className="text-xs text-zinc-300 leading-relaxed mb-3 bg-zinc-900/60 p-3 rounded-lg border border-zinc-800/60">
                  {hyp.reasoning}
                </p>

                {/* Citations Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px] font-mono">
                  <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-900/40">
                    <div className="text-emerald-400 font-semibold mb-1 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>SUPPORTING EVIDENCE ({hyp.supporting.length})</span>
                    </div>
                    <ul className="space-y-0.5 text-zinc-300">
                      {hyp.supporting.map((s, i) => (
                        <li key={i}>• {s}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="p-2.5 rounded-lg bg-red-950/20 border border-red-900/30">
                    <div className="text-red-400 font-semibold mb-1 flex items-center gap-1.5">
                      <XCircle className="w-3.5 h-3.5" />
                      <span>CONTRADICTING EVIDENCE ({hyp.contradicting.length})</span>
                    </div>
                    <ul className="space-y-0.5 text-zinc-400">
                      {hyp.contradicting.map((c, i) => (
                        <li key={i}>• {c}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
