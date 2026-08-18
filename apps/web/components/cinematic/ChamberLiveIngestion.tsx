'use client';

import React, { useState } from 'react';
import { Activity, ShieldCheck, Terminal, Filter, RefreshCw, AlertTriangle, FileCode } from 'lucide-react';

export default function ChamberLiveIngestion() {
  const [selectedLog, setSelectedLog] = useState<number>(0);

  const mockEvents = [
    {
      id: 'EVT-9041',
      timestamp: '2026-08-18T18:32:01.104Z',
      source: 'AWS/CloudWatch',
      service: 'auth-service',
      metric: 'DatabaseConnectionExhaustion',
      value: '250/250 connections (100%)',
      severity: 'CRITICAL',
      sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      payload: {
        alarm_name: 'AuthService-DB-PoolExhausted',
        instance_id: 'i-09f1a2384a92c8101',
        metric_name: 'ActiveConnections',
        namespace: 'AWS/CockroachDB',
        period: 60,
        threshold: 240,
        unit: 'Count'
      }
    },
    {
      id: 'EVT-9042',
      timestamp: '2026-08-18T18:32:04.450Z',
      source: 'AWS/EC2-Audit',
      service: 'vpc-main-security',
      metric: 'AuthorizeSecurityGroupIngress',
      value: 'Rule added on port 22/tcp 0.0.0.0/0',
      severity: 'HIGH',
      sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      payload: {
        security_group_id: 'sg-0a89f92',
        vpc_id: 'vpc-0823491f',
        ip_protocol: 'tcp',
        from_port: 22,
        to_port: 22,
        cidr_ip: '0.0.0.0/0'
      }
    },
    {
      id: 'EVT-9043',
      timestamp: '2026-08-18T18:32:08.820Z',
      source: 'CockroachDB/Telemetry',
      service: 'cockroach-node-03',
      metric: 'RangeLeaseContention',
      value: 'sql.txn.restarts > 4.8%',
      severity: 'WARNING',
      sha256: '6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b',
      payload: {
        node_id: 3,
        cluster_id: 'valid-shaman-32362',
        range_id: 1042,
        contended_keys: ['users.email_idx', 'auth_tokens.session_id'],
        contention_time_ms: 1840
      }
    }
  ];

  return (
    <section className="py-20 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-10 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <span>CHAMBER 02</span>
          <span>·</span>
          <span>PRODUCTION SIGNAL INGESTION & EVIDENCE PRESERVATION</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-bold text-zinc-100 mb-3">
          Raw Telemetry Ingestion & Cryptographic Evidence Chain
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          Signals from CloudWatch alarms, audit trails, and CockroachDB internals are captured with immutable SHA-256 evidence hashing, preventing phantom hallucinations before reasoning begins.
        </p>
      </div>

      {/* Main Grid: Signal Waterfall & Evidence Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Signal Stream */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-zinc-800 text-xs font-mono text-zinc-400">
            <span className="flex items-center gap-2">
              <Activity className="w-3.5 h-3.5 text-emerald-400" />
              LIVE TELEMETRY STREAM
            </span>
            <span className="text-emerald-400">3 CAPTURED SIGNALS</span>
          </div>

          {mockEvents.map((evt, idx) => {
            const isSelected = selectedLog === idx;
            return (
              <div
                key={evt.id}
                onClick={() => setSelectedLog(idx)}
                className={`p-4 rounded-xl cursor-pointer transition-all duration-200 border ${
                  isSelected
                    ? 'bg-zinc-900/90 border-emerald-500/50 shadow-lg shadow-emerald-950/40'
                    : 'bg-zinc-950/60 border-zinc-800/60 hover:border-zinc-700 hover:bg-zinc-900/40'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold font-mono text-zinc-200">{evt.id}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300">
                      {evt.source}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded ${
                      evt.severity === 'CRITICAL'
                        ? 'bg-red-950/80 border border-red-800/60 text-red-300'
                        : evt.severity === 'HIGH'
                        ? 'bg-amber-950/80 border border-amber-800/60 text-amber-300'
                        : 'bg-zinc-800 text-zinc-300'
                    }`}
                  >
                    {evt.severity}
                  </span>
                </div>
                <div className="text-sm font-semibold text-zinc-100 mb-1">{evt.metric}</div>
                <div className="text-xs text-zinc-400 font-mono mb-2">{evt.value}</div>
                <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500 pt-2 border-t border-zinc-800/50">
                  <span>Target: {evt.service}</span>
                  <span className="text-emerald-400/80">SHA: {evt.sha256.substring(0, 12)}...</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right: Cryptographic Evidence Inspector */}
        <div className="lg:col-span-5">
          <div className="vault-panel p-5 rounded-xl border border-zinc-800/80 bg-zinc-950/80 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-zinc-800">
                <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 font-semibold">
                  <ShieldCheck className="w-4 h-4" />
                  <span>EVIDENCE INTEGRITY RECORD</span>
                </div>
                <span className="text-[10px] font-mono text-zinc-500">VERIFIED IMMUTABLE</span>
              </div>

              <div className="space-y-3 mb-4">
                <div>
                  <span className="text-[10px] font-mono text-zinc-500 uppercase">Evidence Identifier</span>
                  <div className="text-xs font-mono text-zinc-200 font-semibold">{mockEvents[selectedLog].id}</div>
                </div>

                <div>
                  <span className="text-[10px] font-mono text-zinc-500 uppercase">Cryptographic SHA-256 Hash</span>
                  <div className="text-[11px] font-mono text-emerald-300 break-all p-2 rounded bg-zinc-900 border border-zinc-800">
                    {mockEvents[selectedLog].sha256}
                  </div>
                </div>

                <div>
                  <span className="text-[10px] font-mono text-zinc-500 uppercase">Source System & Timestamp</span>
                  <div className="text-xs font-mono text-zinc-300">
                    {mockEvents[selectedLog].source} · {mockEvents[selectedLog].timestamp}
                  </div>
                </div>
              </div>

              {/* Raw JSON Payload */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono text-zinc-500 uppercase">Preserved Raw Payload</span>
                  <FileCode className="w-3 h-3 text-zinc-500" />
                </div>
                <pre className="p-3 rounded-lg bg-zinc-900/90 border border-zinc-800 text-[11px] font-mono text-zinc-300 overflow-x-auto max-h-44">
                  {JSON.stringify(mockEvents[selectedLog].payload, null, 2)}
                </pre>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-[11px] font-mono text-zinc-400">
              <span>Grounding Invariant</span>
              <span className="text-emerald-400 font-medium">100% CITED IN HYPOTHESIS</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
