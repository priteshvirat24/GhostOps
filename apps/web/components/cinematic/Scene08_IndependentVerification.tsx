'use client';

import React from 'react';
import { Activity, ShieldCheck, CheckCircle2, TrendingDown, ArrowRight, ShieldAlert, Cpu, Database } from 'lucide-react';

export default function Scene08_IndependentVerification() {
  const verificationProof = [
    {
      source: 'AWS/EC2 Security Audit',
      operation: 'ec2:DescribeSecurityGroups',
      target: 'sg-0a89f92',
      finding: 'Ingress rules verified untouched. Transit Gateway peering integrity intact.',
      status: 'VERIFIED'
    },
    {
      source: 'AWS/CloudWatch Metric Reader',
      operation: 'cloudwatch:GetMetricData',
      target: 'AuthService-DB-PoolExhausted',
      finding: 'Connection pool dropped from 250 (100%) to 45 (18%). Alarms normalized.',
      status: 'VERIFIED'
    },
    {
      source: 'CockroachDB Internal Telemetry',
      operation: 'SHOW RANGES FROM TABLE auth_tokens',
      target: 'Range 1042',
      finding: 'Leaseholder relocated to Node 1. Contention time dropped from 1,840ms -> 2ms.',
      status: 'VERIFIED'
    }
  ];

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-12 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <span>SCENE 08</span>
          <span>·</span>
          <span>INDEPENDENT OUT-OF-BAND VERIFICATION</span>
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-zinc-100 mb-4">
          Execution Says: "I did it." Verification Says: "Let me check."
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          GhostOps never trusts self-reported agent success claims. A completely decoupled verification agent reads independent AWS CloudWatch telemetry and EC2 state to prove invariant restoration before declaring victory.
        </p>
      </div>

      {/* Decoupled Dialogue Card */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="vault-panel p-5 rounded-2xl border border-zinc-800 bg-zinc-950/80">
          <div className="flex items-center gap-2 text-xs font-mono text-zinc-400 font-bold mb-2">
            <Cpu className="w-4 h-4 text-zinc-400" />
            <span>EXECUTION AGENT CLAIM</span>
          </div>
          <p className="text-sm font-mono text-zinc-200 italic">
            "I executed CockroachDB range relocation and drained the auth-service connection pool. Task marked complete."
          </p>
          <div className="mt-3 text-[10px] font-mono text-zinc-500">Status: UNVERIFIED AGENT CLAIM</div>
        </div>

        <div className="vault-panel p-5 rounded-2xl border border-emerald-500/50 bg-emerald-950/20 shadow-xl shadow-emerald-950/30">
          <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 font-bold mb-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>INDEPENDENT VERIFIER RESPONSE</span>
          </div>
          <p className="text-sm font-mono text-emerald-200">
            "Queried CloudWatch directly: p99 latency dropped to 18ms (threshold: 200ms). Error rate is 0.00%. Invariants verified."
          </p>
          <div className="mt-3 text-[10px] font-mono text-emerald-400 font-bold">VERDICT: INDEPENDENTLY PROVED</div>
        </div>
      </div>

      {/* Proof Feed Grid */}
      <div className="space-y-3 mb-8">
        {verificationProof.map((item, idx) => (
          <div key={idx} className="vault-card p-4 rounded-xl border border-zinc-800/80 bg-zinc-950/70 flex flex-col sm:flex-row sm:items-center justify-between gap-3 font-mono text-xs">
            <div>
              <div className="flex items-center gap-2 text-zinc-300 font-bold mb-1">
                <span className="text-emerald-400">{item.source}</span>
                <span className="text-zinc-600">·</span>
                <span className="text-zinc-400">{item.operation}</span>
              </div>
              <p className="text-[11px] text-zinc-400 leading-relaxed">{item.finding}</p>
            </div>
            <span className="px-3 py-1 rounded-lg bg-emerald-950 text-emerald-300 border border-emerald-700/50 text-[10px] font-bold self-start sm:self-center shrink-0 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              {item.status}
            </span>
          </div>
        ))}
      </div>

      {/* Trust Score Delta Card */}
      <div className="vault-panel p-6 rounded-2xl border border-zinc-800 bg-zinc-950/90 flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-xs">
        <div>
          <span className="text-zinc-500 uppercase text-[10px] block">Institutional Memory Trust Delta</span>
          <div className="text-zinc-100 font-bold text-sm mt-0.5">Precedent #1402 Trust Score Elevation</div>
          <div className="text-zinc-400 text-[11px] mt-0.5">Verified successful execution increments precedent reliability weight across fleet.</div>
        </div>
        <div className="flex items-center gap-3 p-3 rounded-xl bg-zinc-900 border border-zinc-800 shrink-0">
          <span className="text-zinc-400">0.85 (Base)</span>
          <ArrowRight className="w-4 h-4 text-emerald-400" />
          <span className="text-emerald-400 font-bold text-base">+0.07 (Bonus)</span>
          <ArrowRight className="w-4 h-4 text-emerald-400" />
          <span className="text-emerald-300 font-bold text-base">0.92 (New Trust)</span>
        </div>
      </div>
    </section>
  );
}
