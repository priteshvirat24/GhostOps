'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { DEFAULT_NODES, NodePoint, createFacetedGeometry, getNodeColor, PALETTE } from '@/lib/3d-math';

interface HeroVaultSceneProps {
  onSelectNode?: (node: NodePoint) => void;
  activeChamberIndex?: number;
}

export default function HeroVaultScene({ onSelectNode, activeChamberIndex = 0 }: HeroVaultSceneProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<NodePoint | null>(null);
  const [fps, setFps] = useState(60);

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // 1. Scene setup
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(PALETTE.obsidian, 0.08);

    // 2. Camera setup
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 7.5);

    // 3. Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    container.appendChild(renderer.domElement);

    // 4. Lighting setup (Volumetric & Obsidian highlights)
    const ambientLight = new THREE.AmbientLight(0x2a3d31, 1.2);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xa7c4b5, 2.4);
    dirLight1.position.set(5, 8, 5);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x4ade80, 1.8);
    dirLight2.position.set(-6, -4, 3);
    scene.add(dirLight2);

    const coreLight = new THREE.PointLight(0x4ade80, 2.0, 12);
    coreLight.position.set(0, 0, 0);
    scene.add(coreLight);

    // 5. Obsidian Vault Core
    const coreGroup = new THREE.Group();
    scene.add(coreGroup);

    const coreGeo = new THREE.IcosahedronGeometry(1.3, 0);
    const coreMat = new THREE.MeshPhysicalMaterial({
      color: 0x091012,
      metalness: 0.85,
      roughness: 0.15,
      transmission: 0.6,
      thickness: 1.2,
      ior: 1.6,
      reflectivity: 0.9,
      clearcoat: 1.0,
      clearcoatRoughness: 0.1,
      wireframe: false,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    coreGroup.add(coreMesh);

    // Wireframe outer cage
    const wireGeo = new THREE.IcosahedronGeometry(1.45, 1);
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x4ade80,
      wireframe: true,
      transparent: true,
      opacity: 0.25,
    });
    const wireMesh = new THREE.Mesh(wireGeo, wireMat);
    coreGroup.add(wireMesh);

    // 6. Neural Memory Nodes
    const nodeMeshes: { mesh: THREE.Mesh; data: NodePoint }[] = [];
    const nodesGroup = new THREE.Group();
    scene.add(nodesGroup);

    DEFAULT_NODES.forEach((node) => {
      const geo = createFacetedGeometry(node.category, node.size);
      const color = getNodeColor(node.category);
      const mat = new THREE.MeshStandardMaterial({
        color: color,
        metalness: 0.4,
        roughness: 0.25,
        emissive: color,
        emissiveIntensity: 0.25,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(...node.position);
      mesh.userData = { id: node.id, nodeData: node };
      nodesGroup.add(mesh);
      nodeMeshes.push({ mesh, data: node });

      // Subtle node halo
      const haloGeo = new THREE.RingGeometry(node.size * 1.2, node.size * 1.35, 16);
      const haloMat = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.35,
        side: THREE.DoubleSide,
      });
      const haloMesh = new THREE.Mesh(haloGeo, haloMat);
      haloMesh.lookAt(camera.position);
      mesh.add(haloMesh);
    });

    // 7. Dynamic 3D Particle Links
    const lineMaterial = new THREE.LineBasicMaterial({
      color: 0x6f8f7c,
      transparent: true,
      opacity: 0.35,
    });
    const linesGroup = new THREE.Group();
    scene.add(linesGroup);

    const linkPairs: [THREE.Vector3, THREE.Vector3][] = [];
    DEFAULT_NODES.forEach((node) => {
      const startPos = new THREE.Vector3(...node.position);
      node.connections.forEach((targetId) => {
        const targetNode = DEFAULT_NODES.find((n) => n.id === targetId);
        if (targetNode) {
          const endPos = new THREE.Vector3(...targetNode.position);
          const points = [startPos, endPos];
          const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
          const line = new THREE.Line(lineGeo, lineMaterial);
          linesGroup.add(line);
          linkPairs.push([startPos, endPos]);
        }
      });
    });

    // 8. Traveling Pulse Particles along Links
    const pulseCount = 30;
    const pulseGeo = new THREE.BufferGeometry();
    const pulsePositions = new Float32Array(pulseCount * 3);
    const pulseProgress = new Float32Array(pulseCount).fill(0).map(() => Math.random());
    const pulseLinkIndex = new Uint8Array(pulseCount).fill(0).map(() => Math.floor(Math.random() * linkPairs.length));

    pulseGeo.setAttribute('position', new THREE.BufferAttribute(pulsePositions, 3));
    const pulseMat = new THREE.PointsMaterial({
      color: 0x4ade80,
      size: 0.12,
      transparent: true,
      opacity: 0.9,
      blending: THREE.AdditiveBlending,
    });
    const pulsePoints = new THREE.Points(pulseGeo, pulseMat);
    scene.add(pulsePoints);

    // 9. Floating background micro-dust
    const dustCount = 80;
    const dustGeo = new THREE.BufferGeometry();
    const dustPos = new Float32Array(dustCount * 3);
    for (let i = 0; i < dustCount * 3; i += 3) {
      dustPos[i] = (Math.random() - 0.5) * 14;
      dustPos[i + 1] = (Math.random() - 0.5) * 10;
      dustPos[i + 2] = (Math.random() - 0.5) * 8;
    }
    dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
    const dustMat = new THREE.PointsMaterial({
      color: 0x8fae9d,
      size: 0.04,
      transparent: true,
      opacity: 0.4,
    });
    const dustPoints = new THREE.Points(dustGeo, dustMat);
    scene.add(dustPoints);

    // 10. Pointer Parallax & Raycasting
    let targetRotX = 0;
    let targetRotY = 0;
    let mouseX = 0;
    let mouseY = 0;
    const raycaster = new THREE.Raycaster();
    const mouseVec = new THREE.Vector2();

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;
      mouseX = (x - 0.5) * 2;
      mouseY = (y - 0.5) * 2;
      targetRotY = mouseX * 0.45;
      targetRotX = mouseY * 0.35;

      mouseVec.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouseVec.y = -(e.clientY / window.innerHeight) * 2 + 1;
    };

    const handleClick = () => {
      raycaster.setFromCamera(mouseVec, camera);
      const intersects = raycaster.intersectObjects(nodeMeshes.map((n) => n.mesh));
      if (intersects.length > 0) {
        const hit = intersects[0].object.userData.nodeData as NodePoint;
        if (hit && onSelectNode) {
          onSelectNode(hit);
        }
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    container.addEventListener('click', handleClick);

    // 11. Render loop
    let animationFrameId: number;
    let clock = new THREE.Clock();
    let frameCount = 0;
    let lastTime = performance.now();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const delta = clock.getDelta();
      const elapsed = clock.getElapsedTime();

      // FPS tracking
      frameCount++;
      const now = performance.now();
      if (now - lastTime >= 1000) {
        setFps(Math.round((frameCount * 1000) / (now - lastTime)));
        frameCount = 0;
        lastTime = now;
      }

      // Smooth parallax interpolation
      coreGroup.rotation.y += (targetRotY - coreGroup.rotation.y) * 0.05 + 0.003;
      coreGroup.rotation.x += (targetRotX - coreGroup.rotation.x) * 0.05;
      nodesGroup.rotation.y = coreGroup.rotation.y * 0.7;
      nodesGroup.rotation.x = coreGroup.rotation.x * 0.7;
      linesGroup.rotation.y = nodesGroup.rotation.y;
      linesGroup.rotation.x = nodesGroup.rotation.x;

      // Breathing vault scale
      const breathe = 1 + Math.sin(elapsed * 1.5) * 0.04;
      coreMesh.scale.set(breathe, breathe, breathe);
      wireMesh.rotation.y -= 0.006;
      wireMesh.rotation.z += 0.004;

      // Node subtle self-rotation
      nodeMeshes.forEach(({ mesh, data }, idx) => {
        mesh.rotation.y += 0.01 + idx * 0.002;
        mesh.rotation.x += 0.005;
        const bob = Math.sin(elapsed * 2 + idx) * 0.05;
        mesh.position.y = data.position[1] + bob;
      });

      // Update traveling pulse particles
      if (linkPairs.length > 0) {
        const positions = pulseGeo.attributes.position.array as Float32Array;
        for (let i = 0; i < pulseCount; i++) {
          pulseProgress[i] += delta * 0.6;
          if (pulseProgress[i] >= 1.0) {
            pulseProgress[i] = 0;
            pulseLinkIndex[i] = Math.floor(Math.random() * linkPairs.length);
          }
          const pair = linkPairs[pulseLinkIndex[i]];
          if (pair) {
            const [start, end] = pair;
            const t = pulseProgress[i];
            const p = new THREE.Vector3().lerpVectors(start, end, t);
            // Apply group rotation
            p.applyEuler(nodesGroup.rotation);
            positions[i * 3] = p.x;
            positions[i * 3 + 1] = p.y;
            positions[i * 3 + 2] = p.z;
          }
        }
        pulseGeo.attributes.position.needsUpdate = true;
      }

      // Camera camera chamber transition
      const targetZ = 7.5 - activeChamberIndex * 0.4;
      const targetY = -activeChamberIndex * 0.2;
      camera.position.z += (targetZ - camera.position.z) * 0.05;
      camera.position.y += (targetY - camera.position.y) * 0.05;

      // Raycasting hover check
      raycaster.setFromCamera(mouseVec, camera);
      const intersects = raycaster.intersectObjects(nodeMeshes.map((n) => n.mesh));
      if (intersects.length > 0) {
        const hit = intersects[0].object.userData.nodeData as NodePoint;
        setHoveredNode(hit);
        document.body.style.cursor = 'pointer';
      } else {
        setHoveredNode(null);
        document.body.style.cursor = 'default';
      }

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
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      container.removeEventListener('click', handleClick);
      cancelAnimationFrame(animationFrameId);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
      document.body.style.cursor = 'default';
    };
  }, [activeChamberIndex, onSelectNode]);

  return (
    <div className="relative w-full h-full min-h-[600px] overflow-hidden select-none">
      <div ref={mountRef} className="absolute inset-0 w-full h-full" />

      {/* Floating HUD Indicator */}
      <div className="absolute top-6 left-6 pointer-events-none z-10 flex items-center gap-3">
        <div className="vault-badge px-3 py-1.5 rounded-full flex items-center gap-2 text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-emerald-300 font-mono tracking-wider font-medium">LIVING MEMORY VAULT</span>
        </div>
        <div className="vault-badge px-2.5 py-1 rounded-full text-[10px] text-zinc-400 font-mono">
          {fps} FPS · 1536-DIM
        </div>
      </div>

      {/* Interactive Node Hover Card */}
      {hoveredNode && (
        <div className="absolute bottom-8 right-8 z-20 max-w-sm pointer-events-none transition-all duration-200">
          <div className="vault-card p-4 rounded-xl border border-emerald-500/40 bg-zinc-950/90 shadow-2xl backdrop-blur-xl">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono tracking-widest text-emerald-400 px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/50">
                {hoveredNode.category}
              </span>
              {hoveredNode.confidence && (
                <span className="text-[11px] font-mono text-zinc-300 font-medium">
                  Conf: {(hoveredNode.confidence * 100).toFixed(0)}%
                </span>
              )}
            </div>
            <h4 className="text-sm font-semibold text-zinc-100 mb-1">{hoveredNode.label}</h4>
            <p className="text-xs text-zinc-400 leading-relaxed">{hoveredNode.details}</p>
            <div className="mt-3 pt-2 border-t border-zinc-800/80 flex items-center justify-between text-[10px] font-mono text-zinc-500">
              <span>Links: {hoveredNode.connections.length} nodes</span>
              <span className="text-emerald-400">CLICK TO INSPECT →</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
