import { memo, useMemo } from "react";
import type { StarSummary, StarReward } from "../types";

function formatStarTime(dateStr: string | null): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
}

const STARS_PER_YUAN = 3;

/** 预生成每颗星的随机参数 */
function generateStarProps(count: number) {
  const props = [];
  for (let i = 0; i < count; i++) {
    props.push({
      size: 30 + Math.random() * 14,          // 30-44px
      rotate: -12 + Math.random() * 24,       // -12°~+12° 随机旋转
    });
  }
  return props;
}

/** 生成每颗星的独立 CSS 规则（纯静态立体效果） */
function buildStarCSS(props: ReturnType<typeof generateStarProps>): string {
  let css = '';
  props.forEach((p, i) => {
    css += `.sw-s${i}{display:inline-block;line-height:1;` +
      `width:${p.size.toFixed(1)}px;height:${p.size.toFixed(1)}px;` +
      `transform:rotate(${p.rotate.toFixed(1)}deg);` +
      `filter:drop-shadow(0 3px 6px rgba(0,0,0,.35)) drop-shadow(0 1px 2px rgba(180,120,0,.3));` +
      `vertical-align:middle;margin:2px;}`;
  });
  return css;
}

/** SVG 立体星星 */
function StarSVG() {
  return (
    <svg viewBox="0 0 24 24" width="100%" height="100%">
      <path d="M12 2l2.9 6.26L22 9.27l-5 4.87L18.18 22 12 18.56 5.82 22 7 14.14 2 9.27l7.1-1.01z"
        fill="url(#swStarGrad)" />
      <path d="M12 2l2.9 6.26L22 9.27l-5 4.87L18.18 22 12 18.56 5.82 22 7 14.14 2 9.27l7.1-1.01z"
        fill="url(#swStarHi)" />
    </svg>
  );
}

