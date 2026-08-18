'use client';

import React, { useState, useEffect, useRef } from 'react';
import ExperienceNav from '../components/cinematic/ExperienceNav';
import ChamberHero from '../components/cinematic/ChamberHero';
import ChamberLiveIngestion from '../components/cinematic/ChamberLiveIngestion';
import ChamberNeuralMemory from '../components/cinematic/ChamberNeuralMemory';
import ChamberMultiTierReasoning from '../components/cinematic/ChamberMultiTierReasoning';
import ChamberTemporalDrift from '../components/cinematic/ChamberTemporalDrift';
import ChamberGovernedRemediation from '../components/cinematic/ChamberGovernedRemediation';
import ChamberTelemetryVerification from '../components/cinematic/ChamberTelemetryVerification';
import ChamberLearningCDC from '../components/cinematic/ChamberLearningCDC';
import ChamberCounterfactualReplay from '../components/cinematic/ChamberCounterfactualReplay';
import ChamberLiveDemoModal from '../components/cinematic/ChamberLiveDemoModal';
import { getHealth } from '../lib/api';
import { SystemHealth } from '../types';
import { NodePoint } from '../lib/3d-math';

export default function GhostOpsExperience() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [activeChamber, setActiveChamber] = useState<number>(0);
  const [isDemoModalOpen, setIsDemoModalOpen] = useState<boolean>(false);
  const [selectedNode, setSelectedNode] = useState<NodePoint | null>(null);

  // Section references for scroll navigation
  const chamberRefs = [
    useRef<HTMLDivElement>(null), // 0: Hero Vault
    useRef<HTMLDivElement>(null), // 1: Ingestion
    useRef<HTMLDivElement>(null), // 2: Neural Memory
    useRef<HTMLDivElement>(null), // 3: Reasoning
    useRef<HTMLDivElement>(null), // 4: Temporal Drift
    useRef<HTMLDivElement>(null), // 5: Governed Saga
    useRef<HTMLDivElement>(null), // 6: Verification
    useRef<HTMLDivElement>(null), // 7: CDC Learning
    useRef<HTMLDivElement>(null), // 8: Benchmark
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
      const scrollPos = window.scrollY + 200;
      chamberRefs.forEach((ref, idx) => {
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

  const scrollToChamber = (index: number) => {
    setActiveChamber(index);
    const targetRef = chamberRefs[index];
    if (targetRef && targetRef.current) {
      targetRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <main className="min-h-screen bg-[#07090e] text-[#f5f6f0] selection:bg-emerald-500/30 selection:text-white relative">
      {/* Top Research Instrument Navigation Bar */}
      <ExperienceNav
        health={health}
        activeChamber={activeChamber}
        onSelectChamber={scrollToChamber}
        onOpenDemo={() => setIsDemoModalOpen(true)}
      />

      {/* Chamber 01: Hero Living Memory Vault */}
      <div ref={chamberRefs[0]}>
        <ChamberHero
          onOpenDemo={() => setIsDemoModalOpen(true)}
          onExploreMemory={() => scrollToChamber(2)}
          onExploreBenchmark={() => scrollToChamber(8)}
          onSelectNode={(node) => setSelectedNode(node)}
        />
      </div>

      {/* Chamber 02: Production Signal Ingestion & Evidence Chain */}
      <div ref={chamberRefs[1]} className="border-t border-zinc-900 bg-gradient-to-b from-[#07090e] to-[#0c1017]">
        <ChamberLiveIngestion />
      </div>

      {/* Chamber 03: Living Neural Memory & Native Vector Retrieval */}
      <div ref={chamberRefs[2]} className="border-t border-zinc-900 bg-[#07090e]">
        <ChamberNeuralMemory />
      </div>

      {/* Chamber 04: Multi-Tier Model Reasoning & Competing Hypotheses */}
      <div ref={chamberRefs[3]} className="border-t border-zinc-900 bg-gradient-to-b from-[#07090e] to-[#0c1017]">
        <ChamberMultiTierReasoning />
      </div>

      {/* Chamber 05: Deterministic Temporal Drift Engine (Flagship Incident #1847) */}
      <div ref={chamberRefs[4]} className="border-t border-zinc-900 bg-[#07090e]">
        <ChamberTemporalDrift />
      </div>

      {/* Chamber 06: Governed Remediation & 2-Phase Commit Saga */}
      <div ref={chamberRefs[5]} className="border-t border-zinc-900 bg-gradient-to-b from-[#07090e] to-[#0c1017]">
        <ChamberGovernedRemediation />
      </div>

      {/* Chamber 07: Independent Telemetry Verification */}
      <div ref={chamberRefs[6]} className="border-t border-zinc-900 bg-[#07090e]">
        <ChamberTelemetryVerification />
      </div>

      {/* Chamber 08: Post-Remediation Learning & CockroachDB CDC */}
      <div ref={chamberRefs[7]} className="border-t border-zinc-900 bg-gradient-to-b from-[#07090e] to-[#0c1017]">
        <ChamberLearningCDC />
      </div>

      {/* Chamber 09: Counterfactual Replay & Regression Benchmark Suite */}
      <div ref={chamberRefs[8]} className="border-t border-zinc-900 bg-[#07090e]">
        <ChamberCounterfactualReplay />
      </div>

      {/* Interactive 3-Minute Live Incident Simulation Modal */}
      <ChamberLiveDemoModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
      />

      {/* Global Cinematic Footer */}
      <footer className="py-12 px-6 border-t border-zinc-900 bg-zinc-950 text-center font-mono text-xs text-zinc-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-emerald-400 font-bold">GHOSTOPS</span>
            <span>·</span>
            <span>SYSTEM OF RECORD & AUTONOMOUS REASONING ENGINE</span>
          </div>
          <div className="flex items-center gap-4 text-zinc-400">
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
