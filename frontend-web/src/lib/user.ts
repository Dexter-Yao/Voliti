// ABOUTME: 从 cookie 读取当前登录用户的 user_id
// ABOUTME: voliti_access cookie 在登录时由 server action 设置

export function getUserId(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith("voliti_user_id="));
  return match ? decodeURIComponent(match.split("=")[1]) : null;
}

export function getTodayDateString(): string {
  return new Date().toISOString().slice(0, 10);
}
