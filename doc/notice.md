# Notice

## 2026-03-09 L2 task001 环境踩坑

1. `git worktree add` 在沙箱下可能报错：
   - 现象：`cannot lock ref ... unable to create directory for .git/refs/heads/...`
   - 原因：沙箱禁止写 `.git/refs`
   - 处理：使用提权执行 `git worktree add`。

2. `npm install` 在沙箱下可能失败：
   - 现象：`EPERM: operation not permitted`（写 `~/.npm/_logs` 或拉取 registry）
   - 处理：提权执行 `npm install`。

3. 本地联通验证时注意代理：
   - 若系统开启代理（如 `127.0.0.1:7897`），`curl 127.0.0.1` 可能被错误转发。
   - 处理：请求本地端口时使用 `env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY curl ...`。

4. 在 zsh 沙箱中后台命令可能触发 `nice(5) failed`：
   - 处理：后台运行前执行 `unsetopt BG_NICE`，或改用 `bash` 执行验证脚本。
