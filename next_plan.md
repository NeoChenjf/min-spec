# min-spec 交接文档（next_plan）

> 前一个 agent 因频繁卡顿移交。本文档让你无缝接手。**任务主体已完成约 90%，只差验证收尾和一个待确认的 bug 修复。**

## 一、这个项目是什么

`/Users/chenjunfeng/projects/min-spec` 是一套**语言无关的个人小项目开发 spec / agent harness**，从美团 hic-spec 的重型企业级 harness（`hic-agent-harness`）精简继承而来。

完整设计与决策记录见：`/Users/chenjunfeng/.claude/plans/shimmying-conjuring-melody.md`（**接手前务必先读这份**，它是已获用户批准的实施计划）。

### 三条核心设计主线（不可动摇）
1. **三层职责分离**：`harness/spec.md` 定原则（永不变）→ `project.toml` 定命令（随项目变，改一处）→ `scripts/gate.py` 只读 toml + 执行 + 看退出码（跨语言通用）。
2. **退出码是唯一裁判**：非零=失败，**绝不解析命令的 stdout 文本**（这是语言无关的关键）。
3. **非阻塞留痕 + 强制门禁分离**：留痕（写 JSONL）失败绝不挡人干活（try/except 吞异常）；唯一例外是 `git.pre_commit` 跑的门禁，它非零退出会故意拦提交。

## 二、已完成的文件（全部已创建）

```
min-spec/
├── README.md                      ✅ 一分钟起步 + 设计说明
├── project.toml                   ✅ 真相源示例（本仓用 validate.py 当 test 门禁）
├── .gitignore                     ✅ 忽略 .harness/
├── harness/
│   ├── spec.md                    ✅ 开发宪法：4 阶段 + 门禁/留痕原则
│   ├── workflow-dag.json          ✅ 4 阶段 DAG：plan→build→verify→report
│   ├── state-schema.json          ✅ 运行状态机 schema
│   ├── gate-card.schema.json      ✅ 门禁结论卡契约
│   ├── reporting-hooks.json       ✅ 轻量 hook 注册表（3 类）
│   └── agents/README.md           ✅ 3 个 subagent 角色合同
├── scripts/
│   ├── gate.py                    ✅ ★门禁核心（含 Python<3.11 的 TOML 兜底解析器）
│   ├── detect.py                  ✅ 语言探测兜底
│   ├── report_hook.py             ✅ 轻量留痕 CLI（写 JSONL）
│   ├── init.py                    ✅ 初始化：探测→生成 toml 草稿 + state
│   └── validate.py                ✅ 结构自洽校验器
├── .githooks/pre-commit           ✅ 唯一 git 门禁入口
├── docs/meta/sessions/            ✅ JSONL 留痕落点
├── docs/meta/gates/               ✅ gate card 落点
└── examples/hello-node/           ✅ 验证用 Node 示例（已建 project.toml）
```

## 三、关键环境事实（很重要）

- **系统 `python3` 是 3.9.6**（`/usr/bin/python3`，保留不动），**没有 tomllib**（3.11+ 才内置）。
- 新装了 **Python 3.13.14 通过 uv 管理**（`uv run python`），但系统默认 `python3` 仍是 3.9。
- **决策：min-spec 脚本一律用 `python3`（不绑 uv）**，因为核心卖点是"零依赖、谁都能跑"。为此 `gate.py` 已加极简 TOML 兜底解析器 `_parse_gates_minimal()`，让它在裸 3.9 下也能正确读 `[gates]`。**保留这个兜底，不要删，也不要把 python3 改成 uv run。**

## 四、已发现并已修复（待最终确认）的 bug

**Bug**：`gate.py` 原来写 `if toml_path.exists() and tomllib is not None:` —— 在 3.9（无 tomllib）下直接跳过 toml 读取、走探测兜底，导致 `project.toml` 形同虚设、门禁全 skipped。

**修复**：已在 `scripts/gate.py` 的 `load_gates()` 加 `_parse_gates_minimal()`（tomllib 不可用时用它解析 `key = "value"`）。**修复已写入文件，但最后一次验证运行被卡顿打断，尚未确认输出。** 第一件事就是跑验证 B 确认。

## 五、你要做的事：跑完端到端验证 A–F

工作目录 `cd /Users/chenjunfeng/projects/min-spec`。逐条跑，**一次一个命令**。

### A. 结构自洽（已通过，可复跑确认）
```bash
python3 scripts/validate.py; echo "退出码=$?"
```
期望：打印"min-spec 校验通过：结构自洽。"，退出码 0。

