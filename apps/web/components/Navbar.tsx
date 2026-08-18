import React from 'react';
import { ShieldAlert, Database, Cpu, Activity } from 'lucide-react';
import { SystemHealth } from '../types';

interface NavbarProps {
  health: SystemHealth | null;
}

export default function Navbar({ health }: NavbarProps) {
  const isHealthy = health?.status === 'ok';

  return (
    <header className="glass-panel sticky top-0 z-50 px-6 py-4 border-b border-gray-800 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-purple-600/20 rounded-lg border border-purple-500/30">
          <ShieldAlert className="w-6 h-6 text-purple-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
            GhostOps
          </h1>
          <p className="text-xs text-gray-400 font-mono">The production memory that survives the engineer</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-gray-900/80 border border-gray-800 text-xs">
          <Database className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-gray-300">CockroachDB:</span>
          <span className={health?.database_connected ? "text-emerald-400 font-semibold" : "text-rose-400 font-semibold"}>
            {health?.database_connected ? "Connected" : "Disconnected"}
          </span>
        </div>

        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-gray-900/80 border border-gray-800 text-xs">
          <Cpu className="w-3.5 h-3.5 text-purple-400" />
          <span className="text-gray-300">AWS Mode:</span>
          <span className="text-purple-300 font-semibold">
            {health?.aws_mock_mode ? "Mock Active" : "AWS Live"}
          </span>
        </div>

        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-gray-900/80 border border-gray-800 text-xs">
          <Activity className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-gray-300">Status:</span>
          <span className={`inline-block w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
          <span className={isHealthy ? "text-emerald-400 font-bold uppercase" : "text-rose-400 font-bold uppercase"}>
            {health?.status || "OFFLINE"}
          </span>
        </div>
      </div>
    </header>
  );
}
