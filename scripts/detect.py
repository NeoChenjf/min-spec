#!/usr/bin/env python3
"""项目类型自动探测：扫描标志文件，猜出 build/test/lint 命令。

它是兜底机制，不是真相源——真相源永远是 project.toml。
被 gate.py（toml 缺失时临时兜底）和 init.py（生成 toml 草稿）复用。

探测命中即返回该语言的命令字典；未命中返回空 dict（全跳过、不报错）。
对 package.json 会读取实际存在的 scripts 字段裁剪，避免声明不存在的命令。
"""

from __future__ import annotations

import json
from pathlib import Path


def _node_gates(root: Path) -> dict[str, str]:
    """Node：按 package.json 里实际有的 scripts 裁剪。"""
    gates: dict[str, str] = {}
    try:
        pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
        scripts = pkg.get("scripts", {}) or {}
    except (OSError, json.JSONDecodeError):
        scripts = {}
    if "build" in scripts:
        gates["build"] = "npm run build"
    if "test" in scripts:
        gates["test"] = "npm test"
    if "lint" in scripts:
        gates["lint"] = "npm run lint"
    # 连 scripts 都没有时，至少给一个 test 占位（npm test 缺省会非零，提醒补声明）
    return gates or {"test": "npm test"}


# 探测表：(标志文件, 命令字典 或 生成函数)。按顺序匹配，命中即返回。
_RULES: list[tuple[str, object]] = [
    ("package.json", _node_gates),
    ("pyproject.toml", {"test": "pytest -q", "lint": "ruff check ."}),
    ("setup.py", {"test": "pytest -q"}),
    ("pom.xml", {"build": "mvn -q compile", "test": "mvn -q test"}),
    ("build.gradle", {"build": "./gradlew build -q", "test": "./gradlew test -q"}),
    ("go.mod", {"build": "go build ./...", "test": "go test ./..."}),
    ("Cargo.toml", {"build": "cargo build", "test": "cargo test", "lint": "cargo clippy"}),
]


def guess_gates(root: Path) -> dict[str, str]:
    """返回探测到的 gates 命令字典；未命中返回 {}。"""
    for marker, spec in _RULES:
        if (root / marker).exists():
            return spec(root) if callable(spec) else dict(spec)
    return {}


def guess_language(root: Path) -> str:
    for marker, _ in _RULES:
        if (root / marker).exists():
            return marker
    return ""


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    print(json.dumps({
        "root": str(target),
        "marker": guess_language(target),
        "gates": guess_gates(target),
    }, ensure_ascii=False, indent=2))
