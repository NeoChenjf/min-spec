#!/usr/bin/env python3
"""min-spec harness 结构校验器。

只做可审计的结构检查，不硬编码任何业务结论。

检查项：
  1. 各契约文件 / 执行手册 / skill / 脚本 / git hook 存在
     （含 harness/orchestrator.md、skill/ 四个 SKILL.md）
  2. workflow-dag.json 自洽（每 stage 字段齐全、next 指向存在、恰一终点）
  3. state-schema.json 的 current_stage 枚举 == DAG 的 stage 列表
  4. reporting-hooks.json 三类齐全、git.pre_commit=strict 其余 never
  5. gate-card.schema.json 必填字段与 gate.py 实际写出的字段一致（防漂移）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS = REPO_ROOT / "harness"

REQUIRED_FILES = [
    "harness/spec.md",
    "harness/AGENT.md",
    "harness/orchestrator.md",
    "harness/plan-note-template.md",
    "harness/workflow-dag.json",
    "harness/state-schema.json",
    "harness/gate-card.schema.json",
    "harness/reporting-hooks.json",
    "harness/agents/README.md",
    "skill/clarify/SKILL.md",
    "skill/impl-plan/SKILL.md",
    "skill/impl/SKILL.md",
    "skill/review/SKILL.md",
    "skill/retro/SKILL.md",
    "scripts/gate.py",
    "scripts/detect.py",
    "scripts/report_hook.py",
    "scripts/init.py",
    "scripts/validate.py",
    ".githooks/pre-commit",
]


def load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        errors.append(f"无法解析 JSON: {path.relative_to(REPO_ROOT)} ({e})")
        return None


def check_files(errors: list[str]) -> None:
    for rel in REQUIRED_FILES:
        if not (REPO_ROOT / rel).exists():
            errors.append(f"缺少必需文件: {rel}")


def check_dag(errors: list[str]) -> list[str]:
    dag = load_json(HARNESS / "workflow-dag.json", errors)
    if not dag:
        return []
    stages = dag.get("stages", {})
    if not stages:
        errors.append("workflow-dag.json: stages 为空")
        return []
    terminals = 0
    for name, st in stages.items():
        for field in ("checkpoint", "required_outputs", "writes", "next"):
            if field not in st:
                errors.append(f"DAG stage '{name}' 缺字段 {field}")
        nxt = st.get("next", [])
        if not nxt:
            terminals += 1
        for target in nxt:
            if target not in stages:
                errors.append(f"DAG stage '{name}' 的 next 指向不存在的 '{target}'")
    if terminals != 1:
        errors.append(f"DAG 应恰有 1 个终点 stage（next=[]），实际 {terminals} 个")
    return list(stages.keys())


def check_state_schema(errors: list[str], dag_stages: list[str]) -> None:
    schema = load_json(HARNESS / "state-schema.json", errors)
    if not schema:
        return
    for key in ("run_id", "status", "current_stage", "stages"):
        if key not in schema.get("required", []):
            errors.append(f"state-schema.json: required 缺 {key}")
    enum = schema.get("properties", {}).get("current_stage", {}).get("enum", [])
    if dag_stages and set(enum) != set(dag_stages):
        errors.append(
            f"state-schema current_stage 枚举 {sorted(enum)} 与 DAG stages {sorted(dag_stages)} 不一致")


def check_hooks(errors: list[str]) -> None:
    reg = load_json(HARNESS / "reporting-hooks.json", errors)
    if not reg:
        return
    cats = reg.get("categories", {})
    for needed in ("git_lifecycle", "pipeline_stage", "quality_gate"):
        if needed not in cats:
            errors.append(f"reporting-hooks.json 缺分类 {needed}")
    for cat, body in cats.items():
        for hook in body.get("hooks", []):
            hid = hook.get("id", "?")
            blocking = hook.get("blocking")
            if hid == "git.pre_commit":
                if blocking != "strict":
                    errors.append(f"hook {hid} 的 blocking 应为 strict，实际 {blocking}")
            else:
                if blocking != "never":
                    errors.append(f"hook {hid} 的 blocking 应为 never，实际 {blocking}")


def check_gate_card_schema(errors: list[str]) -> None:
    schema = load_json(HARNESS / "gate-card.schema.json", errors)
    if not schema:
        return
    fm = schema.get("properties", {}).get("frontmatter", {}).get("required", [])
    # 必须与 gate.py 写出的 frontmatter 一致
    expected = {"gate_id", "version", "phase", "generated_at", "decision"}
    if set(fm) != expected:
        errors.append(
            f"gate-card.schema frontmatter.required {sorted(fm)} 与 gate.py 写出字段 {sorted(expected)} 不一致")


def main() -> int:
    errors: list[str] = []
    check_files(errors)
    if errors:  # 文件都不全，后续 JSON 检查没意义
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    dag_stages = check_dag(errors)
    check_state_schema(errors, dag_stages)
    check_hooks(errors)
    check_gate_card_schema(errors)

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print("min-spec 校验通过：结构自洽。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
