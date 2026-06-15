# min-spec 开发 Spec

这是 min-spec 的开发宪法。它定义**做事的流程和原则**，但**不绑定任何编程语言**——同一套流程，无论你写 Go、Python、TypeScript 还是 Rust，都照常运转。

## 一、三层职责分离（语言无关的核心）

| 层 | 是什么 | 多久变一次 | 文件 |
|---|---|---|---|
| **原则层** | "必须过门禁"这条规矩 | 永不变 | 本文件 `harness/spec.md` |
| **声明层** | build/test/lint 到底是哪几条命令 | 随项目变，改一处 | 项目根 `project.toml` |
| **执行层** | 读声明 → 跑命令 → 看退出码 | 一次写好，跨语言通用 | `scripts/gate.py` |

比喻：本文件是**交通法**（"红灯停"永远成立），`project.toml` 是**这条路口的信号灯配时表**（每个路口不同），`gate.py` 是**只认红绿灯不认路名的司机**。换城市（换语言）只换配时表，法和司机都不动。

## 二、四阶段工作流

完整定义见 `harness/workflow-dag.json`。一次开发按 `plan → build → verify → report` 推进：

| 阶段 | 做什么 | 人审 | 产物 |
|---|---|---|---|
| **plan** | 理解需求、定方案 | **强制人审** | plan_note + JSONL 留痕 |
| **build** | 写代码 | 自动放行 | changeset + JSONL 留痕 |
| **verify** | 跑门禁（build/test/lint 全过） | **强制人审** | gate card + JSONL 留痕 |
| **report** | 小结 | 产物审 | summary + JSONL 留痕 |

## 三、门禁原则（唯一会挡你的东西）

1. **退出码是唯一裁判**：`project.toml` 里 `[gates]` 声明的每条命令，退出码 `0` 即过，非零即挂。**绝不解析命令的输出文本**——因为 npm / pytest / cargo 的输出格式天差地别，但"非零=失败"是所有语言通用的契约。
2. **执行顺序**：`build → test → lint`，任一非零即停（快速失败）。
3. **缺省即跳过**：`project.toml` 里没声明的门禁（比如纯脚本项目没 `build`）直接跳过，**不报错**，gate card 记为 `skipped`。
4. **结论必须落证据**：每次门禁（无论过没过）都产出一张 gate card 到 `docs/meta/gates/{run_id}-gate.md`，结构见 `harness/gate-card.schema.json`。

跑门禁：`python3 scripts/gate.py`

## 四、留痕原则（不挡你，只记账）

- 阶段切换、门禁结果、subagent 检查都通过 `scripts/report_hook.py` 追加到 `docs/meta/sessions/{run_id}.jsonl`。
- **非阻塞**：留痕写入失败（磁盘满、目录只读等）一律被吞掉，**绝不影响你干活**。
- **唯一例外**：`git.pre_commit`（`.githooks/pre-commit`）会跑门禁，门禁挂就拦提交——但这是**门禁**，不是留痕。
- hook 注册表见 `harness/reporting-hooks.json`。

## 五、subagent 角色

3 个角色（`impact-analyzer` / `scope-guard` / `plan-reviewer`），职责与"必须产出证据路径"的铁律见 `harness/agents/README.md`。

## 六、起步

```bash
# 1. 为当前项目生成 project.toml 草稿（自动探测语言，请人工确认）
python3 scripts/init.py

# 2. 启用 git 门禁（一次性）
git config core.hooksPath .githooks

# 3. 校验这套 harness 结构自洽
python3 scripts/validate.py

# 4. 手动跑一次门禁
python3 scripts/gate.py
```

## 七、Agent 执行清单（每次需求必跑）

接到需求后，按以下清单逐项执行。完整步骤和命令见 `harness/AGENT.md`。

```
[ ] plan 阶段
    [ ] 读懂需求，列出假设，用户确认
    [ ] 分析影响面（impact-analyzer 角色）
    [ ] 写 plan_note（用 harness/plan-note-template.md）
    [ ] ⚠️  mandatory_review：用户确认 plan_note 后才能进入 build

[ ] build 阶段
    [ ] 按 plan_note 范围写代码
    [ ] 检查 git diff，无超范围改动（scope-guard 角色）
    [ ] 留痕（report_hook.py emit）

[ ] verify 阶段
    [ ] python3 scripts/gate.py
    [ ] gate card decision=pass
    [ ] ⚠️  mandatory_review：用户确认 gate card

[ ] report 阶段
    [ ] 输出 summary（做了什么 / 改了哪些文件 / gate 结论）
    [ ] git commit（pre-commit hook 自动再跑一次门禁）
```

> **两个不可跳过的强制人审点**：plan 方案确认 + verify gate card 确认。
> 其余阶段 Agent 可自动推进。
