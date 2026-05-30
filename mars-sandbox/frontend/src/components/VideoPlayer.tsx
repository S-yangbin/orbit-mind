import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Spin, Button, Space, Tag, Typography, Tabs, Input, message, Popconfirm,
  Select, Tooltip, Progress, Card, Empty,
} from "antd";
import {
  ArrowLeftOutlined, PlayCircleOutlined, PauseCircleOutlined,
  StepForwardOutlined, StepBackwardOutlined, ReloadOutlined,
  PlusOutlined, EditOutlined, DeleteOutlined, CheckCircleFilled,
  StarFilled, StarOutlined, RedoOutlined,
} from "@ant-design/icons";
import { fetchVideo, getStreamUrl, processVideo } from "../api/videos";
import {
  updateSegment, createSegment, deleteSegment, upsertNote, updateProgress,
} from "../api/videos";
import type { VideoInfo, VideoSegmentInfo } from "../types";
import { useIsMobile } from "../hooks/useIsMobile";

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const TYPE_COLORS: Record<string, string> = {
  intro: "#1890ff",
  qa: "#52c41a",
  explanation: "#722ed1",
  outro: "#fa8c16",
  other: "#8c8c8c",
};

const TYPE_LABELS: Record<string, string> = {
  intro: "导入",
  qa: "问答",
  explanation: "讲解",
  outro: "结语",
  other: "其他",
};

function formatTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
}

