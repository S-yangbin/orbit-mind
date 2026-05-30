import { useState } from "react";
import { Modal, Form, Input, Upload, Progress, message } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import { uploadVideo, processVideo } from "../api/videos";
import { useIsMobile } from "../hooks/useIsMobile";

const { Dragger } = Upload;

const ALLOWED_TYPES = [".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"];

interface Props {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function VideoUpload({ visible, onClose, onSuccess }: Props) {
  const [form] = Form.useForm();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadPct, setUploadPct] = useState(0);
  const isMobile = useIsMobile();

  const handleUpload = async () => {
    if (!file) {
      message.warning("请选择视频文件");
      return;
    }
    const title = form.getFieldValue("title") || file.name.replace(/\.[^.]+$/, "");

    setUploading(true);
    setUploadPct(0);
    try {
      const result = await uploadVideo(file, title, setUploadPct);
      message.success("上传成功！正在启动智能分析...");
      // Trigger processing
      try {
        await processVideo(result.id);
      } catch {
        // Processing might take a while, don't block
      }
      onSuccess();
      handleClose();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      message.error(err?.response?.data?.detail || "上传失败，请重试");
    }
    setUploading(false);
  };

  const handleClose = () => {
    form.resetFields();
    setFile(null);
    setUploadPct(0);
    setUploading(false);
    onClose();
  };

  return (
    <Modal
      title="上传作业视频"
      open={visible}
      onOk={handleUpload}
      onCancel={handleClose}
      confirmLoading={uploading}
      okText="上传并分析"
      cancelText="取消"
      width={isMobile ? "calc(100vw - 16px)" : 520}
    >
      <Form form={form} layout="vertical">
        <Form.Item label="视频标题" name="title" rules={[{ required: true, message: "请输入视频标题" }]}>
          <Input placeholder="例如：Unit 5 作业视频" />
        </Form.Item>

        <Form.Item label="视频文件">
          <Dragger
            accept={ALLOWED_TYPES.join(",")}
            maxCount={1}
            beforeUpload={(f) => {
              const ext = "." + f.name.split(".").pop()?.toLowerCase();
              if (!ALLOWED_TYPES.includes(ext)) {
                message.error(`不支持的格式：${ext}`);
                return Upload.LIST_IGNORE;
              }
              if (f.size > 2 * 1024 * 1024 * 1024) {
                message.error("文件大小不能超过 2GB");
                return Upload.LIST_IGNORE;
              }
              setFile(f);
              return false; // manual upload
            }}
            onRemove={() => setFile(null)}
            fileList={file ? [{ uid: "-1", name: file.name, status: "done" } as never] : []}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽视频文件到此处</p>
            <p className="ant-upload-hint">
              支持 MP4、MOV、AVI、MKV、WebM 等格式，最大 2GB
            </p>
          </Dragger>
        </Form.Item>

        {uploading && (
          <Progress percent={uploadPct} status="active" strokeColor="#7c3aed" />
        )}
      </Form>
    </Modal>
  );
}