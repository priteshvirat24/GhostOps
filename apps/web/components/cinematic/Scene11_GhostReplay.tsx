'use client';

import React, { useState } from 'react';
import { Play, AlertOctagon, RotateCcw, ShieldCheck, ArrowRight, CheckCircle2, XCircle } from 'lucide-react';
import { triggerCounterfactualReplay } from '../../lib/api';

export default function Scene11_GhostReplay() {
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [replayVerdict, setReplayVerdict] = useState<string>('DO_NOT_REPLAY');

  const handleRunReplay = async () => {
    setIsRunning(true);
    try {
      await triggerCounterfactualReplay({ incident_id: 'PREC-1847', target_env: 'current_2026' });
      setReplayVerdict('DO_NOT_REPLAY');
    } catch (e) {
      console.error(e);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-12 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-950/80 border border-red-500/40 text-red-400 text-xs font-mono mb-3">
          <span>SCENE 11</span>
          <span>·</span>
          <span>FLAGSHIP COUNTERFACTUAL REPLAY · INCIDENT #1847</span>
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-zinc-100 mb-4">
          "Would We Replay This Fix Today?" The Flagship Test
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          In 2024, Incident #1847 was resolved by modifying Security Group ingress rules. Today, our VPC topology routes traffic through a Transit Gateway. When GhostOps replays this incident counterfactually, it deterministically refuses to execute the old fix.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Interactive Replay Comparison */}
        <div className="lg:col-span-7 space-y-4">
          <div className="vault-panel p-6 sm:p-7 rounded-2xl border border-zinc-800 bg-zinc-950/90 shadow-2xl space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <span className="text-zinc-200 font-bold text-sm">TARGET PRECEDENT: #1847 (2024 RESOLUTION)</span>
              <span className="px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-zinc-400 text-[10px]">
                Vector Match: 94.2%
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-zinc-900/80 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] uppercase block mb-1">2024 Environment State</span>
                <span className="text-zinc-100 font-bold block mb-1">Direct VPC Subnet</span>
                <p className="text-zinc-400 text-[11px]">Local Security Group sg-0a89f92 controlled all traffic. Modifying port 22/tcp restored access.</p>
              </div>

              <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-900/40">
                <span className="text-amber-400 text-[10px] uppercase block mb-1">2026 Environment State</span>
                <span className="text-amber-200 font-bold block mb-1">Transit Gateway Attached</span>
                <p className="text-zinc-400 text-[11px]">Security groups are subordinate to Transit Gateway route tables. Reapplying 2024 fix breaks internal peering.</p>
              </div>
            </div>

            {/* Replay Trigger Action */}
            <div className="pt-3 border-t border-zinc-800 flex items-center justify-between">
              <div>
                <span className="text-[10px] text-zinc-500 block">Simulation Mode:</span>
                <span className="text-zinc-300 font-bold text-xs">Full 9D Temporal Replay</span>
              </div>
              <button
                onClick={handleRunReplay}
                disabled={isRunning}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold text-xs font-mono transition-all shadow-lg active:scale-95 disabled:opacity-50"
              >
                <Play className={`w-3.5 h-3.5 fill-current ${isRunning ? 'animate-spin' : ''}`} />
                <span>{isRunning ? 'RUNNING REPLAY ENGINE...' : 'TRIGGER COUNTERFACTUAL REPLAY'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right: The Final Replay Verdict Box */}
        <div className="lg:col-span-5">
          <div className="vault-panel p-6 sm:p-7 rounded-2xl border border-red-500/60 bg-red-950/40 shadow-2xl shadow-red-950/40 h-full flex flex-col justify-between font-mono text-xs">
            <div>
              <div className="flex items-center gap-2.5 text-red-400 font-bold text-sm mb-3 pb-2 border-b border-red-800/60">
                <AlertOctagon className="w-5 h-5 text-red-400 animate-pulse" />
                <span>REPLAY DECISION: DO_NOT_REPLAY</span>
              </div>

              <div className="space-y-3 text-zinc-200 text-xs leading-relaxed mb-4">
                <p>
                  <strong>Why Naive RAG Would Fail:</strong> A standard LLM + RAG system looks at the 94% semantic similarity score and proposes the 2024 Security Group modification, taking down production.
                </p>
                <p>
                  <strong>How GhostOps Prevents Outages:</strong> GhostOps computes the 9-dimension diff, identifies the Transit Gateway topology shift, detects the 0.12 compatibility score, and strictly halts execution.
                </p>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-zinc-950/80 border border-zinc-800 text-[11px] text-zinc-400 flex items-center justify-between">
              <span>Unsafe Replay Prevention:</span>
              <span className="text-emerald-400 font-bold">100% BLOCKED</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
