'use client';

import React, { useState, useEffect, useRef } from 'react';
import InteractiveCursor from '../components/cinematic/InteractiveCursor';
import ExperienceNav from '../components/cinematic/ExperienceNav';
import Scene01_Hero from '../components/cinematic/Scene01_Hero';
import Scene02_ProblemSolution from '../components/cinematic/Scene02_ProblemSolution';
import Scene03_MemoryVault from '../components/cinematic/Scene03_MemoryVault';
import Scene04_InvestigationGraph from '../components/cinematic/Scene04_InvestigationGraph';
import Scene05_TemporalChamber from '../components/cinematic/Scene05_TemporalChamber';
import Scene06_RemediationGovernance from '../components/cinematic/Scene06_RemediationGovernance';
import Scene07_SagaExecution from '../components/cinematic/Scene07_SagaExecution';
import Scene08_IndependentVerification from '../components/cinematic/Scene08_IndependentVerification';
import Scene09_LearningLoop from '../components/cinematic/Scene09_LearningLoop';
import Scene10_CDCStream from '../components/cinematic/Scene10_CDCStream';
import Scene11_GhostReplay from '../components/cinematic/Scene11_GhostReplay';
import Scene12_EvaluationBenchmark from '../components/cinematic/Scene12_EvaluationBenchmark';
import ChamberLiveDemoModal from '../components/cinematic/ChamberLiveDemoModal';
import JudgeModeExperience from '../components/cinematic/JudgeModeExperience';
import { getHealth } from '../lib/api';
import { SystemHealth } from '../types';
import { NodePoint } from '../lib/3d-math';

