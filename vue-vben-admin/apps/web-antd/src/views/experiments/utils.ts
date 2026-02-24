/** 格式化文件大小 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

/** 格式化日期时间 */
export function formatDateTime(dt: string | null | undefined): string {
  if (!dt) return '—';
  return new Date(dt).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/** 格式化日期 */
export function formatDate(dt: string | null | undefined): string {
  if (!dt) return '—';
  return new Date(dt).toLocaleDateString('zh-CN');
}

/** 计算剩余天数 */
export function remainingDays(endTime: string): number {
  const diff = new Date(endTime).getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}

/** 实验状态标签文本 */
export const EXPERIMENT_STATUS_LABEL: Record<string, string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
};

/** 实验状态颜色（Ant Design Tag color） */
export const EXPERIMENT_STATUS_COLOR: Record<string, string> = {
  draft: 'default',
  published: 'success',
  archived: 'purple',
};

/** 提交状态标签 */
export const SUBMISSION_STATUS_LABEL: Record<string, string> = {
  draft: '草稿',
  submitted: '已提交',
  graded: '已批改',
};

export const SUBMISSION_STATUS_COLOR: Record<string, string> = {
  draft: 'default',
  submitted: 'processing',
  graded: 'success',
};

/** 难度 */
export const DIFFICULTY_LABEL: Record<string, string> = {
  easy: '简单',
  medium: '中等',
  hard: '困难',
};

export const DIFFICULTY_COLOR: Record<string, string> = {
  easy: 'success',
  medium: 'warning',
  hard: 'error',
};

/** 分类 */
export const CATEGORY_LABEL: Record<string, string> = {
  linux: 'Linux 系统',
  network: '网络技术',
  virtualization: '虚拟化',
};

/** 文档类型 */
export const DOC_TYPE_LABEL: Record<string, string> = {
  guide: '指导书',
  reference: '参考资料',
  video: '视频教程',
};
