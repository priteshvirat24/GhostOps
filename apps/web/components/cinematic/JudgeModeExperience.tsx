'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  Pause,
  SkipForward,
  SkipBack,
  RotateCcw,
  X,
  Shield,
  Database,
  Cpu,
  Activity,
  Layers,
  GitCompare,
  Lock,
  CheckCircle2,
  AlertOctagon,
  Sparkles,
  ArrowRight,
  Radio,
  Clock,
  ChevronRight
} from 'lucide-react';
import HeroVaultScene from '../3d/scenes/HeroVaultScene';
import TemporalDiffScene from '../3d/scenes/TemporalDiffScene';
import InvestigationGraphScene from '../3d/scenes/InvestigationGraphScene';
import { SystemHealth } from '../../types';

interface JudgeModeExperienceProps {
  isOpen: boolean;
  onClose: () => void;
  health?: SystemHealth | null;
}

const ACTS = [
  { id: 'INTRO', title: 'THE HOOK', subtitle: 'Why GhostOps Exists', duration: 10 },
  { id: 'PROBLEM', title: 'WHY RUNBOOKS FAIL', subtitle: 'The Trial-and-Error Trap', duration: 12 },
  { id: 'MEMORY', title: 'INSTITUTIONAL MEMORY', subtitle: 'CockroachDB Native VECTOR(1536)', duration: 14 },
  { id: 'INVESTIGATION', title: 'MULTI-TIER REASONING', subtitle: 'Grounded Hypothesis Battle', duration: 14 },
  { id: 'TEMPORAL', title: 'TEMPORAL REASONING', subtitle: 'The Core Differentiator', duration: 16 },
  { id: 'GOVERNANCE', title: 'REMEDIATION GOVERNANCE', subtitle: 'Code Governs · Human Authorizes', duration: 14 },
  { id: 'ACTION', title: '2PC SAGA EXECUTION', subtitle: 'Transactional Mutation & Rollback', duration: 12 },
  { id: 'VERIFICATION', title: 'INDEPENDENT VERIFIER', subtitle: 'Decoupled Out-of-Band Proof', duration: 14 },
  { id: 'LEARNING', title: 'CONTINUOUS LEARNING', subtitle: 'Knowledge Consolidates to Memory', duration: 12 },
  { id: 'CDC', title: 'CDC STREAMING', subtitle: 'Durable Changefeed to Fleet Bus', duration: 10 },
  { id: 'REPLAY', title: 'GHOST REPLAY (INCIDENT #1847)', subtitle: 'The "Wow" Decision: DO NOT REPLAY', duration: 18 },
  { id: 'CLOSE', title: 'THE FINAL FRAME', subtitle: 'GhostOps Knows When NOT to Repeat History', duration: 12 },
];

