import { Routes, Route, Navigate, useParams, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Spin } from 'antd';
import {
  UploadOutlined,
  ThunderboltOutlined,
  EditOutlined,
  ExportOutlined,
} from '@ant-design/icons';
import { useEffect, useState } from 'react';
import { getProject } from '../services/api';
import type { Project } from '../types';
import ImportPage from './Import';
import ConversionPage from './Conversion';
import EditorPage from './Editor';
import ExportPage from './Export';

const { Sider, Content } = Layout;

export default function ProjectWorkspace() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getProject(id)
      .then(setProject)
      .catch(() => setProject(null))
      .finally(() => setLoading(false));
  }, [id]);

  if (!id) return <Navigate to="/" />;
  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!project) return <div>项目不存在</div>;

  const base = `/project/${id}`;
  const step = location.pathname.replace(base, '').replace(/^\//, '') || 'import';

  const menuItems = [
    { key: 'import', icon: <UploadOutlined />, label: '① 导入' },
    { key: 'convert', icon: <ThunderboltOutlined />, label: '② 转换' },
    { key: 'edit', icon: <EditOutlined />, label: '③ 编辑' },
    { key: 'export', icon: <ExportOutlined />, label: '④ 导出' },
  ];

  return (
    <Layout style={{ background: '#fff', minHeight: 600 }}>
      <Sider width={180} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: '16px 12px', fontWeight: 600, borderBottom: '1px solid #f0f0f0' }}>
          {project.name}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[step.split('/')[0]]}
          items={menuItems}
          onClick={({ key }) => navigate(`${base}/${key}`)}
        />
      </Sider>
      <Content style={{ padding: 24 }}>
        <Routes>
          <Route index element={<Navigate to="import" replace />} />
          <Route path="import" element={<ImportPage projectId={id} onUpdate={setProject} />} />
          <Route path="convert" element={<ConversionPage projectId={id} project={project} onUpdate={setProject} />} />
          <Route path="edit" element={<EditorPage projectId={id} />} />
          <Route path="export" element={<ExportPage projectId={id} project={project} />} />
        </Routes>
      </Content>
    </Layout>
  );
}
