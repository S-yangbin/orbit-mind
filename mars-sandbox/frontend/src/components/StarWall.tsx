import { memo } from "react";
import type { StarSummary, StarReward } from "../types";

/** 根据 created_at 格式化显示时间 */
function formatStarTime(dateStr: string | null): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  const month = d.getMonth() + 1;
  const day = d.getDate();
  const h = d.getHours().toString().padStart(2, "0");
  const m = d.getMinutes().toString().padStart(2, "0");
  return `${month}/${day} ${h}:${m}`;
}

export const StarWall = memo(function StarWall({
  starSummary,
}: {
  starSummary: StarSummary | undefined;
}) {
  if (!starSummary) {
    return (
      <div style={{
        borderRadius: 16,
        padding: "20px 24px",
        background: "rgba(255,255,255,0.08)",
        backdropFilter: "blur(12px)",
        textAlign: "center",
        color: "rgba(255,255,255,0.5)",
      }}>
        加载星星数据中...
      </div>
    );
  }

  const { total_stars, total_value, unredeemed_stars, unredeemed_value, recent_stars } = starSummary;

  // Build star grid: each star record expands into individual star icons
  const starIcons: { id: number; awarded_by: string; reason: string | null; created_at: string | null }[] = [];
  for (const record of recent_stars) {
    for (let i = 0; i < record.stars; i++) {
      starIcons.push({
        id: record.id,
        awarded_by: record.awarded_by,
        reason: record.reason,
        created_at: record.created_at,
      });
    }
  }

  return (
    <div style={{
      borderRadius: 16,
      padding: "20px 24px",
      background: "rgba(255,255,255,0.08)",
      backdropFilter: "blur(12px)",
      display: "flex",
      flexDirection: "column",
      gap: 16,
      minHeight: "60vh",
    }}>
      {/* Header: totals */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
        <span style={{ fontSize: 24 }}>⭐</span>
        <span style={{
          fontSize: 20,
          fontWeight: 700,
          color: "#fff",
          textShadow: "0 1px 4px rgba(0,0,0,0.3)",
        }}>
          星星墙
        </span>
      </div>

      {/* Summary cards */}
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <div style={{
          flex: 1,
          minWidth: 120,
          background: "linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)",
          borderRadius: 14,
          padding: "14px 18px",
          boxShadow: "0 4px 16px rgba(245,158,11,0.3)",
        }}>
          <div style={{ fontSize: 13, color: "rgba(255,255,255,0.85)", fontWeight: 500 }}>
            总星星数
          </div>
          <div style={{ fontSize: 32, fontWeight: 800, color: "#fff", lineHeight: 1.2 }}>
            {total_stars}
            <span style={{ fontSize: 14, fontWeight: 500, marginLeft: 4 }}>颗</span>
          </div>
        </div>
        <div style={{
          flex: 1,
          minWidth: 120,
          background: "linear-gradient(135deg, #34d399 0%, #10b981 100%)",
          borderRadius: 14,
          padding: "14px 18px",
          boxShadow: "0 4px 16px rgba(16,185,129,0.3)",
        }}>
          <div style={{ fontSize: 13, color: "rgba(255,255,255,0.85)", fontWeight: 500 }}>
            可兑换
          </div>
          <div style={{ fontSize: 32, fontWeight: 800, color: "#fff", lineHeight: 1.2 }}>
            {unredeemed_value}
            <span style={{ fontSize: 14, fontWeight: 500, marginLeft: 4 }}>元</span>
          </div>
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.75)", marginTop: 2 }}>
            {unredeemed_stars} 颗未兑换
          </div>
        </div>
        <div style={{
          flex: 1,
          minWidth: 120,
          background: "linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%)",
          borderRadius: 14,
          padding: "14px 18px",
          boxShadow: "0 4px 16px rgba(124,58,237,0.3)",
        }}>
          <div style={{ fontSize: 13, color: "rgba(255,255,255,0.85)", fontWeight: 500 }}>
            累计价值
          </div>
          <div style={{ fontSize: 32, fontWeight: 800, color: "#fff", lineHeight: 1.2 }}>
            {total_value}
            <span style={{ fontSize: 14, fontWeight: 500, marginLeft: 4 }}>元</span>
          </div>
        </div>
      </div>

      {/* Star grid visualization */}
      {starIcons.length === 0 ? (
        <div style={{
          textAlign: "center",
          color: "rgba(255,255,255,0.5)",
          padding: "40px 0",
          fontSize: 16,
        }}>
          完成学习计划就能获得星星哦 ⭐
        </div>
      ) : (
        <div style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 6,
          justifyContent: "flex-start",
          alignContent: "flex-start",
          padding: "8px 0",
        }}>
          {starIcons.map((icon, idx) => (
            <div
              key={`${icon.id}-${idx}`}
              title={`${icon.reason || "奖励"} - ${icon.awarded_by} ${formatStarTime(icon.created_at)}`}
              style={{
                width: 28,
                height: 28,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 20,
                filter: "drop-shadow(0 1px 2px rgba(245,158,11,0.4))",
                animation: `starFadeIn 0.3s ease ${Math.min(idx * 0.03, 1)}s both`,
              }}
            >
              ⭐
            </div>
          ))}
        </div>
      )}

      {/* Recent records */}
      {recent_stars.length > 0 && (
        <div style={{ marginTop: "auto" }}>
          <div style={{
            fontSize: 14,
            fontWeight: 600,
            color: "rgba(255,255,255,0.7)",
            marginBottom: 8,
          }}>
            最近获得
          </div>
          <div style={{
            display: "flex",
            flexDirection: "column",
            gap: 6,
            maxHeight: 160,
            overflowY: "auto",
          }}>
            {recent_stars.slice(0, 10).map((record: StarReward) => (
              <div
                key={record.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  background: "rgba(255,255,255,0.06)",
                  borderRadius: 10,
                  padding: "8px 12px",
                }}
              >
                <span style={{ fontSize: 16 }}>⭐</span>
                <span style={{
                  fontSize: 18,
                  fontWeight: 700,
                  color: "#fbbf24",
                  minWidth: 28,
                }}>
                  +{record.stars}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontSize: 13,
                    color: "#fff",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}>
                    {record.reason || "学习奖励"}
                  </div>
                  <div style={{ fontSize: 11, color: "rgba(255,255,255,0.45)" }}>
                    {record.awarded_by} · {formatStarTime(record.created_at)}
                  </div>
                </div>
                {record.redeemed === 1 && (
                  <span style={{
                    fontSize: 10,
                    color: "#34d399",
                    background: "rgba(52,211,153,0.15)",
                    padding: "2px 6px",
                    borderRadius: 4,
                    fontWeight: 500,
                  }}>
                    已兑换
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Inline keyframes for star animation */}
      <style>{`
        @keyframes starFadeIn {
          from { opacity: 0; transform: scale(0.5) translateY(-8px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }
      `}</style>
    </div>
  );
});
