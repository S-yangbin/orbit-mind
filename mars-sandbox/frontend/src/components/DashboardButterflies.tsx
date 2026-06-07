import { useEffect, useRef, memo } from "react";

/* ───────── 常量 ───────── */
const BUTTERFLY_COUNT = 5;

const PALETTE = [
  { color: "#f0abfc", accent: "#e879f9" },
  { color: "#fcd34d", accent: "#f59e0b" },
  { color: "#67e8f9", accent: "#22d3ee" },
  { color: "#86efac", accent: "#4ade80" },
  { color: "#fca5a5", accent: "#f87171" },
  { color: "#c4b5fd", accent: "#a78bfa" },
];

function randomTarget() {
  return { x: 5 + Math.random() * 85, y: 5 + Math.random() * 55 };
}

/* ───────── 单个蝴蝶 SVG（memo 避免无意义重渲染） ───────── */
const ButterflySvg = memo(function ButterflySvg({
  size,
  color,
  accent,
  flapId,
}: {
  size: number;
  color: string;
  accent: string;
  flapId: string;
}) {
  return (
    <svg width={size} height={size * 0.8} viewBox="0 0 100 80" style={{ overflow: "visible" }}>
      <g style={{ transformOrigin: "50px 40px", animation: `${flapId}_left 0.55s ease-in-out infinite alternate` }}>
        <ellipse cx="28" cy="28" rx="28" ry="24" fill={color} opacity="0.88" />
        <ellipse cx="26" cy="25" rx="15" ry="12" fill={accent} opacity="0.45" />
        <circle cx="20" cy="32" r="5" fill="white" opacity="0.2" />
        <ellipse cx="24" cy="50" rx="18" ry="15" fill={color} opacity="0.78" />
        <ellipse cx="22" cy="48" rx="9" ry="8" fill={accent} opacity="0.35" />
      </g>
      <g style={{ transformOrigin: "50px 40px", animation: `${flapId}_right 0.55s ease-in-out infinite alternate` }}>
        <ellipse cx="72" cy="28" rx="28" ry="24" fill={color} opacity="0.88" />
        <ellipse cx="74" cy="25" rx="15" ry="12" fill={accent} opacity="0.45" />
        <circle cx="80" cy="32" r="5" fill="white" opacity="0.2" />
        <ellipse cx="76" cy="50" rx="18" ry="15" fill={color} opacity="0.78" />
        <ellipse cx="78" cy="48" rx="9" ry="8" fill={accent} opacity="0.35" />
      </g>
      <ellipse cx="50" cy="40" rx="3.5" ry="20" fill="#1e293b" opacity="0.65" />
      <path d="M50 22 Q42 10 36 6" stroke="#1e293b" strokeWidth="1.2" fill="none" opacity="0.45" />
      <path d="M50 22 Q58 10 64 6" stroke="#1e293b" strokeWidth="1.2" fill="none" opacity="0.45" />
      <circle cx="36" cy="6" r="1.8" fill="#1e293b" opacity="0.45" />
      <circle cx="64" cy="6" r="1.8" fill="#1e293b" opacity="0.45" />
    </svg>
  );
});

/* ───────── 蝴蝶数据（脱离 React state） ───────── */
interface ButterflyData {
  x: number;
  y: number;
  speed: number;
  wobble: number;
  targetX: number;
  targetY: number;
  flipX: boolean;
}

/* ───────── 主组件（零 state，纯 ref + DOM） ───────── */
export function DashboardButterflies() {
  const containerRef = useRef<HTMLDivElement>(null);
  const dataRef = useRef<ButterflyData[]>([]);
  const rafRef = useRef(0);
  const frameRef = useRef(0);

  /* 初始化数据（只执行一次） */
  if (dataRef.current.length === 0) {
    dataRef.current = Array.from({ length: BUTTERFLY_COUNT }, () => {
      const t = randomTarget();
      return {
        x: 10 + Math.random() * 80,
        y: 10 + Math.random() * 45,
        speed: 0.002 + Math.random() * 0.004,
        wobble: 3 + Math.random() * 5,
        targetX: t.x,
        targetY: t.y,
        flipX: false,
      };
    });
  }

  /* 动画帧：直接操作 DOM style，不触发 React 重渲染 */
  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];

    // 定期更换目标点
    for (let i = 0; i < BUTTERFLY_COUNT; i++) {
      const schedule = () => {
        const delay = 8000 + Math.random() * 16000;
        return setTimeout(() => {
          const t = randomTarget();
          dataRef.current[i].targetX = t.x;
          dataRef.current[i].targetY = t.y;
          timers.push(schedule());
        }, delay);
      };
      timers.push(schedule());
    }

    const tick = () => {
      frameRef.current++;
      const f = frameRef.current;
      const container = containerRef.current;
      if (!container) { rafRef.current = requestAnimationFrame(tick); return; }

      const children = container.children;
      for (let i = 0; i < BUTTERFLY_COUNT; i++) {
        const b = dataRef.current[i];
        const el = children[i] as HTMLElement | undefined;
        if (!el) continue;

        const dx = b.targetX - b.x;
        const dy = b.targetY - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist > 0.5) {
          b.x += (dx / dist) * b.speed * 0.3;
          b.y += (dy / dist) * b.speed * 0.3;
        }

        const wobbleY = Math.sin(f * 0.018 + i * 2) * b.wobble * 0.4;
        const wobbleX = Math.cos(f * 0.013 + i * 3) * b.wobble * 0.2;

        const finalX = Math.max(2, Math.min(95, b.x + wobbleX));
        const finalY = Math.max(3, Math.min(60, b.y + wobbleY));
        b.flipX = dx < -0.1;

        const rotate = Math.sin(f * 0.012 + i) * 5;
        el.style.left = `${finalX}%`;
        el.style.top = `${finalY}%`;
        el.style.transform = `scaleX(${b.flipX ? -1 : 1}) rotate(${rotate}deg)`;
      }

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(rafRef.current);
      timers.forEach(clearTimeout);
    };
  }, []);

  return (
    <>
      <style>{butterflyKeyframes}</style>
      <div ref={containerRef}>
        {dataRef.current.map((b, i) => {
          const palette = PALETTE[i % PALETTE.length];
          const size = 18 + (i * 3) % 12; // 稳定大小
          return (
            <div
              key={i}
              style={{
                position: "fixed",
                left: `${b.x}%`,
                top: `${b.y}%`,
                zIndex: 3,
                pointerEvents: "none",
                userSelect: "none",
                opacity: 0.6 + (i % 3) * 0.12,
                filter: "drop-shadow(0 2px 6px rgba(0,0,0,0.2))",
                willChange: "left, top, transform",
              }}
            >
              <ButterflySvg
                size={size}
                color={palette.color}
                accent={palette.accent}
                flapId={`bf${i}`}
              />
            </div>
          );
        })}
      </div>
    </>
  );
}

/* ───────── CSS 动画 ───────── */
const butterflyKeyframes = Array.from({ length: BUTTERFLY_COUNT }, (_, i) => `
@keyframes bf${i}_left {
  0%   { transform: scaleX(1) skewY(0deg); }
  100% { transform: scaleX(0.4) skewY(12deg); }
}
@keyframes bf${i}_right {
  0%   { transform: scaleX(1) skewY(0deg); }
  100% { transform: scaleX(0.4) skewY(-12deg); }
}
`).join("\n");
