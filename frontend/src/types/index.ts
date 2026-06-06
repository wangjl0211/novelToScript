/** 项目与 API 类型定义 */

export interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  chapter_count: number;
  conversion_status: string;
  has_script: boolean;
}

export interface ChapterInfo {
  index: number;
  title: string;
  word_count: number;
}

export interface UploadResult {
  title: string;
  author?: string;
  chapter_count: number;
  chapters: ChapterInfo[];
}

export interface ConversionProgress {
  project_id: string;
  status: string;
  total_chapters: number;
  completed_chapters: number;
  current_chapter?: number;
  message: string;
  chapter_statuses: Record<number, string>;
  logs: string[];
}

export interface AppSettings {
  llm_provider: string;
  llm_base_url: string;
  llm_model: string;
  llm_temperature: number;
  llm_max_tokens: number;
  has_api_key: boolean;
  max_concurrent_requests: number;
  chapter_retry_count: number;
  quality_mode: string;
  mock_llm: boolean;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}
