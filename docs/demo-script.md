# 赛事演示流程（3-5 分钟）

# openKylin 桌面演示脚本（3-5 分钟）

本脚本只描述待录制操作，不宣称视频已录制。使用用户级凭据文件加载环境变量，录屏时遮挡终端中的密钥输入和任何敏感响应。当前自动化 SSH 会话没有 `DISPLAY`/Wayland 图形变量，因此视频尚未录制；具备 openKylin 桌面会话时可运行 `scripts/record_desktop_demo.sh runs/desktop-demo 300` 录制 5 分钟画面并生成 SHA256/媒体信息。

录制前准备：

```bash
mkdir -p runs/desktop-demo
ffmpeg -version | head -1
test -n "${DISPLAY:-}" && echo "desktop display ready" || echo "run from desktop terminal"
```

## 0:00-0:30 安装与环境

```bash
uname -a
cat /etc/os-release
dpkg-deb --info dist/kylin-memory-bench_0.2.0_all.deb
bash scripts/install_deb.sh dist/kylin-memory-bench_0.2.0_all.deb
kmb validate --strict --suite /usr/share/kylin-memory-bench/suites/core-zh.yaml
```

## 0:30-1:00 配置与六类案例

```bash
kmb list-cases --suite /usr/share/kylin-memory-bench/suites/core-zh.yaml
set -a; . "$HOME/.config/kmb/credentials.env"; set +a
```

展示两份配置的 `name`、`model`、`base_url` 和 `api_key_env`，不要打开或打印凭据文件。

## 1:00-2:30 双 Agent 真实对比

```bash
python -m kmb.cli compare \
  --agents configs/agent-grok-memory.yaml configs/agent-deepseek-memory.yaml \
  --suite suites/core-zh.yaml \
  --out runs/demo-real --run-id demo-real-20260906 --seed 42 --retries 1 --timeout 180
python scripts/verify_run.py runs/demo-real/grok-memory-controller --strict
python scripts/verify_run.py runs/demo-real/deepseek-memory-controller --strict
```

打开 `runs/demo-real/comparison.html`，展示两款真实后端、六维雷达图和失败统计。展开一个案例，指出 `evidence.jsonl` 中 `source=model` 的请求/回答与 `source=wrapper` 的记忆、动作事件；强调这是统一包装层下的系统级行为，不是模型原生记忆证明。

## 2:30-3:30 无记忆对照

```bash
python -m kmb.cli compare \
  --agents configs/agent-grok-memory.yaml configs/agent-grok-no-memory.yaml \
  --suite suites/core-zh.yaml \
  --out runs/demo-baseline --run-id demo-baseline-20260906 --seed 42 --retries 1 --timeout 180
```

展示 no-memory Agent 的 `mode=no_memory_baseline`、`memory_disabled_events`、recall miss 和动作阻断理由。说明它仍完成同样六类案例和真实 API 请求，关闭的只是外部记忆/动作控制器。

## 3:30-4:30 证据、报告与复现

```bash
find runs/demo-real -maxdepth 2 -type f | sort
find runs/demo-baseline -maxdepth 2 -type f | sort
sha256sum runs/demo-real/comparison.json runs/demo-baseline/comparison.json
```

最后展示 JSON/JSONL、Markdown、HTML、SVG 文件和运行 ID、seed、重试参数。若现场需要卸载，在演示结束后执行 `bash scripts/uninstall_deb.sh`，不删除用户选择保留的结果目录。

## 4:30-5:00 发布包生命周期（可选镜头）

若终端具备 `sudo/root`，使用下列脚本完整记录安装、版本检查、验证、升级、升级后验证、卸载和残留检查。该脚本把每一步 stdout/stderr/退出码分别保存到结果目录：

```bash
bash scripts/record_deb_lifecycle.sh runs/deb-lifecycle-demo \
  dist/kylin-memory-bench_0.2.0_all.deb \
  dist/kylin-memory-bench_0.2.0+test1_all.deb
```

若当前会话没有 sudo/root，只展示 `dpkg-deb --info`、`dpkg-deb --contents` 和已完成的用户态 payload smoke，不得把它讲成系统级 `dpkg -i` 成功。
