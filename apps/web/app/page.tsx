'use client';

import React, { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import StatusCard from '../components/StatusCard';
import IncidentList from '../components/IncidentList';
import MemoryStats from '../components/MemoryStats';
import IncidentDetailModal from '../components/IncidentDetailModal';
import AgentInvestigationSection from '../components/AgentInvestigationSection';
import AgentTraceSection from '../components/AgentTraceSection';
import HistoricalMemorySection from '../components/HistoricalMemorySection';
import RemediationGovernanceSection from '../components/RemediationGovernanceSection';
import SagaExecutionSection from '../components/SagaExecutionSection';
import GhostReplaySection from '../components/GhostReplaySection';
import LearningConsolidationSection from '../components/LearningConsolidationSection';
import SentinelControlSection from '../components/SentinelControlSection';
import EvaluationSection from '../components/EvaluationSection';

import { fetchSystemHealth, fetchIncidents, fetchAgentTraces, fetchRemediationPlans, fetchIncidentDetail } from '../lib/api';
import { SystemHealth, Incident, AgentTrace, RemediationPlan, IncidentDetail } from '../types';
import { AlertCircle, Brain, ShieldCheck, GitBranch, Cpu, Award, Zap, History, RefreshCw } from 'lucide-react';

type TabType = 'dashboard' | 'investigation' | 'trace' | 'memory' | 'remediation' | 'replay' | 'sentinel' | 'evaluation';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [traces, setTraces] = useState<AgentTrace[]>([]);
  const [plans, setPlans] = useState<RemediationPlan[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<IncidentDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [healthData, incidentData, traceData, planData] = await Promise.all([
        fetchSystemHealth(),
        fetchIncidents(),
        fetchAgentTraces(),
        fetchRemediationPlans(),
      ]);
      setHealth(healthData);
      setIncidents(incidentData);
      setTraces(traceData);
      setPlans(planData);
    } catch (e) {
      console.error('Failed to fetch dashboard data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 12000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectIncident = async (incidentId: string) => {
    const detail = await fetchIncidentDetail(incidentId);
    if (detail) {
      setSelectedIncident(detail);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0B0F19] text-gray-100 font-sans selection:bg-purple-500/30">
      <Navbar health={health} />

      {/* Navigation Sub-Header Bar */}
      <div className="glass-panel sticky top-[73px] z-40 px-6 py-2.5 border-b border-gray-800 bg-[#0B0F19]/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto flex items-center justify-between overflow-x-auto gap-2">
          <div className="flex items-center space-x-1.5 min-w-max">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center space-x-1.5 ${
                activeTab === 'dashboard'
                  ? 'bg-purple-600/30 text-purple-300 border border-purple-500/40 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-850'
              }`}
            >
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Overview</span>
            </button>

            <button
              onClick={() => setActiveTab('investigation')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center space-x-1.5 ${
                activeTab === 'investigation'
                  ? 'bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-850'
              }`}
            >
              <GitBranch className="w-3.5 h-3.5" />
              <span>Investigation Graph</span>
            </button>

            <button
              onClick={() => setActiveTab('trace')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center space-x-1.5 ${
                activeTab === 'trace'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/50 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-850'
              }`}
            >
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span>Agent Trace (ReAct)</span>
            </button>

            <button
              onClick={() => setActiveTab('memory')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center space-x-1.5 ${
                activeTab === 'memory'
                  ? 'bg-purple-600/30 text-purple-300 border border-purple-500/40 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-850'
              }`}
            >
              <Brain className="w-3.5 h-3.5" />
              <span>Memory Graph & CDC</span>
            </button>

            <button
              onClick={() => setActiveTab('remediation')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center space-x-1.5 ${
                activeTab === 'remediation'
                  ? 'bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-850'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Saga Remediation</span>
            </button>

            <button
              onClick={() => setActiveTab('replay')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center space-x-1.5 ${
                activeTab === 'replay'
                  ? 'bg-amber-600/30 text-amber-300 border border-amber-500/40 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-850'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>Ghost Replay</span>
            </button>

            <button
              onClick={() => setActiveTab('sentinel')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center space-x-1.5 ${
                activeTab === 'sentinel'
                  ? 'bg-rose-600/30 text-rose-300 border border-rose-500/40 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-850'
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              <span>Sentinel Monitor</span>
            </button>

            <button
              onClick={() => setActiveTab('evaluation')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center space-x-1.5 ${
                activeTab === 'evaluation'
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/50 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-850'
              }`}
            >
              <Award className="w-3.5 h-3.5 text-emerald-400" />
              <span>Evaluation & Sandbox</span>
            </button>
          </div>

          <button
            onClick={loadDashboardData}
            className="p-1.5 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-gray-200 transition"
            title="Reload telemetry data"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <main className="flex-1 p-6 space-y-6 max-w-7xl mx-auto w-full">
        {/* TAB 1: OVERVIEW DASHBOARD */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Metric Cards Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatusCard
                title="Active Incidents"
                value={incidents.length}
                subtitle="Raw telemetry isolated"
                icon={AlertCircle}
                color="rose"
              />
              <StatusCard
                title="CockroachDB Vector Memory"
                value="CSPANN Live"
                subtitle="1536-dim unified SQL query"
                icon={Brain}
                color="purple"
              />
              <StatusCard
                title="Governed Sagas"
                value={plans.length}
                subtitle="L0-L5 Risk & Rollbacks"
                icon={ShieldCheck}
                color="emerald"
              />
              <StatusCard
                title="Active ReAct Traces"
                value={traces.length}
                subtitle="Multi-agent isolated graph"
                icon={GitBranch}
                color="cyan"
              />
            </div>

            {/* Core Dashboard Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <IncidentList incidents={incidents} onSelectIncident={handleSelectIncident} />
              </div>

              <div className="space-y-6">
                <MemoryStats />

                {/* PRD v3.0 Compliance Card */}
                <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-3 bg-gradient-to-br from-[#0c1424] to-[#0B0F19]">
                  <h3 className="text-xs font-bold text-gray-200 uppercase tracking-wider flex items-center justify-between">
                    <span>CockroachDB × AWS Hackathon</span>
                    <span className="text-emerald-400 font-mono">v3.0 Target</span>
                  </h3>
                  <p className="text-xs text-gray-400">
                    All 4 CockroachDB tools and load-bearing AWS services are meaningfully integrated.
                  </p>
                  <div className="space-y-2 text-xs font-mono text-gray-400 pt-1">
                    <div className="flex items-center space-x-2 text-emerald-400 font-semibold">
                      <span>✓ CockroachDB Managed MCP Server:</span>
                      <span className="text-gray-300">Live Read/Write Tool Surface</span>
                    </div>
                    <div className="flex items-center space-x-2 text-emerald-400 font-semibold">
                      <span>✓ CockroachDB VECTOR + CSPANN:</span>
                      <span className="text-gray-300">Unified Relational + Vector</span>
                    </div>
                    <div className="flex items-center space-x-2 text-emerald-400 font-semibold">
                      <span>✓ ccloud CLI Agent Sandbox:</span>
                      <span className="text-gray-300">Ephemeral Cluster Dry-Run</span>
                    </div>
                    <div className="flex items-center space-x-2 text-emerald-400 font-semibold">
                      <span>✓ Multi-Tier Bedrock Inference:</span>
                      <span className="text-gray-300">Fast & Reasoning Tiers</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: AGENT INVESTIGATION GRAPH */}
        {activeTab === 'investigation' && (
          <AgentInvestigationSection incidentId={incidents[0]?.id} />
        )}

        {/* TAB 3: AGENT TRACE (ReAct) */}
        {activeTab === 'trace' && (
          <AgentTraceSection traces={traces} onRefresh={loadDashboardData} />
        )}

        {/* TAB 4: MEMORY GRAPH & CDC */}
        {activeTab === 'memory' && (
          <div className="space-y-6">
            <HistoricalMemorySection incidentId={incidents[0]?.id} />
            <LearningConsolidationSection incidentId={incidents[0]?.id} />
          </div>
        )}

        {/* TAB 5: SAGA REMEDIATION & GOVERNANCE */}
        {activeTab === 'remediation' && (
          <div className="space-y-6">
            <RemediationGovernanceSection incidentId={incidents[0]?.id} />
            <SagaExecutionSection incidentId={incidents[0]?.id} />
          </div>
        )}

        {/* TAB 6: GHOST REPLAY */}
        {activeTab === 'replay' && (
          <GhostReplaySection incidentId={incidents[0]?.id} />
        )}

        {/* TAB 7: SENTINEL AUTONOMOUS MONITOR */}
        {activeTab === 'sentinel' && (
          <SentinelControlSection />
        )}

        {/* TAB 8: EVALUATION & CCLOUD SANDBOX */}
        {activeTab === 'evaluation' && (
          <EvaluationSection />
        )}
      </main>

      {/* Incident Detail Modal */}
      {selectedIncident && (
        <IncidentDetailModal
          incident={selectedIncident}
          onClose={() => setSelectedIncident(null)}
        />
      )}
    </div>
  );
}
