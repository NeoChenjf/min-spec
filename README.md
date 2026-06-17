# min-spec

一套**语言无关**的个人小项目开发 spec / agent harness。

无论你写 Go、Python、TypeScript 还是 Rust，同一套流程和脚本照常运转——**换语言只改一个 `project.toml`**。

它把一条重型企业级需求交付链路精简成五阶段、剥掉所有平台绑定，让 AI 做小需求时也能**从需求分析一路自动跑到提交、再回头沉淀经验**。

## 这套 harness 替你跑完整条链路

接到需求时**不要直接写代码**，而是读 `harness/orchestrator.md`（主 Agent 合同），按五阶段 DAG 推进：

```
clarify ──→ plan ──→ build ──→ verify ──→ retrospect
需求澄清    技术路线+   分阶段写码   退出码      回读留痕、
（多轮、    五要素      ↳ 每Phase:   门禁       沉淀经验
 不假设）   Phase计划    写→独立反思             反哺下次
            +独立评审    →修复→提交
```

| 阶段 | 做什么 | 产物 | 人审 |
|---|---|---|---|
| **clarify** | 多轮澄清需求、不假设，定影响面与验收标准 | `{run_id}-clarification.md` | **强制** |
| **plan** | 定技术路线，拆 Phase（里程碑/原子步骤/依赖/验证/风险回滚五要素）+ 独立评审 | `{run_id}-impl-plan.md` | **强制** |
| **build** | 切 feature 分支，每 Phase：写码 → 独立上下文反思 → 修复 → commit | 代码 + commit | 每 Phase review |
| **verify** | 跑退出码门禁收口 | `{run_id}-gate.md` gate card | **强制** |
| **retrospect** | 回读本次 jsonl 留痕 + 产物，提炼经验，追加进跨交付经验库 | `{run_id}-retro.md` + `lessons.md` | 建议 |

整次交付用同一个 `run_id`（`YYYYMMDD-HHMMSS` 或需求编号）串联所有产物。

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

装到别的项目：见 `harness/AGENT.md`。

## 设计三主线

1. **三层职责分离**：`harness/spec.md` 定原则（永不变）→ `project.toml` 定命令（随项目变，改一处）→ `scripts/gate.py` 只读 toml + 执行 + 看退出码（跨语言通用）。
2. **退出码是唯一裁判**：非零=失败，绝不解析命令输出文本。
3. **非阻塞留痕 + 强制门禁分离**：留痕失败不挡你干活；唯一会挡你的是 `git.pre_commit` 跑的门禁。

## 目录

| 路径 | 作用 |
|---|---|
| `harness/AGENT.md` | 入口路由 + 如何把 min-spec 装到其他项目 |
| `harness/orchestrator.md` | ★主 Agent 合同：五阶段路由、前置校验、子 Agent spawn |
| `harness/spec.md` | 开发宪法：门禁/留痕原则（只读，永不变） |
| `harness/workflow-dag.json` | 五阶段 DAG：clarify→plan→build→verify→retrospect |
| `harness/state-schema.json` | 运行状态机 schema |
| `harness/gate-card.schema.json` | 门禁结论卡结构契约 |
| `harness/reporting-hooks.json` | 轻量 hook 注册表 |
| `harness/plan-note-template.md` | 历史模板，可参考 |
| `harness/knowledge/` | 分层知识库：L1 跨阶段原则 + L2 阶段操作规则（随模板分发，子 Agent 开工前读） |
| `skill/clarify/SKILL.md` | clarify 阶段执行指令 |
| `skill/impl-plan/SKILL.md` | plan 阶段执行指令 |
| `skill/impl/SKILL.md` | build 阶段 Phase 编码（子 Agent） |
| `skill/review/SKILL.md` | build 阶段 Phase 独立评审（独立子 Agent） |
| `skill/retro/SKILL.md` | retrospect 阶段复盘沉淀执行指令 |
| `project.toml` | ★真相源：声明 build/test/lint 命令 |
| `scripts/gate.py` | ★门禁：读 toml→跑命令→退出码裁判→产 gate card |
| `scripts/detect.py` | 语言探测（toml 缺失时兜底 / init 时生成草稿） |
| `scripts/report_hook.py` | 轻量留痕 CLI（写 JSONL，吞异常，非阻塞） |
| `scripts/init.py` | 初始化：探测→生成 toml 草稿 + state 初值 |
| `scripts/validate.py` | 结构自洽校验器 |
| `.githooks/pre-commit` | 唯一 git 门禁入口 |
| `docs/meta/requirements/` | clarification + impl-plan 落点 |
| `docs/meta/sessions/` | JSONL 留痕落点 |
| `docs/meta/gates/` | gate card 产物落点 |
| `docs/meta/retro/` | retro card 产物落点（每次交付复盘） |
| `docs/meta/knowledge/lessons.md` | 跨交付经验库（retrospect 只追加沉淀） |
| `.harness/state.json` | 运行态（gitignore） |

接到需求从 `harness/orchestrator.md` 开始；原则细节见 `harness/spec.md`。
