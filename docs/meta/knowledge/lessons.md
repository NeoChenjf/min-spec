# 经验库（lessons）

> 跨交付沉淀的可复用教训。由 retrospect 阶段（`skill/retro/SKILL.md`）**只追加不覆盖**地写入。
> 每条带「适用阶段」标签——将来若把经验自动回写进对应 skill 的「常见陷阱」段，标签即落点路由依据。

## L-20260617-030038-1 ｜适用阶段：plan
- **教训**：改「贯穿性概念」（阶段名、产物路径等散落多处的东西）前，先全仓 `grep` 旧表述，一次性圈定影响面再动手。
- **由来**：加 retrospect 阶段时，发现阶段定义散在 workflow-dag / state-schema / orchestrator / spec / AGENT / README / CLAUDE 七处，且 spec 还停留在旧的 plan→build→verify→report，差点漏改。
- **来源**：20260617-030038

## L-20260617-030038-2 ｜适用阶段：build
- **教训**：给 DAG 加阶段时，新阶段若是新终点，必须同步把原终点的 `next` 指向它，否则会出现两个终点，`validate.py` 的「恰 1 个终点」校验直接挂。
- **由来**：本次给 verify 之后加 retrospect，靠改前确认了这条 check 才一次过。
- **来源**：20260617-030038
