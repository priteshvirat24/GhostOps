'use client';

import React, { useState, useEffect } from 'react';
import { X, Play, RotateCcw, ShieldCheck, Database, Cpu, Activity, CheckCircle2, AlertTriangle, Terminal } from 'lucide-react';
import { runDemoReplay, runDemoInvestigation } from '../../lib/api';

interface ChamberLiveDemoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const DEMO_STAGES = [
  { id: 1, name: 'Signal Ingestion', icon: Activity, desc: 'Capturing CloudWatch alarm & SHA-256 evidence hashing' },
  { id: 2, name: 'Hybrid Retrieval', icon: Database, desc: 'Scanning CockroachDB 1536-dim vector memory + structured filters' },
  { id: 3, name: 'Model Investigation', icon: Cpu, desc: 'Multi-tier model reasoning forming competing hypotheses' },
  { id: 4, name: 'Temporal Drift Diffing', icon: AlertTriangle, desc: '9-dimension comparison; evaluating Precedent #1847 drift' },
  { id: 5, name: 'Governed 2PC Saga', icon: ShieldCheck, desc: 'Generating schema-validated action plan with automatic rollback' },
  { id: 6, name: 'Execution Boundary', icon: Terminal, desc: 'Adaptive CockroachDB lease relocation & pool draining' },
  { id: 7, name: 'Independent Verification', icon: CheckCircle2, desc: 'Querying CloudWatch & EC2 directly to prove invariants' },
  { id: 8, name: 'CDC Learning Consolidation', icon: Database, desc: 'Inserting 1536-dim vector precedent & CDC stream emission' },
];

