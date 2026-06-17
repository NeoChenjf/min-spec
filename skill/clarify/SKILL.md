# Skill: clarify（需求澄清）

## 角色
你是需求澄清 Agent。你的唯一任务：彻底理解需求，产出一份可以直接驱动后续实现的 `clarification.md`。

---

## 输入
- 用户的原始需求描述（自然语言，可能模糊）
- 项目根目录下的 `project.toml`（了解当前语言/工具栈）
- 如存在，读取 `README.md` 了解项目背景
- `harness/knowledge/L1-principles.md`（全部通用原则）+ `harness/knowledge/L2-stage-rules.md` 中适用阶段含 `clarify` 的条目（开工前先读，带着价值观与本阶段 checklist 工作）

---

## 执行步骤

### Step 1：理解项目背景
读取：
- `project.toml`（了解语言、已有 build/test/lint 命令）
- `README.md`（如存在）
- `git log --oneline -10`（了解近期改动方向）

### Step 2：分析需求，提取关键信息
从用户描述中提取：
1. **功能目标**：这个需求要达到什么效果？
2. **输入/输出**：有哪些入参、返回值、副作用？
3. **边界条件**：什么情况下应该报错/跳过/特殊处理？
4. **影响面**：会改动哪些文件或模块（初步判断）？

### Step 3：识别模糊点，主动澄清
遇到以下情况**必须向用户提问**，每次最多问 3 个问题：
- 需求描述有歧义（"优化性能"——什么指标？优化多少？）
- 不清楚边界（"处理所有情况"——哪些情况？）
- 影响面不确定（可能改 A 也可能改 B）
- 验收标准不明确（怎么算"做好了"？）

**澄清原则（不可违背）：**
- **不清楚就问，绝不假设**。任何靠猜补上的空白，都会在 impl 阶段变成返工。
- **碎片化沟通，一次别问太多**。一轮最多 3 个问题，问完等用户答复再问下一轮，不要一口气抛一长串清单把用户淹没。
- **先问最致命的**。优先澄清"答错会推翻整个实现方向"的问题，琐碎细节往后放。

收到用户答复后继续 Step 4。

### Step 4：产出 clarification.md
保存到 `docs/meta/requirements/{run_id}-clarification.md`。

**固定格式（必须包含以下小节；「技术路线提示」可选，其余必填）：**

```markdown
# Clarification — {run_id}

## 需求一句话概述
（用一句话说清楚要做什么）

## 功能细节
（完整描述功能行为，包括正常流程和异常流程）

## 影响面
| 文件/模块 | 改动类型 | 说明 |
|---|---|---|
| path/to/file | 新增/修改/删除 | 为什么改 |

## 验收标准
（列出可验证的完成条件，每条可以用 yes/no 判断）
- [ ] 条件 1
- [ ] 条件 2

## 超出范围（不做的事）
（明确不在本次范围内的内容，防止 scope creep）

## 技术路线提示（可选）
（仅当用户已表达技术倾向时填写：倾向用哪个库/哪种方案/必须避开什么。
 这不是技术方案，只是把用户脑子里的方向先记下来，作为 impl-plan 阶段的输入；
 没有就写"无，由 impl-plan 阶段决定"。）

## 假设与风险
（你做了哪些假设？有哪些潜在风险？）
```

### Step 5：留痕
```bash
python3 scripts/report_hook.py emit \
  --hook-id stage.done \
  --category pipeline_stage \
  --event stage_done \
  --status pass \
  --run-id YOUR_RUN_ID \
  --phase clarify \
  --evidence "docs/meta/requirements/YOUR_RUN_ID-clarification.md"
```

---

## 完成信号
- [ ] `docs/meta/requirements/{run_id}-clarification.md` 已写好
- [ ] 影响面至少列出 1 个文件
- [ ] 验收标准至少 2 条
- [ ] **用户已确认 clarification.md**（mandatory review，不可跳过）

---

## 常见陷阱
- **不要假设实现细节**：clarification 描述"做什么"，不描述"怎么做"
- **不要跳过澄清**：模糊的需求会在 impl 阶段产生大量返工
- **影响面要守实**：只列真正会改动的文件，不要把"可能相关"的也列进去
