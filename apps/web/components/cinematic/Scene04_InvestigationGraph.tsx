'use client';

import React, { useState } from 'react';
import { Cpu, CheckCircle2, XCircle, BrainCircuit, ShieldAlert, FileText, ChevronRight, Play } from 'lucide-react';
import InvestigationGraphScene from '../3d/scenes/InvestigationGraphScene';

export default function Scene04_InvestigationGraph() {
  const [selectedStage, setSelectedStage] = useState<number>(3); // Default to Hypothesis A

  const stagesData = [
    {
      id: 0,
      name: 'INCIDENT ROOT',
      title: 'Database Connection Starvation & Latency Spike',
      confidence: '100%',
      model: 'CloudWatch / Sentinel Ingest',
      summary: 'Auth-service reported 250/250 maxed connections on CockroachDB port 26257 with p99 latency spiking to 2,400ms.',
      evidenceRefs: ['EVT-9041 (TCP Pool Exceeded)', 'EVT-9042 (SG Ingress Modification)']
    },
    {
      id: 1,
      name: 'EVIDENCE PRESERVATION',
      title: 'Cryptographic SHA-256 Telemetry Hash',
      confidence: '100%',
      model: 'SHA-256 Evidence Chain',
      summary: 'Raw CloudWatch JSON alarm payload preserved with hash e3b0c442... Proof of unsevered network path and transaction restart rate > 4.8%.',
      evidenceRefs: ['SHA-256: e3b0c442...', 'SHA-256: 9f86d081...']
    },
    {
      id: 2,
      name: 'HYBRID MEMORY MATCH',
      title: 'CockroachDB Native Vector Precedent Retrieval',
      confidence: '94%',
      model: 'Titan Text V2 + Cosine Similarity',
      summary: 'Matched Precedent #1847 (Score: 0.94) and Precedent #1402 (Score: 0.91). Evaluated against 6-factor hybrid weighting.',
      evidenceRefs: ['PREC-1847 (2024 Fix)', 'PREC-1402 (2025 Fix)']
    },
    {
      id: 3,
      name: 'HYPOTHESIS A (SELECTED)',
      title: 'Range Leaseholder Contention on Node 3',
      confidence: '92%',
      model: 'deepseek.v3.2 (Reasoning Tier)',
      summary: 'Range 1042 leaseholder on node 3 is experiencing serializable conflict retry storms. Adaptive relocation to idle node 1 will resolve the hotspot.',
      evidenceRefs: ['EVT-9043 (sql.txn.restarts > 4.8%)', 'PREC-1402 (Historical validation)']
    },
    {
      id: 4,
      name: 'HYPOTHESIS B (REJECTED)',
      title: 'Network Firewall Port Blocking',
      confidence: '34%',
      model: 'zai.glm-4.7-flash (Fast Tier)',
      summary: 'Hypothesis that SG rule blocked traffic is rejected because internal TCP handshake latency remains 1.2ms and connection count is maxed, not zero.',
      evidenceRefs: ['EVT-9042 (SG Modified)', 'Active TCP sessions open']
    },
    {
      id: 5,
      name: 'TEMPORAL DRIFT DIFF',
      title: '9-Dimension Environment Drift Evaluation',
      confidence: '98%',
      model: 'Deterministic Drift Engine',
      summary: 'Precedent #1847 direct SG rule fix rejected with DO_NOT_EXECUTE due to 2026 Transit Gateway drift. Precedent #1402 adaptive range relocation approved.',
      evidenceRefs: ['9 Dimensions Diffed', 'Verdict: DO_NOT_EXECUTE on #1847']
    }
  ];

  const current = stagesData[selectedStage];

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="mb-12 text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-3">
          <span>SCENE 04</span>
          <span>·</span>
          <span>THE LIVE INVESTIGATION GRAPH</span>
        </div>
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-zinc-100 mb-4">
          Multi-Tier Reasoning & Grounded Hypothesis Battle
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base max-w-3xl leading-relaxed">
          GhostOps forms an interactive 3D reasoning graph. Click through each node to inspect structured evidence citations, competing hypotheses, and deterministic routing decisions.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: 3D Investigation Graph */}
        <div className="lg:col-span-6 flex flex-col justify-between">
          <div className="h-[400px] w-full mb-4">
            <InvestigationGraphScene activeStep={selectedStage} onNodeClick={(idx) => setSelectedStage(idx)} />
          </div>

          {/* Stepped Selector Tabs */}
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5 p-1 rounded-xl bg-zinc-900 border border-zinc-800">
            {stagesData.map((st) => (
              <button
                key={st.id}
                onClick={() => setSelectedStage(st.id)}
                className={`py-1.5 px-2 rounded-lg text-[10px] font-mono transition-all text-center ${
                  selectedStage === st.id
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/50 font-bold'
                    : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                0{st.id + 1} {st.name.split(' ')[0]}
              </button>
            ))}
          </div>
        </div>

        {/* Right: Structured Node Inspector Card */}
        <div className="lg:col-span-6">
          <div className="vault-panel p-6 rounded-2xl border border-zinc-800 bg-zinc-950/90 shadow-2xl h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-zinc-800">
                <div>
                  <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-widest block">
                    STAGE 0{current.id + 1} · {current.name}
                  </span>
                  <h3 className="text-base font-bold text-zinc-100 font-mono mt-0.5">{current.title}</h3>
                </div>
                <span className="text-xs font-mono font-bold text-emerald-400 px-2.5 py-1 rounded bg-emerald-950 border border-emerald-800/50">
                  {current.confidence} Conf
                </span>
              </div>

              {/* Model & Source */}
              <div className="mb-4 text-xs font-mono text-zinc-400">
                <span className="text-zinc-500">Reasoning Engine: </span>
                <span className="text-zinc-200 font-semibold">{current.model}</span>
              </div>

              {/* Concise Reasoning Summary */}
              <div className="p-4 rounded-xl bg-zinc-900/80 border border-zinc-800 text-xs font-mono text-zinc-300 leading-relaxed mb-4">
                <span className="text-emerald-400 font-bold block mb-1 uppercase text-[10px]">
                  Structured Reasoning Summary:
                </span>
                {current.summary}
              </div>

              {/* Grounded Evidence Citations */}
              <div>
                <span className="text-[10px] font-mono text-zinc-500 uppercase block mb-1.5">
                  Supporting Evidence References:
                </span>
                <div className="space-y-1.5 font-mono text-xs">
                  {current.evidenceRefs.map((ref, i) => (
                    <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-zinc-900/50 border border-zinc-800/60 text-zinc-300 text-[11px]">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      <span>{ref}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-6 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-[11px] font-mono text-zinc-400">
              <span>Zero Hallucination Gate</span>
              <span className="text-emerald-400 font-bold">100% EVIDENCE GROUNDED</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
