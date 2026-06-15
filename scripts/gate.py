#!/usr/bin/env python3
"""min-spec 质量门禁——三层职责分离的"执行层"。

它只做三件事：读 project.toml → 执行声明的命令 → 看退出码。
不认任何语言、不解析任何输出文本。退出码是唯一裁判（0=过，非零=挂）。

优先级：
  1. 项目根有 project.toml → 以 [gates] 为真相源
  2. 没有 → detect.py 探测兜底（临时用，不写盘）

执行顺序固定 build → test → lint；缺省的门禁跳过（不报错）；任一 fail 即停。
产出 gate card 到 docs/meta/gates/{run_id}-gate.md，并整体退出码=裁决。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import detect

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # 3.10 及更早
    tomllib = None

REPO_ROOT = Path(__file__).resolve().parents[1]
GATES_ORDER = ["build", "test", "lint"]
VERSION = "0.1.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def resolve_root() -> Path:
    env = os.environ.get("MINSPEC_PROJECT_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd()


def resolve_run_id() -> str:
    rid = os.environ.get("MINSPEC_RUN_ID")
    if rid:
        return rid
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _parse_gates_minimal(text: str) -> dict[str, str]:
    """极简 TOML 兜底解析器（Python < 3.11 无 tomllib 时用）。

    只解析 min-spec [gates] 段用到的 `key = "value"` / `key = 'value'` 语法，
    足够覆盖本项目，不追求完整 TOML 合规。
    """
    gates: dict[str, str] = {}
    in_gates = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            in_gates = line[1:-1].strip() == "gates"
            continue
        if not in_gates or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        # 去掉行尾注释（在引号外的 #）
        val = val.strip()
        if val and val[0] in "\"'":
            quote = val[0]
            end = val.find(quote, 1)
            val = val[1:end] if end != -1 else val[1:]
        else:
            val = val.split("#", 1)[0].strip()
        if key in GATES_ORDER and val.strip():
            gates[key] = val
    return gates


def load_gates(root: Path) -> tuple[dict[str, str], str]:
    """返回 (gates 命令字典, 来源标记)。toml 优先，缺失则探测兜底。"""
    toml_path = root / "project.toml"
    if toml_path.exists():
        try:
            if tomllib is not None:
                with toml_path.open("rb") as fh:
                    cfg = tomllib.load(fh)
                raw_gates = cfg.get("gates", {}) or {}
                gates = {k: v for k, v in raw_gates.items()
                         if k in GATES_ORDER and isinstance(v, str) and v.strip()}
            else:
                # Python < 3.11：用极简兜底解析器
                gates = _parse_gates_minimal(toml_path.read_text(encoding="utf-8"))
            return gates, "project.toml"
        except (OSError, ValueError):
            pass
    # 兜底：探测（不写盘）
    return detect.guess_gates(root), "auto-detect"


def emit_hook(root: Path, run_id: str, gate: str, status: str, exit_code) -> None:
    """非阻塞留痕：失败也不影响门禁本身。"""
    hook = REPO_ROOT / "scripts" / "report_hook.py"
    if not hook.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(hook), "emit",
             "--hook-id", "quality.gate_run",
             "--category", "quality_gate",
             "--event", "gate_run",
             "--source", "gate.py",
             "--status", status,
             "--run-id", run_id,
             "--phase", "verify",
             "--metadata", f"gate={gate}",
             "--metadata", f"exit_code={exit_code}",
             "--project-root", str(root),
             "--quiet"],
            cwd=str(root), timeout=15,
        )
    except Exception:
        return


def write_gate_card(root: Path, run_id: str, decision: str,
                    results: list[dict], blocking: dict | None) -> Path:
    rel = f"docs/meta/gates/{run_id}-gate.md"
    path = root / rel
    rows = "\n".join(
        f"| {r['gate']} | {r['status']} | {r.get('exit_code', '-')} | {r.get('cmd', '-')} |"
        for r in results
    )
    blocking_reason = (
        f"{blocking['gate']} gate exited {blocking['exit_code']}" if blocking else None
    )
    next_action = (
        f"修复 {blocking['gate']} 失败后重跑 scripts/gate.py" if blocking else None
    )
    contract = json.dumps({
        "decision": decision,
        "evidence_path": rel,
        "blocking_reason": blocking_reason,
        "next_action": next_action,
    }, ensure_ascii=False, indent=2)
    content = f"""---
gate_id: {run_id}
version: {VERSION}
phase: verify
generated_at: {utc_now_iso()}
decision: {decision}
---

## Gate Result

| gate | status | exit_code | cmd |
|---|---|---|---|
{rows}

## Output Contract
```json
{contract}
```
"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError:
        pass
    return path


def main() -> int:
    root = resolve_root()
    run_id = resolve_run_id()
    gates, source = load_gates(root)

    print(f"[min-spec gate] root={root} run_id={run_id} source={source}")

    results: list[dict] = []
    blocking: dict | None = None

    for name in GATES_ORDER:
        cmd = gates.get(name)
        if not cmd:
            results.append({"gate": name, "status": "skipped", "exit_code": "-", "cmd": "-"})
            continue

        print(f"\n[gate:{name}] $ {cmd}")
        # 退出码是唯一裁判：不捕获输出，直通终端；只取 returncode。
        proc = subprocess.run(cmd, shell=True, cwd=str(root))
        status = "pass" if proc.returncode == 0 else "fail"
        result = {"gate": name, "status": status, "exit_code": proc.returncode, "cmd": cmd}
        results.append(result)
        emit_hook(root, run_id, name, status, proc.returncode)

        if status == "fail":
            blocking = result
            break  # 快速失败

    decision = "block" if blocking else (
        "pass" if any(r["status"] == "pass" for r in results) else "skip"
    )
    card = write_gate_card(root, run_id, decision, results, blocking)

    card_disp = card.relative_to(root) if card.is_relative_to(root) else card
    print(f"\n[min-spec gate] decision={decision}  card={card_disp}")
    return 0 if decision in ("pass", "skip") else 1


if __name__ == "__main__":
    raise SystemExit(main())
