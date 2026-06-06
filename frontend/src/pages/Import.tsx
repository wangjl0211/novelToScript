import { useEffect, useState } from 'react';
import { Alert, Card, Table, Upload, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { getChapters, getProject, uploadNovel } from '../services/api';
import type { ChapterInfo, Project } from '../types';

interface Props {
  projectId: string;
  onUpdate: (p: Project) => void;
}

export default function ImportPage({ projectId, onUpdate }: Props) {
  const [chapters, setChapters] = useState<ChapterInfo[]>([]);
  const [title, setTitle] = useState('');
  const [uploading, setUploading] = useState(false);

  const loadChapters = async () => {
    try {
      const data = await getChapters(projectId);
      setTitle(data.title);
      setChapters(data.chapters);
    } catch {
      setChapters([]);
    }
  };

  useEffect(() => {
    loadChapters();
  }, [projectId]);

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.txt,.docx',
    showUploadList: false,
    beforeUpload: async (file) => {
      setUploading(true);
      try {
        const result = await uploadNovel(projectId, file);
        setTitle(result.title);
        setChapters(result.chapters);
        const project = await getProject(projectId);
        onUpdate(project);
        message.success(`上传成功，共识别 ${result.chapter_count} 章`);
      } catch (err: unknown) {
        const detail =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        message.error(detail || '上传失败');
      } finally {
        setUploading(false);
      }
      return false;
    },
  };

  const columns = [
    { title: '序号', dataIndex: 'index', width: 80 },
    { title: '章节标题', dataIndex: 'title' },
    { title: '字数', dataIndex: 'word_count', width: 100 },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>导入小说</h2>

      <Card style={{ marginBottom: 16 }}>
        <Upload.Dragger {...uploadProps} disabled={uploading}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽上传 TXT / DOCX 文件</p>
          <p className="ant-upload-hint">需包含至少 3 个章节，支持「第X章」或「Chapter X」格式</p>
        </Upload.Dragger>
      </Card>

      {chapters.length > 0 && chapters.length < 3 && (
        <Alert
          type="warning"
          message="章节数不足"
          description={`当前仅识别 ${chapters.length} 章，需要至少 3 章才能进行转换。`}
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {chapters.length > 0 && (
        <Card title={`《${title}》章节预览（共 ${chapters.length} 章）`}>
          <Table rowKey="index" columns={columns} dataSource={chapters} pagination={false} size="small" />
        </Card>
      )}
    </div>
  );
}
