'use client';

import React, { useState } from 'react';
import { ShieldCheck, Lock, Play, RotateCcw, AlertTriangle, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function ChamberGovernedRemediation() {
  const [sagaState, setSagaState] = useState<'PENDING' | 'SNAPSHOT' | 'EXECUTING' | 'VERIFYING' | 'COMMITTED'>('COMMITTED');

  const sagaSteps = [
    {
      step: 1,
      name: 'Pre-Execution Snapshot',
      action: 'SNAPSHOT_STATE',
      target: 'arn:aws:ec2:eu-north-1:318767729779:security-group/sg-0a89f92',
      status: 'SUCCESS',
      details: 'Captured JSON pre-state of SG ingress rules & active connection pool counters.'
    },
    {
      step: 2,
      name: 'Execute Adaptive Range Relocation',
      action: 'COCKROACH_RELOCATE_RANGE',
      target: 'crdb://valid-shaman-32362/ranges/1042',
      status: 'SUCCESS',
      details: 'Transferred leaseholder for range 1042 from overloaded node 3 to idle node 1.'
    },
    {
      step: 3,
      name: 'Drain Stale TCP Connections',
      action: 'DRAIN_CONNECTION_POOL',
      target: 'service://auth-service/pool',
      status: 'SUCCESS',
      details: 'Reaped 180 idle connections; connection count normalized to 45/250.'
    },
    {
      step: 4,
      name: 'Independent Out-of-Band Verification',
      action: 'VERIFY_TELEMETRY',
      target: 'AWS/CloudWatch + EC2 Reader',
      status: 'SUCCESS',
      details: 'Verified 0 connection errors and p99 latency normalized to 18ms for 120s.'
    }
  ];

  return (
    <section className="py-20 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-10 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <span>CHAMBER 06</span>
          <span>·</span>
          <span>GOVERNED REMEDIATION & 2-PHASE COMMIT SAGA</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100 mb-3">
          Model-Driven Governed Planner & 2PC Saga Execution Boundary
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          GhostOps never allows raw unvalidated script execution. Remediation plans are generated against a strict action catalog, snapshot pre-state, require policy governance approval, and support automatic rollback compensation.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Governance Policy & Approval Gate */}
        <div className="lg:col-span-5 space-y-4">
          <div className="vault-panel p-5 rounded-xl border border-zinc-800 bg-zinc-950/80">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-zinc-800">
              <span className="text-xs font-mono text-emerald-400 font-semibold flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5" />
                GOVERNANCE SAFETY GATE
              </span>
              <span className="text-[10px] font-mono text-emerald-400 font-bold px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800/50">
                APPROVED
              </span>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div className="p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] uppercase block">Blast Radius Assessment</span>
                <div className="text-zinc-200 font-semibold mt-0.5">LOCALIZED_SERVICE (Tier 2)</div>
                <div className="text-zinc-400 text-[11px] mt-1">Impact isolated to auth-service pool. Zero customer-facing downtime.</div>
              </div>

              <div className="p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] uppercase block">Compensation Invariant</span>
                <div className="text-emerald-400 font-semibold mt-0.5">AUTOMATIC ROLLBACK ENABLED</div>
                <div className="text-zinc-400 text-[11px] mt-1">If CloudWatch p99 fails to normalize within 60s, state reverts via pre-snapshot.</div>
              </div>

              <div className="p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] uppercase block">Action Catalog Validation</span>
                <div className="text-zinc-200 font-semibold mt-0.5">2/2 ACTIONS WHITELISTED</div>
                <div className="text-zinc-400 text-[11px] mt-1">Both actions conform to strictly typed Pydantic parameter schemas.</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: 2PC Saga Step Timeline */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-zinc-400 pb-1 border-b border-zinc-800">
            <span>2PC SAGA EXECUTION LIFECYCLE</span>
            <span className="text-emerald-400 font-semibold">ALL STEPS COMMITTED</span>
          </div>

          <div className="space-y-2.5">
            {sagaSteps.map((s) => (
              <div key={s.step} className="vault-card p-4 rounded-xl border border-zinc-800/80 bg-zinc-950/70">
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-emerald-950 border border-emerald-500/40 text-emerald-400 text-[10px] font-mono font-bold flex items-center justify-center">
                      {s.step}
                    </span>
                    <span className="text-xs font-mono font-bold text-zinc-100">{s.name}</span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/40 flex items-center gap-1 font-semibold">
                    <CheckCircle2 className="w-3 h-3" />
                    {s.status}
                  </span>
                </div>

                <div className="text-[11px] text-zinc-300 font-mono mb-1.5 p-2 rounded bg-zinc-900/60 border border-zinc-800/60">
                  <span className="text-zinc-500 block text-[10px]">Action: {s.action}</span>
                  <span className="text-emerald-400">{s.target}</span>
                </div>

                <p className="text-xs text-zinc-400 leading-relaxed">{s.details}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
