'use client';

import React, { useState } from 'react';
import { GitCompare, AlertOctagon, Check, X, ShieldAlert, Sparkles, Layers } from 'lucide-react';
import TemporalDiffScene from '../3d/scenes/TemporalDiffScene';

export default function Scene05_TemporalChamber() {
  const [selectedLayer, setSelectedLayer] = useState<number>(0);

  const environmentLayers = [
    {
      id: 1,
      name: 'VPC Peering & Transit Gateway',
      category: 'Topology',
      baseline2024: 'Direct local 10.0.0.0/16 VPC peering',
      current2026: 'Transit Gateway attachment tgw-attach-091a2',
      status: 'DANGEROUS_INCOMPATIBILITY',
      drifted: true,
      impact: 'Direct SG rule modification would sever Transit Gateway routing table for 8 downstream microservices.'
    },
    {
      id: 2,
      name: 'Security Group Ingress Boundary',
      category: 'Configuration',
      baseline2024: 'sg-0a89f92 permitted 10.0.0.0/16 on 26257',
      current2026: 'sg-0a89f92 restricted to 10.2.0.0/20 subnet',
      status: 'DANGEROUS_INCOMPATIBILITY',
      drifted: true,
      impact: 'Replaying #1847 grants 0.0.0.0/0 global ingress, violating zero-trust production invariant.'
    },
    {
      id: 3,
      name: 'IAM Execution Role & KMS Keys',
      category: 'Security/State',
      baseline2024: 'Wildcard LegacyDbAccessRole',
      current2026: 'Strict GhostOpsServiceRole-v2 with KMS boundary',
      status: 'DRIFTED',
      drifted: true,
      impact: 'Requires explicit resource-level KMS decrypt permissions.'
    },
    {
      id: 4,
      name: 'CockroachDB Engine Version',
      category: 'Database',
      baseline2024: 'CockroachDB v23.2.4 (Single AZ)',
      current2026: 'CockroachDB v24.1.2 (Multi-Region Cloud)',
      status: 'STABLE',
      drifted: false,
      impact: 'Native VECTOR(1536) and range relocation syntax fully compatible.'
    },
    {
      id: 5,
      name: 'Cluster Topology & Nodes',
      category: 'Scale',
      baseline2024: '3-node EC2 cluster (m5.xlarge)',
      current2026: '5-node serverless across 3 AZs',
      status: 'DRIFTED',
      drifted: true,
      impact: 'Requires multi-AZ quorum calculation rather than single-node restart.'
    },
    {
      id: 6,
      name: 'TLS Certificate Authority',
      category: 'Dependencies',
      baseline2024: 'Self-signed internal certs',
      current2026: 'AWS ACM Private CA auto-rotated',
      status: 'STABLE',
      drifted: false,
      impact: 'Certificate rotation automated by AWS.'
    },
    {
      id: 7,
      name: 'Container OS & Kernel',
      category: 'Version',
      baseline2024: 'Amazon Linux 2 (Kernel 5.10)',
      current2026: 'Amazon Linux 2023 (Kernel 6.1)',
      status: 'STABLE',
      drifted: false,
      impact: 'Systemd service definitions compatible.'
    },
    {
      id: 8,
      name: 'Connection Pool Reaper Policy',
      category: 'Traffic',
      baseline2024: 'client_idle_timeout = 300s',
      current2026: 'client_idle_timeout = 60s, max_conns = 250',
      status: 'DRIFTED',
      drifted: true,
      impact: 'Aggressive pool reclamation actively drops idle sockets.'
    },
    {
      id: 9,
      name: 'Audit & Telemetry Pipeline',
      category: 'State',
      baseline2024: 'Syslog local files',
      current2026: 'CloudWatch Logs + Real CDC Stream',
      status: 'STABLE',
      drifted: false,
      impact: 'Real-time telemetry event bus active.'
    }
  ];

  const current = environmentLayers[selectedLayer];
  const driftedCount = environmentLayers.filter((l) => l.drifted).length;

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-12 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-950/80 border border-amber-500/40 text-amber-400 text-xs font-mono mb-3">
          <span>SCENE 05</span>
          <span>·</span>
          <span>THE TEMPORAL REASONING CHAMBER</span>
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-zinc-100 mb-4">
          THEN vs NOW: 9-Layer Layered Environment Diffing
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          GhostOps evaluates historical precedents against physical environment layers. When a historical fix is incompatible with current network topology, GhostOps issues an architectural <span className="text-red-400 font-bold">DO_NOT_EXECUTE</span> verdict.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: 3D Dual-Ring Topology Scene & Verdict Banner */}
        <div className="lg:col-span-6 flex flex-col justify-between">
          <div className="h-[380px] w-full mb-4">
            <TemporalDiffScene driftCount={driftedCount} verdict="DO_NOT_EXECUTE" />
          </div>

          {/* Architectural Verdict Object */}
          <div className="p-5 rounded-2xl border border-red-500/60 bg-red-950/50 backdrop-blur-xl shadow-2xl shadow-red-950/40">
            <div className="flex items-center justify-between mb-2 pb-2 border-b border-red-800/60">
              <div className="flex items-center gap-2 text-red-400 font-mono font-bold text-sm">
                <AlertOctagon className="w-5 h-5 text-red-400 animate-pulse" />
                <span>ARCHITECTURAL VERDICT: DO_NOT_EXECUTE</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-700 font-bold">
                COMPATIBILITY: 0.12
              </span>
            </div>
            <p className="text-xs text-zinc-200 leading-relaxed font-mono">
              Precedent #1847 has a 94% vector match, but 5/9 environment layers have drifted. Executing the 2024 Security Group modification would sever Transit Gateway connections. GhostOps prevents unsafe execution.
            </p>
          </div>
        </div>

        {/* Right: 9 Physical Environment Layers List */}
        <div className="lg:col-span-6 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-zinc-400 pb-1 border-b border-zinc-800">
            <span>PHYSICAL ENVIRONMENT LAYERS (THEN vs NOW)</span>
            <span className="text-amber-400 font-semibold">{driftedCount}/9 DRIFTED LAYERS</span>
          </div>

          <div className="space-y-2 max-h-[480px] overflow-y-auto pr-1">
            {environmentLayers.map((layer, idx) => {
              const isSelected = selectedLayer === idx;
              return (
                <div
                  key={layer.id}
                  onClick={() => setSelectedLayer(idx)}
                  className={`p-3.5 rounded-xl cursor-pointer transition-all border ${
                    isSelected
                      ? 'bg-zinc-900 border-amber-500/60 shadow-lg shadow-amber-950/30'
                      : 'bg-zinc-950/60 border-zinc-800/60 hover:bg-zinc-900/40 hover:border-zinc-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold font-mono text-zinc-100">{layer.name}</span>
                      <span className="text-[10px] font-mono text-zinc-500">[{layer.category}]</span>
                    </div>
                    <span
                      className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded flex items-center gap-1 ${
                        layer.status === 'DANGEROUS_INCOMPATIBILITY'
                          ? 'bg-red-950 text-red-300 border border-red-800/60'
                          : layer.status === 'DRIFTED'
                          ? 'bg-amber-950 text-amber-300 border border-amber-800/60'
                          : 'bg-emerald-950 text-emerald-300 border border-emerald-800/60'
                      }`}
                    >
                      {layer.drifted ? <X className="w-3 h-3" /> : <Check className="w-3 h-3" />}
                      {layer.status.replace('_', ' ')}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-zinc-400 mt-2 bg-zinc-900/60 p-2 rounded-lg">
                    <div>
                      <span className="text-zinc-500 block">THEN (2024 Baseline):</span>
                      <span className="text-zinc-300">{layer.baseline2024}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block">NOW (2026 Current):</span>
                      <span className={layer.drifted ? 'text-amber-300 font-semibold' : 'text-zinc-300'}>
                        {layer.current2026}
                      </span>
                    </div>
                  </div>

                  {isSelected && (
                    <div className="mt-2 text-[11px] font-mono text-zinc-300 p-2.5 rounded bg-amber-950/20 border border-amber-900/40">
                      <span className="text-amber-400 font-bold block mb-0.5 text-[10px]">DRIFT IMPACT:</span>
                      {layer.impact}
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
