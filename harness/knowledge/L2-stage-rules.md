# L2 — 阶段操作规则（绑定到具体阶段的可执行 checklist）

> **L2 是绑定到某一个或某几个阶段、可在该阶段当 checklist 用的操作规则**：能明确说出
> 「在 X 阶段开工/收尾时执行」。它是 [`L1-principles.md`](L1-principles.md) 价值观在具体阶段的落地动作。
>
> 标题里的 `适用阶段` **必须**是 DAG 阶段名（`clarify` / `plan` / `build` / `verify` / `retrospect`，
> 见 `harness/workflow-dag.json`）——`scripts/validate.py::check_knowledge` 会校验这一点。
> 多阶段用逗号分隔。`derives` 引用 L1 的 `P{n}` 编号，不复述其内容（守唯一事实源 P10）。

---

## S1 ｜适用阶段：clarify, plan ｜tags: spec-freeze, anti-rework
- **规则**：Spec 前置收敛——进入阶段前一次性收敛该阶段的所有关键 Spec（参数、策略、验收口径），再集中实现。
- **derives**：P1(小步快走), P9(沟通)
- **落到执行**：clarify 收敛验收标准与影响面、plan 收敛技术路线与 Phase 拆分；对应两个 mandatory_review。避免边做边改导致返工。
- **来源**：workbook（跨项目通用沉淀）

## S2 ｜适用阶段：verify ｜tags: acceptance, evidence
- **规则**：阶段验收与记录——每阶段完成必须执行验收（自动化优先）；验收工具不可用时允许简化替代，但必须写明「替代方案 + 限制 + 改进建议」。
- **derives**：P5(可追溯)
- **落到执行**：对应 `scripts/gate.py` 跑退出码门禁 + gate card「结论必落证据」；不可裸跳过验收。
- **来源**：workbook（跨项目通用沉淀）

## S3 ｜适用阶段：build, retrospect ｜tags: issue-log, traceability
- **规则**：问题记录规范——执行中记录每一步遇到的问题/报错与解决方案；若未遇到问题，明确标注「未遇到」。
- **derives**：P5(可追溯)
- **落到执行**：build 时随手记录、写进 JSONL 留痕；retrospect 时回读这些记录提炼三类信号（澄清回环 / spec 漂移 / 门禁卡点）。
- **来源**：workbook（跨项目通用沉淀）

## S4 ｜适用阶段：build ｜tags: review, pre-commit
- **规则**：代码审查检查清单——提交前逐项过：理解现有设计? 改动最小? 单一职责? 向后兼容? 加了测试? 命名清晰? 有无重复?
- **derives**：P3(最小改动), P6(向后兼容), P7(单一职责), P8(前置阅读)
- **落到执行**：对应 `skill/review/SKILL.md` 与 scope-guard 角色；在 git commit 前执行。
- **来源**：workbook（跨项目通用沉淀）

## S5 ｜适用阶段：build ｜tags: reproducible, environment
- **规则**：安装/环境记录——任何依赖/工具安装步骤必须写成可复现的步骤（命令 + 执行结果 + 失败原因，如有）。
- **derives**：P5(可追溯)
- **落到执行**：环境类操作不能只在脑子里跑一遍；写下来下次/交接时能照着重来。
- **来源**：workbook（跨项目通用沉淀）

---

## 变更日志
- 2026-06-17 初版：从 Finguard workbook（work_log_and_tracking / experience_rules）抽象出 5 条绑定阶段的操作规则，覆盖 clarify/plan/build/verify/retrospect。