export default function GhostOpsExperience() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [activeChamber, setActiveChamber] = useState<number>(0);
  const [isDemoModalOpen, setIsDemoModalOpen] = useState<boolean>(false);
  const [isJudgeModeOpen, setIsJudgeModeOpen] = useState<boolean>(false);
  const [selectedNode, setSelectedNode] = useState<NodePoint | null>(null);

  // Section references for scroll navigation across all 12 scenes
  const sceneRefs = [
    useRef<HTMLDivElement>(null), // 0: The Hook
    useRef<HTMLDivElement>(null), // 1: Problem / Solution
    useRef<HTMLDivElement>(null), // 2: Memory Vault
    useRef<HTMLDivElement>(null), // 3: Investigation Graph
    useRef<HTMLDivElement>(null), // 4: Temporal Chamber
    useRef<HTMLDivElement>(null), // 5: Governance
    useRef<HTMLDivElement>(null), // 6: 2PC Saga
    useRef<HTMLDivElement>(null), // 7: Verification
    useRef<HTMLDivElement>(null), // 8: Learning Loop
    useRef<HTMLDivElement>(null), // 9: CDC Stream
    useRef<HTMLDivElement>(null), // 10: Ghost Replay
    useRef<HTMLDivElement>(null), // 11: Benchmark
  ];

  // Fetch real backend system health
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await getHealth();
        setHealth(data);
      } catch (e) {
        console.error('Failed to fetch backend health:', e);
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  // Track active section on scroll
  useEffect(() => {
    const handleScroll = () => {
      const scrollPos = window.scrollY + 250;
      sceneRefs.forEach((ref, idx) => {
        if (ref.current) {
          const top = ref.current.offsetTop;
          const height = ref.current.offsetHeight;
          if (scrollPos >= top && scrollPos < top + height) {
            setActiveChamber(idx);
          }
        }
      });
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToScene = (index: number) => {
    setActiveChamber(index);
    const targetRef = sceneRefs[index];
    if (targetRef && targetRef.current) {
      targetRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <main className="min-h-screen bg-[#07090e] text-[#f5f6f0] selection:bg-emerald-500/30 selection:text-white relative">
      {/* Custom Interactive Cursor */}
      <InteractiveCursor />

      {/* Top Research Instrument Navigation Bar */}
      <ExperienceNav
        health={health}
        activeChamber={activeChamber}
        onSelectChamber={scrollToScene}
        onOpenDemo={() => setIsDemoModalOpen(true)}
        onOpenJudgeMode={() => setIsJudgeModeOpen(true)}
      />

      {/* Scene 01: Hero / The Hook */}
      <div ref={sceneRefs[0]}>
        <Scene01_Hero
          onOpenDemo={() => setIsDemoModalOpen(true)}
          onOpenJudgeMode={() => setIsJudgeModeOpen(true)}
          onExploreMemory={() => scrollToScene(2)}
          onExploreBenchmark={() => scrollToScene(11)}
          onSelectNode={(node) => setSelectedNode(node)}
        />
      </div>

      {/* Scene 02: Problem -> Solution Split Scene */}
      <div ref={sceneRefs[1]} className="border-t border-zinc-900 bg-gradient-to-b from-[#07090e] to-[#0c1017]">
        <Scene02_ProblemSolution />
      </div>

      {/* Scene 03: The Flagship Memory Vault */}
      <div ref={sceneRefs[2]} className="border-t border-zinc-900 bg-[#07090e]">
        <Scene03_MemoryVault />
      </div>

      {/* Scene 04: Live Investigation Graph */}
      <div ref={sceneRefs[3]} className="border-t border-zinc-900 bg-gradient-to-b from-[#07090e] to-[#0c1017]">
        <Scene04_InvestigationGraph />
      </div>

      {/* Scene 05: Temporal Reasoning Chamber (9-Layer Diff) */}
      <div ref={sceneRefs[4]} className="border-t border-zinc-900 bg-[#07090e]">
        <Scene05_TemporalChamber />
      </div>

      {/* Scene 06: Remediation Governance Boundary */}
      <div ref={sceneRefs[5]} className="border-t border-zinc-900 bg-gradient-to-b from-[#07090e] to-[#0c1017]">
        <Scene06_RemediationGovernance />
      </div>

      {/* Scene 07: 2-Phase Commit Saga Execution Pipeline */}
      <div ref={sceneRefs[6]} className="border-t border-zinc-900 bg-[#07090e]">
        <Scene07_SagaExecution />
      </div>

      {/* Scene 08: Independent Out-of-Band Telemetry Verification */}
      <div ref={sceneRefs[7]} className="border-t border-zinc-900 bg-gradient-to-b from-[#07090e] to-[#0c1017]">
        <Scene08_IndependentVerification />
      </div>

      {/* Scene 09: Closed-Loop Institutional Learning */}
      <div ref={sceneRefs[8]} className="border-t border-zinc-900 bg-[#07090e]">
        <Scene09_LearningLoop />
      </div>

      {/* Scene 10: CockroachDB Change Data Capture (CDC) */}
      <div ref={sceneRefs[9]} className="border-t border-zinc-900 bg-gradient-to-b from-[#07090e] to-[#0c1017]">
        <Scene10_CDCStream />
      </div>

      {/* Scene 11: Flagship Counterfactual Replay (Incident #1847) */}
      <div ref={sceneRefs[10]} className="border-t border-zinc-900 bg-[#07090e]">
        <Scene11_GhostReplay />
      </div>

      {/* Scene 12: Empirical Regression Benchmark Harness */}
      <div ref={sceneRefs[11]} className="border-t border-zinc-900 bg-gradient-to-b from-[#07090e] to-[#0c1017]">
        <Scene12_EvaluationBenchmark />
      </div>

      {/* Interactive 3-Minute Live Incident Simulation Modal */}
      <ChamberLiveDemoModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
      />

      {/* Dedicated Judge Mode Theatre */}
      <JudgeModeExperience
        isOpen={isJudgeModeOpen}
        onClose={() => setIsJudgeModeOpen(false)}
        health={health}
      />

      {/* Global Research Instrument Footer */}
      <footer className="py-14 px-6 border-t border-zinc-900 bg-zinc-950 text-center font-mono text-xs text-zinc-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-emerald-400 font-bold">GHOSTOPS</span>
            <span>·</span>
            <span>AUTONOMOUS INSTITUTIONAL MEMORY & REASONING VAULT</span>
          </div>
          <div className="flex items-center gap-4 text-zinc-400 text-[11px]">
            <span>CockroachDB Cloud Serverless</span>
            <span>·</span>
            <span>Amazon Bedrock Mantle</span>
            <span>·</span>
            <span>1536-Dim Native Vector</span>
          </div>
        </div>
      </footer>
    </main>
  );
}
