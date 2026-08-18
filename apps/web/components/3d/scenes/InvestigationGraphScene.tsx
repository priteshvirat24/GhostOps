'use client';

import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { PALETTE } from '../../../lib/3d-math';

interface InvestigationGraphSceneProps {
  activeStep?: number;
  onNodeClick?: (stepIndex: number) => void;
}

export default function InvestigationGraphScene({ activeStep = 4, onNodeClick }: InvestigationGraphSceneProps) {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(PALETTE.obsidian, 0.1);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 50);
    camera.position.set(0, 0, 7.0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0x2a3d31, 1.4);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x4ade80, 2.5, 12);
    pointLight.position.set(0, 3, 3);
    scene.add(pointLight);

    const graphGroup = new THREE.Group();
    scene.add(graphGroup);

    // 6 progressive stages: Incident -> Evidence -> Memory -> H1/H2 -> Temporal Diff -> Validation
    const stages = [
      { id: 0, label: 'INCIDENT', pos: [0, 0, 0], color: PALETTE.warmWhite, size: 0.45 },
      { id: 1, label: 'EVIDENCE', pos: [-2.2, 1.5, 0.5], color: PALETTE.mutedMint, size: 0.32 },
      { id: 2, label: 'MEMORY', pos: [2.2, 1.5, -0.5], color: PALETTE.sage, size: 0.35 },
      { id: 3, label: 'HYPOTHESIS A', pos: [-1.2, -1.8, 0.8], color: PALETTE.luminousGreen, size: 0.32 },
      { id: 4, label: 'HYPOTHESIS B', pos: [1.2, -1.8, 0.8], color: PALETTE.dangerRed, size: 0.30 },
      { id: 5, label: 'TEMPORAL DIFF', pos: [0, -2.8, -1.0], color: PALETTE.accentAmber, size: 0.38 },
    ];

    const meshes: THREE.Mesh[] = [];

    stages.forEach((st) => {
      const geo = new THREE.IcosahedronGeometry(st.size, 1);
      const isUnlocked = st.id <= activeStep;
      const mat = new THREE.MeshStandardMaterial({
        color: isUnlocked ? st.color : 0x22262d,
        metalness: 0.5,
        roughness: 0.3,
        emissive: isUnlocked ? st.color : 0x000000,
        emissiveIntensity: isUnlocked ? 0.35 : 0.0,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(...(st.pos as [number, number, number]));
      mesh.userData = { stageId: st.id };
      graphGroup.add(mesh);
      meshes.push(mesh);
    });

    // Connecting lines between stages
    const connections: [number, number][] = [
      [0, 1],
      [0, 2],
      [1, 3],
      [1, 4],
      [2, 3],
      [2, 4],
      [3, 5],
      [4, 5],
    ];

    const linesGroup = new THREE.Group();
    graphGroup.add(linesGroup);

    const lineMat = new THREE.LineBasicMaterial({
      color: 0x6f8f7c,
      transparent: true,
      opacity: 0.4,
    });

    connections.forEach(([from, to]) => {
      const p1 = new THREE.Vector3(...(stages[from].pos as [number, number, number]));
      const p2 = new THREE.Vector3(...(stages[to].pos as [number, number, number]));
      const lineGeo = new THREE.BufferGeometry().setFromPoints([p1, p2]);
      const line = new THREE.Line(lineGeo, lineMat);
      linesGroup.add(line);
    });

    let frameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      frameId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      graphGroup.rotation.y = Math.sin(elapsed * 0.2) * 0.25;
      graphGroup.rotation.x = Math.cos(elapsed * 0.15) * 0.15;

      meshes.forEach((m, idx) => {
        m.rotation.y += 0.01 + idx * 0.002;
      });

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!mountRef.current) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(frameId);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [activeStep, onNodeClick]);

  return (
    <div className="relative w-full h-full min-h-[380px] overflow-hidden rounded-2xl border border-emerald-500/20 bg-zinc-950/80">
      <div ref={mountRef} className="absolute inset-0 w-full h-full" />
      <div className="absolute bottom-4 left-4 z-10 pointer-events-none flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
        <span className="text-[11px] font-mono text-zinc-400">PROGRESSIVE REASONING GRAPH · 6 STAGES</span>
      </div>
    </div>
  );
}
