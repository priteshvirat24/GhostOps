'use client';

import React, { useState } from 'react';
import { GitCompare, AlertOctagon, Check, X, ShieldAlert, Sparkles } from 'lucide-react';
import TemporalDiffScene from '../3d/scenes/TemporalDiffScene';

export default function ChamberTemporalDrift() {
  const [selectedDim, setSelectedDim] = useState<number>(0);

  const dimensions = [
    {
      name: 'Security Group Ingress Rules',
      baseline: 'sg-0a89f92 allowed 10.0.0.0/16 on 26257',
      current: 'sg-0a89f92 restricted to 10.2.0.0/20 (VPC peered subnet)',
      drifted: true,
      impact: 'Direct application of #1847 fix would grant unrestricted global ingress, violating zero-trust policy.'
    },
    {
      name: 'IAM Role Policy & KMS Key',
      baseline: 'arn:aws:iam::318767729779:role/LegacyDbAccessRole',
      current: 'arn:aws:iam::318767729779:role/GhostOpsServiceRole-v2',
      drifted: true,
      impact: 'Legacy policy permitted wildcards; new role requires explicit resource-level KMS decrypt permissions.'
    },
    {
      name: 'VPC Route Table & Peering',
      baseline: 'Direct local route table 10.0.0.0/16',
      current: 'Transit Gateway attachment tgw-attach-091a2',
      drifted: true,
      impact: 'Modifying local route table would drop Transit Gateway routes for backend services.'
    },
    {
      name: 'CockroachDB Major Version',
      baseline: 'v23.2.4 (Single-region cluster)',
      current: 'v24.1.2 (Multi-region serverless with native vector)',
      drifted: false,
      impact: 'Fully backwards-compatible schema syntax.'
    },
    {
      name: 'Node Topology & Replica Count',
      baseline: '3-node EC2 cluster (m5.xlarge)',
      current: '5-node distributed topology across 3 AZs',
      drifted: true,
      impact: 'Requires quorum calculation across 3 AZs instead of simple single-host restart.'
    },
    {
      name: 'TLS Certificate Authority',
      baseline: 'Self-signed internal certs',
      current: 'AWS ACM Private CA with automatic rotation',
      drifted: false,
      impact: 'No manual certificate replacement needed.'
    },
    {
      name: 'Container OS & Kernel',
      baseline: 'Amazon Linux 2 (Kernel 5.10)',
      current: 'Amazon Linux 2023 (Kernel 6.1)',
      drifted: false,
      impact: 'Systemd service definitions compatible.'
    },
    {
      name: 'Connection Pool Timeout',
      baseline: 'client_idle_timeout = 300s',
      current: 'client_idle_timeout = 60s, max_conns = 250',
      drifted: true,
      impact: 'Aggressive connection reaping in place.'
    },
    {
      name: 'Audit & Telemetry Export',
      baseline: 'Syslog local file',
      current: 'CloudWatch Logs + CDC Stream',
      drifted: false,
      impact: 'Real-time telemetry pipeline active.'
    }
  ];

  const driftedCount = dimensions.filter((d) => d.drifted).length;

  return (
    <section className="py-20 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-10 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-950/80 border border-amber-500/40 text-amber-400 text-xs font-mono mb-3">
          <span>CHAMBER 05</span>
          <span>·</span>
          <span>DETERMINISTIC TEMPORAL REASONING & DRIFT DIFFING</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100 mb-3">
          Flagship Scenario: Why Naive RAG Fails & GhostOps Rejects Stale Precedents
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          Incident #1847 looks like a 94% vector match. However, GhostOps deterministically diffs 9 environment dimensions between 2024 and 2026. Because the VPC and IAM topologies drifted, GhostOps issues a mandatory <span className="text-red-400 font-bold">DO_NOT_EXECUTE</span> verdict, preventing a catastrophic production outage.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: 3D Temporal Diff Scene */}
        <div className="lg:col-span-6 flex flex-col justify-between">
          <div className="h-[360px] w-full mb-4">
            <TemporalDiffScene driftCount={driftedCount} verdict="DO_NOT_EXECUTE" />
          </div>

          {/* Verdict Banner Card */}
          <div className="p-4 rounded-xl border border-red-500/50 bg-red-950/40 backdrop-blur-md">
            <div className="flex items-center gap-2.5 text-red-400 font-bold font-mono text-sm mb-1.5">
              <AlertOctagon className="w-5 h-5 text-red-400 animate-pulse" />
              <span>TEMPORAL SAFETY VERDICT: DO_NOT_EXECUTE</span>
            </div>
            <p className="text-xs text-zinc-300 leading-relaxed font-mono">
              Compatibility Score: <span className="text-red-400 font-bold">0.12 (Below 0.60 Safety Gate)</span>.
              Replaying precedent #1847 would modify security group rules without Transit Gateway awareness, severing 8 microservices.
            </p>
          </div>
        </div>

        {/* Right: 9-Dimension Diff Matrix */}
        <div className="lg:col-span-6 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-zinc-400 pb-1 border-b border-zinc-800">
            <span>9-DIMENSION ENVIRONMENT DIFF</span>
            <span className="text-amber-400 font-semibold">{driftedCount}/9 DRIFTED DIMENSIONS</span>
          </div>

          <div className="space-y-2 max-h-[460px] overflow-y-auto pr-1">
            {dimensions.map((dim, idx) => {
              const isSelected = selectedDim === idx;
              return (
                <div
                  key={idx}
                  onClick={() => setSelectedDim(idx)}
                  className={`p-3.5 rounded-xl cursor-pointer transition-all border ${
                    isSelected
                      ? 'bg-zinc-900 border-amber-500/50 shadow-md shadow-amber-950/20'
                      : 'bg-zinc-950/60 border-zinc-800/60 hover:bg-zinc-900/40 hover:border-zinc-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold font-mono text-zinc-200">{dim.name}</span>
                    <span
                      className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded flex items-center gap-1 ${
                        dim.drifted
                          ? 'bg-red-950 text-red-300 border border-red-800/50'
                          : 'bg-emerald-950 text-emerald-300 border border-emerald-800/50'
                      }`}
                    >
                      {dim.drifted ? <X className="w-3 h-3" /> : <Check className="w-3 h-3" />}
                      {dim.drifted ? 'DRIFTED' : 'STABLE'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-zinc-400 mt-2 bg-zinc-900/50 p-2 rounded">
                    <div>
                      <span className="text-zinc-500 block">2024 Baseline:</span>
                      <span className="text-zinc-300">{dim.baseline}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block">2026 Current:</span>
                      <span className={dim.drifted ? 'text-amber-300' : 'text-zinc-300'}>{dim.current}</span>
                    </div>
                  </div>

                  {isSelected && (
                    <div className="mt-2 text-[11px] text-zinc-300 p-2 rounded bg-amber-950/20 border border-amber-900/30">
                      <span className="text-amber-400 font-semibold font-mono text-[10px] block mb-0.5">DRIFT IMPACT:</span>
                      {dim.impact}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
