'use client';

import React from 'react';
import { Activity, ShieldCheck, CheckCircle2, TrendingDown, ArrowDownRight } from 'lucide-react';

export default function ChamberTelemetryVerification() {
  const metrics = [
    {
      name: 'Active DB Connection Pool',
      pre: '250 / 250 (100%)',
      post: '45 / 250 (18%)',
      change: '-82.0%',
      status: 'VERIFIED_HEALTHY',
      unit: 'Count'
    },
    {
      name: 'Auth-Service p99 Latency',
      pre: '2,400 ms',
      post: '18 ms',
      change: '-99.2%',
      status: 'VERIFIED_HEALTHY',
      unit: 'Milliseconds'
    },
    {
      name: 'Transaction Retry Storm Rate',
      pre: '4.80 %',
      post: '0.02 %',
      change: '-99.6%',
      status: 'VERIFIED_HEALTHY',
      unit: 'Percentage'
    },
    {
      name: 'HTTP 500 / 504 Error Rate',
      pre: '12.40 %',
      post: '0.00 %',
      change: '-100.0%',
      status: 'VERIFIED_HEALTHY',
      unit: 'Percentage'
    }
  ];

  return (
    <section className="py-20 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-10 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <span>CHAMBER 07</span>
          <span>·</span>
          <span>INDEPENDENT OUT-OF-BAND TELEMETRY VERIFICATION</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100 mb-3">
          Independent AWS Telemetry Reader & Post-Remediation Invariant Proof
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          GhostOps does not trust self-reported agent success. A decoupled telemetry reader pulls real CloudWatch metrics and EC2 states to independently verify invariant restoration before marking an incident resolved.
        </p>
      </div>

      {/* Delta Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {metrics.map((m, idx) => (
          <div key={idx} className="vault-card p-4 rounded-xl border border-zinc-800/80 bg-zinc-950/80">
            <div className="flex items-center justify-between text-[10px] font-mono text-zinc-400 mb-2">
              <span>{m.name}</span>
              <span className="text-emerald-400 font-bold px-1.5 py-0.5 rounded bg-emerald-950 border border-emerald-800/40">
                {m.change}
              </span>
            </div>

            <div className="space-y-1.5 my-3">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-zinc-500">PRE:</span>
                <span className="text-red-400 font-semibold">{m.pre}</span>
              </div>
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-zinc-500">POST:</span>
                <span className="text-emerald-400 font-bold">{m.post}</span>
              </div>
            </div>

            <div className="pt-2 border-t border-zinc-800/60 flex items-center justify-between text-[10px] font-mono text-emerald-300">
              <span className="flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                {m.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Out-of-Band Reader Proof Box */}
      <div className="vault-panel p-5 rounded-xl border border-zinc-800 bg-zinc-950/80">
        <div className="flex items-center justify-between mb-3 pb-2 border-b border-zinc-800 text-xs font-mono">
          <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4" />
            <span>INDEPENDENT VERIFICATION AUDIT LOG</span>
          </span>
          <span className="text-zinc-400">AWS SDK (boto3) DIRECT READ</span>
        </div>
        <div className="p-3 rounded-lg bg-zinc-900 font-mono text-xs text-zinc-300 space-y-1">
          <div className="text-zinc-500">// Bypassing agent state — querying Amazon CloudWatch & EC2 directly</div>
          <div>[18:32:45 UTC] <span className="text-emerald-400">ec2:DescribeSecurityGroups(sg-0a89f92)</span> &rarr; Rules verified untouched.</div>
          <div>[18:32:46 UTC] <span className="text-emerald-400">cloudwatch:GetMetricData(AuthService-DB-PoolExhausted)</span> &rarr; 45 conns (Threshold: 240).</div>
          <div>[18:32:48 UTC] <span className="text-emerald-400">cockroach:SHOW RANGES FROM TABLE auth_tokens</span> &rarr; Leaseholder active on node 1.</div>
          <div className="text-emerald-400 font-semibold mt-2">[18:32:50 UTC] VERIFICATION VERDICT: ALL INVARIANTS SATISFIED &rarr; PROCEED TO CONSOLIDATION</div>
        </div>
      </div>
    </section>
  );
}
