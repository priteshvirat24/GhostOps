'use client';

import React, { useState } from 'react';
import { Database, Filter, Layers, ShieldCheck, AlertOctagon, Archive, CheckCircle2, Search } from 'lucide-react';
import MemoryConstellationScene from '../3d/scenes/MemoryConstellationScene';

export default function Scene03_MemoryVault() {
  const [filterType, setFilterType] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const memoryCatalog = [
    {
      id: 'MEM-1847',
      title: 'Direct Security Group Ingress SSH Modification',
      category: 'NEGATIVE_KNOWLEDGE',
      typeLabel: 'DO NOT REPEAT',
      trustScore: 0.95,
      vectorScore: 0.94,
      status: 'STRICTLY_REJECTED',
      badgeColor: 'border-red-500/60 bg-red-950/80 text-red-300',
      reason: '2024 fix granted global ingress; 2026 Transit Gateway peering makes direct SG mutation dangerous.'
    },
    {
      id: 'MEM-1402',
      title: 'CockroachDB Range Leaseholder Contention Rebalance',
      category: 'HIGH_TRUST',
      typeLabel: 'HIGH TRUST PRECEDENT',
      trustScore: 0.94,
      vectorScore: 0.91,
      status: 'VERIFIED_ACTIVE',
      badgeColor: 'border-emerald-500/60 bg-emerald-950/80 text-emerald-300',
      reason: 'Adaptive lease transfer from hot node 3 to node 1 reduces retry storm by 99.6%.'
    },
    {
      id: 'MEM-0912',
      title: 'Manual EC2 Instance Reboot on CPU Spike',
      category: 'SUPERSEDED',
      typeLabel: 'SUPERSEDED',
      trustScore: 0.40,
      vectorScore: 0.72,
      status: 'DEPRECATED',
      badgeColor: 'border-zinc-700 bg-zinc-900/80 text-zinc-400',
      reason: 'Superseded by auto-healing Horizontal Pod Autoscaler definition in v24.1.'
    },
    {
      id: 'MEM-1109',
      title: 'Auth-Service Connection Pool Starvation Drainage',
      category: 'HIGH_TRUST',
      typeLabel: 'HIGH TRUST PRECEDENT',
      trustScore: 0.92,
      vectorScore: 0.89,
      status: 'VERIFIED_ACTIVE',
      badgeColor: 'border-emerald-500/60 bg-emerald-950/80 text-emerald-300',
      reason: 'Reaps stale idle pool connections without terminating active transaction sessions.'
    },
    {
      id: 'MEM-0822',
      title: 'Direct pg_terminate_backend on CockroachDB',
      category: 'NEGATIVE_KNOWLEDGE',
      typeLabel: 'DO NOT REPEAT',
      trustScore: 0.98,
      vectorScore: 0.65,
      status: 'STRICTLY_REJECTED',
      badgeColor: 'border-red-500/60 bg-red-950/80 text-red-300',
      reason: 'Postgres internal function pg_terminate_backend is invalid in CockroachDB; use CANCEL QUERY.'
    }
  ];

  const filteredMemories = memoryCatalog.filter((m) => {
    const matchesFilter = filterType === 'ALL' || m.category === filterType;
    const matchesSearch = searchQuery === '' || m.title.toLowerCase().includes(searchQuery.toLowerCase()) || m.reason.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-12 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <span>SCENE 03</span>
          <span>·</span>
          <span>THE INSTITUTIONAL MEMORY VAULT</span>
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-zinc-100 mb-4">
          Durable Precedents, Trust Scores & Negative Knowledge
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          GhostOps manages 46 institutional memory vectors in CockroachDB Serverless. Memory is not a flat cache: it explicitly encodes <span className="text-red-400 font-semibold">Negative Knowledge ("DO NOT REPEAT")</span>, <span className="text-zinc-400 font-semibold">Superseded Fixes</span>, and <span className="text-emerald-400 font-semibold">High-Trust Precedents</span>.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: 3D Vector Space Constellation */}
        <div className="lg:col-span-6 flex flex-col justify-between">
          <div className="h-[420px] w-full mb-4">
            <MemoryConstellationScene />
          </div>

          {/* Semantic Encoding Legend */}
          <div className="grid grid-cols-3 gap-3 text-center text-[10px] font-mono">
            <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/40">
              <span className="text-emerald-400 font-bold block mb-1">HIGH TRUST</span>
              <span className="text-zinc-400">Stable, luminous green</span>
            </div>
            <div className="p-3 rounded-xl bg-red-950/40 border border-red-500/40">
              <span className="text-red-400 font-bold block mb-1">DO NOT REPEAT</span>
              <span className="text-zinc-400">Negative knowledge crystal</span>
            </div>
            <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800">
              <span className="text-zinc-400 font-bold block mb-1">SUPERSEDED</span>
              <span className="text-zinc-500">Translucent ghosted glass</span>
            </div>
          </div>
        </div>

        {/* Right: Interactive Memory Catalog Explorer */}
        <div className="lg:col-span-6 space-y-4">
          {/* Search & Filter Bar */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 p-2 rounded-xl bg-zinc-900 border border-zinc-800">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search CockroachDB memory vectors..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-xs font-mono text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div className="flex items-center gap-1 overflow-x-auto">
              {(['ALL', 'HIGH_TRUST', 'NEGATIVE_KNOWLEDGE', 'SUPERSEDED'] as const).map((cat) => (
                <button
                  key={cat}
                  onClick={() => setFilterType(cat)}
                  className={`px-2.5 py-1 rounded-lg text-[10px] font-mono whitespace-nowrap transition-all ${
                    filterType === cat
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/50 font-bold'
                      : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800'
                  }`}
                >
                  {cat === 'NEGATIVE_KNOWLEDGE' ? 'NEGATIVE' : cat}
                </button>
              ))}
            </div>
          </div>

          {/* Memory Items List */}
          <div className="space-y-3 max-h-[440px] overflow-y-auto pr-1">
            {filteredMemories.map((m) => (
              <div key={m.id} className="vault-card p-4 rounded-xl border border-zinc-800/80 bg-zinc-950/75">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-zinc-100">{m.id}</span>
                    <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded border ${m.badgeColor}`}>
                      {m.typeLabel}
                    </span>
                  </div>
                  <span className="text-xs font-mono font-bold text-emerald-400">
                    Trust: {(m.trustScore * 100).toFixed(0)}%
                  </span>
                </div>

                <h4 className="text-xs font-semibold text-zinc-100 mb-1.5">{m.title}</h4>
                <p className="text-xs text-zinc-400 leading-relaxed mb-2.5 font-mono">{m.reason}</p>

                <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500 pt-2 border-t border-zinc-800/60">
                  <span>VECTOR SIMILARITY: {(m.vectorScore * 100).toFixed(0)}%</span>
                  <span className={m.status === 'STRICTLY_REJECTED' ? 'text-red-400 font-bold' : 'text-emerald-400'}>
                    STATUS: {m.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
