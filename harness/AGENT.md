# min-spec 入口

> **你（Agent）接到需求后，第一件事是：读 `harness/orchestrator.md`，然后按里面的阶段路由开始执行。**

本文件只做两件事：
1. 教你怎么把 min-spec 复制到自己的项目
2. 说明整个文件夹的结构

执行逻辑、阶段定义、Skill 指引、子 Agent spawn 方式——**全在 `orchestrator.md` 里**，不要在这里找。

---

## 一次性初始化（把 min-spec 装到你的项目）

```bash
# 1. 复制 harness、scripts、skill 到你的项目根
cp -r /path/to/min-spec/harness   your-project/
cp -r /path/to/min-spec/scripts   your-project/
cp -r /path/to/min-spec/skill     your-project/
cp    /path/to/min-spec/.githooks/pre-commit  your-project/.githooks/pre-commit

# 2. 自动生成 project.toml 草稿（会探测语言和命令）
cd your-project
python3 scripts/init.py

# 3. 打开 project.toml，确认 [gates] 里的命令能跑通

# 4. 启用 git 门禁（一次性）
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit

# 5. 验证 harness 结构自洽
python3 scripts/validate.py
```

---

## 文件夹说明

```
your-project/
├── harness/
│   ├── AGENT.md           ← 本文件（初始化指引 + 入口路由）
│   ├── orchestrator.md    ← ★ 主 Agent 合同，从这里开始
│   ├── spec.md            ← 原则层宪法（只读）
│   ├── plan-note-template.md  ← 历史模板，可参考
│   └── workflow-dag.json  ← 阶段 DAG 定义
│
├── skill/                 ← 按阶段加载的执行指令
│   ├── clarify/SKILL.md   ← Stage 1：需求澄清
│   ├── impl-plan/SKILL.md ← Stage 2：拆步骤
│   ├── impl/SKILL.md      ← Stage 3：Phase 编码（子 Agent）
│   └── review/SKILL.md    ← Stage 3：Phase 评审（独立子 Agent）
│
├── scripts/               ← 门禁/留痕工具（只读，不要改）
│   ├── gate.py            ← 门禁执行器
│   ├── report_hook.py     ← 留痕工具
│   ├── init.py            ← 初始化向导
│   └── validate.py        ← 结构校验器
│
├── project.toml           ← ★ 你唯一需要配置的文件
├── .githooks/
│   └── pre-commit         ← git 门禁 hook
│
└── docs/meta/
    ├── gates/             ← gate card 落点
    ├── sessions/          ← 留痕 JSONL 落点
    └── requirements/      ← clarification + impl-plan 落点
```

---

## run_id 约定

整次需求交付用同一个 `run_id` 串联所有产物（clarification、impl-plan、gate card、留痕）。

```bash
# 用时间戳生成
export MINSPEC_RUN_ID="$(date +%Y%m%d-%H%M%S)"

# 或用需求编号
export MINSPEC_RUN_ID="task-42"
```

---

## 下一步

👉 **读 `harness/orchestrator.md`，然后开始执行。**
