# TODOS

## P3: 智能签到提醒
- **What:** Coach 根据用户习惯自动调整签到提醒时间，而非固定时间
- **Why:** 固定时间提醒的响应率低，用户习惯因人而异。智能调整可提高签到参与度
- **Pros:** 更好的签到响应率，Coach 参与度提升
- **Cons:** 需要 Coach 行为适配（写入 preferred_checkin_time），增加后端复杂度
- **Context:** Settings 页偏好设置中已有签到提醒时间的手动设置（DatePicker）。扩展为 Coach 写入 Store 的 `preferred_checkin_time`，iOS 端读取并自动调整本地 UNNotification
- **Effort:** M (human) → S (CC+gstack)
- **Priority:** P3
- **Depends on:** Settings 页基础功能完成
- **Source:** /plan-ceo-review 2026-04-06, cherry-pick ceremony deferred
