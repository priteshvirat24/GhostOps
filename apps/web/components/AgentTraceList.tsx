import React from 'react';
import { GitCommit, Play, CheckCircle, Clock } from 'lucide-react';
import { AgentTrace } from '../types';

interface AgentTraceListProps {
  traces: AgentTrace[];
}

export default function AgentTraceList({ traces }: AgentTraceListProps) {
  return (
    <div className="glass-panel p-6 rounded-xl border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-100 flex items-center space-x-2">
          <GitCommit className="w-5 h-5 text-cyan-400" />
          <span>Agent Trace & State Graph</span>
        </h2>
        <span className="text-xs bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-2.5 py-0.5 rounded-full font-medium">
          LangGraph Stateful Graph
        </span>
      </div>

      {traces.length === 0 ? (
        <div className="py-6 text-center text-gray-500 text-sm">
          No agent traces recorded yet. Dry-run pipeline ready.
        </div>
      ) : (
        <div className="space-y-3">
          {traces.map((trace) => (
            <div key={trace.id} className="p-3 bg-gray-900/60 rounded-lg border border-gray-800 flex items-center justify-between">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono text-cyan-400 font-bold">{trace.thread_id}</span>
                  <span className="text-[10px] bg-gray-800 text-gray-300 px-2 py-0.5 rounded font-mono">
                    {trace.graph_name}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  Active Node: <span className="text-purple-300 font-semibold">{trace.current_node}</span>
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono text-emerald-400 flex items-center space-x-1">
                  <Play className="w-3 h-3 text-emerald-400 fill-emerald-400" />
                  <span>{trace.status}</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
