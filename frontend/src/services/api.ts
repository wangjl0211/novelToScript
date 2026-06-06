/** API 客户端 */

import axios from 'axios';
import type { AppSettings, Project, UploadResult, ValidationResult } from '../types';

const api = axios.create({ baseURL: '/api' });

export async function listProjects(): Promise<Project[]> {
  const { data } = await api.get<Project[]>('/projects');
  return data;
}

export async function createProject(name: string, description?: string): Promise<Project> {
  const { data } = await api.post<Project>('/projects', { name, description });
  return data;
}

export async function getProject(id: string): Promise<Project> {
  const { data } = await api.get<Project>(`/projects/${id}`);
  return data;
}

export async function deleteProject(id: string): Promise<void> {
  await api.delete(`/projects/${id}`);
}

export async function uploadNovel(projectId: string, file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post<UploadResult>(`/projects/${projectId}/upload`, form);
  return data;
}

export async function getChapters(projectId: string) {
  const { data } = await api.get(`/projects/${projectId}/chapters`);
  return data;
}

export async function startConversion(projectId: string): Promise<void> {
  await api.post(`/projects/${projectId}/convert`);
}

export async function getScript(projectId: string): Promise<string> {
  const { data } = await api.get<{ content: string }>(`/projects/${projectId}/script`);
  return data.content;
}

export async function saveScript(projectId: string, content: string): Promise<void> {
  await api.put(`/projects/${projectId}/script`, { content });
}

export async function validateScript(projectId: string, content: string): Promise<ValidationResult> {
  const { data } = await api.post<ValidationResult>(`/projects/${projectId}/script/validate`, {
    content,
  });
  return data;
}

export async function exportScript(projectId: string, format: string): Promise<Blob> {
  const { data } = await api.post(
    `/projects/${projectId}/export`,
    { format },
    { responseType: 'blob' },
  );
  return data;
}

export async function getSettings(): Promise<AppSettings> {
  const { data } = await api.get<AppSettings>('/settings');
  return data;
}

export async function updateSettings(settings: Partial<AppSettings & { api_key?: string }>): Promise<AppSettings> {
  const { data } = await api.put<AppSettings>('/settings', settings);
  return data;
}

export function connectProgress(projectId: string, onMessage: (data: unknown) => void): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws/projects/${projectId}/progress`);
  ws.onmessage = (ev) => {
    try {
      onMessage(JSON.parse(ev.data));
    } catch {
      /* 忽略非 JSON 消息 */
    }
  };
  return ws;
}
