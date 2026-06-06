import { useState, useEffect, useRef, useCallback } from "react";

/* ───────── 类型 ───────── */
type PetKind = "dog" | "cat";
type PetAction =
  | "idle"
  | "walk"
  | "run"
  | "lick"
  | "chase_tail"
  | "sleep"
  | "flee"
  | "gone"
  | "enter";

interface PetState {
  kind: PetKind;
  x: number;
  y: number;
  action: PetAction;
  flipX: boolean;
  clickCount: number;
  gone: boolean;
  heartVisible: boolean;
  heartKey: number;
  sweatVisible: boolean;
  zzzVisible: boolean;
  speechBubble: string;
  speechVisible: boolean;
  trails: { x: number; y: number; key: number }[];
}

/* ───────── 常量 ───────── */
const MAX_CLICKS_DOG = 7;
const MAX_CLICKS_CAT = 5; // 猫更不耐烦
const CLICK_DECAY_INTERVAL = 8000; // 8秒减1次点击计数
const GONE_DURATION = 120_000;
const WALK_SPEED = 0.3;
const RUN_SPEED = 0.85;
const FLEE_SPEED = 2.8;

const EMOJI: Record<PetKind, Record<string, string>> = {
  dog: { idle: "🐶", walk: "🐕", run: "🐕‍🦺", sleep: "🐶" },
  cat: { idle: "🐱", walk: "🐈", run: "🐈‍⬛", sleep: "🐱" },
};

const SPEECHES: Record<PetKind, Record<string, string[]>> = {
  dog: {
    lick: ["汪汪~ 舒服!", "舔舔舔~", "嗯…好痒~"],
    chase_tail: ["尾巴别跑!", "转圈圈~", "抓到了…才怪!"],
    idle: ["汪! 你好呀~", "摇摇尾巴~", "想摸摸我吗?"],
    sleep: ["Zzz…", "呼噜噜…汪…"],
    clicked: ["汪! 好开心!", "嘿嘿~再摸摸", "摇尾巴摇尾巴"],
    annoyed: ["别点了啦!", "我生气了!", "哼! 不理你了"],
    flee: ["我跑了!!", "拜拜~", "太多了!!"],
    enter: ["我回来啦!", "想我了没?", "汪汪~又见面了"],
  },
  cat: {
    lick: ["喵~ 优雅~", "舔毛时间~", "呼噜噜…"],
    chase_tail: ["尾巴!站住!", "喵喵旋转~", "哼,抓不到"],
    idle: ["喵… 看我干嘛", "伸懒腰~", "高冷地坐着"],
    sleep: ["Zzz…喵…", "呼噜噜…"],
    clicked: ["喵~ 还行吧", "勉强让你摸", "呼噜噜~"],
    annoyed: ["够了!", "本喵不高兴了", "别烦我!"],
    flee: ["哼!走了!", "不伺候了!", "再见!"],
    enter: ["本喵回来了", "想我没? 才怪", "喵~又见面了"],
  },
};

/* ───────── 工具函数 ───────── */
function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomPos(): { x: number; y: number } {
  return { x: 5 + Math.random() * 82, y: 58 + Math.random() * 32 };
}

function clamp(v: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, v));
}

let trailKeyCounter = 0;

