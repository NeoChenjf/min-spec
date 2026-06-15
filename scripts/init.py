#!/usr/bin/env python3
"""min-spec 初始化：为当前项目生成 project.toml 草稿 + state.json 初值。

跑一次探测（detect.py），把猜到的 build/test/lint 命令写进 project.toml，
每条带 `# 自动探测，请确认` 注释——之后一律以这份声明为真相源。
已存在 project.toml 时默认不覆盖（除非 --force）。
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import detect

GATES_ORDER = ["build", "test", "lint"]


def resolve_root(arg: str | None) -> Path:
    if arg:
        return Path(arg).expanduser().resolve()
    env = os.environ.get("MINSPEC_PROJECT_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd()


def render_toml(name: str, language: str, gates: dict[str, str]) -> str:
    lines = [
        "# project.toml —— min-spec 真相源。门禁只读这里，不认语言。",
        "# 换语言/换命令只改这一个文件。每条命令只看退出码（0=过，非零=挂）。",
        "",
        "[project]",
        f'name = "{name}"',
    ]
    if language:
        lines.append(f'language = "{language}"  # 自动探测，纯标注，门禁不依赖')
    lines += ["", "[gates]",
              "# 缺省的门禁会被跳过（不报错）。下面是自动探测结果，请确认后删掉本行注释。"]
    if gates:
        for key in GATES_ORDER:
            if key in gates:
                lines.append(f'{key} = "{gates[key]}"  # 自动探测，请确认')
    else:
        lines += ['# 未探测到已知项目类型，请手动声明，例如：',
                  '# test = "your-test-command"']
    return "\n".join(lines) + "\n"


def write_state(root: Path) -> Path:
    path = root / ".harness" / "state.json"
    state = {
        "schema": "min-spec-state-v1",
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
        "status": "initialized",
        "current_stage": "plan",
        "stages": {},
        "gate": None,
        "artifacts": [],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(prog="init", description="生成 project.toml 草稿 + state 初值")
    ap.add_argument("--root", default="", help="目标项目根，默认 cwd")
    ap.add_argument("--force", action="store_true", help="已存在 project.toml 时也覆盖")
    args = ap.parse_args()

    root = resolve_root(args.root)
    toml_path = root / "project.toml"
    gates = detect.guess_gates(root)
    language = detect.guess_language(root)
    name = root.name

    if toml_path.exists() and not args.force:
        print(f"[init] 已存在 {toml_path}，未覆盖（加 --force 可覆盖）。探测结果如下供参考：")
        print(json.dumps({"marker": language, "gates": gates}, ensure_ascii=False, indent=2))
    else:
        toml_path.write_text(render_toml(name, language, gates), encoding="utf-8")
        print(f"[init] 已生成 {toml_path}（探测来源：{language or '未命中'}）")
        print("[init] ⚠️ 请人工确认 [gates] 命令，确认后删掉 '# 自动探测，请确认' 注释。")

    state_path = write_state(root)
    print(f"[init] 已写入 {state_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
