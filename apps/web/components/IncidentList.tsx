import React, { useState } from 'react';
import { AlertCircle, Clock, ExternalLink, Play, RefreshCw, CheckCircle2, ShieldCheck, Database, Cpu, Zap, Activity } from 'lucide-react';
import { Incident } from '../types';

interface IncidentListProps {
  incidents: Incident[];
  onSelectIncident: (incidentId: string) => void;
  onRefresh?: () => void;
}

export default function IncidentList({ incidents, onSelectIncident, onRefresh }: IncidentListProps) {
  const [runningDemo, setRunningDemo] = useState<boolean>(false);
  const [demoResult, setDemoResult] = useState<any>(null);
  const [demoError, setDemoError] = useState<string | null>(null);

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

  const handleRunDemo = async () => {
    setRunningDemo(true);
    setDemoError(null);
    try {
      const res = await fetch('http://localhost:8000/api/v1/demo/run', {
        method: 'POST'
      });
      if (!res.ok) {
        throw new Error(`Demo failed with status ${res.status}`);
      }
      const data = await res.json();
      setDemoResult(data);
      if (onRefresh) {
        onRefresh();
      }
    } catch (e: any) {
      setDemoError(e.message || "Failed to execute demo flow");
    } finally {
      setRunningDemo(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Active Incidents Container */}
      <div className="glass-panel p-6 rounded-xl border border-gray-800 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-100 flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-rose-400" />
            <span>Active & Ingested Production Incidents</span>
          </h2>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRunDemo}
              disabled={runningDemo}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white rounded-lg text-xs font-bold transition shadow-lg shadow-purple-950/30 disabled:opacity-50"
            >
              {runningDemo ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              <span>⚡ Launch 3-Minute Live Demo Flow</span>
            </button>
            <span className="text-xs bg-gray-800 px-2.5 py-1 rounded-full text-gray-400 font-mono">
              Total: {incidents.length}
            </span>
          </div>
        </div>

        {demoError && (
          <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-500/40 text-xs text-rose-300 font-mono">
            ⚠️ {demoError}
          </div>
        )}

        {/* Live Demo Results Summary */}
        {demoResult && (
          <div className="p-4 rounded-xl bg-gradient-to-r from-purple-950/30 via-slate-900 to-emerald-950/30 border border-purple-500/30 space-y-3">
            <div className="flex items-center justify-between border-b border-gray-800 pb-2">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-gray-200">End-to-End Demo Sequence Executed</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950 border border-purple-500/30 text-purple-300">
                  {demoResult.demo_id}
                </span>
              </div>
              <span className="text-[11px] font-mono text-cyan-300 font-semibold">
                {demoResult.duration_ms} ms
              </span>
            </div>

            <p className="text-xs text-gray-300 font-mono">{demoResult.summary}</p>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-2 pt-1 text-[11px] font-mono">
              {demoResult.steps.map((s: any) => (
                <div key={s.order} className="p-2 rounded bg-gray-900/80 border border-gray-800 flex items-center justify-between">
                  <span className="text-gray-400 truncate">{s.order}. {s.name}</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 ml-1" />
                </div>
              ))}
            </div>
          </div>
        )}

        {incidents.length === 0 ? (
          <div className="py-8 text-center text-gray-500 text-sm">
            No active telemetry incidents detected. Click &quot;Launch 3-Minute Live Demo Flow&quot; to seed a live incident.
          </div>
        ) : (
          <div className="space-y-3">
            {incidents.map((incident) => (
              <div
                key={incident.id}
                onClick={() => onSelectIncident(incident.id)}
                className="p-4 rounded-xl bg-gray-900/60 border border-gray-800/80 hover:border-cyan-500/50 hover:bg-gray-900 transition cursor-pointer group"
              >
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${getSeverityBadge(incident.severity)}`}>
                        {incident.severity}
                      </span>
                      <span className="text-xs bg-gray-800 text-cyan-300 font-mono px-2 py-0.5 rounded border border-gray-700">
                        {incident.service} ({incident.region})
                      </span>
                      <h3 className="text-sm font-semibold text-gray-200 group-hover:text-cyan-300 transition">
                        {incident.title}
                      </h3>
                    </div>
                    <p className="text-xs text-gray-400 line-clamp-2">{incident.description}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] text-gray-500 font-mono flex items-center space-x-1">
                      <Clock className="w-3 h-3 text-gray-500" />
                      <span>{new Date(incident.start_time).toLocaleTimeString()}</span>
                    </span>
                    <ExternalLink className="w-4 h-4 text-gray-600 group-hover:text-cyan-400 transition" />
                  </div>
                </div>

                <div className="mt-3 pt-2 border-t border-gray-800/60 flex items-center justify-between text-xs text-gray-400 font-mono">
                  <div>
                    <span className="text-gray-500">Resource: </span>
                    <code className="text-cyan-300 bg-gray-950 px-1.5 py-0.5 rounded border border-gray-800">
                      {incident.target_resource_id || "sg-012345"}
                    </code>
                  </div>
                  <div>
                    <span className="text-gray-500">Memory Status: </span>
                    <span className="text-purple-300 font-semibold">{incident.memory_status || "VECTOR_STORED"}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