export function VideoPlayer() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const isMobile = useIsMobile();

  const [video, setVideo] = useState<VideoInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [loopSegment, setLoopSegment] = useState<number | null>(null); // segment id for loop
  const [playbackRate, setPlaybackRate] = useState(1);
  const [noteText, setNoteText] = useState("");
  const [editingSegment, setEditingSegment] = useState<number | null>(null);
  const [editValues, setEditValues] = useState<Partial<VideoSegmentInfo>>({});
  const [showAddSegment, setShowAddSegment] = useState(false);
  const [newSegment, setNewSegment] = useState({ title: "", segment_type: "qa", start_time: 0, end_time: 0 });

  const loadVideo = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const v = await fetchVideo(Number(id));
      setVideo(v);
      // Load note for first segment
      if (v.segments.length > 0 && v.segments[0].notes.length > 0) {
        setNoteText(v.segments[0].notes[0].content);
      }
    } catch {
      message.error("加载视频失败");
    }
    setLoading(false);
  }, [id]);

  useEffect(() => {
    loadVideo();
  }, [loadVideo]);

  // Auto-refresh when processing
  useEffect(() => {
    if (video && (video.status === "processing" || video.status === "pending")) {
      const timer = setInterval(loadVideo, 5000);
      return () => clearInterval(timer);
    }
  }, [video, loadVideo]);

  // Time update — use callback ref so listeners attach immediately when <video> mounts
  const videoCallbackRef = useCallback((node: HTMLVideoElement | null) => {
    // Clean up old element
    const old = videoRef.current;
    if (old) {
      old.removeEventListener("timeupdate", onTimeUpdate);
      old.removeEventListener("loadedmetadata", onDurationLoad);
      old.removeEventListener("play", onPlayEvent);
      old.removeEventListener("pause", onPauseEvent);
    }
    videoRef.current = node;
    if (node) {
      node.addEventListener("timeupdate", onTimeUpdate);
      node.addEventListener("loadedmetadata", onDurationLoad);
      node.addEventListener("play", onPlayEvent);
      node.addEventListener("pause", onPauseEvent);
      // Sync initial state
      setCurrentTime(node.currentTime);
      if (node.duration && !isNaN(node.duration)) setDuration(node.duration);
      setIsPlaying(!node.paused);
    }
  }, []);

  // Stable event handler functions (read from ref, not closure)
  function onTimeUpdate() {
    if (videoRef.current) setCurrentTime(videoRef.current.currentTime);
  }
  function onDurationLoad() {
    if (videoRef.current) setDuration(videoRef.current.duration);
  }
  function onPlayEvent() { setIsPlaying(true); }
  function onPauseEvent() { setIsPlaying(false); }

  /** Read current playback time directly from the video element (fallback to state) */
  const getCurrentVideoTime = useCallback(() => {
    return videoRef.current?.currentTime ?? 0;
  }, []);

  // Loop logic
  useEffect(() => {
    const el = videoRef.current;
    if (!el || loopSegment === null) return;
    const seg = video?.segments.find((s) => s.id === loopSegment);
    if (!seg) return;
    const checkLoop = () => {
      if (el.currentTime >= seg.end_time) {
        el.currentTime = seg.start_time;
        el.play();
      }
      if (el.currentTime < seg.start_time) {
        el.currentTime = seg.start_time;
      }
    };
    el.addEventListener("timeupdate", checkLoop);
    return () => el.removeEventListener("timeupdate", checkLoop);
  }, [loopSegment, video]);

  // Find current segment
  const currentSegment = video?.segments.find(
    (s) => currentTime >= s.start_time && currentTime <= s.end_time
  );

  // Update note when segment changes
  useEffect(() => {
    if (currentSegment?.notes.length) {
      setNoteText(currentSegment.notes[0].content);
    } else {
      setNoteText("");
    }
  }, [currentSegment?.id]);

  const seekTo = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      videoRef.current.play();
    }
  };

  const togglePlay = () => {
    if (videoRef.current) {
      if (videoRef.current.paused) videoRef.current.play();
      else videoRef.current.pause();
    }
  };

  const goNext = () => {
    if (!video || video.segments.length === 0) return;
    const t = videoRef.current?.currentTime ?? currentTime;
    // Find first segment that starts after current time
    const idx = video.segments.findIndex((s) => s.start_time > t);
    const target = idx >= 0 ? video.segments[idx] : video.segments[0];
    if (target) seekTo(target.start_time);
  };

  const goPrev = () => {
    if (!video || video.segments.length === 0) return;
    const t = videoRef.current?.currentTime ?? currentTime;
    // Find last segment that ends before current time
    let idx = -1;
    for (let i = video.segments.length - 1; i >= 0; i--) {
      if (video.segments[i].end_time < t) {
        idx = i;
        break;
      }
    }
    const target = idx >= 0 ? video.segments[idx] : video.segments[video.segments.length - 1];
    if (target) seekTo(target.start_time);
  };

  const toggleLoop = (segId: number) => {
    setLoopSegment(loopSegment === segId ? null : segId);
  };

  // --- Segment editing ---
  const startEdit = (seg: VideoSegmentInfo) => {
    setEditingSegment(seg.id);
    setEditValues({ title: seg.title, segment_type: seg.segment_type, start_time: seg.start_time, end_time: seg.end_time });
  };

  const saveEdit = async (segId: number) => {
    try {
      // Filter out null values to match SegmentUpdateData type
      const data: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(editValues)) {
        if (v !== null && v !== undefined) data[k] = v;
      }
      await updateSegment(segId, data as Parameters<typeof updateSegment>[1]);
      message.success("分段已更新");
      setEditingSegment(null);
      loadVideo();
    } catch {
      message.error("更新失败");
    }
  };

  const cancelEdit = () => {
    setEditingSegment(null);
    setEditValues({});
  };

  const handleAddSegment = async () => {
    if (!video) return;
    if (!newSegment.title.trim()) { message.warning("请输入标题"); return; }
    try {
      await createSegment(video.id, newSegment);
      message.success("分段已添加");
      setShowAddSegment(false);
      setNewSegment({ title: "", segment_type: "qa", start_time: 0, end_time: 0 });
      loadVideo();
    } catch {
      message.error("添加失败");
    }
  };

  const handleDeleteSegment = async (segId: number) => {
    try {
      await deleteSegment(segId);
      message.success("分段已删除");
      loadVideo();
    } catch {
      message.error("删除失败");
    }
  };

  const handleSaveNote = async () => {
    if (!currentSegment) return;
    try {
      await upsertNote(currentSegment.id, noteText);
      message.success("笔记已保存");
      // Update local timestamp without full page reload
      setVideo((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          segments: prev.segments.map((s) =>
            s.id === currentSegment.id
              ? { ...s, notes: [{ ...s.notes[0], content: noteText, updated_at: new Date().toISOString() }] }
              : s
          ),
        };
      });
    } catch {
      message.error("保存笔记失败");
    }
  };

  const toggleMastered = async (seg: VideoSegmentInfo) => {
    const newMastered = seg.progress?.mastered ? 0 : 1;
    try {
      await updateProgress(seg.id, { mastered: newMastered });
      // Update local state directly to avoid full-page spinner flash
      setVideo((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          segments: prev.segments.map((s) =>
            s.id === seg.id
              ? { ...s, progress: { ...s.progress, mastered: newMastered, segment_id: seg.id, id: s.progress?.id ?? 0, loop_count: s.progress?.loop_count ?? 0, last_practiced_at: new Date().toISOString() } }
              : s
          ),
        };
      });
    } catch {
      message.error("操作失败");
    }
  };

  const handleRetry = async () => {
    if (!video) return;
    try {
      await processVideo(video.id);
      message.success("已重新开始处理");
      // Update local state directly to avoid full-page spinner flash
      setVideo({ ...video, status: "processing", error_message: "" });
    } catch {
      message.error("重试失败");
    }
  };

  if (loading) {
    return <div style={{ textAlign: "center", padding: "80px 0" }}><Spin size="large" /></div>;
  }

  if (!video) {
    return <Empty description="视频不存在" />;
  }

  const masteredCount = video.segments.filter((s) => s.progress?.mastered).length;
  const segCount = video.segments.length;
  const progressPct = segCount > 0 ? Math.round((masteredCount / segCount) * 100) : 0;

  return (
    <div style={{
      height: isMobile ? "auto" : "calc(100vh - 112px)",
      display: "flex",
      flexDirection: isMobile ? "column" : "row",
      gap: isMobile ? 12 : 16,
    }}>
      {/* LEFT: Video player */}
      <div style={{ flex: isMobile ? undefined : 1, display: "flex", flexDirection: "column", gap: 8 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/videos")} style={{ alignSelf: "flex-start" }}>
          返回列表
        </Button>

        {video.status === "processing" || video.status === "pending" ? (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: "#000", borderRadius: 8, color: "#fff" }}>
            <Spin size="large" />
            <Text style={{ color: "#fff", marginTop: 16 }}>
              {video.status === "pending" ? "等待处理..." : "正在分析视频，请稍候..."}
            </Text>
            <Text style={{ color: "#aaa", fontSize: 12, marginTop: 8 }}>
              系统正在提取音频、进行语音识别和智能分段
            </Text>
          </div>
        ) : video.status === "error" ? (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: "#000", borderRadius: 8, color: "#fff", gap: 16 }}>
            <Text type="danger" style={{ color: "#ff4d4f", fontSize: 16 }}>处理失败</Text>
            <Text style={{ color: "#aaa", fontSize: 12, maxWidth: 400, textAlign: "center" }}>{video.error_message}</Text>
            <Space>
              <Button icon={<RedoOutlined />} onClick={handleRetry}>重试处理</Button>
              <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/videos")}>返回列表</Button>
            </Space>
          </div>
        ) : (
          <div style={{ background: "#000", borderRadius: 8, overflow: "hidden", position: "relative" }}>
            <video
              ref={videoCallbackRef}
              src={video.oss_url || getStreamUrl(video.id)}
              style={{ width: "100%", maxHeight: "100%", display: "block" }}
              controls
              preload="auto"
            />

            {/* Custom timeline with segment markers */}
            {duration > 0 && video.segments.length > 0 && (
              <div style={{
                display: "flex", height: 6, background: "#333",
                marginTop: -4, position: "relative", zIndex: 1,
              }}>
                {video.segments.map((seg) => (
                  <Tooltip key={seg.id} title={`${seg.title} (${formatTime(seg.start_time)}-${formatTime(seg.end_time)})`}>
                    <div
                      style={{
                        width: `${((seg.end_time - seg.start_time) / duration) * 100}%`,
                        height: "100%",
                        background: TYPE_COLORS[seg.segment_type] || "#666",
                        cursor: "pointer",
                        opacity: currentTime >= seg.start_time && currentTime <= seg.end_time ? 1 : 0.5,
                        transition: "opacity 0.2s",
                      }}
                      onClick={() => seekTo(seg.start_time)}
                    />
                  </Tooltip>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Playback controls */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <Button icon={<StepBackwardOutlined />} onClick={goPrev} size="small">上一段</Button>
          <Button
            type="primary"
            icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={togglePlay}
            size="small"
          >
            {isPlaying ? "暂停" : "播放"}
          </Button>
          <Button icon={<StepForwardOutlined />} onClick={goNext} size="small">下一段</Button>
          <Select
            value={playbackRate}
            onChange={(v) => {
              setPlaybackRate(v);
              if (videoRef.current) videoRef.current.playbackRate = v;
            }}
            size="small"
            style={{ width: 80 }}
            options={[0.5, 0.75, 1, 1.25, 1.5, 2].map((r) => ({ label: `${r}x`, value: r }))}
          />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {formatTime(currentTime)} / {formatTime(duration)}
          </Text>
        </div>
      </div>

      {/* RIGHT: Segments / Notes / Controls panel */}
      <div style={{ width: isMobile ? "100%" : 360, display: "flex", flexDirection: "column", gap: 8 }}>
        <Card size="small">
          <Title level={5} style={{ margin: 0 }}>{video.title}</Title>
          {segCount > 0 && (
            <Progress percent={progressPct} size="small" style={{ marginTop: 8 }}
              format={() => `${masteredCount}/${segCount} 已掌握`}
              strokeColor="#52c41a"
            />
          )}
        </Card>

        <Tabs
          defaultActiveKey="segments"
          size="small"
          style={{ flex: 1 }}
          items={[
            {
              key: "segments",
              label: `分段 (${segCount})`,
              children: (
                <div style={{ maxHeight: isMobile ? 400 : "calc(100vh - 320px)", overflowY: "auto" }}>
                  {video.segments.length === 0 ? (
                    <Empty description="暂无分段，AI 处理中或手动添加" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                  ) : (
                    video.segments.map((seg) => {
                      const isCurrent = currentTime >= seg.start_time && currentTime <= seg.end_time;
                      const isLooping = loopSegment === seg.id;
                      const isEditing = editingSegment === seg.id;

                      return (
                        <Card
                          key={seg.id}
                          size="small"
                          style={{
                            marginBottom: 8,
                            border: isCurrent ? `2px solid ${TYPE_COLORS[seg.segment_type]}` : undefined,
                            background: isLooping ? "#f6ffed" : undefined,
                          }}
                          title={
                            isEditing ? (
                              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                                <Input
                                  size="small"
                                  value={editValues.title || seg.title}
                                  onChange={(e) => setEditValues((v) => ({ ...v, title: e.target.value }))}
                                />
                                <Space>
                                  <Select
                                    size="small"
                                    value={editValues.segment_type || seg.segment_type}
                                    onChange={(v) => setEditValues((pv) => ({ ...pv, segment_type: v }))}
                                    style={{ width: 80 }}
                                    options={Object.entries(TYPE_LABELS).map(([k, l]) => ({ label: l, value: k }))}
                                  />
                                </Space>
                                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                                  <Text type="secondary" style={{ fontSize: 11, whiteSpace: "nowrap", minWidth: 52 }}>
                                    {formatTime(currentTime)}
                                  </Text>
                                  <Button
                                    size="small"
                                    onClick={() => setEditValues((v) => ({ ...v, start_time: Math.floor(getCurrentVideoTime()) }))}
                                  >
                                    设为开始
                                  </Button>
                                  <Button
                                    size="small"
                                    onClick={() => setEditValues((v) => ({ ...v, end_time: Math.floor(getCurrentVideoTime()) }))}
                                  >
                                    设为结束
                                  </Button>
                                </div>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  开始: {formatTime(editValues.start_time ?? seg.start_time)}  ·  结束: {formatTime(editValues.end_time ?? seg.end_time)}
                                </Text>
                                <Space>
                                  <Button size="small" type="primary" onClick={() => saveEdit(seg.id)}>保存</Button>
                                  <Button size="small" onClick={cancelEdit}>取消</Button>
                                </Space>
                              </div>
                            ) : (
                              <Space>
                                <span
                                  style={{ cursor: "pointer" }}
                                  onClick={() => seekTo(seg.start_time)}
                                >
                                  {seg.title}
                                </span>
                                <Tag color={TYPE_COLORS[seg.segment_type]}>
                                  {TYPE_LABELS[seg.segment_type] || seg.segment_type}
                                </Tag>
                                {seg.progress?.mastered ? (
                                  <CheckCircleFilled style={{ color: "#52c41a" }} />
                                ) : null}
                              </Space>
                            )
                          }
                          extra={
                            !isEditing && (
                              <Space size={0}>
                                <Tooltip title={isLooping ? "取消循环" : "循环播放此段"}>
                                  <Button
                                    type={isLooping ? "primary" : "text"}
                                    size="small"
                                    icon={<ReloadOutlined />}
                                    onClick={(e) => { e.stopPropagation(); toggleLoop(seg.id); }}
                                  />
                                </Tooltip>
                                <Tooltip title={seg.progress?.mastered ? "标记为未掌握" : "标记为已掌握"}>
                                  <Button
                                    type="text"
                                    size="small"
                                    icon={seg.progress?.mastered ? <StarFilled style={{ color: "#faad14" }} /> : <StarOutlined />}
                                    onClick={(e) => { e.stopPropagation(); toggleMastered(seg); }}
                                  />
                                </Tooltip>
                                <Tooltip title="编辑">
                                  <Button type="text" size="small" icon={<EditOutlined />}
                                    onClick={(e) => { e.stopPropagation(); startEdit(seg); }}
                                  />
                                </Tooltip>
                                <Popconfirm title="确定删除此分段？" onConfirm={() => handleDeleteSegment(seg.id)}>
                                  <Button type="text" size="small" danger icon={<DeleteOutlined />}
                                    onClick={(e) => e.stopPropagation()}
                                  />
                                </Popconfirm>
                              </Space>
                            )
                          }
                        >
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {formatTime(seg.start_time)} - {formatTime(seg.end_time)}
                          </Text>
                          {seg.transcription && (
                            <Paragraph
                              ellipsis={{ rows: 2, expandable: true, symbol: "展开" }}
                              style={{ marginTop: 4, fontSize: 12, color: "#666" }}
                            >
                              {seg.transcription}
                            </Paragraph>
                          )}
                        </Card>
                      );
                    })
                  )}

                  {/* Add segment form */}
                  {showAddSegment ? (
                    <Card size="small" style={{ marginBottom: 8 }}>
                      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                        <Input
                          size="small" placeholder="分段标题"
                          value={newSegment.title}
                          onChange={(e) => setNewSegment((v) => ({ ...v, title: e.target.value }))}
                        />
                        <Space>
                          <Select size="small" style={{ width: 80 }} value={newSegment.segment_type}
                            onChange={(v) => setNewSegment((pv) => ({ ...pv, segment_type: v }))}
                            options={Object.entries(TYPE_LABELS).map(([k, l]) => ({ label: l, value: k }))}
                          />
                        </Space>
                        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                          <Text type="secondary" style={{ fontSize: 11, whiteSpace: "nowrap", minWidth: 52 }}>
                            当前位置: {formatTime(currentTime)}
                          </Text>
                          <Button
                            size="small"
                            onClick={() => setNewSegment((v) => ({ ...v, start_time: Math.floor(getCurrentVideoTime()) }))}
                          >
                            设为开始
                          </Button>
                          <Button
                            size="small"
                            onClick={() => setNewSegment((v) => ({ ...v, end_time: Math.floor(getCurrentVideoTime()) }))}
                          >
                            设为结束
                          </Button>
                        </div>
                        <Space>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            开始: {formatTime(newSegment.start_time)}
                          </Text>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            结束: {formatTime(newSegment.end_time)}
                          </Text>
                        </Space>
                        <Space>
                          <Button size="small" type="primary" onClick={handleAddSegment}>添加</Button>
                          <Button size="small" onClick={() => setShowAddSegment(false)}>取消</Button>
                        </Space>
                      </div>
                    </Card>
                  ) : (
                    <Button
                      type="dashed" block icon={<PlusOutlined />}
                      onClick={() => {
                        setNewSegment({ title: "", segment_type: "qa", start_time: Math.floor(getCurrentVideoTime()), end_time: Math.floor(getCurrentVideoTime()) + 30 });
                        setShowAddSegment(true);
                      }}
                    >
                      手动添加分段
                    </Button>
                  )}
                </div>
              ),
            },
            {
              key: "notes",
              label: "笔记",
              children: (
                <div>
                  {currentSegment ? (
                    <div>
                      <Text strong>{currentSegment.title}</Text>
                      <Tag color={TYPE_COLORS[currentSegment.segment_type]} style={{ marginLeft: 8 }}>
                        {TYPE_LABELS[currentSegment.segment_type]}
                      </Tag>
                      <TextArea
                        rows={10}
                        value={noteText}
                        onChange={(e) => setNoteText(e.target.value)}
                        placeholder="为当前分段添加学习笔记..."
                        style={{ marginTop: 12 }}
                      />
                      <Button type="primary" onClick={handleSaveNote} style={{ marginTop: 8 }} block>
                        保存笔记
                      </Button>
                      {currentSegment.notes.length > 0 && (
                        <div style={{ marginTop: 12 }}>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            上次保存：{new Date(currentSegment.notes[0].updated_at).toLocaleString("zh-CN")}
                          </Text>
                        </div>
                      )}
                    </div>
                  ) : (
                    <Empty description="播放视频时自动显示当前分段笔记" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                  )}
                </div>
              ),
            },
            {
              key: "controls",
              label: "播放控制",
              children: (
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <Card size="small" title="单段循环">
                    {currentSegment ? (
                      <div>
                        <Text>当前分段：{currentSegment.title}</Text>
                        <br />
                        <Button
                          type={loopSegment === currentSegment.id ? "primary" : "default"}
                          icon={<ReloadOutlined />}
                          onClick={() => toggleLoop(currentSegment.id)}
                          style={{ marginTop: 8 }}
                          block
                        >
                          {loopSegment === currentSegment.id ? "取消循环" : "循环播放当前分段"}
                        </Button>
                      </div>
                    ) : (
                      <Text type="secondary">请先播放视频</Text>
                    )}
                  </Card>

                  <Card size="small" title="播放速度">
                    <Select
                      value={playbackRate}
                      onChange={(v) => {
                        setPlaybackRate(v);
                        if (videoRef.current) videoRef.current.playbackRate = v;
                      }}
                      style={{ width: "100%" }}
                      options={[0.5, 0.75, 1, 1.25, 1.5, 2].map((r) => ({ label: `${r}x`, value: r }))}
                    />
                  </Card>

                  <Card size="small" title="快捷操作">
                    <Space direction="vertical" style={{ width: "100%" }}>
                      <Button icon={<StepBackwardOutlined />} onClick={goPrev} block>上一段</Button>
                      <Button icon={<StepForwardOutlined />} onClick={goNext} block>下一段</Button>
                    </Space>
                  </Card>
                </div>
              ),
            },
          ]}
        />
      </div>
    </div>
  );
}