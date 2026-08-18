import React from 'react';
import { Brain, Cpu, Database, Sparkles } from 'lucide-react';

export default function MemoryStats() {
  return (
    <div className="glass-panel p-6 rounded-xl border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-100 flex items-center space-x-2">
          <Brain className="w-5 h-5 text-purple-400" />
          <span>Institutional Memory Engine</span>
        </h2>
        <span className="text-xs bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2.5 py-0.5 rounded-full font-medium">
          CockroachDB VECTOR(1536)
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-3 bg-gray-900/60 rounded-lg border border-gray-800">
          <div className="flex items-center space-x-2 text-xs text-gray-400">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Hybrid Search Index</span>
          </div>
          <p className="text-sm font-bold text-gray-200 mt-1">Structured + Vector</p>
          <p className="text-[11px] text-gray-500 mt-0.5">Cosine distance active</p>
        </div>

        <div className="p-3 bg-gray-900/60 rounded-lg border border-gray-800">
          <div className="flex items-center space-x-2 text-xs text-gray-400">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" />
            <span>Embedding Model</span>
          </div>
          <p className="text-sm font-bold text-gray-200 mt-1">Titan Embeddings</p>
          <p className="text-[11px] text-gray-500 mt-0.5">1536 dimensions</p>
        </div>
      </div>

      <div className="mt-4 p-3 bg-purple-950/20 rounded-lg border border-purple-900/40 text-xs text-purple-300">
        Operational memory records survive engineer turnover, automatically indexing resolution SOPs, temporal infrastructure states, and historical root cause analyses.
      </div>
    </div>
  );
}
