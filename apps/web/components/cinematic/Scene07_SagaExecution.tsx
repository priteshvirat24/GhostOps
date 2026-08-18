'use client';

import React, { useState } from 'react';
import { Play, RotateCcw, ShieldCheck, CheckCircle2, AlertTriangle, ArrowRight, RefreshCw, Layers } from 'lucide-react';

export default function Scene07_SagaExecution() {
  const [sagaStage, setSagaStage] = useState<number>(4); // Default to COMPLETED
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  const stages = [
    { id: 0, name: 'PRECHECK', desc: 'Validating action parameters against Pydantic schema catalog' },
    { id: 1, name: 'SNAPSHOT', desc: 'Capturing immutable pre-execution state for 100% reversible rollback' },
    { id: 2, name: 'EXECUTING', desc: 'Executing governed CockroachDB range relocation & pool drainage' },
    { id: 3, name: 'VERIFYING', desc: 'Independent out-of-band telemetry reader checking invariant health' },
    { id: 4, name: 'COMMITTED', desc: '2PC Saga committed successfully; proceeding to institutional learning' }
  ];

  const handleSimulateSaga = () => {
    setIsSimulating(true);
    setSagaStage(0);
    setTimeout(() => setSagaStage(1), 800);
    setTimeout(() => setSagaStage(2), 1600);
    setTimeout(() => setSagaStage(3), 2400);
    setTimeout(() => {
      setSagaStage(4);
      setIsSimulating(false);
    }, 3200);
  };

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-12 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <span>SCENE 07</span>
          <span>·</span>
          <span>THE 2-PHASE COMMIT SAGA PIPELINE</span>
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-zinc-100 mb-4">
          Physical 2PC Saga Lifecycle & Deterministic Compensation
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          GhostOps executes remediation as a transactional 2-phase commit saga. If independent telemetry detects any invariant violation during verification, the compensation coordinator automatically rolls back the system to the pre-execution snapshot.
        </p>
      </div>

      {/* Interactive Saga Controller Bar */}
      <div className="flex items-center justify-between gap-4 p-4 rounded-xl bg-zinc-900 border border-zinc-800 mb-8 font-mono text-xs">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-zinc-200 font-semibold">Active Saga: SAGA-2026-904-EXEC</span>
          <span className="text-zinc-500">|</span>
          <span className="text-emerald-400">Target: crdb-valid-shaman-32362</span>
        </div>
        <button
          onClick={handleSimulateSaga}
          disabled={isSimulating}
          className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-bold transition-all disabled:opacity-50"
        >
          <Play className={`w-3.5 h-3.5 fill-current ${isSimulating ? 'animate-spin' : ''}`} />
          <span>{isSimulating ? 'EXECUTING SAGA...' : 'RE-RUN 2PC PIPELINE'}</span>
        </button>
      </div>

      {/* 5-Stage Physical Saga Pipeline */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mb-8">
        {stages.map((st) => {
          const isPassed = sagaStage > st.id;
          const isCurrent = sagaStage === st.id;

          return (
            <div
              key={st.id}
              className={`vault-card p-4 rounded-xl border text-left transition-all ${
                isCurrent
                  ? 'border-emerald-500 bg-emerald-950/70 text-emerald-300 shadow-lg shadow-emerald-950/40 scale-105'
                  : isPassed
                  ? 'border-emerald-800/40 bg-zinc-900/80 text-zinc-300'
                  : 'border-zinc-800/60 bg-zinc-950/60 text-zinc-500'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider">STAGE 0{st.id + 1}</span>
                {isPassed || isCurrent ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <span className="w-2 h-2 rounded-full bg-zinc-700" />
                )}
              </div>
              <h4 className="text-xs font-bold font-mono text-zinc-100 mb-1">{st.name}</h4>
              <p className="text-[11px] font-mono leading-relaxed text-zinc-400">{st.desc}</p>
            </div>
          );
        })}
      </div>

      {/* Execution Audit Log & Compensation Rollback Box */}
      <div className="vault-panel p-6 rounded-2xl border border-zinc-800 bg-zinc-950/90 shadow-xl font-mono text-xs">
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-800 text-xs">
          <span className="text-emerald-400 font-bold flex items-center gap-2">
            <ShieldCheck className="w-4 h-4" />
            <span>TRANSACTIONAL SAGA AUDIT TRAIL</span>
          </span>
          <span className="text-zinc-500">Zero Invariant Violations · 2/2 Sub-actions Verified</span>
        </div>

        <div className="p-4 rounded-xl bg-zinc-900 space-y-1.5 text-zinc-300 text-[11px]">
          <div>[18:32:20 UTC] <span className="text-emerald-400">[PRECHECK]</span> Action payload schema matches CockroachDB Action Catalog v1.0.</div>
          <div>[18:32:21 UTC] <span className="text-emerald-400">[SNAPSHOT]</span> Pre-state snapshot stored: sg-0a89f92 rules (1) + active conns (250).</div>
          <div>[18:32:22 UTC] <span className="text-emerald-400">[EXECUTING]</span> Executed `EXPERIMENTAL_RELOCATE` on range 1042 &rarr; node 1 leaseholder active.</div>
          <div>[18:32:23 UTC] <span className="text-emerald-400">[EXECUTING]</span> Drained idle auth-service connection pool &rarr; active conns dropped to 45.</div>
          <div>[18:32:25 UTC] <span className="text-emerald-400">[VERIFYING]</span> CloudWatch p99 latency dropped 2,400ms &rarr; 18ms. Error rate = 0.00%.</div>
          <div className="text-emerald-400 font-bold mt-2">[18:32:26 UTC] [COMMITTED] 2PC Saga committed. Pre-snapshot archived. Proceeding to institutional learning.</div>
        </div>
      </div>
    </section>
  );
}
