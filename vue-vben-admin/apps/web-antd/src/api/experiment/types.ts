// ─────────────────────── 枚举 / 常量 ───────────────────────

export type ExperimentStatus = 'draft' | 'published' | 'archived';
export type ExperimentDifficulty = 'easy' | 'medium' | 'hard';
export type ExperimentCategory = 'linux' | 'network' | 'virtualization' | string;
export type SubmissionStatus = 'draft' | 'submitted' | 'graded';
export type GradeStatus = 'pending' | 'completed';
export type DocType = 'guide' | 'reference' | 'video';
export type FileCategory = 'screenshot' | 'video' | 'document' | 'other';
export type IndexStatus = 'pending' | 'processing' | 'completed' | 'failed';

// ─────────────────────── 用户简要 ───────────────────────

export interface UserBrief {
  id: number;
  username: string;
  name: string;
}

// ─────────────────────── 统计 ───────────────────────

export interface ExperimentStats {
  total_students: number;
  submitted_count: number;
  graded_count: number;
}

// ─────────────────────── CourseExperiment ───────────────────────

export interface ExperimentListItem {
  id: number;
  title: string;
  course_code: string;
  category: ExperimentCategory;
  difficulty: ExperimentDifficulty;
  estimated_hours: number;
  start_time: string;
  end_time: string;
  total_score: number;
  status: ExperimentStatus;
  is_active: boolean;
  late_submission_allowed: boolean;
  teacher: UserBrief;
  stats: ExperimentStats;
  created_at: string;
  /** 当前登录学生的提交摘要（教师视角为 null） */
  my_submission?: MySubmissionBrief | null;
}

export interface ExperimentDetail extends ExperimentListItem {
  description: string;
  objectives: string[];
  late_penalty_rate: number;
  required_resources: Record<string, any>;
  pve_template_id: string;
  scoring_criteria: Record<string, number>;
  guidebooks: GuidebookListItem[];
  my_submission: MySubmissionBrief | null;
  updated_at: string;
}

export interface MySubmissionBrief {
  id: number;
  submission_status: SubmissionStatus;
  submit_time: string | null;
  is_late: boolean;
  score: number | null;
  grade_status: GradeStatus;
}

export interface CreateExperimentPayload {
  title: string;
  course_code?: string;
  description?: string;
  objectives?: string[];
  category: ExperimentCategory;
  difficulty?: ExperimentDifficulty;
  estimated_hours?: number;
  start_time: string;
  end_time: string;
  late_submission_allowed?: boolean;
  late_penalty_rate?: number;
  required_resources?: Record<string, any>;
  pve_template_id?: string;
  total_score?: number;
  scoring_criteria?: Record<string, number>;
  status?: ExperimentStatus;
  is_active?: boolean;
  remark?: string;
}

// ─────────────────────── CourseGuidebook ───────────────────────

export interface GuidebookListItem {
  id: number;
  experiment: number;
  title: string;
  doc_type: DocType;
  description: string;
  file_name: string;
  file_size: number;
  file_type: string;
  is_indexed: boolean;
  index_status: IndexStatus;
  is_public: boolean;
  view_count: number;
  download_count: number;
  download_url: string;
  created_at: string;
}

export interface GuidebookPreviewResult {
  file_type: string;
  // Markdown
  content?: string;
  html?: string;
  // PDF
  preview_url?: string;
  page_count?: number | null;
  // Video / other
  media_url?: string;
}

// ─────────────────────── CourseSubmission ───────────────────────

export interface SubmissionListItem {
  id: number;
  experiment: number;
  student: UserBrief;
  submission_status: SubmissionStatus;
  submit_time: string | null;
  is_late: boolean;
  grade_status: GradeStatus;
  score: number | null;
  report_title: string;
  created_at: string;
}

export interface ScoringDetailItem {
  score: number;
  total: number;
  comment: string;
}

export interface SubmissionDetail {
  id: number;
  experiment: number;
  experiment_info: { id: number; title: string };
  student: UserBrief;
  graded_by: UserBrief | null;
  submission_status: SubmissionStatus;
  submit_time: string | null;
  is_late: boolean;
  report_title: string;
  report_content: string;
  vm_info: Record<string, any>;
  operation_logs: any[];
  score: number | null;
  grade_status: GradeStatus;
  graded_at: string | null;
  feedback: string;
  scoring_details: Record<string, ScoringDetailItem>;
  revision_count: number;
  last_auto_save: string | null;
  attachments: AttachmentItem[];
  created_at: string;
  updated_at: string;
}

// ─────────────────────── CourseAttachment ───────────────────────

export interface AttachmentItem {
  id: number;
  submission: number;
  file_name: string;
  file_path: string;
  file_size: number;
  file_type: string;
  file_category: FileCategory;
  description: string;
  step_number: number | null;
  thumbnail_path: string;
  thumbnail_url: string | null;
  file_url: string;
  uploaded_by_id: number;
  created_at: string;
  is_deleted: boolean;
}

// ─────────────────────── 通用响应 ───────────────────────

export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

export interface PaginatedData<T = any> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