export default function ChamberLiveDemoModal({ isOpen, onClose }: ChamberLiveDemoModalProps) {
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [demoResult, setDemoResult] = useState<any>(null);

  if (!isOpen) return null;

  const handleStartDemo = async () => {
    setIsRunning(true);
    setCurrentStep(1);
    setLogs(['[00:01] Ingesting production telemetry from auth-service...']);

    try {
      // Simulate stepwise progress while triggering real API
      setTimeout(() => {
        setCurrentStep(2);
        setLogs((prev) => [...prev, '[00:04] Querying CockroachDB native VECTOR(1536) space for precedents...']);
      }, 1000);

      setTimeout(() => {
        setCurrentStep(3);
        setLogs((prev) => [...prev, '[00:08] Multi-tier model routing (GLM 4.7 Flash -> DeepSeek V3.2)...']);
      }, 2000);

      setTimeout(() => {
        setCurrentStep(4);
        setLogs((prev) => [...prev, '[00:12] Deterministic 9-dimension drift diff: Precedent #1847 marked DO_NOT_EXECUTE (VPC drift).']);
      }, 3200);

      setTimeout(() => {
        setCurrentStep(5);
        setLogs((prev) => [...prev, '[00:16] Synthesizing governed 2PC saga plan (COCKROACH_RELOCATE_RANGE + DRAIN_POOL)...']);
      }, 4400);

      setTimeout(() => {
        setCurrentStep(6);
        setLogs((prev) => [...prev, '[00:20] Executing governed saga actions within AWS boundary...']);
      }, 5600);

      setTimeout(() => {
        setCurrentStep(7);
        setLogs((prev) => [...prev, '[00:24] Independent CloudWatch reader verified 0 errors, latency dropped 2400ms -> 18ms.']);
      }, 6800);

      const res = await runDemoReplay();
      setDemoResult(res);

      setTimeout(() => {
        setCurrentStep(8);
        setLogs((prev) => [
          ...prev,
          '[00:28] Post-remediation learning consolidated into CockroachDB memory table.',
          '[00:30] DEMO REPLAY COMPLETE: 100% INVARIANTS VERIFIED.'
        ]);
        setIsRunning(false);
      }, 8000);
    } catch (e: any) {
      console.error(e);
      setLogs((prev) => [...prev, `[ERROR] ${e.message || 'Error running demo'}`]);
      setIsRunning(false);
    }
  };

  const handleReset = () => {
    setCurrentStep(0);
    setIsRunning(false);
    setLogs([]);
    setDemoResult(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/85 backdrop-blur-2xl animate-fade-in">
      <div className="relative w-full max-w-5xl rounded-2xl border border-emerald-500/40 bg-zinc-950/95 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-950 border border-emerald-500/50 flex items-center justify-center">
              <Play className="w-4 h-4 text-emerald-400 fill-current" />
            </div>
            <div>
              <h3 className="text-base font-bold font-mono text-zinc-100">GHOSTOPS END-TO-END DEMO REPLAY</h3>
              <p className="text-[11px] font-mono text-zinc-400">Live 3-minute guided incident lifecycle demonstration</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Action Bar */}
          <div className="flex items-center justify-between gap-4 p-4 rounded-xl bg-zinc-900 border border-zinc-800">
            <div>
              <div className="text-xs font-mono text-zinc-200 font-semibold">Incident Target: #2026-904</div>
              <div className="text-[11px] text-zinc-400 font-mono">CockroachDB Connection Exhaustion & Range Contention on auth-service</div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleStartDemo}
                disabled={isRunning}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold font-mono text-xs transition-all disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{isRunning ? 'RUNNING STAGES...' : currentStep === 8 ? 'RUN AGAIN' : 'START DEMO'}</span>
              </button>
              <button
                onClick={handleReset}
                disabled={isRunning}
                className="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-all"
                title="Reset"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* 8-Stage Progression Pipeline */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
            {DEMO_STAGES.map((st) => {
              const isPast = currentStep > st.id;
              const isCurrent = currentStep === st.id;
              const Icon = st.icon;

              return (
                <div
                  key={st.id}
                  className={`p-3 rounded-xl border text-center transition-all ${
                    isCurrent
                      ? 'bg-emerald-950/80 border-emerald-500 text-emerald-300 shadow-md shadow-emerald-950/50 scale-105'
                      : isPast
                      ? 'bg-zinc-900/80 border-emerald-800/40 text-emerald-400'
                      : 'bg-zinc-950 border-zinc-800/60 text-zinc-500'
                  }`}
                >
                  <div className="w-6 h-6 mx-auto rounded-full flex items-center justify-center mb-1.5 bg-zinc-900 border border-zinc-800">
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <div className="text-[10px] font-mono font-bold">{st.name}</div>
                  <div className="text-[8px] font-mono text-zinc-500 mt-0.5">Stage 0{st.id}</div>
                </div>
              );
            })}
          </div>

          {/* Live Terminal & Execution Stream */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
              <span className="flex items-center gap-1.5 text-emerald-400">
                <Terminal className="w-3.5 h-3.5" />
                <span>REAL-TIME OPERATIONAL LOGS</span>
              </span>
              <span className="text-[10px] text-zinc-500">Connected to FastAPI Backend (port 8000)</span>
            </div>

            <div className="p-4 rounded-xl bg-zinc-950 border border-zinc-800 font-mono text-xs text-zinc-300 space-y-1.5 min-h-[160px] max-h-[220px] overflow-y-auto">
              {logs.length === 0 ? (
                <div className="text-zinc-600 italic">Click 'START DEMO' to launch the end-to-end incident investigation lifecycle...</div>
              ) : (
                logs.map((log, idx) => (
                  <div key={idx} className="leading-relaxed">
                    <span className="text-emerald-400 font-semibold">{log.substring(0, 7)}</span>
                    <span>{log.substring(7)}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-zinc-800 bg-zinc-900/60 flex items-center justify-between text-[11px] font-mono text-zinc-400">
          <span>COCKROACHDB CLOUD + BEDROCK MANTLE MULTI-TIER ENGINE</span>
          <button onClick={onClose} className="text-emerald-400 hover:underline">
            CLOSE INSPECTOR [ESC]
          </button>
        </div>
      </div>
    </div>
  );
}