/* ───────── 单个宠物渲染 ───────── */
function PetView({ state, onClick }: { state: PetState; onClick: () => void }) {
  const size = state.kind === "dog" ? 50 : 44;
  const actionKey = state.action === "flee" ? "run" : state.action === "enter" ? "walk" : state.action;
  const emoji = EMOJI[state.kind][actionKey] || EMOJI[state.kind].idle;
  const animClass = getAnimClass(state.action);

  return (
    <>
      {/* 脚印轨迹 */}
      {state.trails.map((t) => (
        <div
          key={t.key}
          style={{
            position: "fixed",
            left: `${t.x}%`,
            top: `${t.y + 3}%`,
            fontSize: 12,
            opacity: 0.3,
            zIndex: 99,
            pointerEvents: "none",
            animation: "petTrailFade 2s ease forwards",
          }}
        >
          🐾
        </div>
      ))}

      <div
        onClick={(e) => {
          e.stopPropagation();
          onClick();
        }}
        style={{
          position: "fixed",
          left: `${state.x}%`,
          top: `${state.y}%`,
          zIndex: 100,
          cursor: state.gone ? "default" : "pointer",
          transition:
            state.action === "flee" ||
            state.action === "walk" ||
            state.action === "run"
              ? "none"
              : "left 1s ease, top 1s ease",
          transform: `scaleX(${state.flipX ? -1 : 1})`,
          opacity: state.gone ? 0 : 1,
          pointerEvents: state.gone ? "none" : "auto",
          userSelect: "none",
        }}
      >
        {/* 地面阴影 */}
        <div
          style={{
            position: "absolute",
            bottom: -4,
            left: "50%",
            transform: "translateX(-50%)",
            width: size * 0.7,
            height: 8,
            borderRadius: "50%",
            background: "rgba(0,0,0,0.18)",
            filter: "blur(3px)",
            pointerEvents: "none",
          }}
        />

        {/* 主体 emoji */}
        <div
          style={{
            fontSize: size,
            lineHeight: 1,
            filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.25))",
            animation: animClass,
            position: "relative",
          }}
        >
          {emoji}

          {/* 睡觉的 Zzz */}
          {state.action === "sleep" && (
            <div
              style={{
                position: "absolute",
                top: -16,
                right: -18,
                fontSize: 16,
                animation: "petZzz 2s ease infinite",
                pointerEvents: "none",
              }}
            >
              💤
            </div>
          )}
        </div>

        {/* 爱心 */}
        {state.heartVisible && (
          <div
            key={state.heartKey}
            style={{
              position: "absolute",
              top: -28,
              left: "50%",
              transform: "translateX(-50%)",
              fontSize: 22,
              animation: "petFloatUp 1s ease forwards",
              pointerEvents: "none",
            }}
          >
            ❤️
          </div>
        )}

        {/* 不耐烦 */}
        {state.sweatVisible && (
          <div
            style={{
              position: "absolute",
              top: -18,
              right: -8,
              fontSize: 18,
              animation: "petSweatUp 0.8s ease forwards",
              pointerEvents: "none",
            }}
          >
            💢
          </div>
        )}

        {/* 气泡 */}
        {state.speechVisible && state.speechBubble && (
          <div
            style={{
              position: "absolute",
              bottom: size + 10,
              left: "50%",
              transform: `scaleX(${state.flipX ? -1 : 1}) translateX(-50%)`,
              background: "rgba(255,255,255,0.95)",
              borderRadius: 14,
              padding: "6px 14px",
              fontSize: 13,
              fontWeight: 500,
              color: "#334155",
              whiteSpace: "nowrap",
              boxShadow: "0 2px 14px rgba(0,0,0,0.15)",
              animation: "petFadeInUp 0.3s ease",
              pointerEvents: "none",
            }}
          >
            {state.speechBubble}
            <div
              style={{
                position: "absolute",
                bottom: -6,
                left: "50%",
                transform: "translateX(-50%)",
                width: 0,
                height: 0,
                borderLeft: "6px solid transparent",
                borderRight: "6px solid transparent",
                borderTop: "6px solid rgba(255,255,255,0.95)",
              }}
            />
          </div>
        )}

        {/* 名字 */}
        {!state.gone && (
          <div
            style={{
              textAlign: "center",
              marginTop: 4,
              fontSize: 11,
              fontWeight: 600,
              color: "rgba(255,255,255,0.85)",
              textShadow: "0 1px 4px rgba(0,0,0,0.5)",
              transform: `scaleX(${state.flipX ? -1 : 1})`,
            }}
          >
            {state.kind === "dog" ? "旺财" : "咪咪"}
          </div>
        )}
      </div>
    </>
  );
}

