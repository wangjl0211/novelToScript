import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  Empty,
  Input,
  Modal,
  Popconfirm,
  Space,
  Table,
  Tag,
  message,
} from 'antd';
import { PlusOutlined, DeleteOutlined, FolderOpenOutlined } from '@ant-design/icons';
import { createProject, deleteProject, listProjects } from '../services/api';
import type { Project } from '../types';

const statusMap: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '待转换' },
  running: { color: 'processing', text: '转换中' },
  completed: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
  partial: { color: 'warning', text: '部分完成' },
};

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [name, setName] = useState('');
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try {
      setProjects(await listProjects());
    } catch {
      message.error('加载项目列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async () => {
    if (!name.trim()) {
      message.warning('请输入项目名称');
      return;
    }
    try {
      const project = await createProject(name.trim());
      message.success('项目创建成功');
      setModalOpen(false);
      setName('');
      navigate(`/project/${project.id}`);
    } catch {
      message.error('创建项目失败');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteProject(id);
      message.success('已删除');
      load();
    } catch {
      message.error('删除失败');
    }
  };

  const columns = [
    { title: '项目名称', dataIndex: 'name', key: 'name' },
    {
      title: '章节数',
      dataIndex: 'chapter_count',
      key: 'chapter_count',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'conversion_status',
      key: 'status',
      width: 120,
      render: (s: string) => {
        const info = statusMap[s] || statusMap.pending;
        return <Tag color={info.color}>{info.text}</Tag>;
      },
    },
    {
      title: '剧本',
      dataIndex: 'has_script',
      key: 'has_script',
      width: 80,
      render: (v: boolean) => (v ? '有' : '-'),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: unknown, record: Project) => (
        <Space>
          <Button
            type="link"
            icon={<FolderOpenOutlined />}
            onClick={() => navigate(`/project/${record.id}`)}
          >
            打开
          </Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>我的项目</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          新建项目
        </Button>
      </div>

      <Card>
        {projects.length === 0 && !loading ? (
          <Empty description="暂无项目，点击上方按钮创建">
            <Button type="primary" onClick={() => setModalOpen(true)}>
              新建项目
            </Button>
          </Empty>
        ) : (
          <Table rowKey="id" columns={columns} dataSource={projects} loading={loading} />
        )}
      </Card>

      <Modal
        title="新建项目"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => setModalOpen(false)}
        okText="创建"
        cancelText="取消"
      >
        <Input
          placeholder="项目名称"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onPressEnter={handleCreate}
        />
      </Modal>
    </div>
  );
}
