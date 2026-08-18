'use client';

import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { PALETTE } from '../../../lib/3d-math';

interface TemporalDiffSceneProps {
  driftCount?: number;
  verdict?: string;
}

export default function TemporalDiffScene({ driftCount = 3, verdict = 'DO_NOT_EXECUTE' }: TemporalDiffSceneProps) {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(PALETTE.obsidian, 0.12);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 50);
    camera.position.set(0, 0, 5.5);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0x2a3d31, 1.4);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0xf59e0b, 2.5, 8);
    pointLight.position.set(0, 2, 2);
    scene.add(pointLight);

    // Dual-Ring Topology: Ring A (2024 Baseline) vs Ring B (2026 Current)
    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    // Baseline Ring (Sage / Stable)
    const baseGeo = new THREE.TorusGeometry(1.6, 0.04, 16, 64);
    const baseMat = new THREE.MeshStandardMaterial({
      color: PALETTE.sage,
      metalness: 0.6,
      roughness: 0.3,
      emissive: PALETTE.sage,
      emissiveIntensity: 0.2,
    });
    const baseRing = new THREE.Mesh(baseGeo, baseMat);
    baseRing.position.z = -0.5;
    rootGroup.add(baseRing);

    // Current Ring (Amber / Drifted)
    const currGeo = new THREE.TorusGeometry(1.6, 0.04, 16, 64);
    const currMat = new THREE.MeshStandardMaterial({
      color: PALETTE.accentAmber,
      metalness: 0.6,
      roughness: 0.3,
      emissive: PALETTE.accentAmber,
      emissiveIntensity: 0.4,
    });
    const currRing = new THREE.Mesh(currGeo, currMat);
    currRing.position.z = 0.5;
    rootGroup.add(currRing);

    // Connecting Drift Shards (9 dimensions)
    const dimCount = 9;
    const shardsGroup = new THREE.Group();
    rootGroup.add(shardsGroup);

    for (let i = 0; i < dimCount; i++) {
      const angle = (i / dimCount) * Math.PI * 2;
      const x1 = Math.cos(angle) * 1.6;
      const y1 = Math.sin(angle) * 1.6;
      const z1 = -0.5;

      const isDrifted = i < driftCount;
      const x2 = Math.cos(angle + (isDrifted ? 0.25 : 0)) * 1.6;
      const y2 = Math.sin(angle + (isDrifted ? 0.25 : 0)) * 1.6;
      const z2 = 0.5;

      const points = [new THREE.Vector3(x1, y1, z1), new THREE.Vector3(x2, y2, z2)];
      const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
      const lineMat = new THREE.LineBasicMaterial({
        color: isDrifted ? PALETTE.dangerRed : PALETTE.mutedMint,
        transparent: true,
        opacity: isDrifted ? 0.85 : 0.25,
      });
      const line = new THREE.Line(lineGeo, lineMat);
      shardsGroup.add(line);

      if (isDrifted) {
        const markerGeo = new THREE.OctahedronGeometry(0.12, 0);
        const markerMat = new THREE.MeshBasicMaterial({ color: PALETTE.dangerRed });
        const marker = new THREE.Mesh(markerGeo, markerMat);
        marker.position.set((x1 + x2) / 2, (y1 + y2) / 2, 0);
        shardsGroup.add(marker);
      }
    }

    let frameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      frameId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      rootGroup.rotation.y = elapsed * 0.2;
      rootGroup.rotation.x = Math.sin(elapsed * 0.15) * 0.2;

      baseRing.rotation.z = -elapsed * 0.1;
      currRing.rotation.z = elapsed * 0.15;

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
  }, [driftCount, verdict]);

  return (
    <div className="relative w-full h-full min-h-[360px] overflow-hidden rounded-2xl border border-amber-500/20 bg-zinc-950/80">
      <div ref={mountRef} className="absolute inset-0 w-full h-full" />
      <div className="absolute bottom-4 left-4 z-10 pointer-events-none flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
        <span className="text-[11px] font-mono text-zinc-400">9-DIM DRIFT TOPOLOGY · VERDICT: {verdict}</span>
      </div>
    </div>
  );
}