function getAnimClass(action: PetAction): string {
  switch (action) {
    case "walk":
      return "petWalk 0.4s ease infinite alternate";
    case "run":
      return "petRun 0.25s ease infinite alternate";
    case "flee":
      return "petRun 0.18s ease infinite alternate";
    case "lick":
      return "petLick 1s ease infinite";
    case "chase_tail":
      return "petChaseTail 0.6s ease infinite";
    case "sleep":
      return "petSleep 3s ease infinite";
    case "enter":
      return "petEnter 0.8s ease";
    default:
      return "petIdle 2s ease infinite";
  }
}

/* ───────── 主组件 ───────── */
export function DashboardPets() {
  const mkInit = (kind: PetKind): PetState => ({
    kind,
    ...randomPos(),
    action: "idle",
    flipX: false,
    clickCount: 0,
    gone: false,
    heartVisible: false,
    heartKey: 0,
    sweatVisible: false,
    zzzVisible: false,
    speechBubble: "",
    speechVisible: false,
    trails: [],
  });

  const [dog, setDog] = useState<PetState>(() => mkInit("dog"));
  const [cat, setCat] = useState<PetState>(() => mkInit("cat"));

  const dogRef = useRef(dog);
  const catRef = useRef(cat);
  dogRef.current = dog;
  catRef.current = cat;

  const dogTarget = useRef<{ x: number; y: number } | null>(null);
  const catTarget = useRef<{ x: number; y: number } | null>(null);

  /* ── 点击计数衰减 ── */
  useEffect(() => {
    const timer = setInterval(() => {
      setDog((p) => (p.clickCount > 0 ? { ...p, clickCount: p.clickCount - 1 } : p));
      setCat((p) => (p.clickCount > 0 ? { ...p, clickCount: p.clickCount - 1 } : p));
    }, CLICK_DECAY_INTERVAL);
    return () => clearInterval(timer);
  }, []);

  /* ── 行为切换（随机间隔） ── */
  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    const schedule = () => {
      const delay = 3000 + Math.random() * 5000;
      timeout = setTimeout(() => {
        updateBehavior("dog");
        updateBehavior("cat");
        schedule();
      }, delay);
    };
    schedule();
    return () => clearTimeout(timeout);
  }, []);

  /* ── 移动帧 ── */
  useEffect(() => {
    let raf: number;
    let frameCount = 0;
    const tick = () => {
      frameCount++;
      moveStep("dog", frameCount);
      moveStep("cat", frameCount);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  /* ── 回来 ── */
  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    if (dog.gone) {
      timers.push(
        setTimeout(() => {
          const pos = randomPos();
          dogTarget.current = null;
          setDog((p) => ({
            ...p,
            ...pos,
            gone: false,
            action: "enter",
            clickCount: 0,
            speechBubble: pick(SPEECHES.dog.enter),
            speechVisible: true,
            trails: [],
          }));
          timers.push(setTimeout(() => setDog((p) => ({ ...p, speechVisible: false })), 2500));
          timers.push(setTimeout(() => setDog((p) => ({ ...p, action: "idle" })), 1200));
        }, GONE_DURATION),
      );
    }
    if (cat.gone) {
      timers.push(
        setTimeout(() => {
          const pos = randomPos();
          catTarget.current = null;
          setCat((p) => ({
            ...p,
            ...pos,
            gone: false,
            action: "enter",
            clickCount: 0,
            speechBubble: pick(SPEECHES.cat.enter),
            speechVisible: true,
            trails: [],
          }));
          timers.push(setTimeout(() => setCat((p) => ({ ...p, speechVisible: false })), 2500));
          timers.push(setTimeout(() => setCat((p) => ({ ...p, action: "idle" })), 1200));
        }, GONE_DURATION + 20000),
      );
    }
    return () => timers.forEach(clearTimeout);
  }, [dog.gone, cat.gone]);

  /* ── 行为逻辑 ── */
  const updateBehavior = useCallback(
    (kind: PetKind) => {
      const setter = kind === "dog" ? setDog : setCat;
      const ref = kind === "dog" ? dogRef : catRef;
      const target = kind === "dog" ? dogTarget : catTarget;
      const speeches = SPEECHES[kind];

      if (ref.current.gone) return;
      // 正在逃跑中不要打断
      if (ref.current.action === "flee") return;

      const r = Math.random();

      // 狗有时会跟着猫
      if (kind === "dog" && r < 0.15 && !catRef.current.gone) {
        target.current = { x: catRef.current.x + (Math.random() * 10 - 5), y: catRef.current.y };
        setter((p) => ({ ...p, action: "run", flipX: (target.current?.x ?? p.x) < p.x }));
        return;
      }

      if (r < 0.22) {
        target.current = randomPos();
        setter((p) => ({ ...p, action: "walk", flipX: (target.current?.x ?? p.x) < p.x }));
      } else if (r < 0.35) {
        target.current = randomPos();
        setter((p) => ({ ...p, action: "run", flipX: (target.current?.x ?? p.x) < p.x }));
      } else if (r < 0.5) {
        target.current = null;
        setter((p) => ({ ...p, action: "lick", speechBubble: pick(speeches.lick), speechVisible: true }));
        setTimeout(() => setter((p) => ({ ...p, speechVisible: false })), 2500);
      } else if (r < 0.62) {
        target.current = null;
        setter((p) => ({
          ...p,
          action: "chase_tail",
          speechBubble: pick(speeches.chase_tail),
          speechVisible: true,
        }));
        setTimeout(() => setter((p) => ({ ...p, speechVisible: false })), 2000);
      } else if (r < 0.75) {
        // 睡觉
        target.current = null;
        setter((p) => ({ ...p, action: "sleep", zzzVisible: true }));
      } else {
        target.current = null;
        setter((p) => ({ ...p, action: "idle" }));
      }
    },
    [],
  );

  /* ── 每帧移动 ── */
  const moveStep = useCallback(
    (kind: PetKind, frameCount: number) => {
      const setter = kind === "dog" ? setDog : setCat;
      const ref = kind === "dog" ? dogRef : catRef;
      const target = kind === "dog" ? dogTarget : catTarget;

      if (ref.current.gone || !target.current) return;
      const { action } = ref.current;
      if (action !== "walk" && action !== "run" && action !== "flee") return;

      const speed = action === "flee" ? FLEE_SPEED : action === "run" ? RUN_SPEED : WALK_SPEED;
      const tx = target.current.x;
      const ty = target.current.y;

      setter((p) => {
        const dx = tx - p.x;
        const dy = ty - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        // 留下脚印（每 30 帧）
        let newTrails = p.trails;
        if (action !== "flee" && frameCount % 30 === 0) {
          newTrails = [...p.trails.slice(-4), { x: p.x, y: p.y, key: ++trailKeyCounter }];
        }

        if (dist < 1.2) {
          target.current = null;
          return { ...p, action: "idle" as PetAction, trails: newTrails };
        }
        return {
          ...p,
          x: clamp(p.x + (dx / dist) * speed, 2, 93),
          y: clamp(p.y + (dy / dist) * speed, 52, 92),
          flipX: dx < -0.1,
          trails: newTrails,
        };
      });
    },
    [],
  );

  /* ── 清理过期脚印 ── */
  useEffect(() => {
    const timer = setInterval(() => {
      setDog((p) => (p.trails.length > 0 ? { ...p, trails: p.trails.slice(-3) } : p));
      setCat((p) => (p.trails.length > 0 ? { ...p, trails: p.trails.slice(-3) } : p));
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  /* ── 点击互动 ── */
  const handleClick = useCallback(
    (kind: PetKind) => {
      const setter = kind === "dog" ? setDog : setCat;
      const ref = kind === "dog" ? dogRef : catRef;
      const target = kind === "dog" ? dogTarget : catTarget;
      const maxClicks = kind === "dog" ? MAX_CLICKS_DOG : MAX_CLICKS_CAT;
      const speeches = SPEECHES[kind];

      if (ref.current.gone) return;

      const newCount = ref.current.clickCount + 1;

      // 打断了睡觉
      if (ref.current.action === "sleep") {
        setter((p) => ({ ...p, action: "idle", zzzVisible: false }));
      }

      if (newCount >= maxClicks) {
        target.current = null;
        setter((p) => ({
          ...p,
          clickCount: newCount,
          action: "flee",
          speechBubble: pick(speeches.flee),
          speechVisible: true,
          sweatVisible: true,
          zzzVisible: false,
          trails: [],
        }));
        const fleeX = Math.random() > 0.5 ? 108 : -12;
        target.current = { x: fleeX, y: ref.current.y };
        setTimeout(() => {
          setter((p) => ({ ...p, gone: true, speechVisible: false, sweatVisible: false }));
        }, 1600);
        return;
      }

      const annoyedThreshold = maxClicks - 2;
      if (newCount >= annoyedThreshold) {
        setter((p) => ({
          ...p,
          clickCount: newCount,
          action: "idle",
          sweatVisible: true,
          speechBubble: pick(speeches.annoyed),
          speechVisible: true,
          heartVisible: false,
          heartKey: p.heartKey + 1,
        }));
        setTimeout(() => setter((p) => ({ ...p, speechVisible: false, sweatVisible: false })), 1800);
      } else {
        target.current = null;
        setter((p) => ({
          ...p,
          clickCount: newCount,
          action: "idle",
          heartVisible: true,
          heartKey: p.heartKey + 1,
          speechBubble: pick(speeches.clicked),
          speechVisible: true,
        }));
        setTimeout(() => setter((p) => ({ ...p, heartVisible: false })), 1000);
        setTimeout(() => setter((p) => ({ ...p, speechVisible: false })), 2000);
      }
    },
    [],
  );

  return (
    <>
      <style>{petKeyframes}</style>
      <PetView state={dog} onClick={() => handleClick("dog")} />
      <PetView state={cat} onClick={() => handleClick("cat")} />
    </>
  );
}

/* ───────── CSS 动画 ───────── */
const petKeyframes = `
@keyframes petIdle {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}
@keyframes petWalk {
  0% { transform: translateY(0) rotate(-3deg); }
  100% { transform: translateY(-7px) rotate(3deg); }
}
@keyframes petRun {
  0% { transform: translateY(0) rotate(-6deg) scaleX(1.05); }
  100% { transform: translateY(-12px) rotate(6deg) scaleX(0.95); }
}
@keyframes petLick {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(10deg); }
  75% { transform: rotate(-10deg); }
}
@keyframes petChaseTail {
  0% { transform: rotate(0deg) scale(1); }
  25% { transform: rotate(18deg) scale(1.06); }
  50% { transform: rotate(0deg) scale(1); }
  75% { transform: rotate(-18deg) scale(1.06); }
  100% { transform: rotate(0deg) scale(1); }
}
@keyframes petSleep {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(2px) scale(0.97); }
}
@keyframes petEnter {
  0% { transform: scale(0.2); opacity: 0; }
  60% { transform: scale(1.18); opacity: 1; }
  100% { transform: scale(1); opacity: 1; }
}
@keyframes petFloatUp {
  0% { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
  100% { opacity: 0; transform: translateX(-50%) translateY(-35px) scale(1.3); }
}
@keyframes petSweatUp {
  0% { opacity: 1; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(-22px); }
}
@keyframes petFadeInUp {
  0% { opacity: 0; transform: scaleX(var(--flip,1)) translateX(-50%) translateY(8px); }
  100% { opacity: 1; transform: scaleX(var(--flip,1)) translateX(-50%) translateY(0); }
}
@keyframes petZzz {
  0%, 100% { opacity: 0.4; transform: translateY(0) scale(0.8); }
  50% { opacity: 1; transform: translateY(-8px) scale(1.1); }
}
@keyframes petTrailFade {
  0% { opacity: 0.35; }
  100% { opacity: 0; }
}
`;
