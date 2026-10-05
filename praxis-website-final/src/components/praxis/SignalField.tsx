import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

type Column = {
  age: number;
  amplitude: number;
  center: number;
  density: number;
  transient: number;
};

type NoiseState = {
  fast: number;
  medium: number;
  slow: number;
  fastTarget: number;
  mediumTarget: number;
  slowTarget: number;
  fastSteps: number;
  mediumSteps: number;
  slowSteps: number;
  phase: number;
  transient: number;
  transientDecay: number;
};

const COLUMN_COUNT = 224;
const PARTICLES_PER_COLUMN = 42;
const PARTICLE_COUNT = COLUMN_COUNT * PARTICLES_PER_COLUMN;
const FIELD_WIDTH = 22;
const FIELD_HEIGHT = 8;
const TRAVEL_TIME = 18;

function nextTarget(value: number, steps: number, min: number, max: number) {
  if (steps > 0) return { target: value, steps: steps - 1 };
  return {
    target: Math.random(),
    steps: Math.floor(min + Math.random() * (max - min)),
  };
}

/** Produces one new, non-repeating audio-like sample for the rolling buffer. */
function generateSample(noise: NoiseState): Omit<Column, "age"> {
  const fast = nextTarget(noise.fastTarget, noise.fastSteps, 4, 12);
  const medium = nextTarget(noise.mediumTarget, noise.mediumSteps, 14, 38);
  const slow = nextTarget(noise.slowTarget, noise.slowSteps, 45, 120);
  noise.fastTarget = fast.target;
  noise.fastSteps = fast.steps;
  noise.mediumTarget = medium.target;
  noise.mediumSteps = medium.steps;
  noise.slowTarget = slow.target;
  noise.slowSteps = slow.steps;
  noise.fast += (noise.fastTarget - noise.fast) * 0.24;
  noise.medium += (noise.mediumTarget - noise.medium) * 0.075;
  noise.slow += (noise.slowTarget - noise.slow) * 0.022;
  noise.phase += 0.11 + noise.medium * 0.045;

  if (noise.transient < 0.025 && Math.random() < 0.018) {
    noise.transient = 0.65 + Math.random() * 0.75;
    noise.transientDecay = 0.84 + Math.random() * 0.1;
  } else {
    noise.transient *= noise.transientDecay;
  }

  const layered = noise.slow * 0.46 + noise.medium * 0.34 + noise.fast * 0.2;
  const pulse = Math.abs(Math.sin(noise.phase)) * (0.12 + noise.fast * 0.16);
  const amplitude = Math.min(1.3, 0.08 + layered * 0.68 + pulse + noise.transient);

  return {
    amplitude,
    center: (noise.medium - 0.5) * 0.58 + Math.sin(noise.phase * 0.31) * 0.17,
    density: 0.28 + noise.slow * 0.46 + Math.min(0.26, noise.transient * 0.28),
    transient: Math.min(1, noise.transient),
  };
}

function createNoiseState(): NoiseState {
  return {
    fast: Math.random(),
    medium: Math.random(),
    slow: Math.random(),
    fastTarget: Math.random(),
    mediumTarget: Math.random(),
    slowTarget: Math.random(),
    fastSteps: 7,
    mediumSteps: 21,
    slowSteps: 68,
    phase: Math.random() * Math.PI * 2,
    transient: 0,
    transientDecay: 0.9,
  };
}

