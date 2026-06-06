import { useState, useEffect, useCallback } from "react";
import {
  Button,
  Table,
  Upload,
  Input,
  Space,
  message,
  Progress,
  Empty,
  Card,
  Typography,
  Tooltip,
  Tag,
  Modal,
  Image,
  Pagination,
  Spin,
  Breadcrumb,
  Dropdown,
  Select,
} from "antd";
import {
  CloudUploadOutlined,
  CloudDownloadOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  InboxOutlined,
  FileOutlined,
  FileImageOutlined,
  FilePdfOutlined,
  FileZipOutlined,
  FileExcelOutlined,
  FileTextOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  FolderOutlined,
  FolderOpenOutlined,
  FolderAddOutlined,
  DragOutlined,
  CopyOutlined,
  HomeOutlined,
  MoreOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import type { MenuProps } from "antd";
import dayjs from "dayjs";
import { useIsMobile } from "../hooks/useIsMobile";
import { formatSize } from "../utils";
import {
  fetchDriveFiles,
  recordDriveFile,
  deleteDriveFile,
  deleteFolder,
  getSignedDownloadUrl,
  getUploadUrl,
  fetchTextPreview,
  createFolder,
  moveFile,
  copyFile,
  fetchAllFolders,
  type DriveFileData,
  type TextPreviewData,
  type Breadcrumb as BreadcrumbType,
  type FolderInfo,
} from "../api/drive";

const { Dragger } = Upload;
const { Text } = Typography;

const PAGE_SIZE = 50;

interface UploadTask {
  name: string;
  progress: number; // 0-100
}

/** Upload a single file via XHR with progress callback. */
function uploadFileXHR(file: File, uploadUrl: string, contentType: string, onProgress: (pct: number) => void): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", uploadUrl);
    xhr.setRequestHeader("Content-Type", contentType);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => (xhr.status >= 200 && xhr.status < 300 ? resolve() : reject(new Error(`HTTP ${xhr.status}`)));
    xhr.onerror = () => reject(new Error("Network error"));
    xhr.send(file);
  });
}

const IMAGE_EXTS = ["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp", "ico"];
const TEXT_EXTS = [
  "txt", "md", "json", "csv", "tsv", "log", "xml", "html", "htm",
  "css", "js", "ts", "tsx", "jsx", "py", "sh", "yaml", "yml", "toml",
  "ini", "cfg", "conf", "env", "sql", "java", "c", "cpp", "h", "go",
  "rs", "rb", "php", "swift", "kt", "vue", "svelte", "dockerfile",
  "makefile", "gitignore", "editorconfig",
];

function getExt(filename: string): string {
  return filename.split(".").pop()?.toLowerCase() || "";
}

function isImageFile(filename: string): boolean {
  return IMAGE_EXTS.includes(getExt(filename));
}

function isTextFile(filename: string): boolean {
  const ext = getExt(filename);
  return TEXT_EXTS.includes(ext) || !filename.includes(".");
}

function isPreviewable(filename: string, isDir: number): boolean {
  return !isDir && (isImageFile(filename) || isTextFile(filename));
}

function getFileIcon(filename: string, isDir: number) {
  if (isDir) return <FolderOutlined style={{ color: "#faad14", fontSize: 18 }} />;
  const ext = getExt(filename);
  if (IMAGE_EXTS.includes(ext) || ext === "heic")
    return <FileImageOutlined style={{ color: "#52c41a" }} />;
  if (["mp4", "mov", "avi", "mkv", "webm"].includes(ext))
    return <PlayCircleOutlined style={{ color: "#1890ff" }} />;
  if (["pdf"].includes(ext))
    return <FilePdfOutlined style={{ color: "#f5222d" }} />;
  if (["zip", "rar", "7z", "tar", "gz"].includes(ext))
    return <FileZipOutlined style={{ color: "#faad14" }} />;
  if (["xlsx", "xls", "csv"].includes(ext))
    return <FileExcelOutlined style={{ color: "#52c41a" }} />;
  if (TEXT_EXTS.includes(ext))
    return <FileTextOutlined style={{ color: "#1677ff" }} />;
  return <FileOutlined style={{ color: "#8c8c8c" }} />;
}

