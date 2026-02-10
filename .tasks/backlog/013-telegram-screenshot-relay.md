---
id: "013"
priority: low
status: placeholder  # 占位任务，暂不实施。需要先验证 Telegram 频道自收机制是否可行。
module: [recall-android, openclaw, recall]
branch: feat/telegram-screenshot-relay
estimated_scope: medium
---

# 方案 B：通过 Telegram 中转移动端截图到 PC

## 背景

Android 端 RecallMobile 已实现自动截图，但当前 SyncManager 的目标是
`POST /api/upload`（PC 端未实现）。现在 OpenClaw + Telegram Bot 已跑通，
可以利用 Telegram 作为传输通道，实现"手机截图 → Telegram → PC 存储"。

## 架构总览

```
Android RecallMobile
  ↓ Bot API: sendPhoto (用 bot token 发到私有频道)
Telegram Channel (私有频道 "RecallMobile")
  ↓ channel_post update (bot 作为 admin 自动收到)
OpenClaw (@zzf1955_bot)
  ↓ 识别为截图中转 → 下载图片 → POST /api/upload
Recall PC (:5000)
  ↓ 保存到 screenshots/ + 入库 + OCR
Screen Agent (定时轮询分析)
```

## 核心设计决策

### 为什么不需要新建机器人？

利用 Telegram **频道（Channel）** 的特性：

- Bot 作为频道 admin 发送消息时，消息归属于频道（匿名）
- Bot 同时作为 admin 会收到 `channel_post` update
- 因此 **同一个 bot 既是发送者又是接收者**，不需要第二个 bot

### 备选方案（如果频道自收不生效）

创建一个轻量 relay bot（@recall_relay_bot），专门用于 Android 发图：
- Android 用 relay bot token 发图到频道
- 主 bot @zzf1955_bot 作为 admin 收到 channel_post
- 这个方案 100% 可靠，但多一个 bot 要管理

**建议**：先试频道方案，不行再加 relay bot。

## 实现步骤

### 第 0 步：创建 Telegram 私有频道（手动）

1. 在 Telegram 中创建私有频道，名称如 "RecallMobile"
2. 将 @zzf1955_bot 添加为频道管理员（需要 Post Messages 权限）
3. 获取频道的 chat_id（发一条消息后通过 Bot API getUpdates 查看）
4. 记录 channel_id，后续配置用

### 第 1 步：Android 端 — 改造 SyncManager

**文件**: `recall/android/RecallMobile/app/src/main/java/com/recall/mobile/sync/SyncManager.kt`

**改动**：将 `uploadAndDelete()` 的目标从 HTTP upload 改为 Telegram Bot API。

```kotlin
// 核心改动：用 Telegram Bot API 替代直接 HTTP upload
private suspend fun uploadAndDelete(screenshot: Screenshot): Boolean {
    val file = File(screenshot.path)
    if (!file.exists()) {
        database.screenshotDao().updateSyncStatus(screenshot.id, "synced")
        return true
    }

    // Telegram Bot API: sendPhoto
    val url = "https://api.telegram.org/bot${prefs.botToken}/sendPhoto"

    try {
        val requestBody = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("chat_id", prefs.channelId)  // 频道 chat_id
            .addFormDataPart(
                "photo", file.name,
                file.asRequestBody("image/jpeg".toMediaType())
            )
            .addFormDataPart("caption", "mobile|${screenshot.timestamp}")
            .build()

        val request = Request.Builder().url(url).post(requestBody).build()
        val response = client.newCall(request).execute()

        if (response.isSuccessful) {
            file.delete()
            database.screenshotDao().updateSyncStatus(screenshot.id, "synced")
            return true
        } else {
            database.screenshotDao().updateSyncStatus(screenshot.id, "error")
            return false
        }
    } catch (e: Exception) {
        database.screenshotDao().updateSyncStatus(screenshot.id, "error")
        return false
    }
}
```

**AppPreferences 新增字段**：
```kotlin
val botToken: String get() = prefs.getString("bot_token", "") ?: ""
val channelId: String get() = prefs.getString("channel_id", "") ?: ""
```

**设置页面**：添加 Bot Token 和 Channel ID 输入框（替代原来的 Server IP/Port）。

**代理支持**：OkHttpClient 添加代理配置（如果手机需要翻墙访问 Telegram）：
```kotlin
val client = OkHttpClient.Builder()
    .proxy(Proxy(Proxy.Type.HTTP, InetSocketAddress("127.0.0.1", 7897)))
    // ... timeouts
    .build()
```

> 注意：手机端一般直接访问 Telegram，不需要代理。仅国内网络需要。

### 第 2 步：Recall PC 端 — 实现 /api/upload

**文件**: `recall/web/app.py`

按照已有的 `doc/SYNC_API.md` 方案实现 `POST /api/upload` 端点：
- 接收 multipart/form-data（file + timestamp）
- 保存到 `screenshots/YYYY-MM-DD/HH/HHMMSS.jpg`
- 计算 phash，插入数据库
- OCR 由现有 ocr_worker 自动处理

