import { useState, useRef, useEffect } from "react";
import {
  Card,
  Button,
  Upload,
  DatePicker,
  Select,
  Space,
  Tag,
  Input,
  Rate,
  message,
  Spin,
  Typography,
  Result,
  List,
  Image,
} from "antd";
import {
  CameraOutlined,
  UploadOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import type { RecognizedDish, MealLogDish, FamilyMember } from "../types";
import { recognizePhoto, createMealLog, fetchMembers } from "../api/meals";
import dayjs from "dayjs";
import { useIsMobile } from "../hooks/useIsMobile";

const { Text, Title } = Typography;

const MEAL_OPTIONS = [
  { value: "breakfast", label: "早餐" },
  { value: "lunch", label: "午餐" },
  { value: "dinner", label: "晚餐" },
];

function inferMealType(): string {
  const h = new Date().getHours();
  if (h < 10) return "breakfast";
  if (h < 15) return "lunch";
  return "dinner";
}

export function MealRecorder() {
  const [step, setStep] = useState<"upload" | "confirm">("upload");
  const [recognizing, setRecognizing] = useState(false);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imagePath, setImagePath] = useState("");
  const [recognizedDishes, setRecognizedDishes] = useState<RecognizedDish[]>([]);
  const [editDishes, setEditDishes] = useState<MealLogDish[]>([]);
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [mealType, setMealType] = useState(inferMealType());
  const [rating, setRating] = useState(0);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [newDishName, setNewDishName] = useState("");
  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [likedBy, setLikedBy] = useState<number[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);
  const isMobile = useIsMobile();

  useEffect(() => {
    fetchMembers().then(setMembers).catch(() => {});
  }, []);

  const handleFileSelected = async (file: File) => {
    // Show preview
    const url = URL.createObjectURL(file);
    setImageUrl(url);
    setRecognizing(true);

    try {
      const result = await recognizePhoto(
        file,
        selectedDate.format("YYYY-MM-DD"),
        mealType
      );
      setImagePath(result.image_path);
      setRecognizedDishes(result.recognized_dishes);
      setEditDishes(
        result.recognized_dishes.map((d) => ({
          dish_id: d.dish_id,
          name: d.name,
        }))
      );
      setStep("confirm");
    } catch {
      message.error("识别失败，请重试");
      setImageUrl(null);
    } finally {
      setRecognizing(false);
    }
    return false; // prevent antd auto upload
  };

  const removeDish = (idx: number) => {
    setEditDishes(editDishes.filter((_, i) => i !== idx));
  };

  const addManualDish = () => {
    const name = newDishName.trim();
    if (!name) return;
    setEditDishes([...editDishes, { dish_id: null, name }]);
    setNewDishName("");
  };

  const handleSave = async () => {
    if (editDishes.length === 0) {
      message.warning("请至少确认一道菜");
      return;
    }
    setSaving(true);
    try {
      await createMealLog(
        imagePath,
        selectedDate.format("YYYY-MM-DD"),
        mealType,
        editDishes,
        rating || undefined,
        note || undefined,
        undefined,
        likedBy.length > 0 ? likedBy : undefined
      );
      message.success("用餐记录保存成功！");
      resetForm();
    } catch {
      message.error("保存失败");
    } finally {
      setSaving(false);
    }
  };

  const resetForm = () => {
    setStep("upload");
    setImageUrl(null);
    setImagePath("");
    setRecognizedDishes([]);
    setEditDishes([]);
    setRating(0);
    setNote("");
    setLikedBy([]);
  };

  return (
    <div style={{ maxWidth: 600, margin: "0 auto" }}>
      {step === "upload" && (
        <Card
          title={<span style={{ fontWeight: 600 }}>拍照记录用餐</span>}
          style={{ borderRadius: 12, border: "1px solid #f1f5f9" }}
        >
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            <div style={{ display: "flex", gap: 12 }}>
              <div>
                <Text strong style={{ display: "block", marginBottom: 4 }}>日期</Text>
                <DatePicker
                  value={selectedDate}
                  onChange={(d) => d && setSelectedDate(d)}
                  style={{ width: 160 }}
                />
              </div>
              <div>
                <Text strong style={{ display: "block", marginBottom: 4 }}>餐次</Text>
                <Select
                  value={mealType}
                  onChange={setMealType}
                  options={MEAL_OPTIONS}
                  style={{ width: 120 }}
                />
              </div>
            </div>

            <div
              style={{
                border: "2px dashed #e2e8f0",
                borderRadius: 12,
                padding: isMobile ? 24 : 40,
                textAlign: "center",
                background: "#f8fafc",
              }}
            >
              {recognizing ? (
                <div>
                  <Spin size="large" />
                  <div style={{ marginTop: 16 }}>
                    <Text>AI 正在识别菜品...</Text>
                  </div>
                </div>
              ) : (
                <div>
                  <input
                    ref={fileRef}
                    type="file"
                    accept="image/*"
                    capture="environment"
                    style={{ display: "none" }}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleFileSelected(file);
                      e.target.value = ""; // reset
                    }}
                  />
                  <Button
                    type="primary"
                    size="large"
                    icon={<CameraOutlined />}
                    onClick={() => fileRef.current?.click()}
                    style={{ marginBottom: 12 }}
                  >
                    拍照
                  </Button>
                  <br />
                  <Upload
                    accept="image/*"
                    showUploadList={false}
                    beforeUpload={(file) => {
                      handleFileSelected(file as unknown as File);
                      return false;
                    }}
                  >
                    <Button icon={<UploadOutlined />} type="text">
                      从相册选择
                    </Button>
                  </Upload>
                </div>
              )}
            </div>
          </Space>
        </Card>
      )}

      {step === "confirm" && (
        <Card
          title={<span style={{ fontWeight: 600 }}>确认用餐记录</span>}
          style={{ borderRadius: 12, border: "1px solid #f1f5f9" }}
        >
          <div style={{ marginBottom: 16 }}>
            {imageUrl && (
              <Image
                src={imageUrl}
                width="100%"
                style={{ maxHeight: 200, objectFit: "cover", borderRadius: 8 }}
              />
            )}
          </div>

          <Text strong style={{ display: "block", marginBottom: 8 }}>
            识别出的菜品:
          </Text>
          <List
            size="small"
            dataSource={editDishes}
            renderItem={(d, idx) => {
              const original = recognizedDishes.find((r) => r.name === d.name);
              const matched = original?.matched ?? !!d.dish_id;
              return (
                <List.Item
                  actions={[
                    <Button
                      key="del"
                      type="text"
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={() => removeDish(idx)}
                    />,
                  ]}
                >
                  <Space>
                    {matched ? (
                      <CheckCircleOutlined style={{ color: "#52c41a" }} />
                    ) : (
                      <span style={{ color: "#faad14" }} title="新菜品">!</span>
                    )}
                    <Text>{d.name}</Text>
                    {matched && <Tag color="green">已匹配</Tag>}
                    {!matched && <Tag color="orange">新菜品</Tag>}
                  </Space>
                </List.Item>
              );
            }}
          />

          <Space style={{ marginTop: 8, marginBottom: 16 }}>
            <Input
              size="small"
              placeholder="添加遗漏的菜品..."
              value={newDishName}
              onChange={(e) => setNewDishName(e.target.value)}
              onPressEnter={addManualDish}
              style={{ width: 160 }}
            />
            <Button size="small" icon={<PlusOutlined />} onClick={addManualDish}>
              添加
            </Button>
          </Space>

          <div style={{ marginBottom: 12 }}>
            <Text strong>评分: </Text>
            <Rate value={rating} onChange={setRating} />
          </div>

          {members.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ display: "block", marginBottom: 8 }}>
                谁点赞:
              </Text>
              <Space wrap>
                {members.map((m) => (
                    <Button
                      key={m.id}
                      size="small"
                      type={likedBy.includes(m.id) ? "primary" : "default"}
                      onClick={() => {
                        setLikedBy((prev) =>
                          prev.includes(m.id)
                            ? prev.filter((id) => id !== m.id)
                            : [...prev, m.id]
                        );
                      }}
                    >
                      {m.avatar} {m.name}
                    </Button>
                  ))}
              </Space>
            </div>
          )}

          <div style={{ marginBottom: 16 }}>
            <Text strong>备注: </Text>
            <Input.TextArea
              rows={2}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="如：孩子很喜欢吃..."
            />
          </div>

          <Space>
            <Button onClick={resetForm}>取消</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>
              确认保存
            </Button>
          </Space>
        </Card>
      )}
    </div>
  );
}
