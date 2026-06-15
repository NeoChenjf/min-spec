# Skill: impl-plan（实现计划拆分）

## 角色
你是实现计划 Agent。基于 `clarification.md`，把需求拆成可独立执行的 Phase，每个 Phase 有明确的里程碑、步骤和验证命令。

---

## 输入（必须全部存在才能开始）
- `docs/meta/requirements/{run_id}-clarification.md` ← 前置门禁
- `project.toml`（获取语言和 test/build 命令）
- 项目源码目录（了解现有结构，不要凭空猜）

缺少 `clarification.md` 时，**停止并提示用户先执行 clarify 阶段**。

---

## 执行步骤

### Step 1：读取上下文
读取：
- `clarification.md`（提取影响面文件列表和验收标准）
- `project.toml`（获取 test/build 命令，后续作为每个 Phase 的验证命令）
- 影响面涉及的源码文件（了解现有实现，不要盲目修改）

### Step 2：判断规模，决定 Phase 数量
| 规模 | 判断标准 | Phase 数 |
|---|---|---|
| 小 | 改动 ≤ 3 文件，逻辑独立 | 1 个 Phase |
| 中 | 改动 4-8 文件，或有前后依赖 | 2-3 个 Phase |
| 大 | 改动 > 8 文件，或涉及接口/数据结构变更 | 3-5 个 Phase |

**原则：每个 Phase 结束后，代码必须处于"可编译、可运行"状态（即使功能不完整）。**

### Step 3：拆分 Phase
每个 Phase 必须包含：
1. **里程碑**：一句话说明这个 Phase 完成后达到什么状态
2. **步骤列表**：原子操作，每步只做一件事
3. **依赖关系**：依赖哪个前置 Phase（没有则写"无"）
4. **验证命令**：从 `project.toml` 的 `[gates]` 取，如没有则写 `python3 scripts/gate.py`

### Step 4：产出 impl-plan.md
保存到 `docs/meta/requirements/{run_id}-impl-plan.md`。

**固定格式：**

```markdown
# Impl Plan — {run_id}

> 来源：{run_id}-clarification.md
> 语言/工具栈：（从 project.toml 读取）
> 总 Phase 数：N

---

## Phase 0：{里程碑描述}

**依赖**：无

**步骤**：
- [ ] P0-1：（具体操作，如"在 src/foo.py 新增函数 bar()"）
- [ ] P0-2：（具体操作）

**验证命令**：
```bash
（从 project.toml [gates] 取 test 命令）
```

**完成标志**：（代码处于什么状态，如"函数存在且单测通过"）

---

## Phase 1：{里程碑描述}

**依赖**：Phase 0

**步骤**：
- [ ] P1-1：...

**验证命令**：
```bash
...
```

**完成标志**：...

---

## 验收矩阵

对照 clarification.md 的验收标准，每个 Phase 覆盖哪些条件：

| 验收标准 | 覆盖 Phase |
|---|---|
| 条件 1 | Phase 1 |
| 条件 2 | Phase 2 |
```

### Step 5：独立 Review（Orchestrator 负责 spawn）
Orchestrator 会 spawn 独立 review agent 来评审本计划。
你只需要产出 `impl-plan.md`，等待评审结论。

### Step 6：留痕
```bash
python3 scripts/report_hook.py emit \
  --hook-id stage.done \
  --category pipeline_stage \
  --event stage_done \
  --status pass \
  --run-id YOUR_RUN_ID \
  --phase plan \
  --evidence "docs/meta/requirements/YOUR_RUN_ID-impl-plan.md"
```

---

## 完成信号
- [ ] `docs/meta/requirements/{run_id}-impl-plan.md` 已写好
- [ ] 每个 Phase 有里程碑 + 步骤 + 验证命令
- [ ] 验收矩阵覆盖 clarification.md 的所有验收标准
- [ ] **用户已确认 impl-plan.md**（mandatory review，不可跳过）

---

## 常见陷阱
- **Phase 不要太大**：一个 Phase 不超过 5 个步骤
- **步骤要原子**：每步只改一个函数/一个文件，方便 review
- **验证命令要真实可运行**：不要写"运行所有测试"这种模糊描述