export function CloudDrive() {
  const isMobile = useIsMobile();
  const [files, setFiles] = useState<DriveFileData[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadTasks, setUploadTasks] = useState<UploadTask[]>([]);
  const [downloadTask, setDownloadTask] = useState<{ name: string; progress: number } | null>(null);
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbType[]>([]);
  const [currentFolderId, setCurrentFolderId] = useState<number | null>(null);

  // Preview state
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewFile, setPreviewFile] = useState<DriveFileData | null>(null);
  const [previewType, setPreviewType] = useState<"image" | "text" | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [imageUrl, setImageUrl] = useState("");
  const [textData, setTextData] = useState<TextPreviewData | null>(null);

  // Folder create modal
  const [folderModalOpen, setFolderModalOpen] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [folderCreating, setFolderCreating] = useState(false);

  // Move/Copy modal
  const [moveModalOpen, setMoveModalOpen] = useState(false);
  const [moveTarget, setMoveTarget] = useState<DriveFileData | null>(null);
  const [moveMode, setMoveMode] = useState<"move" | "copy">("move");
  const [allFolders, setAllFolders] = useState<FolderInfo[]>([]);
  const [selectedFolderId, setSelectedFolderId] = useState<number | null>(null);
  const [moving, setMoving] = useState(false);

  const loadFiles = useCallback(async (
    p = page,
    q = search,
    folderId: number | null = currentFolderId,
  ) => {
    setLoading(true);
    try {
      const data = await fetchDriveFiles({
        page: p,
        page_size: PAGE_SIZE,
        q: q || undefined,
        parent_id: q ? undefined : folderId,
      });
      setFiles(data.items);
      setTotal(data.total);
      setBreadcrumbs(data.breadcrumbs || []);
    } catch {
      message.error("加载文件失败");
    } finally {
      setLoading(false);
    }
  }, [page, search, currentFolderId]);

  useEffect(() => {
    loadFiles();
  }, [loadFiles]);

  const navigateToFolder = (folderId: number | null) => {
    setCurrentFolderId(folderId);
    setPage(1);
    setSearch("");
    loadFiles(1, "", folderId);
  };

  const handleUpload = async (fileList: File[]) => {
    if (fileList.length === 0) return;
    setUploading(true);
    const tasks: UploadTask[] = fileList.map((f) => ({ name: f.name, progress: 0 }));
    setUploadTasks(tasks);

    const subPath = currentFolderId !== null
      ? breadcrumbs.map((b) => b.filename).join("/") + "/"
      : "";

    let successCount = 0;
    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i];
      const uid = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const ossKey = `clouddisk/${subPath}${uid}-${file.name}`;
      const contentType = file.type || "application/octet-stream";

      try {
        const uploadUrl = await getUploadUrl(ossKey, contentType);
        await uploadFileXHR(file, uploadUrl, contentType, (pct) => {
          setUploadTasks((prev) => prev.map((t, idx) => (idx === i ? { ...t, progress: pct } : t)));
        });
        await recordDriveFile({
          filename: file.name, oss_key: ossKey, file_size: file.size,
          content_type: contentType, parent_id: currentFolderId,
        });
        successCount++;
      } catch (err) {
        console.error("Upload failed:", file.name, err);
        message.error(`上传失败: ${file.name}`);
      }
    }

    setUploading(false);
    setUploadTasks([]);
    if (successCount > 0) {
      message.success(`已上传 ${successCount} 个文件`);
      loadFiles();
    }
  };

  const handleDownload = async (file: DriveFileData) => {
    try {
      const url = await getSignedDownloadUrl(file.oss_key);
      // Use XHR for reliable progress, then create blob URL for iOS Safari compatibility.
      const blob = await new Promise<Blob>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open("GET", url);
        xhr.responseType = "blob";
        xhr.onprogress = (e) => {
          if (e.lengthComputable) {
            setDownloadTask({ name: file.filename, progress: Math.round((e.loaded / e.total) * 100) });
          }
        };
        xhr.onload = () => xhr.status >= 200 && xhr.status < 300 ? resolve(xhr.response) : reject(new Error(`HTTP ${xhr.status}`));
        xhr.onerror = () => reject(new Error("Network error"));
        xhr.send();
      });
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = file.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
      setDownloadTask(null);
    } catch {
      message.error("下载失败");
      setDownloadTask(null);
    }
  };

  const handleDelete = async (file: DriveFileData) => {
    try {
      if (file.is_dir) {
        await deleteFolder(file.id);
      } else {
        await deleteDriveFile(file.id);
      }
      message.success(`已删除: ${file.filename}`);
      loadFiles();
    } catch {
      message.error("删除失败");
    }
  };

  const handlePreview = async (file: DriveFileData) => {
    if (file.is_dir) {
      navigateToFolder(file.id);
      return;
    }
    setPreviewFile(file);
    setPreviewOpen(true);

    if (isImageFile(file.filename)) {
      setPreviewType("image");
      setPreviewLoading(true);
      try {
        const url = await getSignedDownloadUrl(file.oss_key);
        setImageUrl(url);
      } catch {
        message.error("加载图片预览失败");
      } finally {
        setPreviewLoading(false);
      }
    } else if (isTextFile(file.filename)) {
      setPreviewType("text");
      loadTextPreview(file.oss_key, 1);
    }
  };

  const loadTextPreview = async (ossKey: string, p: number) => {
    setPreviewLoading(true);
    try {
      const data = await fetchTextPreview(ossKey, p, 200);
      setTextData(data);
    } catch {
      message.error("加载文本预览失败");
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleTextPageChange = (p: number) => {
    if (previewFile) loadTextPreview(previewFile.oss_key, p);
  };

  const closePreview = () => {
    setPreviewOpen(false);
    setPreviewFile(null);
    setPreviewType(null);
    setImageUrl("");
    setTextData(null);
  };

  const handleSearch = (value: string) => {
    setSearch(value);
    setPage(1);
    loadFiles(1, value);
  };

  // Folder creation
  const handleCreateFolder = async () => {
    const name = newFolderName.trim();
    if (!name) {
      message.warning("请输入文件夹名称");
      return;
    }
    setFolderCreating(true);
    try {
      await createFolder({ filename: name, parent_id: currentFolderId });
      message.success(`文件夹 "${name}" 创建成功`);
      setFolderModalOpen(false);
      setNewFolderName("");
      loadFiles();
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      message.error(detail || "创建文件夹失败");
    } finally {
      setFolderCreating(false);
    }
  };

  // Move/Copy
  const openMoveModal = async (file: DriveFileData, mode: "move" | "copy") => {
    setMoveTarget(file);
    setMoveMode(mode);
    setSelectedFolderId(null);
    setMoveModalOpen(true);
    try {
      const folders = await fetchAllFolders();
      // Exclude self and descendants for move
      setAllFolders(folders.filter((f) => f.id !== file.id));
    } catch {
      message.error("加载文件夹列表失败");
    }
  };

  const handleMoveOrCopy = async () => {
    if (!moveTarget) return;
    setMoving(true);
    try {
      if (moveMode === "move") {
        await moveFile(moveTarget.id, selectedFolderId);
        message.success(`已移动: ${moveTarget.filename}`);
      } else {
        await copyFile(moveTarget.id, selectedFolderId);
        message.success(`已复制: ${moveTarget.filename}`);
      }
      setMoveModalOpen(false);
      loadFiles();
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      message.error(detail || `${moveMode === "move" ? "移动" : "复制"}失败`);
    } finally {
      setMoving(false);
    }
  };

  /** Render action buttons for a file/folder row. */
  const renderActions = (record: DriveFileData, compact = false) => {
    const moreItems: MenuProps["items"] = [
      {
        key: "move",
        icon: <DragOutlined />,
        label: "移动到...",
        onClick: () => openMoveModal(record, "move"),
      },
      ...(!record.is_dir ? [{
        key: "copy",
        icon: <CopyOutlined />,
        label: "复制到...",
        onClick: () => openMoveModal(record, "copy"),
      }] : []),
      { type: "divider" as const },
      {
        key: "delete",
        icon: <DeleteOutlined />,
        label: record.is_dir ? "删除文件夹" : "删除",
        danger: true,
        onClick: () => {
          Modal.confirm({
            title: record.is_dir ? `确认删除文件夹 "${record.filename}" 及其所有内容？` : `确认删除 "${record.filename}"？`,
            okText: "删除",
            okType: "danger",
            cancelText: "取消",
            onOk: () => handleDelete(record),
          });
        },
      },
    ];

    return (
      <Space size={compact ? 4 : 8}>
        {isPreviewable(record.filename, record.is_dir) && (
          <Tooltip title="预览">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined style={{ color: "#7c3aed" }} />}
              onClick={() => handlePreview(record)}
            />
          </Tooltip>
        )}
        {!record.is_dir && (
          <Tooltip title="下载">
            <Button
              type="text"
              size="small"
              icon={<CloudDownloadOutlined />}
              onClick={() => handleDownload(record)}
            />
          </Tooltip>
        )}
        <Dropdown menu={{ items: moreItems }} trigger={["click"]}>
          <Tooltip title="更多操作">
            <Button type="text" size="small" icon={<MoreOutlined />} />
          </Tooltip>
        </Dropdown>
      </Space>
    );
  };

  const columns: ColumnsType<DriveFileData> = [
    {
      title: "名称",
      dataIndex: "filename",
      key: "filename",
      ellipsis: true,
      render: (name: string, record: DriveFileData) => (
        <Space>
          {getFileIcon(name, record.is_dir)}
          <Text
            style={{
              maxWidth: isMobile ? 140 : 300,
              cursor: "pointer",
              fontWeight: record.is_dir ? 600 : undefined,
            }}
            ellipsis={{ tooltip: name }}
            onClick={() => handlePreview(record)}
          >
            {name}
          </Text>
        </Space>
      ),
    },
    {
      title: "大小",
      dataIndex: "file_size",
      key: "file_size",
      width: 100,
      render: (size: number, record: DriveFileData) =>
        record.is_dir ? <Tag color="gold">文件夹</Tag> : <Tag>{formatSize(size)}</Tag>,
      sorter: (a, b) => a.file_size - b.file_size,
    },
    {
      title: "上传时间",
      dataIndex: "created_at",
      key: "created_at",
      width: 180,
      render: (t: string) => dayjs(t).format("YYYY-MM-DD HH:mm"),
      sorter: (a, b) => dayjs(a.created_at).unix() - dayjs(b.created_at).unix(),
      defaultSortOrder: "descend",
    },
    {
      title: "操作",
      key: "actions",
      width: 140,
      render: (_: unknown, record: DriveFileData) => renderActions(record),
    },
  ];

  const mobileColumns: ColumnsType<DriveFileData> = [
    columns[0],
    {
      title: "操作",
      key: "actions",
      width: 100,
      render: (_: unknown, record: DriveFileData) => renderActions(record, true),
    },
  ];

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      {/* Breadcrumb navigation */}
      <Card
        style={{ marginBottom: 12, borderRadius: 12 }}
        styles={{ body: { padding: isMobile ? "8px 12px" : "10px 20px" } }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
          <Breadcrumb
            items={[
              {
                title: (
                  <Space
                    size={4}
                    style={{ cursor: "pointer", color: currentFolderId === null ? "#7c3aed" : "#1677ff" }}
                    onClick={() => navigateToFolder(null)}
                  >
                    <HomeOutlined />
                    <span>根目录</span>
                  </Space>
                ),
              },
              ...breadcrumbs.map((b, i) => ({
                title: (
                  <Space
                    size={4}
                    style={{
                      cursor: "pointer",
                      color: i === breadcrumbs.length - 1 ? "#7c3aed" : "#1677ff",
                      fontWeight: i === breadcrumbs.length - 1 ? 600 : 400,
                    }}
                    onClick={() => navigateToFolder(b.id)}
                  >
                    <FolderOpenOutlined />
                    <span>{b.filename}</span>
                  </Space>
                ),
              })),
            ]}
          />
          <Space>
            <Button
              icon={<FolderAddOutlined />}
              onClick={() => {
                setNewFolderName("");
                setFolderModalOpen(true);
              }}
              size="small"
            >
              {!isMobile && "新建文件夹"}
            </Button>
          </Space>
        </div>
      </Card>

      {/* Upload area */}
      <Card
        style={{ marginBottom: 16, borderRadius: 12 }}
        styles={{ body: { padding: isMobile ? 12 : 20 } }}
      >
        <Dragger
          multiple
          showUploadList={false}
          beforeUpload={(_file, fileList) => {
            if (_file === fileList[0]) {
              handleUpload(fileList as File[]);
            }
            return false;
          }}
          disabled={uploading}
          style={{
            padding: isMobile ? "12px 0" : "20px 0",
            borderRadius: 8,
            border: "2px dashed #d9d9d9",
          }}
        >
          <p style={{ marginBottom: 8 }}>
            <InboxOutlined style={{ fontSize: 36, color: "#7c3aed" }} />
          </p>
          <p style={{ fontSize: 15, fontWeight: 500, color: "#262626" }}>
            点击或拖拽文件到此区域上传
          </p>
          <p style={{ fontSize: 13, color: "#8c8c8c" }}>
            {currentFolderId
              ? `上传到: ${breadcrumbs.map((b) => b.filename).join(" / ") || "当前文件夹"}`
              : "上传到根目录"}
          </p>
        </Dragger>

        {uploading && uploadTasks.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <div style={{ marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
              <CloudUploadOutlined style={{ color: "#7c3aed", fontSize: 16 }} />
              <Text strong style={{ color: "#7c3aed" }}>
                上传中 {uploadTasks.filter((t) => t.progress >= 100).length}/{uploadTasks.length} 个文件
              </Text>
              {uploadTasks.some((t) => t.progress < 100) && <Spin size="small" />}
            </div>
            {uploadTasks.map((task, idx) => {
              const isDone = task.progress >= 100;
              const isActive = !isDone && (idx === 0 || uploadTasks[idx - 1].progress >= 100);
              return (
                <div
                  key={idx}
                  style={{
                    marginBottom: 8, padding: "6px 10px", borderRadius: 6,
                    background: isDone ? "#f6ffed" : isActive ? "#f9f0ff" : "#fafafa",
                    border: `1px solid ${isDone ? "#b7eb8f" : isActive ? "#d3adf7" : "#f0f0f0"}`,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                    <Text ellipsis style={{ maxWidth: isMobile ? 160 : 360, fontSize: 13, fontWeight: isActive ? 500 : 400 }}>
                      {isDone ? "✓ " : isActive ? "↑ " : "  "}{task.name}
                    </Text>
                    <Text style={{ fontSize: 12, color: isDone ? "#52c41a" : "#8c8c8c", minWidth: 40, textAlign: "right" }}>
                      {isDone ? "完成" : `${task.progress}%`}
                    </Text>
                  </div>
                  <Progress
                    percent={task.progress} size="small" showInfo={false}
                    strokeColor={isDone ? "#52c41a" : "#7c3aed"} trailColor="#f0f0f0"
                  />
                </div>
              );
            })}
          </div>
        )}
        {downloadTask && (
          <div style={{ marginTop: 16 }}>
            <div style={{ marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
              <CloudDownloadOutlined style={{ color: downloadTask.progress >= 100 ? "#52c41a" : "#1677ff", fontSize: 16 }} />
              <Text strong style={{ color: downloadTask.progress >= 100 ? "#52c41a" : "#1677ff" }}>
                {downloadTask.progress >= 100 ? "下载完成" : "下载中"}
              </Text>
              {downloadTask.progress < 100 && <Spin size="small" />}
            </div>
            <div style={{
              padding: "6px 10px", borderRadius: 6,
              background: downloadTask.progress >= 100 ? "#f6ffed" : "#e6f4ff",
              border: `1px solid ${downloadTask.progress >= 100 ? "#b7eb8f" : "#91caff"}`,
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                <Text ellipsis style={{ maxWidth: isMobile ? 160 : 360, fontSize: 13 }}>
                  {downloadTask.progress >= 100 ? "✓ " : "↓ "}{downloadTask.name}
                </Text>
                <Text style={{ fontSize: 12, color: downloadTask.progress >= 100 ? "#52c41a" : "#8c8c8c", minWidth: 40, textAlign: "right" }}>
                  {downloadTask.progress >= 100 ? "完成" : `${downloadTask.progress}%`}
                </Text>
              </div>
              <Progress
                percent={downloadTask.progress} size="small" showInfo={false}
                strokeColor={downloadTask.progress >= 100 ? "#52c41a" : "#1677ff"} trailColor="#f0f0f0"
              />
            </div>
          </div>
        )}
      </Card>

      {/* File list */}
      <Card
        title={
          <Space>
            <span>文件列表</span>
            <Tag color="purple">{total} 项</Tag>
          </Space>
        }
        extra={
          <Space>
            <Input.Search
              placeholder="搜索文件"
              allowClear
              onSearch={handleSearch}
              style={{ width: isMobile ? 150 : 240 }}
              prefix={<SearchOutlined />}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <Tooltip title="刷新">
              <Button icon={<ReloadOutlined />} onClick={() => loadFiles()} />
            </Tooltip>
          </Space>
        }
        style={{ borderRadius: 12 }}
        styles={{ body: { padding: 0 } }}
      >
        <Table<DriveFileData>
          rowKey="id"
          columns={isMobile ? mobileColumns : columns}
          dataSource={files}
          loading={loading}
          onRow={(record) => ({
            onDoubleClick: () => {
              if (record.is_dir) navigateToFolder(record.id);
              else if (isPreviewable(record.filename, record.is_dir)) handlePreview(record);
            },
            style: { cursor: record.is_dir ? "pointer" : "default" },
          })}
          pagination={{
            current: page,
            pageSize: PAGE_SIZE,
            total,
            showSizeChanger: false,
            onChange: (p) => {
              setPage(p);
              loadFiles(p, search);
            },
            size: isMobile ? "small" : "default",
          }}
          size={isMobile ? "small" : "middle"}
          locale={{ emptyText: <Empty description={search ? "未找到匹配文件" : "此文件夹为空"} /> }}
        />
      </Card>

      {/* Preview Modal */}
      <Modal
        open={previewOpen}
        onCancel={closePreview}
        footer={null}
        width={previewType === "image" ? undefined : isMobile ? "95vw" : 800}
        title={
          <Space>
            {previewFile && getFileIcon(previewFile.filename, previewFile.is_dir)}
            <span>{previewFile?.filename}</span>
            {previewFile && !previewFile.is_dir && <Tag>{formatSize(previewFile.file_size)}</Tag>}
          </Space>
        }
        styles={{
          body: {
            padding: previewType === "image" ? 12 : 0,
            maxHeight: "80vh",
            overflow: previewType === "text" ? "hidden" : "auto",
          },
        }}
        centered
      >
        {previewLoading && (
          <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
            <Spin size="large" />
          </div>
        )}

        {previewType === "image" && imageUrl && !previewLoading && (
          <div style={{ textAlign: "center" }}>
            <Image
              src={imageUrl}
              alt={previewFile?.filename}
              style={{ maxHeight: "70vh", maxWidth: "100%" }}
              preview={{ src: imageUrl }}
            />
          </div>
        )}

        {previewType === "text" && textData && !previewLoading && (
          <div>
            <div
              style={{
                background: "#1e1e1e",
                color: "#d4d4d4",
                padding: "16px 20px",
                fontFamily: "'Menlo', 'Monaco', 'Courier New', monospace",
                fontSize: 13,
                lineHeight: 1.6,
                whiteSpace: "pre-wrap",
                wordBreak: "break-all",
                maxHeight: "60vh",
                overflow: "auto",
                borderRadius: 8,
                margin: "0 12px",
              }}
            >
              {textData.content || "(空文件)"}
            </div>

            {textData.total_pages > 1 && (
              <div style={{ display: "flex", justifyContent: "center", padding: "12px 0" }}>
                <Pagination
                  current={textData.page}
                  total={textData.total_pages}
                  pageSize={1}
                  onChange={handleTextPageChange}
                  size="small"
                  showSizeChanger={false}
                />
              </div>
            )}

            <div style={{ textAlign: "center", padding: "0 0 8px", color: "#8c8c8c", fontSize: 12 }}>
              共 {textData.total_lines} 行
              {textData.total_pages > 1 && ` · 第 ${textData.page}/${textData.total_pages} 页`}
              {textData.truncated && (
                <Tag color="orange" style={{ marginLeft: 8 }}>文件过大，仅预览前 2MB</Tag>
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* Create Folder Modal */}
      <Modal
        open={folderModalOpen}
        onCancel={() => setFolderModalOpen(false)}
        onOk={handleCreateFolder}
        confirmLoading={folderCreating}
        title={
          <Space>
            <FolderAddOutlined style={{ color: "#faad14" }} />
            <span>新建文件夹</span>
          </Space>
        }
        okText="创建"
        cancelText="取消"
      >
        <Input
          placeholder="输入文件夹名称"
          value={newFolderName}
          onChange={(e) => setNewFolderName(e.target.value)}
          onPressEnter={handleCreateFolder}
          autoFocus
          prefix={<FolderOutlined style={{ color: "#faad14" }} />}
        />
      </Modal>

      {/* Move/Copy Modal */}
      <Modal
        open={moveModalOpen}
        onCancel={() => setMoveModalOpen(false)}
        onOk={handleMoveOrCopy}
        confirmLoading={moving}
        title={
          <Space>
            {moveMode === "move" ? <DragOutlined /> : <CopyOutlined />}
            <span>{moveMode === "move" ? "移动" : "复制"} "{moveTarget?.filename}" 到...</span>
          </Space>
        }
        okText={moveMode === "move" ? "移动" : "复制"}
        cancelText="取消"
      >
        <div style={{ marginBottom: 8, color: "#8c8c8c", fontSize: 13 }}>选择目标文件夹：</div>
        <Select
          style={{ width: "100%" }}
          placeholder="选择目标文件夹（留空=根目录）"
          allowClear
          value={selectedFolderId}
          onChange={(val) => setSelectedFolderId(val ?? null)}
          options={[
            { value: null as any, label: <Space><HomeOutlined />根目录</Space> },
            ...allFolders.map((f) => ({
              value: f.id,
              label: (
                <Space>
                  <FolderOutlined style={{ color: "#faad14" }} />
                  {f.oss_key.replace("clouddisk/", "").replace(/\/$/, "").split("/").join(" / ")}
                </Space>
              ),
            })),
          ]}
        />
      </Modal>
    </div>
  );
}

