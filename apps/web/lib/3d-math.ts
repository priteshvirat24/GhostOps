import * as THREE from 'three';

export interface NodePoint {
  id: string;
  label: string;
  category: 'INCIDENT' | 'MEMORY' | 'EVIDENCE' | 'HYPOTHESIS' | 'TEMPORAL' | 'REMEDIATION' | 'VERIFICATION';
  position: [number, number, number];
  size: number;
  confidence?: number;
  details?: string;
  connections: string[];
}

export const PALETTE = {
  obsidian: 0x07090e,
  charcoal: 0x0c1017,
  graphite: 0x121824,
  sage: 0x6f8f7c,
  mutedMint: 0x8fae9d,
  deepForest: 0x1a2b22,
  luminousGreen: 0x4ade80,
  warmWhite: 0xf5f6f0,
  bone: 0xd6dad0,
  accentAmber: 0xf59e0b,
  dangerRed: 0xef4444,
};

export const DEFAULT_NODES: NodePoint[] = [
  {
    id: 'inc-01',
    label: 'INCIDENT #2026-904',
    category: 'INCIDENT',
    position: [0, 0, 0],
    size: 0.45,
    confidence: 0.96,
    details: 'Database Connection Exhaustion & Latency Spike on auth-service',
    connections: ['ev-01', 'ev-02', 'hyp-01', 'hyp-02']
  },
  {
    id: 'ev-01',
    label: 'EVIDENCE: TCP POOL EXHAUSTION',
    category: 'EVIDENCE',
    position: [-2.2, 1.4, 0.8],
    size: 0.28,
    details: 'Max connection limit reached (250/250) on port 26257',
    connections: ['hyp-01', 'mem-01']
  },
  {
    id: 'ev-02',
    label: 'EVIDENCE: INGRESS RULE DRIFT',
    category: 'EVIDENCE',
    position: [-1.8, -1.6, -1.2],
    size: 0.28,
    details: 'Security Group sg-0a89f92 modified 14 min prior',
    connections: ['hyp-02', 'temp-01']
  },
  {
    id: 'mem-01',
    label: 'PRECEDENT #1847 (2024)',
    category: 'MEMORY',
    position: [2.5, 1.8, -0.6],
    size: 0.35,
    confidence: 0.91,
    details: 'Historical incident resolved via Security Group rule alteration',
    connections: ['temp-01', 'rem-01']
  },
  {
    id: 'mem-02',
    label: 'PRECEDENT #1402 (2025)',
    category: 'MEMORY',
    position: [3.1, -1.2, 1.4],
    size: 0.32,
    confidence: 0.84,
    details: 'Leaseholder imbalance resolved via relocate range statement',
    connections: ['hyp-01', 'rem-01']
  },
  {
    id: 'hyp-01',
    label: 'HYPOTHESIS A: LEASE IMBALANCE',
    category: 'HYPOTHESIS',
    position: [0.8, 2.6, 1.2],
    size: 0.30,
    confidence: 0.88,
    details: 'Range leaseholder hotspot causing contention on node 3',
    connections: ['rem-01']
  },
  {
    id: 'hyp-02',
    label: 'HYPOTHESIS B: STALE PRECEDENT',
    category: 'HYPOTHESIS',
    position: [-0.6, -2.4, 1.6],
    size: 0.30,
    confidence: 0.94,
    details: 'Direct application of #1847 fix would sever internal egress',
    connections: ['temp-01']
  },
  {
    id: 'temp-01',
    label: 'TEMPORAL DRIFT: 9-DIM DIFF',
    category: 'TEMPORAL',
    position: [1.2, -1.8, -2.0],
    size: 0.36,
    confidence: 0.98,
    details: 'VERDICT: DO_NOT_EXECUTE (#1847 fix incompatible with 2026 VPC topology)',
    connections: ['rem-01']
  },
  {
    id: 'rem-01',
    label: 'GOVERNED SAGA: 2PC PLAN',
    category: 'REMEDIATION',
    position: [3.4, 0.2, 0.4],
    size: 0.38,
    confidence: 0.92,
    details: 'Safe adaptive remediation: Rebalance leaseholders + drain connection pool',
    connections: ['ver-01']
  },
  {
    id: 'ver-01',
    label: 'VERIFICATION: EC2 + CW',
    category: 'VERIFICATION',
    position: [2.0, -2.8, 0.2],
    size: 0.34,
    confidence: 1.0,
    details: 'Zero errors observed, p99 latency dropped 2400ms -> 18ms',
    connections: ['inc-01', 'mem-02']
  }
];

export function createFacetedGeometry(category: NodePoint['category'], size: number): THREE.BufferGeometry {
  switch (category) {
    case 'INCIDENT':
      return new THREE.IcosahedronGeometry(size, 2);
    case 'MEMORY':
      return new THREE.DodecahedronGeometry(size, 0);
    case 'EVIDENCE':
      return new THREE.OctahedronGeometry(size, 0);
    case 'HYPOTHESIS':
      return new THREE.TetrahedronGeometry(size, 1);
    case 'TEMPORAL':
      return new THREE.TorusGeometry(size * 0.8, size * 0.25, 12, 24);
    case 'REMEDIATION':
      return new THREE.BoxGeometry(size * 1.3, size * 1.3, size * 1.3);
    case 'VERIFICATION':
      return new THREE.RingGeometry(size * 0.4, size * 1.1, 16);
    default:
      return new THREE.SphereGeometry(size, 16, 16);
  }
}

export function getNodeColor(category: NodePoint['category']): number {
  switch (category) {
    case 'INCIDENT':
      return PALETTE.warmWhite;
    case 'MEMORY':
      return PALETTE.sage;
    case 'EVIDENCE':
      return PALETTE.mutedMint;
    case 'HYPOTHESIS':
      return PALETTE.bone;
    case 'TEMPORAL':
      return PALETTE.accentAmber;
    case 'REMEDIATION':
      return PALETTE.luminousGreen;
    case 'VERIFICATION':
      return PALETTE.luminousGreen;
    default:
      return PALETTE.warmWhite;
  }
}
