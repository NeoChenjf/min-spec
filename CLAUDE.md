# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 这个仓库是什么

min-spec 是一套**语言无关的个人小项目开发 spec / agent harness**——它本身不是某个应用，而是"一套约束 AI 怎么交付需求的流程 + 一组执行脚本"。从美团 hic-spec 的重型企业级 harness 精简而来。设计目标：换语言只改一个 `project.toml`，流程和脚本不动。

仓库有**双重身份**，理解这点是高效工作的前提：
1. **它是一套可被复制到别处的 harness 模板**（`harness/` + `skill/` + `scripts/` 拷到任意项目即可用）。
2. **它同时用自己这套 harness 来约束自身的开发**（本仓的 `project.toml` 把 `python3 scripts/validate.py` 当作 test 门禁）。

## 接到需求时的入口（重要）

**不要直接开始写代码。** 本仓用 Orchestrator/Subagent 模式编排需求交付：

1. 接到任何需求，第一步读 `harness/orchestrator.md`——它是主 Agent 合同，定义了阶段路由、前置校验、子 Agent spawn 方式。
2. 按 orchestrator 的五阶段 DAG 推进：`clarify → plan → build → verify → retrospect`（定义见 `harness/workflow-dag.json`）。
3. `harness/AGENT.md` 是入口路由 + 如何把 min-spec 安装到其他项目的指引。

五阶段与人审点：

| 阶段 | 调度 | 产物落点 | 人审 |
|---|---|---|---|
| clarify | `skill/clarify/SKILL.md` | `docs/meta/requirements/{run_id}-clarification.md` | **强制** |
| plan | `skill/impl-plan/SKILL.md` + spawn 独立 review agent | `docs/meta/requirements/{run_id}-impl-plan.md` | **强制** |
| build | 每个 Phase：spawn `skill/impl/SKILL.md` → spawn `skill/review/SKILL.md` → 必要时 fix | 代码 + commit + JSONL 留痕 | 每 Phase review |
| verify | `python3 scripts/gate.py` | `docs/meta/gates/{run_id}-gate.md` | **强制** |
| retrospect | `skill/retro/SKILL.md` | `docs/meta/retro/{run_id}-retro.md` + `docs/meta/knowledge/lessons.md` | 建议 |

**retrospect（复盘沉淀）是闭环的最后一环**：门禁过后回读本次 jsonl 留痕 + gate + 产物，提炼经验，把可复用的教训追加进跨交付的经验库 `docs/meta/knowledge/lessons.md`，反哺下一次交付。只读 + 追加，不改代码、不动正式产物、不覆盖经验库。

**run_id 约定**：整次交付用同一个 `run_id`（`YYYYMMDD-HHMMSS` 或需求编号）串联所有产物。通过环境变量传递：`export MINSPEC_RUN_ID="$(date +%Y%m%d-%H%M%S)"`。

## 三层职责分离（语言无关的核心机制，不可破坏）

| 层 | 是什么 | 文件 |
|---|---|---|
| 原则层 | "必须过门禁"的规矩，永不变 | `harness/spec.md`（只读宪法） |
| 声明层 | build/test/lint 到底是哪几条命令，随项目变 | `project.toml` 的 `[gates]` 段 |
| 执行层 | 读 toml → 跑命令 → 看退出码，跨语言通用 | `scripts/gate.py` |

铁律（违反就破坏了整套设计）：
- **退出码是唯一裁判**：`gate.py` 只看命令退出码（0=过，非零=挂），**绝不解析命令的 stdout 文本**。
- **门禁失败要改代码，不改门禁**：verify 阶段 `decision=block` 时修复代码重跑，**不要改 `gate.py` 或 `project.toml` 里的命令**让它通过。
- **缺省即跳过**：`project.toml` 没声明的门禁（如纯脚本项目没 build）自动跳过、不报错。
- **`scripts/` 是只读工具**：编排过程中不要改 `scripts/` 下的脚本，除非需求本身就是改进 harness。

## 常用命令

```bash
# 结构自洽校验（本仓的 test 门禁就是它；改了 harness/ 下任何契约后必跑）
python3 scripts/validate.py

# 手动跑质量门禁（读 project.toml 的 [gates]，按 build→test→lint 顺序执行）
python3 scripts/gate.py

# 为一个新项目生成 project.toml 草稿（自动探测语言）+ state 初值
python3 scripts/init.py --root <项目路径>

# 启用 git 门禁（一次性；pre-commit 会自动跑 gate.py，挂了拦提交）
git config core.hooksPath .githooks

# 留痕（非阻塞，写 docs/meta/sessions/{run_id}.jsonl）
python3 scripts/report_hook.py emit --hook-id <id> --category <cat> --event <ev> --status <st> --run-id <run_id>
```

本仓**没有传统单测框架**——`scripts/validate.py` 就是它的测试：它检查所有契约文件存在、DAG 自洽、state schema 的 `current_stage` 枚举与 DAG stages 一致、hook 的 blocking 标记正确、gate-card schema 字段与 `gate.py` 写出的字段不漂移。**改了 `harness/` 下的 DAG / schema / 文件清单后，务必跑 `validate.py` 确认没引入漂移。**

## 关键约束与陷阱

- **Python 版本**：脚本用系统 `python3`（本机是 3.9，无 `tomllib`）。`gate.py` 内置了 `_parse_gates_minimal()` 极简 TOML 兜底解析器来兼容 3.9——**保留它，不要删，也不要把脚本里的 `python3` 改成 `uv run`**，那会破坏"零依赖、谁都能跑"的设计前提。
- **改 DAG 阶段时三处要同步**：`harness/workflow-dag.json` 的 stages、`harness/state-schema.json` 的 `current_stage` 枚举、`scripts/validate.py` 的 `REQUIRED_FILES`——`validate.py` 会校验前两者一致，漏改会报错。
- **新增 skill 或契约文件**：要同步加进 `validate.py` 的 `REQUIRED_FILES`，否则校验通不过。
- **子 Agent 必须独立上下文**：build 阶段的 impl 和 review 各自 spawn、互不共享思考过程（review 要独立建立基线再看代码）。
- **非阻塞留痕**：`report_hook.py` 写 JSONL 失败一律吞异常，绝不阻塞主流程；唯一会挡操作的是 `git.pre_commit`（它跑门禁，是门禁不是留痕）。

## 产物落点

- `docs/meta/requirements/` — clarification + impl-plan
- `docs/meta/gates/` — gate card（门禁结论）
- `docs/meta/retro/` — retro card（每次交付复盘）
- `docs/meta/knowledge/lessons.md` — 跨交付经验库（retrospect 阶段只追加沉淀）
- `docs/meta/sessions/` — JSONL 留痕
- `.harness/state.json` — 单次运行状态（gitignore，不进版本库）
