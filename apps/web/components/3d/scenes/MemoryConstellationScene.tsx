'use client';

import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { PALETTE } from '@/lib/3d-math';

interface MemoryConstellationSceneProps {
  stalenessWeight?: number;
  highlightCategory?: string;
}

export default function MemoryConstellationScene({ stalenessWeight = 0.15, highlightCategory }: MemoryConstellationSceneProps) {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(PALETTE.obsidian, 0.1);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 50);
    camera.position.set(0, 0, 6.0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0x2a3d31, 1.5);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x4ade80, 2.5, 10);
    pointLight.position.set(2, 3, 2);
    scene.add(pointLight);

    // Vector cluster points (Simulating CockroachDB 1536-dim projected into 3D)
    const clusterGroup = new THREE.Group();
    scene.add(clusterGroup);

    const clusterCount = 120;
    const pointGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(clusterCount * 3);
    const colors = new Float32Array(clusterCount * 3);

    const c1 = new THREE.Color(PALETTE.sage);
    const c2 = new THREE.Color(PALETTE.luminousGreen);
    const c3 = new THREE.Color(PALETTE.warmWhite);

    for (let i = 0; i < clusterCount; i++) {
      // 3 primary clusters (Database, Network/Security, Service/Auth)
      const clusterIdx = i % 3;
      const angle = (i / clusterCount) * Math.PI * 2;
      const radius = 1.6 + (Math.random() - 0.5) * 0.9;
      const offset = (clusterIdx - 1) * 1.5;

      positions[i * 3] = Math.cos(angle) * radius + offset * 0.5;
      positions[i * 3 + 1] = Math.sin(angle) * (radius * 0.7) + (Math.random() - 0.5) * 0.6;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 1.8;

      const col = clusterIdx === 0 ? c1 : clusterIdx === 1 ? c2 : c3;
      colors[i * 3] = col.r;
      colors[i * 3 + 1] = col.g;
      colors[i * 3 + 2] = col.b;
    }

    pointGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    pointGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const pointMat = new THREE.PointsMaterial({
      size: 0.12,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
    });
    const pointsMesh = new THREE.Points(pointGeo, pointMat);
    clusterGroup.add(pointsMesh);

    // Cluster Boundary Wire Rings
    const ringGeo = new THREE.TorusGeometry(1.8, 0.015, 8, 48);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x4ade80,
      transparent: true,
      opacity: 0.2,
      wireframe: true,
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 3;
    clusterGroup.add(ring);

    let frameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      frameId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      clusterGroup.rotation.y = elapsed * 0.15;
      clusterGroup.rotation.x = Math.sin(elapsed * 0.1) * 0.15;
      ring.rotation.z = elapsed * 0.08;

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
  }, [stalenessWeight, highlightCategory]);

  return (
    <div className="relative w-full h-full min-h-[360px] overflow-hidden rounded-2xl border border-emerald-500/20 bg-zinc-950/80">
      <div ref={mountRef} className="absolute inset-0 w-full h-full" />
      <div className="absolute bottom-4 left-4 z-10 pointer-events-none flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-[11px] font-mono text-zinc-400">COCKROACHDB VECTOR(1536) TOPOLOGY</span>
      </div>
    </div>
  );
}
