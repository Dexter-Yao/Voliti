// ABOUTME: 从 cookie 读取当前登录用户的 user_id
// ABOUTME: voliti_access cookie 在登录时由 server action 设置

export function getUserId(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith("voliti_user_id="));
  if (!match) return null;
  const eqIdx = match.indexOf("=");
  return decodeURIComponent(match.slice(eqIdx + 1));
}

export function getTodayDateString(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
