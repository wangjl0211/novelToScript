import { useEffect, useState, useCallback } from 'react';
import { Alert, Button, Card, Space, Tabs, Tree, message } from 'antd';
import Editor from '@monaco-editor/react';
import { getScript, saveScript, validateScript } from '../services/api';

interface Props {
  projectId: string;
}

/** 从 YAML 文本构建简易树形预览 */
function buildTreeFromYaml(content: string) {
  const lines = content.split('\n');
  const tree: { title: string; key: string; children?: { title: string; key: string }[] }[] = [];
  let actIdx = 0;
  let sceneIdx = 0;

  for (const line of lines) {
    if (line.match(/^\s*act_number:/)) {
      actIdx++;
      tree.push({ title: `第 ${actIdx} 幕`, key: `act-${actIdx}`, children: [] });
    }
    if (line.match(/^\s*scene_id:/) && tree.length > 0) {
      sceneIdx++;
      const lastAct = tree[tree.length - 1];
      lastAct.children = lastAct.children || [];
      lastAct.children.push({ title: `场景 sc${String(sceneIdx).padStart(3, '0')}`, key: `scene-${sceneIdx}` });
    }
  }
  return tree.length > 0 ? tree : [{ title: '剧本结构', key: 'root', children: [] }];
}

export default function EditorPage({ projectId }: Props) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    getScript(projectId)
      .then((c) => {
        setContent(c);
        setLoaded(true);
      })
      .catch(() => {
        setLoaded(false);
      })
      .finally(() => setLoading(false));
  }, [projectId]);

  const handleValidate = useCallback(async () => {
    try {
      const result = await validateScript(projectId, content);
      setErrors(result.errors);
      if (result.valid) {
        message.success('Schema 校验通过');
      } else {
        message.warning(`发现 ${result.errors.length} 个错误`);
      }
    } catch {
      message.error('校验失败');
    }
  }, [projectId, content]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveScript(projectId, content);
      message.success('保存成功');
      setErrors([]);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: { errors?: string[] } } } })
        ?.response?.data?.detail;
      if (detail && typeof detail === 'object' && detail.errors) {
        setErrors(detail.errors);
      }
      message.error('保存失败，请检查 YAML 格式');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>加载中...</div>;

  if (!loaded) {
    return (
      <Alert
        type="info"
        message="尚未生成剧本"
        description="请先在「转换」步骤完成 AI 转换。"
        showIcon
      />
    );
  }

  const treeData = buildTreeFromYaml(content);

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>剧本编辑</h2>
        <Space>
          <Button onClick={handleValidate}>校验 Schema</Button>
          <Button type="primary" loading={saving} onClick={handleSave}>
            保存
          </Button>
        </Space>
      </div>

      {errors.length > 0 && (
        <Alert
          type="error"
          message="Schema 校验错误"
          description={
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {errors.slice(0, 10).map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          }
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Tabs
        items={[
          {
            key: 'code',
            label: '代码模式',
            children: (
              <Card bodyStyle={{ padding: 0 }}>
                <Editor
                  height="500px"
                  language="yaml"
                  value={content}
                  onChange={(v) => setContent(v || '')}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    wordWrap: 'on',
                  }}
                />
              </Card>
            ),
          },
          {
            key: 'structure',
            label: '结构预览',
            children: (
              <Card>
                <Tree treeData={treeData} defaultExpandAll />
              </Card>
            ),
          },
        ]}
      />
    </div>
  );
}
