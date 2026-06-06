import { useEffect, useRef, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  List,
  Progress,
  Select,
  Space,
  Tag,
  message,
} from 'antd';
import { PlayCircleOutlined } from '@ant-design/icons';
import { connectProgress, getSettings, startConversion } from '../services/api';
import type { ConversionProgress, Project } from '../types';

interface Props {
  projectId: string;
  project: Project;
  onUpdate: (p: Project) => void;
}

const chapterStatusColor: Record<string, string> = {
  waiting: 'default',
  running: 'processing',
  completed: 'success',
  failed: 'error',
};

export default function ConversionPage({ projectId, project }: Props) {
  const [qualityMode, setQualityMode] = useState('standard');
  const [converting, setConverting] = useState(false);
  const [progress, setProgress] = useState<ConversionProgress | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    getSettings().then((s) => setQualityMode(s.quality_mode));
    return () => {
      wsRef.current?.close();
    };
  }, []);

  const handleStart = async () => {
    if (project.chapter_count < 3) {
      message.warning('请先上传至少 3 章的小说');
      return;
    }

    setConverting(true);
    setProgress(null);

    wsRef.current?.close();
    wsRef.current = connectProgress(projectId, (data) => {
      setProgress(data as ConversionProgress);
      const p = data as ConversionProgress;
      if (['completed', 'failed', 'partial'].includes(p.status)) {
        setConverting(false);
        if (p.status === 'completed' || p.status === 'partial') {
          message.success('转换完成');
        } else {
          message.error('转换失败');
        }
      }
    });

    try {
      await startConversion(projectId);
      message.info('转换任务已启动');
    } catch (err: unknown) {
      setConverting(false);
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      message.error(detail || '启动失败');
    }
  };

  const percent = progress
    ? Math.round((progress.completed_chapters / progress.total_chapters) * 100)
    : 0;

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>AI 转换</h2>

      {project.chapter_count < 3 && (
        <Alert
          type="warning"
          message="请先完成小说导入"
          description="需要至少 3 章内容才能开始转换。"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Space>
            <span>质量模式：</span>
            <Select
              value={qualityMode}
              onChange={setQualityMode}
              style={{ width: 160 }}
              options={[
                { value: 'fast', label: '快速（gpt-4o-mini）' },
                { value: 'standard', label: '标准' },
                { value: 'high', label: '高质量' },
              ]}
              disabled={converting}
            />
            <span style={{ color: '#999' }}>
              预估耗时：{project.chapter_count <= 3 ? '2-4' : '6-10'} 分钟
            </span>
          </Space>

          <Button
            type="primary"
            size="large"
            icon={<PlayCircleOutlined />}
            loading={converting}
            disabled={project.chapter_count < 3}
            onClick={handleStart}
          >
            开始转换
          </Button>
        </Space>
      </Card>

      {(converting || progress) && (
        <Card title="转换进度">
          <Progress percent={percent} status={converting ? 'active' : 'success'} />
          <p style={{ marginTop: 8 }}>{progress?.message || '准备中...'}</p>

          {progress?.chapter_statuses && (
            <Space wrap style={{ marginTop: 12 }}>
              {Object.entries(progress.chapter_statuses).map(([idx, status]) => (
                <Tag key={idx} color={chapterStatusColor[status] || 'default'}>
                  第 {idx} 章: {status}
                </Tag>
              ))}
            </Space>
          )}

          {progress?.logs && progress.logs.length > 0 && (
            <List
              size="small"
              header="日志"
              dataSource={progress.logs}
              renderItem={(item) => <List.Item>{item}</List.Item>}
              style={{ marginTop: 16, maxHeight: 200, overflow: 'auto' }}
            />
          )}
        </Card>
      )}
    </div>
  );
}
