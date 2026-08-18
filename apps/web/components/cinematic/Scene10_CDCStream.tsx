'use client';

import React, { useState } from 'react';
import { Database, Radio, GitCommit, RefreshCw, Layers, ShieldCheck, CheckCircle2, ArrowRight } from 'lucide-react';

export default function Scene10_CDCStream() {
  const [selectedFeed, setSelectedFeed] = useState<number>(0);

  const cdcRecords = [
    {
      timestamp: '2026-08-18T18:33:02.110Z',
      topic: 'ghostops.memories',
      op: 'INSERT',
      key: 'mem_2026_0904_db_contention',
      vectorDim: 1536,
      replicationStatus: 'DURABLY_REPLICATED (3 AZs)',
      payload: {
        memory_id: 'mem_2026_0904_db_contention',
        title: 'CockroachDB Range Hotspot Contention Rebalance',
        trust_level: 'HIGH_TRUST',
        trust_score: 0.92,
        embedding_dim: 1536,
        model_version: 'amazon.titan-embed-text-v2:0',
        provenance_incident_id: 'inc-2026-904',
        cdc_lsn: '78912304910239401'
      }
    },
    {
      timestamp: '2026-08-18T18:33:02.450Z',
      topic: 'ghostops.trust_ledger',
      op: 'UPDATE',
      key: 'prec_1402_trust_update',
      vectorDim: 1536,
      replicationStatus: 'DURABLY_REPLICATED (3 AZs)',
      payload: {
        precedent_id: 'PREC-1402',
        old_trust: 0.85,
        new_trust: 0.92,
        delta: 0.07,
        verified_by: 'AWS/CloudWatch+EC2_Reader',
        cdc_lsn: '78912304910239450'
      }
    },
    {
      timestamp: '2026-08-18T18:33:03.012Z',
      topic: 'ghostops.sentinel_events',
      op: 'BROADCAST',
      key: 'sentinel_policy_update',
      vectorDim: 1536,
      replicationStatus: 'EMITTED_TO_FLEET',
      payload: {
        sentinel_id: 'sentinel-fleet-primary',
        action: 'UPDATE_INVARIANT_CACHE',
        active_rules_count: 14,
        cdc_lsn: '78912304910239512'
      }
    }
  ];

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-12 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <span>SCENE 10</span>
          <span>·</span>
          <span>COCKROACHDB CHANGE DATA CAPTURE (CDC)</span>
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-zinc-100 mb-4">
          Durable CDC Changefeeds & Fleet Memory Propagation
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          CockroachDB Change Data Capture guarantees durable, exactly-once stream propagation. When an operational memory is consolidated, the changefeed emits event envelopes to downstream regional sentinels and agent clusters.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Animated Architecture Stream Pipeline */}
        <div className="lg:col-span-5 space-y-4">
          <div className="vault-panel p-6 rounded-2xl border border-zinc-800 bg-zinc-950/80 font-mono text-xs">
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-zinc-800">
              <span className="text-emerald-400 font-bold flex items-center gap-2">
                <Database className="w-4 h-4" />
                <span>CDC CHANGEFEED PIPELINE</span>
              </span>
              <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-bold">
                CONNECTED
              </span>
            </div>

            <div className="space-y-3 text-[11px]">
              <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block uppercase">1. CockroachDB Core Table</span>
                <span className="text-zinc-200 font-bold mt-0.5 block">CREATE CHANGEFEED FOR TABLE memories</span>
                <span className="text-emerald-400 text-[10px]">Zero-overhead distributed change logging</span>
              </div>

              <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block uppercase">2. Streaming Event Bus</span>
                <span className="text-zinc-200 font-bold mt-0.5 block">Kafka / SQS / Webhook Sink</span>
                <span className="text-emerald-400 text-[10px]">End-to-end exactly-once idempotency</span>
              </div>

              <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block uppercase">3. Fleet Memory Subscribers</span>
                <span className="text-zinc-200 font-bold mt-0.5 block">Multi-Region GhostOps Sentinels</span>
                <span className="text-emerald-400 text-[10px]">Active cache invalidation & vector reload</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Live CDC Message Inspector */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between text-xs font-mono text-zinc-400 pb-1 border-b border-zinc-800">
            <span>LIVE CDC EVENT MESSAGES</span>
            <span className="text-emerald-400">STREAM ACTIVE</span>
          </div>

          <div className="space-y-3">
            {cdcRecords.map((rec, idx) => {
              const isSelected = selectedFeed === idx;
              return (
                <div
                  key={idx}
                  onClick={() => setSelectedFeed(idx)}
                  className={`p-4 rounded-xl cursor-pointer transition-all border font-mono text-xs ${
                    isSelected
                      ? 'bg-zinc-900 border-emerald-500/50 shadow-xl shadow-emerald-950/20'
                      : 'bg-zinc-950/70 border-zinc-800/70 hover:bg-zinc-900/40 hover:border-zinc-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-bold text-[10px]">
                        {rec.op}
                      </span>
                      <span className="text-zinc-200 font-bold">{rec.topic}</span>
                    </div>
                    <span className="text-[10px] text-zinc-500">{rec.timestamp}</span>
                  </div>

                  <div className="text-[11px] text-zinc-400 mb-2">
                    <span className="text-zinc-500">Key: </span>
                    <span className="text-emerald-400">{rec.key}</span>
                  </div>

                  {isSelected && (
                    <pre className="p-3 rounded-lg bg-zinc-950 border border-zinc-800 text-[10px] text-zinc-300 overflow-x-auto">
                      {JSON.stringify(rec.payload, null, 2)}
                    </pre>
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
