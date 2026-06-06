import { useEffect, useState } from 'react';
import { Button, Card, Form, Input, InputNumber, Select, Switch, message } from 'antd';
import { getSettings, updateSettings } from '../services/api';
import type { AppSettings } from '../types';

export default function SettingsPage() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getSettings()
      .then((s) => {
        form.setFieldsValue(s);
      })
      .finally(() => setLoading(false));
  }, [form]);

  const handleSave = async (values: AppSettings & { api_key?: string }) => {
    setSaving(true);
    try {
      await updateSettings(values);
      message.success('设置已保存');
    } catch {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>系统设置</h2>

      <Card loading={loading}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          style={{ maxWidth: 600 }}
        >
          <Form.Item label="LLM 提供商" name="llm_provider">
            <Select
              options={[
                { value: 'openai', label: 'OpenAI' },
                { value: 'deepseek', label: 'DeepSeek' },
                { value: 'custom', label: '自定义' },
              ]}
            />
          </Form.Item>

          <Form.Item label="API Base URL" name="llm_base_url">
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>

          <Form.Item label="模型" name="llm_model">
            <Input placeholder="gpt-4o" />
          </Form.Item>

          <Form.Item label="API Key" name="api_key" extra="保存在系统钥匙串，不会明文显示">
            <Input.Password placeholder="输入新的 API Key（留空则不修改）" />
          </Form.Item>

          <Form.Item label="Temperature" name="llm_temperature">
            <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item label="Max Tokens" name="llm_max_tokens">
            <InputNumber min={512} max={128081} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item label="质量模式" name="quality_mode">
            <Select
              options={[
                { value: 'fast', label: '快速' },
                { value: 'standard', label: '标准' },
                { value: 'high', label: '高质量' },
              ]}
            />
          </Form.Item>

          <Form.Item label="最大并发请求数" name="max_concurrent_requests">
            <InputNumber min={1} max={10} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item label="章节重试次数" name="chapter_retry_count">
            <InputNumber min={0} max={5} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label="Mock LLM 模式"
            name="mock_llm"
            valuePropName="checked"
            extra="无 API Key 时可用于测试完整流程"
          >
            <Switch />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={saving}>
              保存设置
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