function ParticleStream({ reducedMotion }: { reducedMotion: boolean }) {
  const pointsRef = useRef<THREE.Points>(null);
  const pointer = useRef({ x: 0, y: 0 });
  const accumulator = useRef(0);
  const elapsed = useRef(0);
  const { viewport } = useThree();

  const stream = useMemo(() => {
    const positions = new Float32Array(PARTICLE_COUNT * 3);
    const alphas = new Float32Array(PARTICLE_COUNT);
    const sizes = new Float32Array(PARTICLE_COUNT);
    const radial = new Float32Array(PARTICLE_COUNT);
    const depth = new Float32Array(PARTICLE_COUNT);
    const jitter = new Float32Array(PARTICLE_COUNT);
    const columns: Column[] = [];
    const noise = createNoiseState();

    for (let column = 0; column < COLUMN_COUNT; column += 1) {
      columns.push({
        age: (column / COLUMN_COUNT) * TRAVEL_TIME,
        ...generateSample(noise),
      });
      for (let particle = 0; particle < PARTICLES_PER_COLUMN; particle += 1) {
        const index = column * PARTICLES_PER_COLUMN + particle;
        // Ordered depth lanes form a coherent waveform surface in one recycled buffer.
        radial[index] = particle / (PARTICLES_PER_COLUMN - 1);
        depth[index] = (radial[index] - 0.5) * 7;
        jitter[index] = Math.random() * Math.PI * 2;
        sizes[index] = 1.7 + Math.pow(Math.random(), 4) * 2.8;
      }
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("aAlpha", new THREE.BufferAttribute(alphas, 1));
    geometry.setAttribute("aSize", new THREE.BufferAttribute(sizes, 1));

    const uniforms = {
      uPixelRatio: { value: 1 },
      uColor: { value: new THREE.Color(0.72, 0.75, 0.78) },
      uBrightColor: { value: new THREE.Color(0.94, 0.95, 0.96) },
      uAccent: { value: new THREE.Color("#c4c9cf") },
      uSignal: { value: new THREE.Color("#868e98") },
    };
    const material = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms,
      vertexShader: /* glsl */ `
        uniform float uPixelRatio;
        attribute float aAlpha;
        attribute float aSize;
        varying float vAlpha;
        varying float vDepth;
        void main() {
          vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
          vAlpha = aAlpha;
          vDepth = clamp((position.z + 3.5) / 7.0, 0.0, 1.0);
          gl_PointSize = aSize * uPixelRatio * (16.0 / max(3.0, -viewPosition.z)) * (0.8 + aAlpha * 1.4);
          gl_Position = projectionMatrix * viewPosition;
        }
      `,
      fragmentShader: /* glsl */ `
        uniform vec3 uColor;
        uniform vec3 uBrightColor;
        uniform vec3 uAccent;
        uniform vec3 uSignal;
        varying float vAlpha;
        varying float vDepth;
        void main() {
          float distanceToCenter = length(gl_PointCoord - vec2(0.5));
          float softDot = 1.0 - smoothstep(0.12, 0.5, distanceToCenter);
          float core = 1.0 - smoothstep(0.0, 0.24, distanceToCenter);
          vec3 tint = mix(uSignal, uAccent, smoothstep(0.12, 0.65, vAlpha));
          vec3 color = mix(tint, uBrightColor, core * smoothstep(0.45, 0.9, vAlpha) * 0.55);
          gl_FragColor = vec4(color, softDot * vAlpha);
        }
      `,
    });

    return { positions, alphas, radial, depth, jitter, columns, noise, geometry, material, uniforms };
  }, []);

  useEffect(() => {
    const style = getComputedStyle(document.documentElement);
    const parseColor = (name: string, fallback: THREE.Color) => {
      const values = style
        .getPropertyValue(name)
        .trim()
        .split(/\s+/)
        .map(Number);
      if (values.length !== 3 || values.some((value) => !Number.isFinite(value))) return fallback;
      const [red = 0.72, green = 0.75, blue = 0.78] = values;
      return new THREE.Color(red, green, blue);
    };
    stream.uniforms.uColor.value = parseColor(
      "--particle-rgb",
      stream.uniforms.uColor.value,
    );
    stream.uniforms.uBrightColor.value = parseColor(
      "--particle-bright-rgb",
      stream.uniforms.uBrightColor.value,
    );
    const onPointerMove = (event: PointerEvent) => {
      pointer.current.x = (event.clientX / window.innerWidth - 0.5) * 2;
      pointer.current.y = (event.clientY / window.innerHeight - 0.5) * 2;
    };
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    return () => window.removeEventListener("pointermove", onPointerMove);
  }, [stream.material]);

  useEffect(
    () => () => {
      stream.geometry.dispose();
      stream.material.dispose();
    },
    [stream.geometry, stream.material],
  );

  useFrame((state, rawDelta) => {
    const dt = reducedMotion ? 0 : Math.min(rawDelta, 0.05);
    elapsed.current += dt;
    accumulator.current += dt;
    const interval = TRAVEL_TIME / COLUMN_COUNT;

    while (!reducedMotion && accumulator.current >= interval) {
      accumulator.current -= interval;
      let oldest = 0;
      for (let i = 1; i < stream.columns.length; i += 1) {
        const candidate = stream.columns[i];
        const currentOldest = stream.columns[oldest];
        if (candidate && currentOldest && candidate.age > currentOldest.age) oldest = i;
      }
      stream.columns[oldest] = { age: 0, ...generateSample(stream.noise) };
    }

    const width = Math.max(FIELD_WIDTH, (viewport.width / Math.max(viewport.height, 1)) * 9.8);
    const height = Math.min(FIELD_HEIGHT, viewport.height * 0.88);

    for (let column = 0; column < COLUMN_COUNT; column += 1) {
      const sample = stream.columns[column];
      if (!sample) continue;
      sample.age += dt;
      const progress = sample.age / TRAVEL_TIME;
      const x = -width * 0.56 + progress * width * 1.12;
      const horizontalFade = Math.sin(Math.PI * Math.min(1, Math.max(0, progress)));

      for (let particle = 0; particle < PARTICLES_PER_COLUMN; particle += 1) {
        const index = column * PARTICLES_PER_COLUMN + particle;
        const positionIndex = index * 3;
        const lane = stream.radial[index] ?? 0;
        const z = stream.depth[index] ?? 0;
        const phase = progress * Math.PI * 10 + lane * 2.4;
        const peakVariation = 0.82 + 0.18 * Math.sin(progress * Math.PI * 5 + sample.center);
        const envelope = sample.amplitude * height * 0.32 * peakVariation;
        const wave = Math.sin(phase) * 0.74 + Math.sin(phase * 2.3 + sample.center) * 0.22;
        const grain = Math.sin(stream.jitter[index] ?? 0);
        stream.positions[positionIndex] = x + grain * 0.024;
        stream.positions[positionIndex + 1] = sample.center * 0.35 + wave * envelope + grain * 0.09;
        stream.positions[positionIndex + 2] = z + grain * 0.045;
        const laneFade = 0.4 + Math.sin(lane * Math.PI) * 0.6;
        const crest = Math.pow(Math.max(0, wave), 3);
        const highlight = crest * (0.2 + sample.transient * 0.35 + sample.density * 0.65);
        stream.alphas[index] = horizontalFade * laneFade * (0.45 + highlight * 1.1);
      }
    }

    const positionAttribute = stream.geometry.getAttribute("position");
    const alphaAttribute = stream.geometry.getAttribute("aAlpha");
    positionAttribute.needsUpdate = true;
    alphaAttribute.needsUpdate = true;
    stream.uniforms.uPixelRatio.value = Math.min(state.gl.getPixelRatio(), 1.75);

    const points = pointsRef.current;
    if (points) {
      const targetX = 0.18 + (reducedMotion ? 0 : pointer.current.y * 0.015);
      const targetY = 0.16 + (reducedMotion ? 0 : pointer.current.x * 0.025);
      points.rotation.x += (targetX - points.rotation.x) * (1 - Math.exp(-2.8 * Math.max(dt, 0.016)));
      points.rotation.y += (targetY - points.rotation.y) * (1 - Math.exp(-2.8 * Math.max(dt, 0.016)));
    }
  });

  return (
    <points ref={pointsRef} frustumCulled={false}>
      <primitive object={stream.geometry} attach="geometry" />
      <primitive object={stream.material} attach="material" />
    </points>
  );
}

export function SignalField({ className = "" }: { className?: string }) {
  const [mounted, setMounted] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    setMounted(true);
    setReducedMotion(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);

  if (!mounted) return null;

  return (
    <div
      aria-hidden
      className={`pointer-events-none absolute inset-0 z-0 opacity-90 [mask-image:linear-gradient(to_bottom,transparent_0%,black_12%,black_82%,transparent_100%)] ${className}`}
    >
      <Canvas
        camera={{ position: [0, 0, 16], fov: 45 }}
        dpr={[1, 1.75]}
        frameloop={reducedMotion ? "demand" : "always"}
        gl={{ alpha: true, antialias: false, powerPreference: "high-performance" }}
      >
        <ParticleStream reducedMotion={reducedMotion} />
      </Canvas>
    </div>
  );
}