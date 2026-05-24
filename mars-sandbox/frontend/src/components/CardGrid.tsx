import { useState, useEffect, useCallback } from "react";
import { Row, Col, Input, Tag, Pagination, Spin, Empty, Select, Space, Button, Segmented } from "antd";
import { ReloadOutlined, SearchOutlined } from "@ant-design/icons";
import { ProjectCard } from "./ProjectCard";
import { EditProjectModal } from "./EditProjectModal";
import { ScanButton } from "./ScanButton";
import { fetchPages } from "../api/pages";
import { fetchTags } from "../api/tags";
import type { Page, Tag as TagType } from "../types";

const CATEGORY_OPTIONS = [
  { label: '工作', value: 'work' },
  { label: '生活', value: 'life' },
];

export function CardGrid() {
  const [pages, setPages] = useState<Page[]>([]);
  const [tags, setTags] = useState<TagType[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [search, setSearch] = useState("");
  const [selectedTag, setSelectedTag] = useState<string | undefined>();
  const [selectedCategory, setSelectedCategory] = useState<string>("work");
  const [editPage, setEditPage] = useState<Page | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [pagesData, tagsData] = await Promise.all([
        fetchPages({
          q: search || undefined,
          tag: selectedTag,
          category: selectedCategory,
          page: currentPage,
          page_size: 20,
          sort: "updated_at",
          order: "desc",
        }),
        fetchTags(),
      ]);
      setPages(pagesData.items);
      setTotal(pagesData.total);
      setTags(tagsData);
    } catch (e) {
      console.error("Failed to load data:", e);
    }
    setLoading(false);
  }, [currentPage, search, selectedTag, selectedCategory]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = () => {
    loadData();
  };

  return (
    <div>
      {/* Category tabs */}
      <div style={{ marginBottom: 24 }}>
        <Segmented
          options={CATEGORY_OPTIONS}
          value={selectedCategory}
          onChange={(v) => {
            setSelectedCategory(v as string);
            setCurrentPage(1);
          }}
          size="large"
        />
      </div>

      {/* Top bar */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 24,
        flexWrap: "wrap",
        gap: 12,
      }}>
        <Space wrap>
          <Input
            placeholder="搜索标题或描述..."
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onPressEnter={() => { setCurrentPage(1); loadData(); }}
            allowClear
            style={{ width: 280 }}
          />
          <Select
            placeholder="按标签筛选"
            value={selectedTag}
            onChange={(v) => { setSelectedTag(v); setCurrentPage(1); }}
            allowClear
            style={{ width: 180 }}
            options={tags.map((t) => ({ label: t.name, value: t.name }))}
          />
        </Space>
        <Space>
          <ScanButton onScanComplete={loadData} />
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
        </Space>
      </div>

      {/* Tag filter bar */}
      {tags.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <span style={{ marginRight: 8, color: "#888", fontSize: 12 }}>标签:</span>
          {tags.map((t) => (
            <Tag
              key={t.id}
              color={selectedTag === t.name ? "blue" : "default"}
              style={{ cursor: "pointer", marginBottom: 4 }}
              onClick={() => {
                setSelectedTag(selectedTag === t.name ? undefined : t.name);
                setCurrentPage(1);
              }}
            >
              {t.name} ({t.page_count})
            </Tag>
          ))}
        </div>
      )}

      {/* Card grid */}
      <Spin spinning={loading}>
        {pages.length === 0 && !loading ? (
          <Empty description="暂无页面数据，请先将 HTML 项目放到 /mnt/oss-sybuddy/html/ 目录下，然后触发扫描" />
        ) : (
          <Row gutter={[16, 16]}>
            {pages.map((p) => (
              <Col xs={24} sm={12} md={8} lg={6} key={p.id}>
                <ProjectCard page={p} onEdit={setEditPage} />
              </Col>
            ))}
          </Row>
        )}
      </Spin>

      {/* Pagination */}
      {total > 20 && (
        <div style={{ textAlign: "center", marginTop: 24 }}>
          <Pagination
            current={currentPage}
            total={total}
            pageSize={20}
            onChange={setCurrentPage}
          />
        </div>
      )}

      {/* Edit modal */}
      {editPage && (
        <EditProjectModal
          page={editPage}
          visible={!!editPage}
          onClose={() => setEditPage(null)}
          onSave={() => {
            setEditPage(null);
            loadData();
          }}
        />
      )}
    </div>
  );
}