export default function JudgeModeExperience({ isOpen, onClose, health }: JudgeModeExperienceProps) {
  const [currentActIndex, setCurrentActIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [actProgress, setActProgress] = useState<number>(0);
  const [autoAdvance, setAutoAdvance] = useState<boolean>(true);

  const currentAct = ACTS[currentActIndex];

  // Timer & auto-advance ticker
  useEffect(() => {
    if (!isOpen || !isPlaying) return;

    const interval = setInterval(() => {
      setActProgress((prev) => {
        const next = prev + 100 / (currentAct.duration * 10);
        if (next >= 100) {
          if (autoAdvance) {
            if (currentActIndex < ACTS.length - 1) {
              setCurrentActIndex((idx) => idx + 1);
              return 0;
            } else {
              setIsPlaying(false);
              return 100;
            }
          }
          return 100;
        }
        return next;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [isOpen, isPlaying, currentActIndex, currentAct.duration, autoAdvance]);

  // Reset progress on act change
  const jumpToAct = (idx: number) => {
    setCurrentActIndex(idx);
    setActProgress(0);
  };

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === ' ' || e.code === 'Space') {
        e.preventDefault();
        setIsPlaying((p) => !p);
      } else if (e.key === 'ArrowRight') {
        if (currentActIndex < ACTS.length - 1) {
          jumpToAct(currentActIndex + 1);
        }
      } else if (e.key === 'ArrowLeft') {
        if (currentActIndex > 0) {
          jumpToAct(currentActIndex - 1);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentActIndex, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] bg-[#07090e] text-[#f5f6f0] flex flex-col justify-between overflow-hidden select-none font-mono">
      {/* Dynamic 3D Living Backdrop */}
      <div className="absolute inset-0 pointer-events-none opacity-40 z-0">
        {currentAct.id === 'TEMPORAL' || currentAct.id === 'REPLAY' ? (
          <TemporalDiffScene driftCount={5} verdict="DO_NOT_EXECUTE" />
        ) : currentAct.id === 'INVESTIGATION' ? (
          <InvestigationGraphScene activeStep={4} />
        ) : (
          <HeroVaultScene activeChamberIndex={currentActIndex} />
        )}
      </div>

      {/* Radial Scanline Grid Overlay */}
      <div className="absolute inset-0 grid-bg radial-mask pointer-events-none z-1 opacity-50" />

      {/* Top Header Bar */}
      <header className="relative z-20 px-6 py-4 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-xl flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-emerald-500/60 flex items-center justify-center shadow-lg shadow-emerald-950/60">
            <Shield className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-widest text-sm text-zinc-100">GHOSTOPS JUDGE MODE</span>
              <span className="text-[10px] px-2 py-0.2 rounded bg-amber-950/80 border border-amber-500/60 text-amber-300 font-bold animate-pulse">
                LIVE EXPERIENCE
              </span>
            </div>
            <span className="text-[10px] text-zinc-400">
              ACT {currentActIndex + 1} OF {ACTS.length} · {currentAct.title}
            </span>
          </div>
        </div>

        {/* Backend Status Indicators */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-zinc-900 border border-zinc-800 text-[10px]">
            <Database className="w-3 h-3 text-emerald-400" />
            <span className="text-zinc-300">CRDB SERVERLESS</span>
            <span className="text-emerald-400 font-bold">CONNECTED</span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-zinc-900 border border-zinc-800 text-[10px]">
            <Cpu className="w-3 h-3 text-emerald-400" />
            <span className="text-zinc-300">BEDROCK MANTLE</span>
            <span className="text-emerald-400 font-bold">LIVE</span>
          </div>

          <button
            onClick={onClose}
            className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-300 text-xs transition-all"
          >
            <X className="w-4 h-4" />
            <span className="hidden sm:inline">EXIT JUDGE MODE (ESC)</span>
          </button>
        </div>
      </header>

      {/* Main Act Canvas */}
      <main className="relative z-10 flex-1 px-6 py-8 flex flex-col justify-center items-center max-w-6xl mx-auto w-full">
        {/* ACT 0: INTRO */}
        {currentAct.id === 'INTRO' && (
          <div className="text-center max-w-3xl space-y-6 animate-fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-zinc-900/90 border border-emerald-500/40 text-emerald-400 text-xs shadow-lg">
              <Sparkles className="w-3.5 h-3.5" />
              <span>THE OPENING HOOK</span>
            </div>
            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-gradient-ivory leading-tight">
              Production incidents repeat <br />
              <span className="text-zinc-400 font-light">because operational memory decays.</span>
            </h1>
            <p className="text-2xl sm:text-3xl text-emerald-400 font-bold">
              GhostOps remembers.
            </p>
            <p className="text-sm sm:text-base text-zinc-300 max-w-2xl mx-auto leading-relaxed">
              When production systems fail, teams frantically search Slack, Jira, and outdated wikis. GhostOps turns operational history into durable, governed memory.
            </p>
          </div>
        )}

        {/* ACT 1: PROBLEM */}
        {currentAct.id === 'PROBLEM' && (
          <div className="w-full max-w-4xl space-y-6 animate-fade-in">
            <div className="text-center">
              <span className="text-red-400 text-xs font-bold uppercase tracking-widest block mb-1">
                ACT 01 · THE PROBLEM
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100">
                Why Runbooks & Naive LLM Search Fail
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-6 rounded-2xl bg-zinc-950/90 border border-red-900/60 shadow-2xl">
                <span className="text-red-400 font-bold text-xs uppercase block mb-3">
                  ⚠️ The Traditional Runbook Trap
                </span>
                <div className="space-y-2 text-xs text-zinc-300">
                  <div className="p-2.5 rounded bg-zinc-900/80 border border-zinc-800">1. Outage occurs at 3 AM</div>
                  <div className="p-2.5 rounded bg-zinc-900/80 border border-zinc-800">2. On-call searches 2-year-old confluence runbook</div>
                  <div className="p-2.5 rounded bg-zinc-900/80 border border-zinc-800">3. Blindly runs 2024 bash script on drifted VPC</div>
                  <div className="p-2.5 rounded bg-red-950/50 border border-red-800 text-red-200 font-bold">
                    4. Breaks Transit Gateway peering & cascades outage
                  </div>
                </div>
              </div>

              <div className="p-6 rounded-2xl bg-zinc-950/90 border border-emerald-500/50 shadow-2xl shadow-emerald-950/30">
                <span className="text-emerald-400 font-bold text-xs uppercase block mb-3">
                  ⚡ How GhostOps Fixes It
                </span>
                <div className="space-y-2 text-xs text-zinc-300">
                  <div className="p-2.5 rounded bg-zinc-900/80 border border-emerald-900/40">1. Ingests raw telemetry + SHA-256 evidence hash</div>
                  <div className="p-2.5 rounded bg-zinc-900/80 border border-emerald-900/40">2. Retrieves 1536-dim vector precedents in CockroachDB</div>
                  <div className="p-2.5 rounded bg-zinc-900/80 border border-amber-500/40 text-amber-300 font-bold">
                    3. Runs 9-dimension deterministic drift comparison
                  </div>
                  <div className="p-2.5 rounded bg-emerald-950/60 border border-emerald-500/60 text-emerald-200 font-bold">
                    4. Rejects unsafe old fixes & executes governed 2PC saga
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ACT 2: MEMORY */}
        {currentAct.id === 'MEMORY' && (
          <div className="w-full max-w-4xl space-y-6 animate-fade-in">
            <div className="text-center">
              <span className="text-emerald-400 text-xs font-bold uppercase tracking-widest block mb-1">
                ACT 02 · INSTITUTIONAL MEMORY
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100">
                CockroachDB Native VECTOR(1536) & Negative Knowledge
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="p-5 rounded-2xl bg-emerald-950/30 border border-emerald-500/50">
                <span className="text-emerald-400 font-bold text-sm block mb-1">HIGH-TRUST PRECEDENTS</span>
                <p className="text-zinc-300 text-[11px] leading-relaxed mb-3">
                  Verified resolutions with proven invariant telemetry (e.g. range leaseholder contention rebalancing).
                </p>
                <div className="text-emerald-400 font-bold text-xs">Trust Level: 0.92 · Active</div>
              </div>

              <div className="p-5 rounded-2xl bg-red-950/30 border border-red-500/50">
                <span className="text-red-400 font-bold text-sm block mb-1">NEGATIVE KNOWLEDGE</span>
                <p className="text-zinc-300 text-[11px] leading-relaxed mb-3">
                  Explicitly encodes <strong>"DO NOT REPEAT"</strong> (e.g. modifying SG rules on drifted VPCs or pg_terminate_backend on CRDB).
                </p>
                <div className="text-red-400 font-bold text-xs">Strictly Blocked by Policy</div>
              </div>

              <div className="p-5 rounded-2xl bg-zinc-900/60 border border-zinc-800">
                <span className="text-zinc-400 font-bold text-sm block mb-1">SUPERSEDED FIXES</span>
                <p className="text-zinc-400 text-[11px] leading-relaxed mb-3">
                  Old manual interventions superseded by automated Kubernetes pod autoscaling and modern architectures.
                </p>
                <div className="text-zinc-500 font-bold text-xs">Deprecation Tracked</div>
              </div>
            </div>
          </div>
        )}

        {/* ACT 3: INVESTIGATION */}
        {currentAct.id === 'INVESTIGATION' && (
          <div className="w-full max-w-4xl space-y-6 animate-fade-in">
            <div className="text-center">
              <span className="text-emerald-400 text-xs font-bold uppercase tracking-widest block mb-1">
                ACT 03 · MULTI-TIER INVESTIGATION
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100">
                Fast Triage vs Deep Reasoning Hypothesis Battle
              </h2>
            </div>

            <div className="p-6 rounded-2xl bg-zinc-950/90 border border-zinc-800 space-y-4 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-zinc-900 border border-zinc-800">
                  <div className="flex items-center justify-between text-zinc-400 mb-2">
                    <span className="font-bold text-zinc-200">Hypothesis A (Selected)</span>
                    <span className="text-emerald-400 font-bold">92% Confidence</span>
                  </div>
                  <p className="text-zinc-300 text-[11px] leading-relaxed">
                    Range 1042 leaseholder contention causing connection pool exhaustion on port 26257.
                  </p>
                  <div className="mt-2 text-[10px] text-zinc-500">Model: deepseek.v3.2 (Reasoning Tier)</div>
                </div>

                <div className="p-4 rounded-xl bg-zinc-900 border border-zinc-800 opacity-60">
                  <div className="flex items-center justify-between text-zinc-400 mb-2">
                    <span className="font-bold text-zinc-200">Hypothesis B (Rejected)</span>
                    <span className="text-red-400 font-bold">34% Confidence</span>
                  </div>
                  <p className="text-zinc-300 text-[11px] leading-relaxed">
                    Security group ingress port blocked. Rejected because internal TCP latency is 1.2ms.
                  </p>
                  <div className="mt-2 text-[10px] text-zinc-500">Model: zai.glm-4.7-flash (Fast Tier)</div>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800 flex items-center justify-between text-[11px]">
                <span className="text-zinc-400">Supporting Evidence Chain:</span>
                <span className="text-emerald-400 font-bold">SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855</span>
              </div>
            </div>
          </div>
        )}

        {/* ACT 4: TEMPORAL */}
        {currentAct.id === 'TEMPORAL' && (
          <div className="w-full max-w-4xl space-y-6 animate-fade-in">
            <div className="text-center">
              <span className="text-amber-400 text-xs font-bold uppercase tracking-widest block mb-1">
                ACT 04 · THE CORE DIFFERENTIATOR
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100">
                "GhostOps does not blindly replay history."
              </h2>
              <p className="text-lg text-amber-300 font-semibold mt-2">
                "It determines whether history still applies to today's drifted infrastructure."
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-zinc-950/90 border border-amber-500/50 shadow-2xl space-y-4 text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
                <span className="text-zinc-300 font-bold">9-DIMENSION ENVIRONMENT DIFF: THEN (2024) vs NOW (2026)</span>
                <span className="text-red-400 font-bold">5/9 LAYERS DRIFTED</span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center text-[10px]">
                <div className="p-2 rounded bg-zinc-900 border border-zinc-800">Topology: Drifted</div>
                <div className="p-2 rounded bg-zinc-900 border border-zinc-800">SG Boundary: Incompatible</div>
                <div className="p-2 rounded bg-zinc-900 border border-zinc-800">IAM Role: Drifted</div>
                <div className="p-2 rounded bg-zinc-900 border border-zinc-800">DB Engine: v24.1.2 (Stable)</div>
                <div className="p-2 rounded bg-zinc-900 border border-zinc-800">Scale: Multi-AZ (Drifted)</div>
                <div className="p-2 rounded bg-zinc-900 border border-zinc-800">Connection Pool: Drifted</div>
              </div>

              <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/60 flex items-center justify-between">
                <div className="flex items-center gap-2 text-red-400 font-bold text-sm">
                  <AlertOctagon className="w-5 h-5" />
                  <span>DETERMINISTIC VERDICT: DO_NOT_EXECUTE (Compatibility: 0.12)</span>
                </div>
                <span className="text-[10px] text-zinc-400">UNSAFE REPLAY PREVENTED</span>
              </div>
            </div>
          </div>
        )}

        {/* ACT 5: GOVERNANCE */}
        {currentAct.id === 'GOVERNANCE' && (
          <div className="w-full max-w-4xl space-y-6 animate-fade-in">
            <div className="text-center">
              <span className="text-emerald-400 text-xs font-bold uppercase tracking-widest block mb-1">
                ACT 05 · REMEDIATION GOVERNANCE
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100">
                The Four Pillars of Autonomous Governance
              </h2>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center text-xs">
              <div className="p-5 rounded-2xl bg-zinc-950/90 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] uppercase block mb-1">1. PROPOSAL</span>
                <div className="text-zinc-100 font-bold text-sm">LLM RECOMMENDS</div>
                <p className="text-zinc-400 text-[10px] mt-2">Suggests candidate action plan</p>
              </div>

              <div className="p-5 rounded-2xl bg-zinc-950/90 border border-emerald-900/50">
                <span className="text-emerald-400 text-[10px] uppercase block mb-1">2. POLICY</span>
                <div className="text-emerald-300 font-bold text-sm">CODE GOVERNS</div>
                <p className="text-zinc-400 text-[10px] mt-2">Enforces Pydantic catalog & blast radius</p>
              </div>

              <div className="p-5 rounded-2xl bg-zinc-950/90 border border-amber-900/50">
                <span className="text-amber-400 text-[10px] uppercase block mb-1">3. HUMAN GATE</span>
                <div className="text-amber-300 font-bold text-sm">HUMAN AUTHORIZES</div>
                <p className="text-zinc-400 text-[10px] mt-2">Dual-phase approval on Tier 1 systems</p>
              </div>

              <div className="p-5 rounded-2xl bg-zinc-950/90 border border-emerald-500/60">
                <span className="text-emerald-400 text-[10px] uppercase block mb-1">4. EXECUTION</span>
                <div className="text-emerald-400 font-bold text-sm">SYSTEM EXECUTES</div>
                <p className="text-zinc-400 text-[10px] mt-2">Strict 2PC transactional saga</p>
              </div>
            </div>
          </div>
        )}

        {/* ACT 6: ACTION */}
        {currentAct.id === 'ACTION' && (
          <div className="w-full max-w-4xl space-y-6 animate-fade-in">
            <div className="text-center">
              <span className="text-emerald-400 text-xs font-bold uppercase tracking-widest block mb-1">
                ACT 06 · 2PC SAGA PIPELINE
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100">
                Transactional 2-Phase Commit & Rollback Protection
              </h2>
            </div>

            <div className="p-6 rounded-2xl bg-zinc-950/90 border border-zinc-800 space-y-4 text-xs">
              <div className="grid grid-cols-5 gap-2 text-center text-[10px]">
                <div className="p-3 rounded-xl bg-zinc-900 border border-emerald-500 text-emerald-300 font-bold">1. PRECHECK</div>
                <div className="p-3 rounded-xl bg-zinc-900 border border-emerald-500 text-emerald-300 font-bold">2. SNAPSHOT</div>
                <div className="p-3 rounded-xl bg-zinc-900 border border-emerald-500 text-emerald-300 font-bold">3. EXECUTING</div>
                <div className="p-3 rounded-xl bg-zinc-900 border border-emerald-500 text-emerald-300 font-bold">4. VERIFYING</div>
                <div className="p-3 rounded-xl bg-emerald-950 border border-emerald-500 text-emerald-200 font-bold">5. COMMITTED</div>
              </div>

              <div className="p-3 rounded-xl bg-zinc-900 text-zinc-300 text-[11px] space-y-1">
                <div>[18:32:21 UTC] Pre-state snapshot stored: active conns (250) + Range 1042 leaseholder on Node 3.</div>
                <div>[18:32:23 UTC] Relocated Range 1042 to Node 1 & drained connection pool.</div>
                <div className="text-emerald-400 font-bold">[18:32:26 UTC] Saga committed with 100% reversible rollback guarantee.</div>
              </div>
            </div>
          </div>
        )}

        {/* ACT 7: VERIFICATION */}
        {currentAct.id === 'VERIFICATION' && (
          <div className="w-full max-w-4xl space-y-6 animate-fade-in">
            <div className="text-center">
              <span className="text-emerald-400 text-xs font-bold uppercase tracking-widest block mb-1">
                ACT 07 · DECOUPLED VERIFICATION
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100">
                Execution says: "I did it." Verification says: "Let me check."
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
              <div className="p-5 rounded-2xl bg-zinc-950/90 border border-zinc-800">
                <span className="text-zinc-500 font-bold uppercase block mb-2">Agent Self-Report</span>
                <p className="text-zinc-400 italic mb-4">"Actions executed successfully. Marking incident resolved."</p>
                <div className="text-zinc-500 text-[10px]">Zero Trust: Self-reporting is ignored by GhostOps</div>
              </div>

              <div className="p-5 rounded-2xl bg-zinc-950/90 border border-emerald-500/50 shadow-2xl shadow-emerald-950/30">
                <span className="text-emerald-400 font-bold uppercase block mb-2">Independent Telemetry Reader</span>
                <div className="space-y-1.5 text-[11px] text-zinc-200 mb-3">
                  <div>· CloudWatch p99 latency: <strong>2400ms &rarr; 18ms</strong></div>
                  <div>· DB active connections: <strong>250 (100%) &rarr; 45 (18%)</strong></div>
                  <div>· Invariant Violations: <strong className="text-emerald-400">0.00%</strong></div>
                </div>
                <div className="text-emerald-400 font-bold text-[10px]">VERDICT: INDEPENDENTLY PROVED</div>
              </div>
            </div>
          </div>
        )}

        {/* ACT 8: LEARNING */}
        {currentAct.id === 'LEARNING' && (
          <div className="w-full max-w-4xl space-y-6 animate-fade-in">
            <div className="text-center">
              <span className="text-emerald-400 text-xs font-bold uppercase tracking-widest block mb-1">
                ACT 08 · CONTINUOUS LEARNING
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100">
                The Intelligence Loop Closes: Memory Consolidation
              </h2>
            </div>

            <div className="p-6 rounded-2xl bg-zinc-950/90 border border-emerald-500/40 shadow-2xl space-y-4 text-xs">
              <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
                <span className="text-zinc-200 font-bold">NEWLY CONSOLIDATED INSTITUTIONAL MEMORY</span>
                <span className="text-emerald-400 font-bold">1536-DIM EMBEDDING</span>
              </div>
              <p className="text-zinc-300 leading-relaxed">
                "Adaptive leaseholder transfer on range hotspots restores latency without SG mutations."
              </p>
              <div className="flex items-center justify-between text-[11px] text-zinc-400 pt-2 border-t border-zinc-800">
                <span>Trust Score Elevation: 0.85 &rarr; <strong className="text-emerald-400">0.92 (+0.07)</strong></span>
                <span className="text-emerald-400 font-bold">DURABLY INSERTED TO COCKROACHDB</span>
              </div>
            </div>
          </div>
        )}

        {/* ACT 9: CDC */}
        {currentAct.id === 'CDC' && (
          <div className="w-full max-w-4xl space-y-6 animate-fade-in">
            <div className="text-center">
              <span className="text-emerald-400 text-xs font-bold uppercase tracking-widest block mb-1">
                ACT 09 · COCKROACHDB CHANGEFEED
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100">
                Durable CDC Event Stream to Regional Fleet Sentinels
              </h2>
            </div>

            <div className="p-6 rounded-2xl bg-zinc-950/90 border border-zinc-800 space-y-3 text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
                <span className="text-zinc-300 font-bold">TOPIC: ghostops.memories</span>
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 font-bold text-[10px]">
                  CDC STREAM ACTIVE
                </span>
              </div>
              <pre className="p-4 rounded-xl bg-zinc-900 text-[10px] text-zinc-300 overflow-x-auto">
{`{
  "topic": "ghostops.memories",
  "op": "INSERT",
  "key": "mem_2026_0904_db_contention",
  "trust_score": 0.92,
  "vector_dim": 1536,
  "replication": "DURABLY_REPLICATED (3 AZs)",
  "cdc_lsn": "78912304910239401"
}`}
              </pre>
            </div>
          </div>
        )}

        {/* ACT 10: REPLAY / THE WOW MOMENT */}
        {currentAct.id === 'REPLAY' && (
          <div className="w-full max-w-4xl space-y-6 animate-fade-in">
            <div className="text-center">
              <span className="text-red-400 text-xs font-bold uppercase tracking-widest block mb-1">
                ACT 10 · THE "WOW" MOMENT · INCIDENT #1847
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100">
                "Would We Replay This Today?"
              </h2>
            </div>

            <div className="p-7 rounded-2xl bg-red-950/40 border border-red-500/70 shadow-2xl shadow-red-950/50 space-y-4 text-xs">
              <div className="flex items-center justify-between pb-3 border-b border-red-800/60">
                <span className="text-zinc-200 font-bold text-sm">TARGET PRECEDENT: #1847 (2024 FIX)</span>
                <span className="text-red-300 font-bold">Vector Match: 94.2%</span>
              </div>

              <div className="p-4 rounded-xl bg-zinc-950/80 border border-zinc-800 text-zinc-200 text-xs leading-relaxed">
                <strong>Why Naive RAG Takes Down Production:</strong> Standard semantic search recommends the 2024 Security Group modification because of the 94% vector match. But since 2024, VPC peering was replaced by a Transit Gateway.
              </div>

              <div className="p-4 rounded-xl bg-red-950 border border-red-500 flex items-center justify-between text-red-200 font-bold text-sm">
                <div className="flex items-center gap-2">
                  <AlertOctagon className="w-6 h-6 text-red-400 animate-pulse" />
                  <span>GHOSTOPS VERDICT: DO NOT REPLAY (100% BLOCKED)</span>
                </div>
                <span className="text-xs bg-red-900 px-3 py-1 rounded">0% UNSAFE REPLAY RATE</span>
              </div>
            </div>
          </div>
        )}

        {/* ACT 11: CLOSE */}
        {currentAct.id === 'CLOSE' && (
          <div className="text-center max-w-3xl space-y-6 animate-fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-zinc-900/90 border border-emerald-500/40 text-emerald-400 text-xs shadow-lg">
              <CheckCircle2 className="w-4 h-4" />
              <span>THE FINAL FRAME</span>
            </div>
            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-gradient-ivory leading-tight">
              GhostOps remembers. <br />
              <span className="text-gradient-sage">GhostOps knows when NOT to repeat history.</span>
            </h1>
            <p className="text-sm sm:text-base text-zinc-300 max-w-2xl mx-auto leading-relaxed">
              30-Case Golden Benchmark: <strong className="text-emerald-400">93.33% P@1</strong>, <strong className="text-emerald-400">100% P@3</strong>, <strong className="text-emerald-400">0.00% Unsafe Replay</strong>. Regression Gate: <strong className="text-emerald-400">PASSED</strong>.
            </p>

            <div className="pt-4 flex items-center justify-center gap-4">
              <button
                onClick={() => jumpToAct(0)}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-200 text-xs font-bold transition-all"
              >
                <RotateCcw className="w-4 h-4" />
                <span>REPLAY JUDGE MODE</span>
              </button>
              <button
                onClick={onClose}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold text-xs transition-all shadow-xl shadow-emerald-500/20"
              >
                <span>EXPLORE INTERACTIVE VAULT</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Bottom Timeline & Controls Bar */}
      <footer className="relative z-20 px-6 py-4 border-t border-zinc-800/80 bg-zinc-950/90 backdrop-blur-xl flex flex-col gap-3">
        {/* Scrubber Progress Track */}
        <div className="w-full bg-zinc-900 h-1.5 rounded-full overflow-hidden flex gap-1 p-0.5">
          {ACTS.map((act, idx) => {
            const isPassed = currentActIndex > idx;
            const isCurrent = currentActIndex === idx;
            return (
              <div
                key={act.id}
                onClick={() => jumpToAct(idx)}
                className="flex-1 h-full rounded-full bg-zinc-800 cursor-pointer overflow-hidden relative"
              >
                <div
                  className="h-full bg-emerald-400 transition-all duration-100 ease-linear"
                  style={{
                    width: isPassed ? '100%' : isCurrent ? `${actProgress}%` : '0%',
                  }}
                />
              </div>
            );
          })}
        </div>

        {/* Playback Controls & Chapter Select */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (currentActIndex > 0) jumpToAct(currentActIndex - 1);
              }}
              disabled={currentActIndex === 0}
              className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 disabled:opacity-30 text-zinc-300"
              title="Previous Act (Left Arrow)"
            >
              <SkipBack className="w-4 h-4" />
            </button>

            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold flex items-center gap-2 transition-all shadow-md active:scale-95"
              title="Play / Pause (Spacebar)"
            >
              {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current" />}
              <span>{isPlaying ? 'PAUSE' : 'RESUME'}</span>
            </button>

            <button
              onClick={() => {
                if (currentActIndex < ACTS.length - 1) jumpToAct(currentActIndex + 1);
              }}
              disabled={currentActIndex === ACTS.length - 1}
              className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 disabled:opacity-30 text-zinc-300"
              title="Next Act (Right Arrow)"
            >
              <SkipForward className="w-4 h-4" />
            </button>

            <button
              onClick={() => jumpToAct(0)}
              className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400"
              title="Restart Experience"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          {/* Act Title & Time Indicator */}
          <div className="flex items-center gap-3 text-zinc-400 text-[11px]">
            <span className="text-zinc-200 font-semibold">{currentAct.subtitle}</span>
            <span className="text-zinc-600">·</span>
            <span>{Math.round((actProgress / 100) * currentAct.duration)}s / {currentAct.duration}s</span>
          </div>

          {/* Auto-advance switch */}
          <div className="flex items-center gap-2 text-zinc-400 text-[11px]">
            <span>AUTO-ADVANCE:</span>
            <button
              onClick={() => setAutoAdvance(!autoAdvance)}
              className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-all ${
                autoAdvance
                  ? 'bg-emerald-950 text-emerald-300 border-emerald-500/50'
                  : 'bg-zinc-900 text-zinc-500 border-zinc-800'
              }`}
            >
              {autoAdvance ? 'ON' : 'OFF'}
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
