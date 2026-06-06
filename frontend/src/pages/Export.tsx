import { useState } from 'react';
import { Alert, Button, Card, Radio, Space, message } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { exportScript } from '../services/api';
import type { Project } from '../types';

interface Props {
  projectId: string;
  project: Project;
}

export default function ExportPage({ projectId, project }: Props) {
  const [format, setFormat] = useState('yaml');
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await exportScript(projectId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${project.name}.${format === 'fountain' ? 'fountain' : format}`;
      a.click();
      URL.revokeObjectURL(url);
      message.success('导出成功');
    } catch {
      message.error('导出失败，请确保已生成剧本');
    } finally {
      setExporting(false);
    }
  };

  if (!project.has_script) {
    return (
      <Alert
        type="info"
        message="尚未生成剧本"
        description="请先完成 AI 转换。"
        showIcon
      />
    );
  }

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>导出剧本</h2>

      <Card>
        <Space direction="vertical" size="large">
          <div>
            <div style={{ marginBottom: 8 }}>选择导出格式：</div>
            <Radio.Group value={format} onChange={(e) => setFormat(e.target.value)}>
              <Radio.Button value="yaml">YAML（主格式）</Radio.Button>
              <Radio.Button value="json">JSON</Radio.Button>
              <Radio.Button value="fountain">Fountain</Radio.Button>
            </Radio.Group>
          </div>

          <Button
            type="primary"
            size="large"
            icon={<DownloadOutlined />}
            loading={exporting}
            onClick={handleExport}
          >
            下载文件
          </Button>
        </Space>
      </Card>
    </div>
  );
}