export const StarWall = memo(function StarWall({
  starSummary,
}: {
  starSummary: StarSummary | undefined;
}) {
  const totalStarCount = useMemo(() => {
    if (!starSummary) return 0;
    let count = 0;
    for (const rec of starSummary.recent_stars) count += rec.stars;
    return count;
  }, [starSummary]);

  const starProps = useMemo(() => generateStarProps(totalStarCount), [totalStarCount]);
  const starCSS = useMemo(() => buildStarCSS(starProps), [starProps]);

  if (!starSummary) {
    return (
      <div className="sw-root sw-loading">
        加载星星数据中...
      </div>
    );
  }

  const { total_stars, total_value, unredeemed_stars, unredeemed_value, recent_stars } = starSummary;

  return (
    <div className="sw-root">
      {/* 共享 SVG 渐变定义 */}
      <svg style={{ position: 'absolute', width: 0, height: 0 }}>
        <defs>
          <linearGradient id="swStarGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ffe066" />
            <stop offset="40%" stopColor="#fbbf24" />
            <stop offset="100%" stopColor="#d97706" />
          </linearGradient>
          <linearGradient id="swStarHi" x1="0%" y1="0%" x2="50%" y2="60%">
            <stop offset="0%" stopColor="#fff8e1" stopOpacity={0.7} />
            <stop offset="100%" stopColor="#fff8e1" stopOpacity={0} />
          </linearGradient>
        </defs>
      </svg>

      {/* 背景光晕层 */}
      <div className="sw-glow" />

      {/* header */}
      <div className="sw-header">
        <span className="sw-header-icon">⭐</span>
        <span className="sw-header-title">星星墙</span>
        {total_stars > 0 && <span className="sw-header-badge">继续努力 ⭐</span>}
      </div>

      {/* summary cards */}
      <div className="sw-cards">
        <div className="sw-card sw-card-gold">
          <div className="sw-card-deco" />
          <div className="sw-card-label">总星星数</div>
          <div className="sw-card-num">{total_stars}<span className="sw-card-unit">颗</span></div>
        </div>
        <div className="sw-card sw-card-green">
          <div className="sw-card-deco" />
          <div className="sw-card-label">可兑换</div>
          <div className="sw-card-num">{unredeemed_value}<span className="sw-card-unit">元</span></div>
          <div className="sw-card-sub">{unredeemed_stars} 颗未兑换</div>
        </div>
        <div className="sw-card sw-card-purple">
          <div className="sw-card-deco" />
          <div className="sw-card-label">累计价值</div>
          <div className="sw-card-num">{total_value}<span className="sw-card-unit">元</span></div>
        </div>
      </div>

      {/* star grid */}
      {totalStarCount > 0 ? (
        <div className="sw-grid">
          <div className="sw-stars">
            {starProps.map((_p, i) => (
              <span key={i} className={`sw-s${i}`}><StarSVG /></span>
            ))}
          </div>
        </div>
      ) : (
        <div className="sw-empty">
          <span className="sw-empty-icon">⭐</span>
          <div>完成学习计划就能获得星星哦</div>
          <div className="sw-empty-sub">每颗星星可兑换 {STARS_PER_YUAN} 元</div>
        </div>
      )}

      {/* recent records */}
      {recent_stars.length > 0 && (
        <div className="sw-recent">
          <div className="sw-recent-title">🏆 最近获得</div>
          <div className="sw-recent-list">
            {recent_stars.slice(0, 10).map((rec: StarReward, ri: number) => (
              <div key={rec.id} className={`sw-rec${ri === 0 ? " sw-rec-new" : ""}${rec.redeemed === 1 ? " sw-rec-redeemed" : ""}`}>
                <div className="sw-rec-avatar">⭐</div>
                <div className="sw-rec-count">+{rec.stars}</div>
                <div className="sw-rec-info">
                  <div className="sw-rec-reason">{rec.reason || "学习奖励"}</div>
                  <div className="sw-rec-meta">{rec.awarded_by} · {formatStarTime(rec.created_at)}</div>
                </div>
                {rec.redeemed === 1
                  ? <span className="sw-rec-tag-green">已兑换 ✓</span>
                  : ri === 0 && <span className="sw-rec-tag-new">NEW</span>
                }
              </div>
            ))}
          </div>
        </div>
      )}

      <style>{`
        /* ── root ── */
        .sw-root {
          border-radius: 20px; padding: 20px 24px; position: relative;
          display: flex; flex-direction: column; gap: 16px; min-height: 60vh;
          overflow: hidden;
        }
        .sw-loading {
          background: transparent; text-align: center; color: rgba(255,255,255,0.5);
          padding: 24px;
        }

        /* ── 背景光晕（静态） ── */
        .sw-glow {
          position: absolute; inset: -40px; pointer-events: none; z-index: 0;
          background: radial-gradient(ellipse at 50% 30%,
            rgba(251,191,36,.1) 0%,
            rgba(168,85,247,.05) 40%,
            transparent 70%);
        }

        /* ── header ── */
        .sw-header { display: flex; align-items: center; gap: 12px; position: relative; z-index: 1; }
        .sw-header-icon { font-size: 28px; }
        .sw-header-title { font-size: 22px; font-weight: 700; color: #fff;
          text-shadow: 0 0 16px rgba(251,191,36,.4), 0 2px 8px rgba(251,191,36,.3); letter-spacing: 1px; }
        .sw-header-badge { font-size: 12px; color: rgba(251,191,36,.85);
          background: rgba(251,191,36,.12); padding: 3px 10px; border-radius: 20px;
          font-weight: 500; margin-left: auto;
          box-shadow: 0 0 8px rgba(251,191,36,.2); }

        /* ── cards ── */
        .sw-cards { display: flex; gap: 12px; flex-wrap: wrap; position: relative; z-index: 1; }
        .sw-card { flex: 1; min-width: 120px; border-radius: 16px; padding: 16px 18px;
          position: relative; overflow: hidden; }
        .sw-card-deco { position: absolute; top: -20px; right: -20px; width: 80px; height: 80px;
          border-radius: 50%; background: rgba(255,255,255,.12); }
        .sw-card-label { font-size: 12px; color: rgba(255,255,255,.9); font-weight: 500;
          text-transform: uppercase; letter-spacing: 1px; }
        .sw-card-num { font-size: 36px; font-weight: 800; color: #fff; line-height: 1.2;
          text-shadow: 0 2px 4px rgba(0,0,0,.15); }
        .sw-card-unit { font-size: 14px; font-weight: 500; margin-left: 4px; opacity: .85; }
        .sw-card-sub { font-size: 11px; color: rgba(255,255,255,.8); margin-top: 4px; }
        .sw-card-gold { background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%);
          box-shadow: 0 4px 20px rgba(245,158,11,.35); }
        .sw-card-green { background: linear-gradient(135deg, #34d399 0%, #10b981 50%, #059669 100%);
          box-shadow: 0 4px 20px rgba(16,185,129,.35); }
        .sw-card-purple { background: linear-gradient(135deg, #a78bfa 0%, #7c3aed 50%, #6d28d9 100%);
          box-shadow: 0 4px 20px rgba(124,58,237,.35); }

        /* ── empty ── */
        .sw-empty { text-align: center; color: rgba(255,255,255,.5); padding: 48px 0;
          font-size: 16px; position: relative; z-index: 1; }
        .sw-empty-icon { font-size: 56px; opacity: .6; display: block; margin-bottom: 8px; }
        .sw-empty-sub { font-size: 13px; color: rgba(255,255,255,.35); margin-top: 4px; }

        /* ── 星星网格 ── */
        .sw-grid {
          position: relative; overflow: hidden; border-radius: 16px;
          padding: 16px 20px; min-height: 100px;
          background: rgba(255,255,255,.03);
          border: 1px solid rgba(251,191,36,.08);
          z-index: 1;
        }
        .sw-stars {
          word-break: break-all;
          line-height: 1.8;
          letter-spacing: 4px;
          display: flex; flex-wrap: wrap; align-items: center; gap: 4px 6px;
        }

        /* ── recent records ── */
        .sw-recent { margin-top: auto; position: relative; z-index: 1; }
        .sw-recent-title { font-size: 14px; font-weight: 600; color: rgba(255,255,255,.7);
          margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }
        .sw-recent-list { display: flex; flex-direction: column; gap: 8px; max-height: 220px;
          overflow-y: auto; padding-right: 4px; }
        .sw-rec { display: flex; align-items: center; gap: 12px;
          background: rgba(255,255,255,.04); border-radius: 12px; padding: 10px 14px;
          border: 1px solid transparent; }
        .sw-rec-new {
          background: linear-gradient(90deg, rgba(251,191,36,.15) 0%, rgba(251,191,36,.04) 100%);
          border-color: rgba(251,191,36,.35);
          box-shadow: 0 0 12px rgba(251,191,36,.15);
        }
        .sw-rec-redeemed { opacity: .65; }
        .sw-rec-avatar { width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
          background: linear-gradient(135deg, rgba(251,191,36,.2) 0%, rgba(245,158,11,.1) 100%);
          display: flex; align-items: center; justify-content: center; font-size: 18px; }
        .sw-rec-count { font-size: 20px; font-weight: 800; color: #fbbf24; min-width: 36px;
          text-shadow: 0 0 8px rgba(251,191,36,.3); }
        .sw-rec-info { flex: 1; min-width: 0; }
        .sw-rec-reason { font-size: 14px; color: #fff; font-weight: 500;
          overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .sw-rec-meta { font-size: 11px; color: rgba(255,255,255,.45); margin-top: 2px; }
        .sw-rec-tag-green { font-size: 11px; color: #34d399; background: rgba(52,211,153,.12);
          padding: 3px 8px; border-radius: 6px; font-weight: 600; white-space: nowrap; }
        .sw-rec-tag-new { font-size: 10px; color: #fbbf24; background: rgba(251,191,36,.15);
          padding: 3px 8px; border-radius: 6px; font-weight: 700; letter-spacing: .5px;
          box-shadow: 0 0 8px rgba(251,191,36,.25); }

        /* ── 每颗星独立规则（动态生成） ── */
        ${starCSS}
      `}</style>
    </div>
  );
});
