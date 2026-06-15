# min-spec

一套**语言无关**的个人小项目开发 spec / agent harness，从美团 hic-spec 的重型企业级 harness（`hic-agent-harness`）精简继承而来。

无论你写 Go、Python、TypeScript 还是 Rust，同一套流程和脚本照常运转——**换语言只改一个 `project.toml`**。

## 一分钟起步

```bash
# 1. 为当前项目生成 project.toml 草稿（自动探测语言，请人工确认 [gates]）
python3 scripts/init.py

# 2. 启用 git 门禁（一次性）
git config core.hooksPath .githooks

# 3. 校验这套 harness 结构自洽
python3 scripts/validate.py

# 4. 手动跑一次门禁
python3 scripts/gate.py
```

## 设计三主线

1. **三层职责分离**：`harness/spec.md` 定原则（永不变）→ `project.toml` 定命令（随项目变，改一处）→ `scripts/gate.py` 只读 toml + 执行 + 看退出码（跨语言通用）。
2. **退出码是唯一裁判**：非零=失败，绝不解析命令输出文本。
3. **非阻塞留痕 + 强制门禁分离**：留痕失败不挡你干活；唯一会挡你的是 `git.pre_commit` 跑的门禁。

## 目录

| 路径 | 作用 |
|---|---|
| `harness/spec.md` | 开发宪法：4 阶段流程 + 门禁/留痕原则 |
| `harness/workflow-dag.json` | 4 阶段 DAG：plan→build→verify→report |
| `harness/state-schema.json` | 运行状态机 schema |
| `harness/gate-card.schema.json` | 门禁结论卡结构契约 |
| `harness/reporting-hooks.json` | 轻量 hook 注册表（3 类） |
| `harness/agents/README.md` | 3 个 subagent 角色合同 |
| `project.toml` | ★真相源：声明 build/test/lint 命令 |
| `scripts/gate.py` | ★门禁：读 toml→跑命令→退出码裁判→产 gate card |
| `scripts/detect.py` | 语言探测（toml 缺失时兜底 / init 时生成草稿） |
| `scripts/report_hook.py` | 轻量留痕 CLI（写 JSONL，吞异常，非阻塞） |
| `scripts/init.py` | 初始化：探测→生成 toml 草稿 + state 初值 |
| `scripts/validate.py` | 结构自洽校验器 |
| `.githooks/pre-commit` | 唯一 git 门禁入口 |
| `docs/meta/sessions/` | JSONL 留痕落点 |
| `docs/meta/gates/` | gate card 产物落点 |
| `.harness/state.json` | 运行态（gitignore） |

详见 `harness/spec.md`。