额外添加标记字段 `source = "mobile"`，区分 PC 截图和手机截图。

### 第 3 步：OpenClaw 端 — 频道消息转发到 Recall

**文件**: `openclaw/src/telegram/bot-handlers.ts`

在 `bot.on("message")` 或新增 `bot.on("channel_post")` 处理器中：

```typescript
bot.on("channel_post", async (ctx) => {
    const post = ctx.channelPost;
    if (!post) return;

    // 检查是否来自配置的截图频道
    const screenshotChannelId = telegramCfg.screenshotChannelId;
    if (!screenshotChannelId || post.chat.id !== Number(screenshotChannelId)) {
        return;
    }

    // 检查 caption 标记
    const caption = post.caption ?? "";
    if (!caption.startsWith("mobile|")) return;

    const timestamp = caption.split("|")[1];

    // 下载图片
    const photo = post.photo;
    if (!photo || photo.length === 0) return;

    const largest = photo[photo.length - 1];
    const file = await bot.api.getFile(largest.file_id);
    const fileUrl =
        `https://api.telegram.org/file/bot${opts.token}/${file.file_path}`;

    // 下载图片 buffer
    const response = await opts.proxyFetch(fileUrl);
    const buffer = Buffer.from(await response.arrayBuffer());

    // 转发到 Recall PC
    const recallUrl = telegramCfg.recallUploadUrl
        ?? "http://localhost:5000/api/upload";
    const form = new FormData();
    form.append("file", new Blob([buffer], { type: "image/jpeg" }),
        "mobile.jpg");
    form.append("timestamp", timestamp);
    form.append("source", "mobile");

    await fetch(recallUrl, { method: "POST", body: form });
});
```

**配置新增**（`openclaw.json`）：
```json5
{
    plugins: {
        entries: {
            telegram: {
                screenshotChannelId: "-100xxxxxxxxxx",
                recallUploadUrl: "http://localhost:5000/api/upload"
            }
        }
    }
}
```

### 第 4 步：验证与测试

1. **手动测试频道自收**：
   用 curl 模拟 Android 发图到频道，确认 bot 收到 channel_post
   ```bash
   curl -X POST "https://api.telegram.org/bot<TOKEN>/sendPhoto" \
     -F "chat_id=<CHANNEL_ID>" \
     -F "photo=@test.jpg" \
     -F "caption=mobile|1706700000000"
   ```

2. **验证 OpenClaw 处理**：
   检查 OpenClaw 日志，确认收到 channel_post 并转发到 Recall

3. **验证 Recall 存储**：
   检查 `screenshots/` 目录和数据库，确认图片已保存

4. **Android 端集成测试**：
   编译安装 APK，确认自动截图 → 自动发送 → PC 端收到

## 数据流详解

```
┌─────────────────┐
│  Android Phone   │
│  RecallMobile    │
│  (自动截图)       │
└────────┬────────┘
         │ Telegram Bot API
         │ POST /bot<TOKEN>/sendPhoto
         │ chat_id = 频道ID
         │ caption = "mobile|<timestamp>"
         ▼
┌─────────────────┐
│  Telegram Cloud  │
│  (私有频道)       │
└────────┬────────┘
         │ channel_post update
         │ (bot 作为 admin 自动收到)
         ▼
┌─────────────────┐
│  OpenClaw        │
│  bot-handlers.ts │
│  (识别截图中转)    │
└────────┬────────┘
         │ POST /api/upload
         │ (multipart: file + timestamp)
         ▼
┌─────────────────┐
│  Recall PC       │
│  web/app.py      │
│  (保存+入库+OCR)  │
└─────────────────┘
```

## 优势

- **不需要局域网**：走 Telegram 云端，手机在任何网络都能同步
- **不需要新建机器人**：复用现有 @zzf1955_bot
- **Android 改动最小**：只改 SyncManager 的上传目标
- **Telegram 做 CDN**：图片先存 Telegram 云端，PC 离线时不丢数据
- **天然重试**：Telegram 消息不会丢，OpenClaw 重启后可重新拉取

## 风险与注意事项

1. **频道自收验证**：需先验证 bot 发到频道后能否收到自己的 channel_post。
   如果不行，创建 @recall_relay_bot（5 分钟搞定），用它发图。
2. **Telegram 文件大小限制**：Bot API 上传限 10MB（截图一般 100-500KB，没问题）
3. **频率限制**：Telegram Bot API 限制约 30 msg/sec，截图频率远低于此
4. **国内网络**：手机端可能需要代理访问 Telegram（或用机场）
5. **隐私**：截图经过 Telegram 服务器，注意敏感信息

## 工作量估算

| 模块 | 改动 | 复杂度 |
|------|------|--------|
| 手动创建频道 | Telegram 操作 | 5 分钟 |
| Android SyncManager | 改上传目标 | 小 |
| Android Settings UI | 新增 token/channel 配置 | 小 |
| Recall /api/upload | 新端点（已有方案） | 小 |
| OpenClaw channel_post | 新 handler | 中 |
| 测试验证 | 端到端 | 中 |
