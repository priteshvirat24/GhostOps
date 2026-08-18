import React, { useState, useEffect } from 'react';
import { X, ShieldAlert, Clock, Database, CheckCircle2, XCircle, FileText, Brain, Cpu, Server, Sparkles, Bot, ShieldCheck } from 'lucide-react';
import { IncidentDetail, IncidentEvidence } from '../types';
import { fetchIncidentEvidence, fetchSimilarIncidents } from '../lib/api';
import HistoricalMemorySection from './HistoricalMemorySection';
import AgentInvestigationSection from './AgentInvestigationSection';
import RemediationGovernanceSection from './RemediationGovernanceSection';

interface IncidentDetailModalProps {
  incident: IncidentDetail;
  onClose: () => void;
}

export default function IncidentDetailModal({ incident, onClose }: IncidentDetailModalProps) {
  const [activeTab, setActiveTab] = useState<'governance' | 'investigation' | 'similar' | 'timeline' | 'infrastructure' | 'actions' | 'evidence' | 'memory'>('governance');
  const [evidenceList, setEvidenceList] = useState<IncidentEvidence[]>([]);
  const [similarCandidates, setSimilarCandidates] = useState<any[]>([]);
  const [loadingSimilar, setLoadingSimilar] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      setLoadingSimilar(true);
      const [evData, simData] = await Promise.all([
        fetchIncidentEvidence(incident.id),
        fetchSimilarIncidents(incident.id, 5),
      ]);
      setEvidenceList(evData);
      if (simData && simData.candidates) {
        setSimilarCandidates(simData.candidates);
      }
      setLoadingSimilar(false);
    }
    loadData();
  }, [incident.id]);

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/40';
      case 'HIGH':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/40';
    }
  };

  const primarySnapshot = incident.snapshots[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
      <div className="glass-panel w-full max-w-5xl rounded-2xl border border-gray-800 bg-[#0F172A] shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-6 border-b border-gray-800 flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center space-x-3">
              <span className={`text-xs font-bold px-2.5 py-1 rounded border uppercase ${getSeverityBadge(incident.severity)}`}>
                {incident.severity}
              </span>
              <span className="text-xs bg-gray-800 text-cyan-300 font-mono px-2.5 py-1 rounded border border-gray-700">
                {incident.service} ({incident.region})
              </span>
              <span className="text-xs bg-purple-950/60 text-purple-300 font-mono px-2.5 py-1 rounded border border-purple-800/50">
                Memory: {incident.memory_status}
              </span>
            </div>
            <h2 className="text-xl font-bold text-gray-100 mt-2">{incident.title}</h2>
            <p className="text-xs text-gray-400">{incident.description}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-gray-800 bg-gray-900/60 px-6 space-x-6 text-sm overflow-x-auto">
          {[
            { id: 'governance', label: 'Remediation Governance', icon: ShieldCheck, badge: 'STAGE 5' },
            { id: 'investigation', label: 'Agent Investigation Engine', icon: Bot, badge: 'STAGE 4' },
            { id: 'similar', label: 'Historical Memory Retrieval', icon: Sparkles, badge: 'HYBRID' },
            { id: 'timeline', label: 'Chronological Timeline', icon: Clock },
            { id: 'infrastructure', label: 'Infrastructure Snapshot', icon: Server },
            { id: 'actions', label: 'Action History', icon: ShieldAlert },
            { id: 'evidence', label: 'Raw Authoritative Evidence', icon: FileText, badge: 'RAW' },
            { id: 'memory', label: 'Derived Operational Memory', icon: Brain, badge: 'DERIVED' },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-3 flex items-center space-x-2 border-b-2 font-medium transition shrink-0 ${
                  isActive
                    ? 'border-emerald-400 text-emerald-300 font-semibold'
                    : 'border-transparent text-gray-400 hover:text-gray-200'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
                {tab.badge && (
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold ${
                      tab.badge === 'STAGE 5'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 animate-pulse'
                        : tab.badge === 'STAGE 4'
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                        : tab.badge === 'RAW'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        : 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                    }`}
                  >
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {/* TAB: STAGE 5 REMEDIATION GOVERNANCE */}
          {activeTab === 'governance' && (
            <RemediationGovernanceSection incidentId={incident.id} />
          )}

          {/* TAB: STAGE 4 AGENT INVESTIGATION ENGINE */}
          {activeTab === 'investigation' && (
            <AgentInvestigationSection incidentId={incident.id} />
          )}

          {/* TAB: HISTORICAL RETRIEVAL ENGINE */}
          {activeTab === 'similar' && (
            loadingSimilar ? (
              <div className="py-8 text-center text-gray-400 text-sm">
                Querying CockroachDB Hybrid Memory Retrieval Engine...
              </div>
            ) : (
              <HistoricalMemorySection candidates={similarCandidates} />
            )
          )}

          {/* TAB: TIMELINE */}
          {activeTab === 'timeline' && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
                Reconstructed Chronological Event Sequence
              </h3>
              <div className="relative border-l-2 border-cyan-500/30 ml-4 pl-6 space-y-4">
                {evidenceList.map((ev) => (
                  <div key={ev.evidence_id} className="relative group">
                    <div className="absolute -left-[31px] top-1.5 w-3 h-3 rounded-full bg-cyan-400 ring-4 ring-gray-900" />
                    <div className="p-4 bg-gray-900/60 rounded-xl border border-gray-800">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-mono text-cyan-400 font-bold uppercase">{ev.source} ({ev.event_type})</span>
                        <span className="text-gray-500 font-mono">{new Date(ev.captured_at).toUTCString()}</span>
                      </div>
                      <p className="text-xs text-gray-300 font-mono bg-gray-950 p-2 rounded border border-gray-800/80 mt-2 overflow-x-auto">
                        {JSON.stringify(ev.raw_payload, null, 2)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB: INFRASTRUCTURE SNAPSHOT */}
          {activeTab === 'infrastructure' && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
                Point-in-Time Infrastructure Snapshot (Immutable)
              </h3>
              {primarySnapshot ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-900/60 rounded-xl border border-gray-800 space-y-2">
                    <span className="text-xs text-gray-400 font-mono">Engine & Versions</span>
                    <p className="text-sm font-bold text-gray-200">{primarySnapshot.db_version}</p>
                    <p className="text-xs text-cyan-400 font-mono">Service Version: {primarySnapshot.service_version}</p>
                    <p className="text-xs text-gray-500">Region: {primarySnapshot.region}</p>
                  </div>
                  <div className="p-4 bg-gray-900/60 rounded-xl border border-gray-800 space-y-2">
                    <span className="text-xs text-gray-400 font-mono">Configuration & Pools</span>
                    <pre className="text-xs font-mono text-gray-300 bg-gray-950 p-2 rounded">
                      {JSON.stringify(primarySnapshot.configuration, null, 2)}
                    </pre>
                  </div>
                  <div className="md:col-span-2 p-4 bg-gray-900/60 rounded-xl border border-gray-800 space-y-2">
                    <span className="text-xs text-gray-400 font-mono">Topology & Dependencies</span>
                    <pre className="text-xs font-mono text-gray-300 bg-gray-950 p-2 rounded">
                      {JSON.stringify(primarySnapshot.dependencies, null, 2)}
                    </pre>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-500">No snapshot recorded.</p>
              )}
            </div>
          )}

          {/* TAB: ACTIONS HISTORY */}
          {activeTab === 'actions' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
                  Attempted Operational Actions History (Including Failures)
                </h3>
                <span className="text-xs bg-amber-500/10 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded">
                  Idempotency Enforced
                </span>
              </div>
              <div className="space-y-3">
                {incident.actions.map((act, index) => {
                  const isSuccess = act.result === 'SUCCESS';
                  return (
                    <div
                      key={act.id}
                      className={`p-4 rounded-xl border ${
                        isSuccess ? 'bg-emerald-950/20 border-emerald-800/40' : 'bg-rose-950/20 border-rose-800/40'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-bold text-gray-400 font-mono">Attempt {index + 1}:</span>
                          <span className="text-xs font-mono font-bold text-gray-200">{act.command}</span>
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                              isSuccess ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                            }`}
                          >
                            {act.result}
                          </span>
                        </div>
                        <span className="text-xs font-mono text-gray-500">{new Date(act.timestamp).toUTCString()}</span>
                      </div>
                      <p className="text-xs text-gray-300 mt-2">{act.reason}</p>
                      {act.error_message && (
                        <p className="text-xs text-rose-400 font-mono bg-rose-950/40 p-2 rounded mt-2 border border-rose-900/50">
                          Error: {act.error_message}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB: RAW EVIDENCE */}
          {activeTab === 'evidence' && (
            <div className="space-y-4">
              <div className="p-3 bg-amber-950/20 border border-amber-800/40 rounded-lg text-xs text-amber-300 flex items-center justify-between">
                <span>AUTHORITATIVE RAW EVIDENCE: Preserved unredacted in database with SHA-256 content hashes.</span>
                <span className="font-mono font-bold">Total Items: {evidenceList.length}</span>
              </div>
              <div className="space-y-3">
                {evidenceList.map((ev) => (
                  <div key={ev.evidence_id} className="p-4 bg-gray-900/60 rounded-xl border border-gray-800 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-amber-400 font-bold">{ev.source} // {ev.source_event_id}</span>
                      <span className="font-mono text-gray-400">Content Hash: {ev.content_hash.slice(0, 16)}...</span>
                    </div>
                    <pre className="text-xs font-mono text-gray-300 bg-gray-950 p-3 rounded overflow-x-auto border border-gray-800">
                      {JSON.stringify(ev.raw_payload, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB: DERIVED OPERATIONAL MEMORY */}
          {activeTab === 'memory' && (
            <div className="space-y-4">
              <div className="p-3 bg-purple-950/20 border border-purple-800/40 rounded-lg text-xs text-purple-300 flex items-center justify-between">
                <span>DERIVED OPERATIONAL MEMORY: Generated from redacted text and indexed into CockroachDB VECTOR(1536).</span>
                <span className="font-mono font-bold">Vector Dimension: 1536</span>
              </div>
              <div className="space-y-3">
                {incident.memories.map((mem) => (
                  <div key={mem.id} className="p-4 bg-gray-900/60 rounded-xl border border-purple-900/40 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-purple-400 font-bold uppercase">Memory Type: {mem.memory_type}</span>
                      <span className="text-xs bg-purple-900/40 text-purple-300 px-2 py-0.5 rounded font-mono">
                        Trust Level: {mem.trust_level}
                      </span>
                    </div>
                    <h4 className="text-sm font-semibold text-gray-200">{mem.title}</h4>
                    <p className="text-xs text-gray-300 bg-gray-950 p-3 rounded border border-gray-800">
                      {mem.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
