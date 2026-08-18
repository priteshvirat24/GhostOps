import React, { useState } from 'react';
import { GitBranch, Shield, Terminal, CheckCircle2, AlertTriangle, Cpu, RefreshCw, Zap, Database, Lock } from 'lucide-react';
import { AgentTrace } from '../types';

interface AgentTraceSectionProps {
  traces: AgentTrace[];
  onRefresh?: () => void;
}

export default function AgentTraceSection({ traces, onRefresh }: AgentTraceSectionProps) {
  const [selectedTraceId, setSelectedTraceId] = useState<string>(traces[0]?.id || 'trace-demo');

  const selectedTrace = traces.find(t => t.id === selectedTraceId) || traces[0];

  return (
    <div className="space-y-6">
      {/* Header & Meta */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 glass-panel p-6 rounded-2xl border border-gray-800 bg-gradient-to-r from-[#0d1222] via-[#0B0F19] to-[#0a1520]">
        <div>
          <div className="flex items-center space-x-3 mb-1">
            <div className="p-2 bg-cyan-500/20 rounded-lg border border-cyan-500/30">
              <Cpu className="w-5 h-5 text-cyan-400" />
            </div>
            <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
              Agent Trace & ReAct Reasoning Graph
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-cyan-950/80 border border-cyan-500/30 text-cyan-300">
                §24 ReAct + Reflection Loop
              </span>
            </h2>
          </div>
          <p className="text-xs text-gray-400">
            Real-time execution trace of isolated specialist sub-agents, typed MCP tool calls, and deterministic reflection self-critiques.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={onRefresh}
            className="flex items-center space-x-2 px-3 py-2 bg-gray-900/90 hover:bg-gray-800 border border-gray-700 rounded-xl text-xs font-medium text-gray-300 transition shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5 text-gray-400" />
            <span>Refresh Traces</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trace List Selector */}
        <div className="glass-panel p-5 rounded-2xl border border-gray-800 space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 flex items-center justify-between">
            <span>Active Orchestrator Traces</span>
            <span className="text-cyan-400 font-mono">{traces.length} Runs</span>
          </h3>

          <div className="space-y-2 max-h-[550px] overflow-y-auto pr-1">
            {traces.length === 0 ? (
              <div className="p-4 text-center text-xs text-gray-500 font-mono">
                No active traces found. Trigger an incident investigation to generate ReAct traces.
              </div>
            ) : (
              traces.map((trace) => (
                <button
                  key={trace.id}
                  onClick={() => setSelectedTraceId(trace.id)}
                  className={`w-full text-left p-3.5 rounded-xl border transition flex flex-col space-y-1.5 ${
                    selectedTraceId === trace.id
                      ? 'bg-cyan-950/40 border-cyan-500/50 shadow-lg shadow-cyan-950/20'
                      : 'bg-gray-900/40 border-gray-800/80 hover:bg-gray-900/80'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-cyan-300 font-semibold truncate max-w-[170px]">
                      {trace.id}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      {trace.status}
                    </span>
                  </div>
                  <div className="text-[11px] text-gray-400 flex items-center justify-between">
                    <span>Node: <strong className="text-gray-200">{trace.current_node}</strong></span>
                    <span className="font-mono text-[10px] text-gray-500">
                      {new Date(trace.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* ReAct Execution Timeline Details */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-6">
            <div className="flex items-center justify-between border-b border-gray-800/80 pb-4">
              <div>
                <h3 className="text-sm font-bold text-gray-100 flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-cyan-400" />
                  <span>ReAct Loop Lifecycle: {selectedTrace?.id || 'run-default'}</span>
                </h3>
                <p className="text-xs font-mono text-gray-400 mt-0.5">
                  Thread: {selectedTrace?.thread_id || 'thread-01'} | Graph: {selectedTrace?.graph_name || 'stage4_investigation_graph'}
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-mono bg-purple-500/10 border border-purple-500/30 text-purple-300">
                  <Lock className="w-3 h-3 text-purple-400" />
                  <span>Prompt Injection Isolated</span>
                </span>
              </div>
            </div>

            {/* Step-by-Step ReAct Nodes */}
            <div className="space-y-4">
              {/* Step 1: Historian */}
              <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2.5">
                    <span className="w-6 h-6 rounded-full bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 text-xs font-mono flex items-center justify-center font-bold">
                      1
                    </span>
                    <span className="text-xs font-bold text-gray-200 font-mono">Historian Specialist</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-gray-800 text-gray-300">
                      Isolated Context
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> 42ms
                  </span>
                </div>
                <div className="text-xs font-mono bg-black/50 p-3 rounded-lg border border-gray-800/80 space-y-1.5 text-gray-300">
                  <p className="text-purple-400"><strong className="text-purple-300">Thought:</strong> Ingest raw telemetry, reconstruct timeline, and separate raw CloudWatch logs from interpretation.</p>
                  <p className="text-cyan-400"><strong className="text-cyan-300">Tool Call:</strong> read_cloudwatch(incident_id) → MCP Tool</p>
                  <p className="text-emerald-400"><strong className="text-emerald-300">Observation:</strong> 4 evidence records captured, SHA-256 hashes generated, untrusted data isolated inside &lt;untrusted_evidence&gt; tags.</p>
                  <p className="text-amber-400"><strong className="text-amber-300">Self-Critique:</strong> Confidence: 0.92 | Raw evidence preserved independently with foreign keys.</p>
                </div>
              </div>

              {/* Step 2: Investigator */}
              <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2.5">
                    <span className="w-6 h-6 rounded-full bg-purple-500/20 border border-purple-500/40 text-purple-300 text-xs font-mono flex items-center justify-center font-bold">
                      2
                    </span>
                    <span className="text-xs font-bold text-gray-200 font-mono">Investigator Specialist</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-300 border border-cyan-800">
                      CockroachDB Unified Query
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> 88ms
                  </span>
                </div>
                <div className="text-xs font-mono bg-black/50 p-3 rounded-lg border border-gray-800/80 space-y-1.5 text-gray-300">
                  <p className="text-purple-400"><strong className="text-purple-300">Thought:</strong> Perform hybrid retrieval combining VECTOR distance with structured SQL filters in one query.</p>
                  <p className="text-cyan-400"><strong className="text-cyan-300">Tool Call:</strong> vector_search(VECTOR(1536) + WHERE service='auth-service')</p>
                  <p className="text-emerald-400"><strong className="text-emerald-300">Observation:</strong> Historical Incident #1847 ranked #1 (Score: 0.91) with 3/3 successful historical precedents.</p>
                  <p className="text-amber-400"><strong className="text-amber-300">Self-Critique:</strong> Confidence: 0.91 | Structural match fraction outranks higher raw vector similarity.</p>
                </div>
              </div>

              {/* Step 3: Temporal Reasoning */}
              <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2.5">
                    <span className="w-6 h-6 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-mono flex items-center justify-center font-bold">
                      3
                    </span>
                    <span className="text-xs font-bold text-gray-200 font-mono">Temporal Reasoning Specialist</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-800">
                      9-Dimension Diff
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> 64ms
                  </span>
                </div>
                <div className="text-xs font-mono bg-black/50 p-3 rounded-lg border border-gray-800/80 space-y-1.5 text-gray-300">
                  <p className="text-purple-400"><strong className="text-purple-300">Thought:</strong> Compare historical vs current infrastructure snapshot along 9 explicit dimensions.</p>
                  <p className="text-cyan-400"><strong className="text-cyan-300">Tool Call:</strong> diff_infra_state(hist_snap, current_snap)</p>
                  <p className="text-emerald-400"><strong className="text-emerald-300">Observation:</strong> 8 of 9 dimensions match (DB version, service version, topology, security group).</p>
                  <p className="text-amber-400"><strong className="text-amber-300">Self-Critique:</strong> Compatibility Score: 0.88 (COMPATIBLE_WITH_DIFFERENCES) | Historical fix remains applicable.</p>
                </div>
              </div>

              {/* Step 4: Validation & Reflection */}
              <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2.5">
                    <span className="w-6 h-6 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs font-mono flex items-center justify-center font-bold">
                      4
                    </span>
                    <span className="text-xs font-bold text-gray-200 font-mono">Validation Specialist</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-950 text-rose-300 border border-rose-800">
                      ccloud Sandbox Proof
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> 112ms
                  </span>
                </div>
                <div className="text-xs font-mono bg-black/50 p-3 rounded-lg border border-gray-800/80 space-y-1.5 text-gray-300">
                  <p className="text-purple-400"><strong className="text-purple-300">Thought:</strong> Evaluate policy engine rules, assign risk tier L2, and run ephemeral ccloud sandbox dry-run.</p>
                  <p className="text-cyan-400"><strong className="text-cyan-300">Tool Call:</strong> sandbox_execute(command="ec2:RevokeSecurityGroupIngress")</p>
                  <p className="text-emerald-400"><strong className="text-emerald-300">Observation:</strong> Sandbox dry-run passed with zero destructive side effects.</p>
                  <p className="text-emerald-400"><strong className="text-emerald-300">Final Verdict:</strong> Validation PASSED (Risk Tier: L2 | Calibrated Confidence: 0.94) → Ready for Governed Execution.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