### B. 门禁 pass + 缺省跳过 + 留痕（★上次被打断处，先验证 bug 修复）
```bash
MINSPEC_PROJECT_ROOT="$PWD/examples/hello-node" MINSPEC_RUN_ID="testB" python3 scripts/gate.py; echo "退出码=$?"
cat examples/hello-node/docs/meta/gates/testB-gate.md
cat examples/hello-node/docs/meta/sessions/testB.jsonl
```
期望：
- 日志里 **`source=project.toml`**（不是 auto-detect——这是验证 bug 已修的关键信号）
- gate card：test=pass、build/lint=skipped，decision=pass，退出码 0
- JSONL 有一条 `quality.gate_run` 事件
- 若仍显示 `source=auto-detect` 或 test=skipped，去查 `gate.py` 的 `_parse_gates_minimal()` 与 `load_gates()`。

### C. 退出码唯一裁判（不被 stdout 骗）
```bash
cat > examples/hello-node/project.toml <<'TOML'
[project]
name = "hello-node"
[gates]
test = "node -e 'console.log(\"ALL TESTS PASSED\"); process.exit(1)'"
TOML
MINSPEC_PROJECT_ROOT="$PWD/examples/hello-node" MINSPEC_RUN_ID="testC" python3 scripts/gate.py; echo "退出码=$?"
```
期望：尽管 stdout 打印 "ALL TESTS PASSED"，因 `exit(1)` → decision=block、退出码 1。

### D. 跨语言不改脚本（Python 示例）
```bash
mkdir -p examples/hello-py
cat > examples/hello-py/project.toml <<'TOML'
[project]
name = "hello-py"
[gates]
test = "python3 -c 'import sys; sys.exit(0)'"
TOML
MINSPEC_PROJECT_ROOT="$PWD/examples/hello-py" MINSPEC_RUN_ID="testD" python3 scripts/gate.py; echo "退出码=$?"
```
期望：同一个 gate.py 一行没改，吃下第二种语言，退出码 0、test=pass。

### E. 探测兜底 + init
```bash
mkdir -p examples/hello-go
printf 'module hello\n\ngo 1.21\n' > examples/hello-go/go.mod
python3 scripts/init.py --root examples/hello-go
cat examples/hello-go/project.toml
```
期望：生成 project.toml 草稿，`[gates]` 自动填 `go build ./...` / `go test ./...`，每条带 `# 自动探测，请确认` 注释；同时生成 `examples/hello-go/.harness/state.json`。

### F. git 门禁阻塞 vs 留痕非阻塞（在 min-spec 本仓根验证）
```bash
git config core.hooksPath .githooks
git add -A && git commit -m "feat: min-spec 语言无关开发 harness 初版

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```
期望：pre-commit 跑 gate.py，本仓 project.toml 的 test=validate.py 通过 → 提交成功。
（可选反向验证：临时把本仓 project.toml 的 test 改成 `python3 -c 'import sys;sys.exit(1)'`，commit 应被拦；验证完改回。）

## 六、收尾

1. 验证通过后，清掉临时产物（testB/testC/testD 的 gate card 与 JSONL 可删；建议保留 hello-node/hello-py/hello-go 作样例）。
2. **提交代码**（见验证 F）。当前分支 `master`，主分支 `main`。用户尚未要求 push，提交即可，**push 前先问一句**。
3. 任务清单（TaskList）里 #4/#6/#7 标 in_progress，跑完验证后逐个置 completed（一次一个 TaskUpdate 调用）。

## 七、配套资源（已就绪，本轮不需再动）

- **HiC 沙箱**：常驻沙箱 `pqqdayw6ewg6x7li3zpf7` 已配好用户 git 身份（chenjunfeng / chenjunfeng09@meituan.com），公钥已备案。另有弹性沙箱 `i93j5n1sk7qnp6enk692i`，内含同份 harness 于 `~/min-spec-work/`。后续若要把 min-spec 推到**内网仓库**才需要用沙箱（本地 Mac 连不上 git.sankuai.com）。推送走 `~/.claude/skills/neo-hic-sandbox/`，惯用身份已写进该 skill 的 SKILL.md。
- 源 harness 参考：`/Users/chenjunfeng/hic-spec/plugin/hic-agent-harness/`。

## 八、给接手 agent 的提醒

- **一次只发一个工具调用**。前一个 agent 频繁在"一条消息塞多个工具调用"时被截断报 malformed（疑似响应被截断/限流），单调用从不出错。
- 脚本里所有 `python3` 指系统 3.9，已靠兜底解析器兼容，**别擅自改成 `uv run`**，那会破坏"零依赖谁都能跑"的设计。
