// ABOUTME: 前端日期辅助函数
// ABOUTME: 仅用于本地 thread 日期键与当日 UI 展示，不承载身份信息

export function getTodayDateString(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
