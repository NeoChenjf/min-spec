# min-spec Agent 执行手册

> 这是你（AI Agent 或实习生）接到一个需求后的**完整行动指南**。
> 按章节顺序执行，每个阶段结束前完成对应的"✅ 完成信号"再推进。

---

## 准备工作（接需求前做一次）

```bash
# 1. 把 min-spec/harness/ 整个文件夹拷贝到你的项目根
cp -r /path/to/min-spec/harness  your-project/
cp -r /path/to/min-spec/scripts  your-project/
cp    /path/to/min-spec/.githooks/pre-commit  your-project/.githooks/pre-commit

# 2. 在你的项目根生成 project.toml 草稿（会自动探测语言）
cd your-project
python3 scripts/init.py

# 3. 打开 project.toml，确认 [gates] 里的命令能跑通，删掉 "# 自动探测，请确认" 注释

# 4. 启用 git 门禁（一次性配置）
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit

# 5. 验证 harness 结构自洽
python3 scripts/validate.py
```

---

## 阶段一：plan（理解需求，定方案）

**目标**：产出一份 `plan_note`，让人类 reviewer 能判断方案是否合理。

### 你要做的事

1. **读懂需求**——如果需求描述模糊，先列出你的理解和假设，**让用户确认后再继续**
2. **分析影响面**（扮演 `impact-analyzer` 角色）：
   - 这次改动会涉及哪些文件/模块？
   - 有没有调用方需要同步修改？
   - 有没有接口/数据结构变化？
3. **写 plan_note**——使用 `harness/plan-note-template.md` 的格式，保存到：
   ```
   docs/meta/plan/{run_id}-plan-note.md
   ```
4. **留痕**：
   ```bash
   python3 scripts/report_hook.py emit \
     --hook-id stage.enter \
     --category pipeline_stage \
     --event stage_enter \
     --status pass \
     --run-id YOUR_RUN_ID \
     --phase plan \
     --evidence "docs/meta/plan/YOUR_RUN_ID-plan-note.md"
   ```

### ✅ 完成信号

- [ ] `docs/meta/plan/{run_id}-plan-note.md` 已写好
- [ ] **用户已确认方案**（mandatory_review，不可跳过）
- [ ] JSONL 留痕已写入

---

## 阶段二：build（写代码）

**目标**：按 plan_note 的方案实现代码，不多改、不少改。

### 你要做的事

1. **按 plan_note 的范围改代码**，每改一处记录在心
2. **改完后，做 scope 检查**（扮演 `scope-guard` 角色）：
   - 运行 `git diff --name-only`，列出所有改动文件
   - 逐一判断：每个文件的改动是否在 plan_note 声明的范围内？
   - 如有超范围改动：**要么 revert，要么在提交前向用户说明原因**
3. **留痕**：
   ```bash
   python3 scripts/report_hook.py emit \
     --hook-id stage.done \
     --category pipeline_stage \
     --event stage_done \
     --status pass \
     --run-id YOUR_RUN_ID \
     --phase build \
     --evidence "$(git diff --name-only | tr '\n' ',')"
   ```

### ✅ 完成信号

- [ ] 代码改动全部在 plan_note 声明的范围内
- [ ] `git diff --name-only` 的结果已检查，无超范围文件
- [ ] JSONL 留痕已写入

---

## 阶段三：verify（跑门禁）

**目标**：让 `gate.py` 跑一遍，产出 gate card，decision 必须是 `pass`。

### 你要做的事

1. **跑门禁**：
   ```bash
   python3 scripts/gate.py
   ```
2. **看输出**：
   - `decision=pass` → 继续
   - `decision=block` → 找到失败的 gate，修复后重跑，直到 pass
3. **看 gate card**：
   ```bash
   cat docs/meta/gates/{run_id}-gate.md
   ```

### 常见失败原因

| 现象 | 排查方向 |
|---|---|
| `source=auto-detect`，test=skipped | `project.toml` 的 `[gates]` 没配或格式错了，检查文件 |
| test=fail，exit_code 非零 | 跑一遍 `project.toml` 里的 test 命令，看报错信息 |
| build=fail | 编译失败，修代码 |

### ✅ 完成信号

- [ ] `gate.py` 输出 `decision=pass`
- [ ] `docs/meta/gates/{run_id}-gate.md` 存在，decision=pass
- [ ] **用户已确认 gate card**（mandatory_review，不可跳过）

---

## 阶段四：report（小结）

**目标**：写一段简短的交付小结，让用户知道"做了什么、验证了什么、有什么遗留问题"。

### 你要做的事

1. **写 summary**，内容包括：
   - 做了什么（一句话）
   - 改动了哪些文件（列表）
   - gate card 结论（pass/block，附路径）
   - 有没有遗留问题或后续建议
2. **留痕**：
   ```bash
   python3 scripts/report_hook.py emit \
     --hook-id stage.done \
     --category pipeline_stage \
     --event stage_done \
     --status pass \
     --run-id YOUR_RUN_ID \
     --phase report \
     --evidence "docs/meta/gates/YOUR_RUN_ID-gate.md"
   ```
3. **提交**（pre-commit hook 会自动再跑一次门禁，通过才能提交成功）：
   ```bash
   git add -A
   git commit -m "feat/fix/chore: 简短描述"
   ```

### ✅ 完成信号

- [ ] summary 已输出给用户
- [ ] `git commit` 成功（pre-commit hook 通过）
- [ ] 用户无异议

---

## 快速参考：run_id 约定

`run_id` 建议用 `YYYYMMDD-HHMMSS` 格式，也可以是需求编号（如 `task-42`）。
整次运行保持同一个 `run_id`，所有留痕和 gate card 都用它串联。

```bash
# 手动生成一个
export MINSPEC_RUN_ID="$(date +%Y%m%d-%H%M%S)"
# 或直接传给命令
MINSPEC_RUN_ID="task-42" python3 scripts/gate.py
```

---

## 紧急情况：门禁一直 block 怎么办

1. 先读 gate card：`cat docs/meta/gates/{run_id}-gate.md`
2. 找到 `blocking_reason`，按 `next_action` 提示修复
3. 修完重跑：`python3 scripts/gate.py`
4. 如果命令本身就应该失败（如临时调试代码），**不要改 gate.py**，要修代码让命令通过
5. 实在不会修：把 gate card 内容发给带你的同学，附上你的修复思路

---

## 文件夹说明（迁移到自己项目后）

```
your-project/
├── harness/          ← 这套 spec，只读，不要改
│   ├── AGENT.md      ← 就是本文件（执行入口）
│   ├── spec.md       ← 原则层宪法
│   ├── plan-note-template.md  ← plan_note 格式模板
│   └── ...
├── scripts/          ← 门禁/留痕工具，只读，不要改
├── project.toml      ← ★唯一需要你配置的文件
├── .githooks/
│   └── pre-commit    ← git 门禁，启用后自动跑
└── docs/meta/        ← 留痕产物（gate card + JSONL）
    ├── gates/
    ├── sessions/
    └── plan/         ← plan_note 落点（需手动建目录）
```
