# Notice

## 2026-03-09 L2 task001 鐜韪╁潙

1. `git worktree add` 鍦ㄦ矙绠变笅鍙兘鎶ラ敊锛?   - 鐜拌薄锛歚cannot lock ref ... unable to create directory for .git/refs/heads/...`
   - 鍘熷洜锛氭矙绠辩姝㈠啓 `.git/refs`
   - 澶勭悊锛氫娇鐢ㄦ彁鏉冩墽琛?`git worktree add`銆?
2. `npm install` 鍦ㄦ矙绠变笅鍙兘澶辫触锛?   - 鐜拌薄锛歚EPERM: operation not permitted`锛堝啓 `~/.npm/_logs` 鎴栨媺鍙?registry锛?   - 澶勭悊锛氭彁鏉冩墽琛?`npm install`銆?
3. 鏈湴鑱旈€氶獙璇佹椂娉ㄦ剰浠ｇ悊锛?   - 鑻ョ郴缁熷紑鍚唬鐞嗭紙濡?`127.0.0.1:7897`锛夛紝`curl 127.0.0.1` 鍙兘琚敊璇浆鍙戙€?   - 澶勭悊锛氳姹傛湰鍦扮鍙ｆ椂浣跨敤 `env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY curl ...`銆?
4. 鍦?zsh 娌欑涓悗鍙板懡浠ゅ彲鑳借Е鍙?`nice(5) failed`锛?   - 澶勭悊锛氬悗鍙拌繍琛屽墠鎵ц `unsetopt BG_NICE`锛屾垨鏀圭敤 `bash` 鎵ц楠岃瘉鑴氭湰銆



1. Workspace scripts may fail to resolve `.bin` shims in this environment.
   - Symptom: `tsc` or `vite` is reported as not found during `npm run ...`.
   - Mitigation: call local CLIs explicitly, for example `node ../node_modules/typescript/bin/tsc` and `node ../node_modules/vite/bin/vite.js`.
2. `node --test` may fail with `spawn EPERM` under sandbox isolation.
   - Symptom: each compiled test file fails before execution.
   - Mitigation: run tests with `--test-isolation=none`.
3. Vite build may fail with `spawn EPERM` because `esbuild` starts a worker process.
   - Mitigation: rerun `npm run build` with escalation when sandbox blocks worker spawning.

