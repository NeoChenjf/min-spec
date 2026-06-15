# min-spec Subagent 角色合同

从 hic-spec 的 6 个企业级角色精简继承而来的 3 个本地角色。它们是**角色约定**，不代表已全局安装为 Agent；可由人或 AI 在对应阶段扮演。

## 铁律

每个角色都**必须产出证据路径**——不写正式结论文件，而是各发一条事件到 `docs/meta/sessions/{run_id}.jsonl`（用 `scripts/report_hook.py emit`），`--evidence` 带上它检查过的文件清单。**门禁（verify 阶段）未通过前，不得关闭本次运行。**

## 角色表

| 角色 | 对应阶段 | 职责 | 必须产出的证据 |
|---|---|---|---|
| `impact-analyzer` | build 前 | 改动前分析影响面 + 跨文件一致性：这次改动会波及哪些文件/模块/调用方；改了接口要同步改调用方 | event=`impact_analyzed`，evidence 列受影响文件 |
| `scope-guard` | build 后、提交前 | 识别"超出本次需求范围"的改动（AI 辅助开发最易顺手改一堆无关文件） | event=`scope_checked`，evidence 列 out-of-scope 文件 |
| `plan-reviewer` | plan | 评审方案是否合理（对应 `workflow-dag.json` 里 plan 的 `mandatory_review`） | event=`plan_reviewed`，evidence 指向 plan_note |

## 精简来源

| min-spec 角色 | 源（hic-agent-harness） | 处理 |
|---|---|---|
| `impact-analyzer` | `hic-impact-analyzer` + `hic-consistency-checker` | 合并 |
| `scope-guard` | `hic-scope-guard` | 保留 |
| `plan-reviewer` | `hic-strategy-reviewer` | 改名 |
| —（已砍） | `hic-efficiency-collector` | 企业级耗时/token 度量，个人项目不需要 |
| —（已砍） | `hic-project-router` | 需求→appkey/repo 映射，单仓项目无意义 |

## 发证据示例

```bash
python3 scripts/report_hook.py emit \
  --hook-id agent.scope_guard \
  --category pipeline_stage \
  --event scope_checked \
  --status pass \
  --evidence "src/foo.ts,src/bar.ts" \
  --metadata role=scope-guard
```
